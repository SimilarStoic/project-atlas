"""Founder spend control: every billable image dispatch is recorded first and needs a step
authorization; nothing here reaches a provider (fake generator, isolated network)."""

from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from project_atlas.production import (
    ACQUISITION_DISPATCH,
    SPEND_AUTHORIZATION,
    ProductionLifecycleError,
)
from tests.test_production_lifecycle import (
    ValidFakeImageGenerator,
    _request,
    _server,
    _spec_of,
    realistic_source_png,
    sized_png,
    transcription,  # noqa: F401  (autouse: no test reaches the real recognizer)
)
from tests.test_web import media_runtime_or_skip, request_json

pytestmark = pytest.mark.spend_gate


def _terms(calls: int, stop: bool = False) -> dict:
    return {
        "authorized_by": "founder",
        "max_image_calls": calls,
        "stop_on_technical_rejection": stop,
        "reason": "test step",
    }


def post_json(server, path: str, payload: dict) -> tuple[dict, int]:
    """Post one JSON body and return (body, status) for success and error responses alike."""

    request = Request(
        f"http://{server.server_address[0]}:{server.server_address[1]}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        return request_json(server, request)
    except HTTPError as error:
        return json.loads(error.read()), error.code


def _dispatches(server, run_id: str) -> list:
    return server.repository.list_production_evidence(run_id, ACQUISITION_DISPATCH)


def test_start_without_authorization_dispatches_nothing_and_resume_needs_one(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(server, tmp_path, "spend-none")
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 422, started
        assert "spend authorization" in started["error"]
        assert generator.inputs == [] and _dispatches(server, "spend-none") == []
        assert started["production"]["spend"]["image_calls"] == 0
        # Resume without an authorization is refused the same way, still with no dispatch.
        resumed, status = post_json(server, "/api/v2/productions/spend-none/resume", {})
        assert status == 422 and generator.inputs == []
        # Through the per-request HTTP service: authorize, then resume acquires.
        authorized, status = post_json(
            server,
            "/api/v2/productions/spend-none/spend-authorization",
            {"evidence": _terms(2)},
        )
        assert status == 200, authorized
        assert authorized["production"]["spend"]["next_step_authorization"]["max_image_calls"] == 2
        resumed, status = post_json(server, "/api/v2/productions/spend-none/resume", {})
        assert status == 200 and resumed["production"]["status"] == "acquisition_review_pending"
        dispatches = _dispatches(server, "spend-none")
        assert len(generator.inputs) == len(dispatches) == 2
        acquisitions = server.repository.list_production_evidence("spend-none", "acquisition")
        assert sorted(item.payload["dispatch_id"] for item in acquisitions) == sorted(
            item.id for item in dispatches
        )
        assert resumed["production"]["spend"] == {
            "image_calls": 2,
            "image_call_ceiling": 2,
            "next_step_authorization": None,  # consumed by the step that used it
        }
    finally:
        server.server_close()


def test_a_step_authorization_caps_dispatches_and_is_never_reused(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    service = server.production_service
    try:
        request, _keys = _request(server, tmp_path, "spend-cap", image_calls=5)
        with pytest.raises(ProductionLifecycleError, match="allows 1 image call"):
            service.start(request | {"spend_authorization": _terms(1)})
        assert len(generator.inputs) == len(_dispatches(server, "spend-cap")) == 1
        # The used authorization is bound to its step: resuming without a new one spends nothing.
        with pytest.raises(ProductionLifecycleError, match="needs a founder spend authorization"):
            service.resume("spend-cap")
        assert len(generator.inputs) == 1
        service.authorize_spend("spend-cap", _terms(1))
        status = service.resume("spend-cap")
        assert status["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == len(_dispatches(server, "spend-cap")) == 2
        # The spend authorization never enters the frozen request or its digest.
        run = server.repository.get_production_run("spend-cap")
        assert "spend_authorization" not in run.request
        assert service.start(request | {"spend_authorization": _terms(3)})["id"] == "spend-cap"
        assert (
            len(server.repository.list_production_evidence("spend-cap", SPEND_AUTHORIZATION)) == 2
        )
    finally:
        server.server_close()


@pytest.mark.parametrize("stop", [True, False])
def test_stop_on_technical_rejection_blocks_the_automatic_retry(tmp_path, stop) -> None:
    runtime = media_runtime_or_skip()
    realistic = realistic_source_png(runtime, tmp_path)
    square = sized_png(runtime, tmp_path, 1080, 1080)
    generator = ValidFakeImageGenerator(sequence=[realistic, square, realistic])
    server = _server(tmp_path, generator, runtime)
    service = server.production_service
    run_id = f"spend-stop-{stop}".lower()
    try:
        request, _keys = _request(server, tmp_path, run_id, image_calls=3)
        if stop:
            with pytest.raises(ProductionLifecycleError, match="stops at the first rejection"):
                service.start(request | {"spend_authorization": _terms(3, stop=True)})
            # The rejected call was dispatched and counted; no retry followed it.
            assert [_spec_of(item) for item in generator.inputs] == [
                f"{run_id}-spec-1",
                f"{run_id}-spec-2",
            ]
            assert service.status(run_id)["spend"]["image_calls"] == 2
        else:
            status = service.start(request | {"spend_authorization": _terms(3)})
            assert status["status"] == "acquisition_review_pending"
            assert len(generator.inputs) == len(_dispatches(server, run_id)) == 3
    finally:
        server.server_close()


def test_a_call_that_raises_after_the_provider_returned_still_counts(tmp_path, monkeypatch):
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    service = server.production_service
    try:
        request, _keys = _request(server, tmp_path, "spend-raise", image_calls=2)

        def broken_inspection(_self, _asset_id):
            raise OSError("probe failed after the provider returned")

        monkeypatch.setattr(
            "project_atlas.production.ManagedAssetSceneAdapter.source_dimensions",
            broken_inspection,
        )
        with pytest.raises(ProductionLifecycleError, match="probe failed"):
            service.start(request | {"spend_authorization": _terms(2)})
        # No acquisition evidence was written, but the dispatch record counts the paid call.
        assert server.repository.list_production_evidence("spend-raise", "acquisition") == []
        assert len(generator.inputs) == 1
        assert service.status("spend-raise")["spend"]["image_calls"] == 1
        monkeypatch.undo()
        service.authorize_spend("spend-raise", _terms(5))
        # The ceiling (2) still holds: only one more call fits, whatever the authorization says.
        with pytest.raises(ProductionLifecycleError, match="ceiling of 2"):
            service.resume("spend-raise")
        assert len(generator.inputs) == 2
    finally:
        server.server_close()


def test_invalid_authorizations_are_refused_before_a_run_exists(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(server, tmp_path, "spend-invalid")
        for bad in (
            {"authorized_by": "founder", "max_image_calls": 0},
            _terms(2) | {"max_image_calls": "2"},
            _terms(2) | {"stop_on_technical_rejection": "yes"},
            _terms(2) | {"extra": 1},
            {k: v for k, v in _terms(2).items() if k != "reason"},
        ):
            response, status = post_json(
                server, "/api/v2/productions", request | {"spend_authorization": bad}
            )
            assert status == 400, response
        with pytest.raises(KeyError):
            server.repository.get_production_run("spend-invalid")
        assert generator.inputs == []
    finally:
        server.server_close()


def test_runs_recorded_before_dispatch_records_keep_their_call_count(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    service = server.production_service
    try:
        request, _keys = _request(server, tmp_path, "spend-legacy", image_calls=4)
        service.start(request | {"spend_authorization": _terms(2)})
        assert service._image_calls("spend-legacy") == 2
        # A historical acquisition record (no dispatch_id) still counts as one call.
        [first, *_rest] = server.repository.list_production_evidence("spend-legacy", "acquisition")
        server.repository.create_production_evidence(
            "spend-legacy:acquisition:attempt:legacy",
            "spend-legacy",
            "acquisition",
            {k: v for k, v in first.payload.items() if k not in {"dispatch_id", "asset_id"}},
            generation_execution_id=first.generation_execution_id,
        )
        assert service._image_calls("spend-legacy") == 3
    finally:
        server.server_close()
