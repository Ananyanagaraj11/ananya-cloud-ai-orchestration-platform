import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.workflow.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_start_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/workflows",
            json={"idempotency_key": "test-key-1", "input_payload": {"source": "demo"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"]
        assert data["status"] in ("awaiting_human", "completed", "running", "failed")


@pytest.mark.asyncio
async def test_idempotency():
    engine = WorkflowEngine()
    r1 = engine.start("ai-data-pipeline", "idem-99", {"x": 1})
    r2 = engine.start("ai-data-pipeline", "idem-99", {"x": 1})
    assert r1["run_id"] == r2["run_id"]


@pytest.mark.asyncio
async def test_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
