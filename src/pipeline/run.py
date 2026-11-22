from src.db.database import get_session, init_db
from src.db.models import RunLog, utc_now
from src.db.repository import save_raw_jobs, save_run_log
from src.sources.base import BaseSource, RawJob
from src.sources.remote_apis import JobicySource, RemotiveSource


def run_ingestion() -> RunLog:
    started_at = utc_now()
    init_db()

    sources: list[BaseSource] = [
        JobicySource(),
        RemotiveSource(),
    ]

    all_raw_jobs: list[RawJob] = []
    counts_by_source: dict[str, int] = {}

    for source in sources:
        try:
            fetched = source.fetch()
        except Exception as exc:
            print(f"[AVISO] [{source.name}] Fallo inesperado al obtener ofertas: {exc}")
            fetched = []
        counts_by_source[source.name] = len(fetched)
        all_raw_jobs.extend(fetched)

    with get_session() as session:
        inserted_count, duplicated_count = save_raw_jobs(session, all_raw_jobs)
        finished_at = utc_now()
        notes = ", ".join(
            f"{source_name}={count}" for source_name, count in counts_by_source.items()
        )
        run_log = save_run_log(
            session,
            started_at=started_at,
            finished_at=finished_at,
            jobs_fetched=len(all_raw_jobs),
            jobs_inserted=inserted_count,
            jobs_duplicated=duplicated_count,
            notes=notes,
        )

    print("Resumen de ingesta (Fase 1)")
    print("---------------------------")
    for source_name, count in counts_by_source.items():
        print(f"Fuente {source_name:<12}: {count} ofertas obtenidas")
    print("---------------------------")
    print(f"Total obtenidas     : {run_log.jobs_fetched}")
    print(f"Nuevas insertadas   : {run_log.jobs_inserted}")
    print(f"Duplicadas omitidas : {run_log.jobs_duplicated}")

    return run_log


if __name__ == "__main__":
    run_ingestion()
