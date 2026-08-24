from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

WORKFLOW_STARTS = Counter("workflow_starts_total", "Workflow runs started")
WORKFLOW_COMPLETIONS = Counter("workflow_completions_total", "Workflow runs completed", ["status"])


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
