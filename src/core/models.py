from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    RECONCILING = "reconciling"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    name: str
    step_type: str
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    name: str
    steps: list[WorkflowStep]
    description: str = ""


class StartWorkflowRequest(BaseModel):
    definition_name: str = "ai-data-pipeline"
    idempotency_key: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRun(BaseModel):
    run_id: str
    definition_name: str
    status: WorkflowStatus
    idempotency_key: str | None = None
    current_step: str | None = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    audit_log: list[dict[str, Any]] = Field(default_factory=list)


class StepExecution(BaseModel):
    run_id: str
    step_name: str
    status: StepStatus
    attempt: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class HumanReviewRequest(BaseModel):
    approved: bool
    feedback: str = ""
