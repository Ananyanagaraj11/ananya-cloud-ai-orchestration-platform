from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


class WorkflowRunRow(Base):
    __tablename__ = "workflow_runs"

    run_id = Column(String, primary_key=True)
    definition_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    idempotency_key = Column(String, unique=True, nullable=True)
    current_step = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    input_payload = Column(JSON, default=dict)
    output_payload = Column(JSON, default=dict)
    audit_log = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class StepExecutionRow(Base):
    __tablename__ = "step_executions"

    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    attempt = Column(Integer, default=1)
    output = Column(JSON, default=dict)
    error = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
        Base.metadata.create_all(_engine)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session() -> Session:
    get_engine()
    return _SessionLocal()


class WorkflowStore:
    def get_by_idempotency(self, key: str) -> WorkflowRunRow | None:
        with get_session() as session:
            return session.query(WorkflowRunRow).filter_by(idempotency_key=key).first()

    def save_run(self, row: WorkflowRunRow) -> None:
        with get_session() as session:
            session.merge(row)
            session.commit()

    def get_run(self, run_id: str) -> WorkflowRunRow | None:
        with get_session() as session:
            return session.query(WorkflowRunRow).filter_by(run_id=run_id).first()

    def list_runs(self, limit: int = 20) -> list[WorkflowRunRow]:
        with get_session() as session:
            return (
                session.query(WorkflowRunRow)
                .order_by(WorkflowRunRow.created_at.desc())
                .limit(limit)
                .all()
            )

    def save_step(self, row: StepExecutionRow) -> None:
        with get_session() as session:
            session.merge(row)
            session.commit()

    def get_steps(self, run_id: str) -> list[StepExecutionRow]:
        with get_session() as session:
            return session.query(StepExecutionRow).filter_by(run_id=run_id).all()


def row_to_run(row: WorkflowRunRow) -> dict:
    return {
        "run_id": row.run_id,
        "definition_name": row.definition_name,
        "status": row.status,
        "idempotency_key": row.idempotency_key,
        "current_step": row.current_step,
        "retry_count": row.retry_count,
        "input_payload": row.input_payload or {},
        "output_payload": row.output_payload or {},
        "audit_log": row.audit_log or [],
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def append_audit(row: WorkflowRunRow, event: str, detail: dict | None = None) -> list:
    log = list(row.audit_log or [])
    log.append({"ts": datetime.utcnow().isoformat(), "event": event, "detail": detail or {}})
    return log
