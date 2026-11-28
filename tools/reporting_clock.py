"""Reporting calendar (KST) separated from source API date windows (UTC).

The GitHub Actions runner is UTC. The scheduled daily 06:10 KST collection
executes at 21:10 UTC on the *previous* calendar day. "New today" must
therefore use KST, while authoritative bid deadlines and official source
search windows retain their original UTC/source-time semantics.

No locale-wide conversion of source deadlines happens in this module.
"""
import datetime as dt

KST = dt.timezone(dt.timedelta(hours=9))
UTC = dt.timezone.utc


def reporting_day(now=None):
    now = now if now is not None else dt.datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("reporting_day requires an aware instant")
    return now.astimezone(KST).date()


def utc_source_day(now=None):
    now = now if now is not None else dt.datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("utc_source_day requires an aware instant")
    return now.astimezone(UTC).date()
