from collections.abc import Iterable
from datetime import datetime
import hashlib
import re

from sqlmodel import Session, select

from src.db.models import Job, RunLog
from src.sources.base import RawJob

_CHUNK_SIZE = 400


def _normalize_for_hash(value: str) -> str:
    lowered = value.lower()
    without_punctuation = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(without_punctuation.split())


def compute_dedup_hash(title: str, company: str) -> str:
    normalized = f"{_normalize_for_hash(title)}|{_normalize_for_hash(company)}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]


def _fetch_existing_values(session: Session, column, candidates: set[str]) -> set[str]:
    if not candidates:
        return set()
    existing: set[str] = set()
    for chunk in _chunked(list(candidates), _CHUNK_SIZE):
        rows = session.exec(select(column).where(column.in_(chunk))).all()
        existing.update(rows)
    return existing


def save_raw_jobs(session: Session, raw_jobs: list[RawJob]) -> tuple[int, int]:
    if not raw_jobs:
        return 0, 0

    prepared: list[tuple[RawJob, str, str]] = [
        (raw, compute_dedup_hash(raw.title, raw.company), raw.url.strip())
        for raw in raw_jobs
    ]

    candidate_hashes = {dedup_hash for _, dedup_hash, _ in prepared}
    candidate_urls = {url for _, _, url in prepared if url}

    seen_hashes = _fetch_existing_values(session, Job.dedup_hash, candidate_hashes)
    seen_urls = _fetch_existing_values(session, Job.url, candidate_urls)

    new_jobs: list[Job] = []
    duplicated_count = 0

    for raw, dedup_hash, clean_url in prepared:
        if dedup_hash in seen_hashes or (clean_url and clean_url in seen_urls):
            duplicated_count += 1
            continue

        seen_hashes.add(dedup_hash)
        if clean_url:
            seen_urls.add(clean_url)

        new_jobs.append(
            Job(
                dedup_hash=dedup_hash,
                url=clean_url,
                source=raw.source,
                external_id=raw.external_id,
                title=raw.title.strip(),
                company=raw.company.strip(),
                location_raw=raw.location_raw.strip(),
                description_text=raw.description_text,
                salary_raw=raw.salary_raw,
                published_at=raw.published_at,
                status="new",
                evaluation_status="pending",
            )
        )

    if new_jobs:
        session.add_all(new_jobs)
        session.commit()

    return len(new_jobs), duplicated_count


def save_run_log(
    session: Session,
    *,
    started_at: datetime,
    finished_at: datetime | None,
    jobs_fetched: int,
    jobs_inserted: int,
    jobs_duplicated: int,
    notes: str | None = None,
) -> RunLog:
    run_log = RunLog(
        started_at=started_at,
        finished_at=finished_at,
        jobs_fetched=jobs_fetched,
        jobs_inserted=jobs_inserted,
        jobs_duplicated=jobs_duplicated,
        notes=notes,
    )
    session.add(run_log)
    session.commit()
    session.refresh(run_log)
    return run_log
