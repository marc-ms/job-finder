from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: int | None = Field(default=None, primary_key=True)
    dedup_hash: str = Field(unique=True, index=True)
    url: str = Field(index=True)
    source: str
    external_id: str | None = Field(default=None)
    title: str
    company: str
    location_raw: str
    description_text: str
    salary_raw: str | None = Field(default=None)
    published_at: datetime | None = Field(default=None)
    fetched_at: datetime = Field(default_factory=utc_now)
    status: str = Field(default="new", index=True)
    evaluation_status: str = Field(default="pending", index=True)

    # Campos reservados para la Fase 2 (evaluacion con IA)
    score: int | None = Field(default=None)
    category: str | None = Field(default=None)
    work_mode: str | None = Field(default=None)
    contract_type: str | None = Field(default=None)
    summary_pros: str | None = Field(default=None)
    summary_cons: str | None = Field(default=None)
    is_fake_remote: bool | None = Field(default=None)
    evaluated_at: datetime | None = Field(default=None)


class RunLog(SQLModel, table=True):
    __tablename__ = "run_logs"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = Field(default=None)
    jobs_fetched: int = Field(default=0)
    jobs_inserted: int = Field(default=0)
    jobs_duplicated: int = Field(default=0)
    notes: str | None = Field(default=None)
