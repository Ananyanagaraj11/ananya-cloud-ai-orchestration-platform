# Azure Deployment Runbook

## Stack (Terraform)

| Resource | File |
|----------|------|
| Resource Group | `infra/terraform/azure/main.tf` |
| Container Registry (ACR) | `infra/terraform/azure/main.tf` |
| PostgreSQL Flexible Server 16 | `infra/terraform/azure/main.tf` |
| Azure Cache for Redis | `infra/terraform/azure/main.tf` |
| Container Apps Environment | `infra/terraform/azure/main.tf` |
| Container App (API) | `infra/terraform/azure/main.tf` |
| Blob Storage | `infra/terraform/azure/main.tf` |
| Log Analytics | `infra/terraform/azure/main.tf` |

## Deploy

```bash
cd infra/terraform/azure
cp terraform.tfvars.example terraform.tfvars
az login

terraform init
terraform plan
terraform apply
```

## Push container

```bash
az acr login --name $ACR_NAME
docker build -t $ACR_LOGIN_SERVER/api:latest ../../..
docker push $ACR_LOGIN_SERVER/api:latest
az containerapp update --name cloud-ai-orch-api --resource-group cloud-ai-orch-rg --image $ACR_LOGIN_SERVER/api:latest
```

## Outputs

- `container_app_url` — public API URL
- `postgres_fqdn` — DATABASE_URL host
- `redis_hostname` — REDIS_URL host
- `storage_account` — Blob exports

## AKS alternative

Deploy `infra/kubernetes/deployment.yaml` to AKS with the same env vars from Terraform outputs.
