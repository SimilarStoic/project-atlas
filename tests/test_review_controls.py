"""Supported review controls: intentionally absent fixtures and prompt revision before
(re)generation. Provider-free: fake generator, isolated network."""

from __future__ import annotations

from hashlib import sha256

import pytest

from project_atlas.production import SPEC_REVISION, ProductionLifecycleError, ProductionRequestError
from tests.test_production_lifecycle import (
    ValidFakeImageGenerator,
    _home_authority,
    _home_request,
    _request,
    _review,
    _server,
    _spec_of,
    _valid_pass,
    realistic_source_png,
    transcription,  # noqa: F401  (autouse: no test reaches the real recognizer)
)
from tests.test_web import media_runtime_or_skip


def test_intentionally_absent_fixture_passes_only_with_a_note(tmp_path) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    service, repository = server.production_service, server.repository
    try:
        request, keys = _home_request(server, tmp_path, "absent", narration_authorized=False)
        _home_authority(server, request["timeline"][0]["scene_id"], "v1")
        service.start(request)
        start_key, finish_key = keys
        unnoted = _valid_pass(server, "absent", start_key)
        unnoted["evidence"]["fixtures"]["table"] = "intentionally_absent"
        with pytest.raises(ProductionRequestError, match="needs a fixture_notes entry"):
            service.review_acquisition(
                "absent", [unnoted, _valid_pass(server, "absent", finish_key)]
            )
        blank = _valid_pass(server, "absent", start_key)
        blank["evidence"]["fixtures"]["table"] = "intentionally_absent"
        blank["evidence"]["fixture_notes"] = {"table": "  "}
        with pytest.raises(ProductionRequestError, match="needs a fixture_notes entry"):
            service.review_acquisition("absent", [blank, _valid_pass(server, "absent", finish_key)])
        assert not [r for r in repository.list_production_qa_reviews("absent")]
        noted = _valid_pass(server, "absent", start_key)
        noted["evidence"]["fixtures"]["table"] = "intentionally_absent"
        noted["evidence"]["fixture_notes"] = {"table": "Kept clear for the beat's props."}
        with pytest.raises(ProductionLifecycleError, match="Narration is not authorized"):
            service.review_acquisition("absent", [noted, _valid_pass(server, "absent", finish_key)])
        recorded = [
            r for r in repository.list_production_qa_reviews("absent") if r.scope == "acquisition"
        ]
        assert len(recorded) == 2 and {r.outcome for r in recorded} == {"passed"}
        [attested] = [r for r in recorded if r.evidence["fixtures"]["table"] != "unchanged"]
        assert attested.evidence["fixtures"]["table"] == "intentionally_absent"
        assert attested.evidence["fixture_notes"]["table"]
    finally:
        server.server_close()


def test_a_missing_or_rejected_variants_prompt_is_revised_with_provenance(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    service, repository = server.production_service, server.repository
    terms = {"authorized_by": "founder", "stop_on_technical_rejection": True, "reason": "test"}
    try:
        request, keys = _request(server, tmp_path, "revise", image_calls=4)
        # One authorized call: the first variant is acquired, the second is still missing.
        with pytest.raises(ProductionLifecycleError, match="allows 1 image call"):
            service.start(request | {"spend_authorization": terms | {"max_image_calls": 1}})

        def revise(spec_id, prompt):
            return service.revise_asset_spec(
                "revise",
                {
                    "asset_spec_id": spec_id,
                    "generation_prompt": prompt,
                    "authorized_by": "founder",
                    "reason": "heavier outlines",
                },
            )

        with pytest.raises(ProductionRequestError, match="passed or awaiting review"):
            revise("revise-spec-1", "Draw state 1 with heavy outlines.")
        with pytest.raises(ProductionRequestError, match="not a variant of this run"):
            revise("someone-elses-spec", "x")
        old = repository.get_asset_spec("revise-spec-2").generation_prompt
        with pytest.raises(ProductionRequestError, match="does not change"):
            revise("revise-spec-2", old)
        revise("revise-spec-2", "Draw state 2 with extra-heavy thick black outlines.")
        [record] = repository.list_production_evidence("revise", SPEC_REVISION)
        assert record.payload["previous_prompt"] == old
        assert record.payload["previous_prompt_sha256"] == sha256(old.encode()).hexdigest()
        assert record.payload["variants"] == ["/".join(keys[1])]
        spec = repository.get_asset_spec("revise-spec-2")
        assert (
            record.payload["prompt_sha256"] == sha256(spec.generation_prompt.encode()).hexdigest()
        )
        # The revised prompt is what the next authorized step generates.
        service.authorize_spend("revise", terms | {"max_image_calls": 1})
        assert service.resume("revise")["status"] == "acquisition_review_pending"
        assert _spec_of(generator.inputs[-1]) == "revise-spec-2"
        assert "extra-heavy thick black outlines" in generator.inputs[-1].prompt
        # After a failed review, the rejected variant's prompt may be revised again.
        reviews = _review([keys[0]], "passed", server, "revise") + _review(
            [keys[1]], "failed", server, "revise"
        )
        service.review_acquisition("revise", reviews)
        revise("revise-spec-2", "Draw state 2 plainly, extra-heavy outlines, no text.")
        assert len(repository.list_production_evidence("revise", SPEC_REVISION)) == 2
    finally:
        server.server_close()
