import asyncio
import uuid
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.models import StepStatus, WorkflowDefinition, WorkflowStatus, WorkflowStep
from src.storage.database import (
    StepExecutionRow,
    WorkflowRunRow,
    WorkflowStore,
    append_audit,
    row_to_run,
)

DEFINITIONS: dict[str, WorkflowDefinition] = {
    "ai-data-pipeline": WorkflowDefinition(
        name="ai-data-pipeline",
        description="Ingest → validate → LLM enrich → human review → export",
        steps=[
            WorkflowStep(name="ingest", step_type="task"),
            WorkflowStep(name="validate", step_type="task"),
            WorkflowStep(name="llm_enrich", step_type="llm"),
            WorkflowStep(name="human_review", step_type="hitl"),
            WorkflowStep(name="export", step_type="task"),
        ],
    ),
}


class WorkflowEngine:
    def __init__(self) -> None:
        self.store = WorkflowStore()
        self.settings = get_settings()

    def start(self, definition_name: str, idempotency_key: str | None, payload: dict) -> dict:
        if idempotency_key:
            existing = self.store.get_by_idempotency(idempotency_key)
            if existing:
                return row_to_run(existing)

        run_id = str(uuid.uuid4())
        row = WorkflowRunRow(
            run_id=run_id,
            definition_name=definition_name,
            status=WorkflowStatus.PENDING.value,
            idempotency_key=idempotency_key,
            current_step=DEFINITIONS[definition_name].steps[0].name,
            input_payload=payload,
            audit_log=append_audit(
                WorkflowRunRow(run_id=run_id, definition_name=definition_name, status="pending"),
                "workflow_started",
                {"definition": definition_name},
            ),
        )
        self.store.save_run(row)
        return row_to_run(row)

    async def execute_run(self, run_id: str) -> dict:
        row = self.store.get_run(run_id)
        if not row:
            raise KeyError(run_id)
        definition = DEFINITIONS[row.definition_name]
        row.status = WorkflowStatus.RUNNING.value
        row.updated_at = datetime.utcnow()
        row.audit_log = append_audit(row, "execution_started")
        self.store.save_run(row)

        context = dict(row.input_payload or {})
        for step in definition.steps:
            if row.status == WorkflowStatus.AWAITING_HUMAN.value:
                break
            row.current_step = step.name
            self.store.save_run(row)
            result = await self._execute_step(run_id, step.name, step.step_type, context)
            context.update(result.get("output", {}))
            if result.get("status") == StepStatus.FAILED.value:
                row.status = WorkflowStatus.FAILED.value
                row.audit_log = append_audit(row, "step_failed", {"step": step.name})
                self.store.save_run(row)
                return row_to_run(row)
            if result.get("status") == "awaiting_human":
                row.status = WorkflowStatus.AWAITING_HUMAN.value
                row.audit_log = append_audit(row, "awaiting_human_review", {"step": step.name})
                self.store.save_run(row)
                return row_to_run(row)

        row.status = WorkflowStatus.COMPLETED.value
        row.output_payload = context
        row.updated_at = datetime.utcnow()
        row.audit_log = append_audit(row, "workflow_completed")
        self.store.save_run(row)
        return row_to_run(row)

    async def approve_human_step(self, run_id: str, approved: bool, feedback: str) -> dict:
        row = self.store.get_run(run_id)
        if not row or row.status != WorkflowStatus.AWAITING_HUMAN.value:
            raise ValueError("Run not awaiting human review")
        if not approved:
            row.status = WorkflowStatus.FAILED.value
            row.audit_log = append_audit(row, "human_rejected", {"feedback": feedback})
            self.store.save_run(row)
            return row_to_run(row)
        row.audit_log = append_audit(row, "human_approved", {"feedback": feedback})
        row.status = WorkflowStatus.RUNNING.value
        self.store.save_run(row)
        definition = DEFINITIONS[row.definition_name]
        steps = [s.name for s in definition.steps]
        idx = steps.index(row.current_step or steps[-1])
        remaining = definition.steps[idx + 1 :]
        context = dict(row.output_payload or row.input_payload or {})
        for step in remaining:
            result = await self._execute_step(run_id, step.name, step.step_type, context)
            context.update(result.get("output", {}))
        row.status = WorkflowStatus.COMPLETED.value
        row.output_payload = context
        row.audit_log = append_audit(row, "workflow_completed_after_hitl")
        self.store.save_run(row)
        return row_to_run(row)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _execute_step(
        self, run_id: str, step_name: str, step_type: str, context: dict
    ) -> dict:
        step_id = str(uuid.uuid4())
        started = datetime.utcnow()
        row = StepExecutionRow(
            id=step_id,
            run_id=run_id,
            step_name=step_name,
            status=StepStatus.RUNNING.value,
            started_at=started,
        )
        self.store.save_step(row)
        await asyncio.sleep(0.05)

        try:
            if step_type == "llm":
                output = {"llm_summary": f"Enriched: {context.get('record_id', 'batch')}"}
            elif step_type == "hitl":
                row.status = "awaiting_human"
                row.finished_at = datetime.utcnow()
                self.store.save_step(row)
                return {"status": "awaiting_human", "output": context}
            elif step_name == "ingest":
                output = {"record_id": context.get("record_id", str(uuid.uuid4())[:8]), "records": 1}
            elif step_name == "validate":
                output = {"valid": True, "schema_version": "v1"}
            else:
                output = {"exported": True, "destination": f"s3://{self.settings.aws_region}/exports"}

            row.status = StepStatus.COMPLETED.value
            row.output = output
            row.finished_at = datetime.utcnow()
            self.store.save_step(row)
            return {"status": StepStatus.COMPLETED.value, "output": output}
        except Exception as exc:
            row.status = StepStatus.FAILED.value
            row.error = str(exc)
            row.finished_at = datetime.utcnow()
            self.store.save_step(row)
            return {"status": StepStatus.FAILED.value, "output": {}}
