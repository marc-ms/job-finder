from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import time
from typing import Any

import httpx

from src.sources.base import BaseSource, RawJob, clean_html

DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_HEADERS = {
    "User-Agent": "job-finder/0.1 (Python httpx; personal job aggregator)",
    "Accept": "application/json",
}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None

    iso_candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _clean_text(value: Any) -> str:
    if not value:
        return ""
    return html.unescape(str(value)).strip()


class JobicySource(BaseSource):
    name = "jobicy"
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"
    QUERIES: tuple[dict[str, str | int], ...] = (
        {"geo": "europe", "industry": "copywriting", "count": 30},
        {"geo": "europe", "industry": "marketing", "count": 30},
        {"geo": "anywhere", "industry": "copywriting", "count": 30},
    )
    REQUEST_DELAY_SECONDS = 2.0

    def __init__(self, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    @staticmethod
    def _format_salary(item: dict[str, Any]) -> str | None:
        salary_min = item.get("salaryMin") or item.get("annualSalaryMin")
        salary_max = item.get("salaryMax") or item.get("annualSalaryMax")
        currency = _clean_text(item.get("salaryCurrency"))
        period = _clean_text(item.get("salaryPeriod"))

        if salary_min is None and salary_max is None:
            return None

        parts: list[str] = []
        if salary_min is not None and salary_max is not None:
            parts.append(f"{salary_min}-{salary_max}")
        elif salary_min is not None:
            parts.append(f"from {salary_min}")
        else:
            parts.append(f"up to {salary_max}")

        if currency:
            parts.append(currency)
        if period:
            parts.append(f"/ {period}")
        return " ".join(parts)

    def _parse_job(self, item: dict[str, Any]) -> RawJob | None:
        title = _clean_text(item.get("jobTitle"))
        company = _clean_text(item.get("companyName"))
        url = _clean_text(item.get("url"))
        if not title or not url:
            return None

        raw_description = item.get("jobDescription") or item.get("jobExcerpt") or ""
        external_id = item.get("id")

        return RawJob(
            source=self.name,
            external_id=str(external_id) if external_id is not None else None,
            title=title,
            company=company or "Desconocida",
            url=url,
            location_raw=_clean_text(item.get("jobGeo")),
            description_text=clean_html(str(raw_description)),
            salary_raw=self._format_salary(item),
            published_at=_parse_datetime(item.get("pubDate")),
        )

    def fetch(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        with httpx.Client(
            timeout=self.timeout,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
        ) as client:
            for index, params in enumerate(self.QUERIES):
                if index > 0:
                    time.sleep(self.REQUEST_DELAY_SECONDS)

                try:
                    response = client.get(self.BASE_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    reason = str(exc).splitlines()[0]
                    print(f"[AVISO] [{self.name}] Error en consulta {params}: {reason}")
                    continue

                raw_items = payload.get("jobs", []) if isinstance(payload, dict) else []
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    parsed = self._parse_job(item)
                    if parsed is not None:
                        jobs.append(parsed)

        return jobs


class RemotiveSource(BaseSource):
    name = "remotive"
    BASE_URL = "https://remotive.com/api/remote-jobs"
    QUERIES: tuple[dict[str, str | int], ...] = (
        {"category": "writing", "limit": 30},
        {"category": "marketing", "limit": 30},
    )
    REQUEST_DELAY_SECONDS = 2.0

    def __init__(self, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def _parse_job(self, item: dict[str, Any]) -> RawJob | None:
        title = _clean_text(item.get("title"))
        company = _clean_text(item.get("company_name"))
        url = _clean_text(item.get("url"))
        if not title or not url:
            return None

        salary = _clean_text(item.get("salary")) or None
        external_id = item.get("id")

        return RawJob(
            source=self.name,
            external_id=str(external_id) if external_id is not None else None,
            title=title,
            company=company or "Desconocida",
            url=url,
            location_raw=_clean_text(item.get("candidate_required_location")),
            description_text=clean_html(str(item.get("description") or "")),
            salary_raw=salary,
            published_at=_parse_datetime(item.get("publication_date")),
        )

    def fetch(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        with httpx.Client(
            timeout=self.timeout,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
        ) as client:
            for index, params in enumerate(self.QUERIES):
                if index > 0:
                    time.sleep(self.REQUEST_DELAY_SECONDS)

                try:
                    response = client.get(self.BASE_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    reason = str(exc).splitlines()[0]
                    print(f"[AVISO] [{self.name}] Error en consulta {params}: {reason}")
                    continue

                raw_items = payload.get("jobs", []) if isinstance(payload, dict) else []
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    parsed = self._parse_job(item)
                    if parsed is not None:
                        jobs.append(parsed)

        return jobs
