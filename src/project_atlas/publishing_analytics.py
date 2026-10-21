"""YouTube Analytics reports for performance checkpoints (Option B; disabled by default).

Pure functions only: checkpoint date windows, report parsing and maturity. The service records
YouTube's values exactly as returned into the existing ``performance_snapshots``; nothing here
derives new metrics.

YouTube Analytics reports whole calendar days in US Pacific time. The checkpoints map to day
windows starting on the publication's Pacific date: 24h -> +1 day, 72h -> +3, 7d -> +7,
28d -> +28 (end date inclusive). A window is due once its end date is complete in Pacific
time, and stays ``immature`` until a further data-lag allowance has passed.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from math import isfinite
from typing import Any

ANALYTICS_METRICS: tuple[str, ...] = (
    "views",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "averageViewPercentage",
    "likes",
    "comments",
    "shares",
    "subscribersGained",
    "subscribersLost",
)
CHECKPOINT_DAYS = {"24h": 1, "72h": 3, "7d": 7, "28d": 28}
CHECKPOINTS = tuple(CHECKPOINT_DAYS)
REPORT_TIMEZONE = "America/Los_Angeles"
# YouTube Analytics data typically lags by up to about three days.
ANALYTICS_DATA_LAG = timedelta(days=3)
# Analytics data may be kept only while a video-existence check is this recent.
EXISTENCE_CHECK_MAX_AGE = timedelta(days=30)
RETENTION_DIMENSION = "elapsedVideoTimeRatio"
RETENTION_METRIC = "audienceWatchRatio"


class AnalyticsReportError(ValueError):
    """A report that is not in the expected shape; nothing is recorded from it."""


def _nth_sunday(year: int, month: int, n: int) -> date:
    first = date(year, month, 1)
    first_sunday = first + timedelta(days=(6 - first.weekday()) % 7)
    return first_sunday + timedelta(weeks=n - 1)


def pacific_offset(moment: datetime) -> timedelta:
    """US Pacific UTC offset under the US daylight-saving rule in force since 2007.

    PDT (UTC-7) from 02:00 local on the second Sunday of March to 02:00 local on the first
    Sunday of November; PST (UTC-8) otherwise. No tz database is needed.
    """

    utc = moment.astimezone(UTC)
    start = datetime.combine(_nth_sunday(utc.year, 3, 2), datetime.min.time(), UTC) + timedelta(
        hours=10
    )  # 02:00 PST = 10:00 UTC
    end = datetime.combine(_nth_sunday(utc.year, 11, 1), datetime.min.time(), UTC) + timedelta(
        hours=9
    )  # 02:00 PDT = 09:00 UTC
    return timedelta(hours=-7) if start <= utc < end else timedelta(hours=-8)


def pacific_date(moment: datetime) -> date:
    if moment.tzinfo is None:
        raise ValueError("A timezone-aware instant is required.")
    return (moment.astimezone(UTC) + pacific_offset(moment)).date()


def pacific_midnight_utc(day: date) -> datetime:
    """The UTC instant of 00:00 Pacific on ``day``."""

    naive = datetime.combine(day, datetime.min.time())
    guess = naive.replace(tzinfo=UTC) + timedelta(hours=8)
    return naive.replace(tzinfo=UTC) - pacific_offset(guess)


def publication_date(public_at: str) -> date:
    """The Pacific publication date; a day-precision attestation is taken as that date."""

    if len(public_at) == 10:
        return date.fromisoformat(public_at)
    moment = datetime.fromisoformat(public_at.replace("Z", "+00:00"))
    return pacific_date(moment)


def checkpoint_window(public_at: str, checkpoint: str) -> tuple[date, date]:
    if checkpoint not in CHECKPOINT_DAYS:
        raise ValueError("Unknown performance checkpoint.")
    start = publication_date(public_at)
    return start, start + timedelta(days=CHECKPOINT_DAYS[checkpoint])


def window_due_at(end: date) -> datetime:
    """A window is complete once its (inclusive) end date has ended in Pacific time."""

    return pacific_midnight_utc(end + timedelta(days=1))


def _columns(payload: Any) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("columnHeaders"), list):
        raise AnalyticsReportError("Analytics report has no column headers.")
    names = []
    for header in payload["columnHeaders"]:
        if not isinstance(header, dict) or not isinstance(header.get("name"), str):
            raise AnalyticsReportError("Analytics column header is malformed.")
        names.append(header["name"])
    if len(set(names)) != len(names):
        raise AnalyticsReportError("Analytics column headers repeat.")
    return names


def _rows(payload: dict[str, Any], width: int) -> list[list[Any]]:
    rows = payload.get("rows") or []
    if not isinstance(rows, list) or any(
        not isinstance(row, list) or len(row) != width for row in rows
    ):
        raise AnalyticsReportError("Analytics rows do not match their column headers.")
    return rows


def parse_metrics_report(
    payload: Any, requested: tuple[str, ...]
) -> tuple[dict[str, Any], dict[str, str], dict[str, str], list[str]]:
    """Values by returned column name (never by position); every requested metric accounted for."""

    columns = _columns(payload)
    rows = _rows(payload, len(columns))
    if len(rows) > 1:
        raise AnalyticsReportError("A per-video total report must have at most one row.")
    row = dict(zip(columns, rows[0], strict=True)) if rows else {}
    metrics: dict[str, Any] = {}
    availability: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for name in requested:
        value = row.get(name)
        if not rows:
            availability[name], reasons[name] = "not_returned", "no-report-rows"
        elif name not in row:
            availability[name], reasons[name] = "not_returned", "column-not-returned"
        elif (
            value is None
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            availability[name], reasons[name] = "not_returned", "value-not-numeric"
        else:
            metrics[name] = value
            availability[name] = "available"
    return metrics, availability, reasons, columns


def parse_retention_report(payload: Any) -> dict[str, Any]:
    columns = _columns(payload)
    if RETENTION_DIMENSION not in columns or RETENTION_METRIC not in columns:
        return {"availability": "unavailable", "reason": "retention-columns-not-returned"}
    rows = _rows(payload, len(columns))
    if not rows:
        return {"availability": "unavailable", "reason": "no-retention-rows"}
    points = []
    for row in rows:
        values = dict(zip(columns, row, strict=True))
        points.append(
            {
                "elapsedVideoTimeRatio": values[RETENTION_DIMENSION],
                "audienceWatchRatio": values[RETENTION_METRIC],
            }
        )
    return {"availability": "available", "points": points}


def maturity(
    now: datetime, due_at: datetime, availability: dict[str, str], retention: dict[str, Any]
) -> str:
    """Never mature before the window and the data lag have passed, nor with anything missing."""

    if now < due_at + ANALYTICS_DATA_LAG:
        return "immature"
    if any(state != "available" for state in availability.values()):
        return "partial"
    if retention.get("availability") != "available":
        return "partial"
    return "mature"
