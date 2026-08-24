# AWS Deployment Runbook

## Stack (Terraform)

| Resource | File |
|----------|------|
| VPC + subnets | `infra/terraform/aws/main.tf` |
| ECR | `infra/terraform/aws/main.tf` |
| RDS PostgreSQL 16 | `infra/terraform/aws/main.tf` |
| ElastiCache Redis 7 | `infra/terraform/aws/main.tf` |
| ECS Fargate cluster + task | `infra/terraform/aws/main.tf` |
| S3 exports bucket | `infra/terraform/aws/main.tf` |
| CloudWatch logs | `infra/terraform/aws/main.tf` |

## Deploy

```bash
cd infra/terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Set db_username, db_password

terraform init
terraform plan
terraform apply
```

## Push container

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker build -t cloud-ai-orchestration ../../..
docker tag cloud-ai-orchestration:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

## Outputs

After `terraform apply`:

- `ecr_repository_url` — push Docker image here
- `rds_endpoint` — DATABASE_URL host
- `redis_endpoint` — REDIS_URL host
- `s3_exports_bucket` — export destination
- `ecs_cluster_name` — attach ECS service + ALB

## Observability

- Container logs → CloudWatch `/ecs/cloud-ai-orchestration-api`
- App metrics → scrape `http://<task-ip>:8040/metrics` via Prometheus
- Health → `/health`

## EKS alternative

Use `infra/kubernetes/deployment.yaml` with EKS instead of ECS Fargate — same image, same env vars.
