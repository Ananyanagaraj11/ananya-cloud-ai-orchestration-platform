from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response

from src.core.models import HumanReviewRequest, StartWorkflowRequest
from src.observability.metrics import WORKFLOW_COMPLETIONS, WORKFLOW_STARTS, metrics_response
from src.storage.database import WorkflowStore, row_to_run
from src.workflow.engine import DEFINITIONS, WorkflowEngine

engine = WorkflowEngine()
store = WorkflowStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Cloud AI Orchestration Platform",
    description="Multi-stage workflow orchestration for AI data pipelines — AWS/Azure ready",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "cloud": "aws-azure-ready",
        "definitions": list(DEFINITIONS.keys()),
    }


@app.get("/metrics")
async def metrics() -> Response:
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)


@app.get("/definitions")
async def list_definitions() -> dict:
    return {k: v.model_dump() for k, v in DEFINITIONS.items()}


@app.post("/workflows")
async def start_workflow(request: StartWorkflowRequest) -> dict:
    WORKFLOW_STARTS.inc()
    run = engine.start(request.definition_name, request.idempotency_key, request.input_payload)
    executed = await engine.execute_run(run["run_id"])
    WORKFLOW_COMPLETIONS.labels(status=executed["status"]).inc()
    return executed


@app.get("/workflows")
async def list_workflows() -> list:
    return [row_to_run(r) for r in store.list_runs()]


@app.get("/workflows/{run_id}")
async def get_workflow(run_id: str) -> dict:
    row = store.get_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return row_to_run(row)


@app.post("/workflows/{run_id}/approve")
async def approve_workflow(run_id: str, body: HumanReviewRequest) -> dict:
    try:
        return await engine.approve_human_step(run_id, body.approved, body.feedback)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
