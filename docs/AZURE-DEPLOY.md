# Azure Deployment Guide

## Target architecture

- **Azure Container Apps** or **AKS** for the FastAPI service
- **Azure Database for PostgreSQL** for workflow state
- **Azure Cache for Redis** for job queue
- **Blob Storage** for export artifacts
- **Azure Monitor** + Prometheus scrape

## Services mapping

| Component | Azure service |
|-----------|---------------|
| API | Container Apps / AKS |
| Database | Azure Database for PostgreSQL Flexible Server |
| Queue | Azure Cache for Redis |
| Secrets | Azure Key Vault |
| Logs | Log Analytics |
| Storage | Blob Storage |

## Environment variables (production)

```
DATABASE_URL=postgresql://user:pass@postgres-server.postgres.database.azure.com/workflows
REDIS_URL=rediss://redis-cache.redis.cache.windows.net:6380/0
CLOUD_PROVIDER=azure
AZURE_REGION=eastus
```

## Deploy steps (summary)

1. Build and push to **Azure Container Registry**
2. Deploy Container App or AKS manifest (`infra/kubernetes/`)
3. Configure PostgreSQL + Redis via Bicep/Terraform in `infra/terraform/azure/`
4. Wire Key Vault references for secrets
5. Health probe: `/health`

## Parity with AWS

Same FastAPI image runs on both clouds — only connection strings and identity change.
