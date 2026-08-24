# Architecture

## Problem

Frontier AI companies orchestrate pipelines that span **hours or days**: ingest data → run models → route to human experts → reconcile state → export results. These systems require:

- Durable state (not in-memory only)
- Idempotent API calls
- Retries with backoff
- Human approval gates
- Full auditability
- Cloud-native deployment on **AWS or Azure**

## Solution

A **workflow engine** (Python/FastAPI) with pluggable cloud infrastructure defined in **Terraform** and **Kubernetes**.

## Component diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  FastAPI Layer   │────▶│ Workflow Engine │
│  (Ops/ML)   │     │  /workflows      │     │  State Machine  │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────┐
                    ▼                                ▼                    ▼
             ┌────────────┐                  ┌────────────┐       ┌────────────┐
             │ PostgreSQL │                  │   Redis    │       │  Audit Log │
             │   State    │                  │   Queue    │       │   (JSON)   │
             └────────────┘                  └────────────┘       └────────────┘
```

## Cloud parity

The **same container image** runs on:

| Target | Provisioned by |
|--------|----------------|
| AWS ECS Fargate | `infra/terraform/aws/` |
| Azure Container Apps | `infra/terraform/azure/` |
| EKS / AKS | `infra/kubernetes/` |
| Local dev | `docker-compose.yml` |

Only connection strings and secrets change between environments.

## Workflow: `ai-data-pipeline`

| Step | Type | Purpose |
|------|------|---------|
| ingest | task | Accept batch / record |
| validate | task | Schema + quality checks |
| llm_enrich | llm | Model enrichment (mock or API) |
| human_review | hitl | Expert approval gate |
| export | task | Write to S3 / Blob |

## Security notes

- RDS / PostgreSQL not publicly accessible in Terraform defaults
- Redis TLS on Azure (`rediss://`)
- Secrets should use AWS Secrets Manager or Azure Key Vault in production (extend Terraform)
- No API keys committed — see `.env.example`
