# AWS Deployment Guide

## Target architecture

- **ECS Fargate** or **EKS** for the FastAPI service
- **RDS PostgreSQL** for workflow state
- **ElastiCache Redis** for job queue
- **S3** for export artifacts
- **CloudWatch** + **Prometheus** for metrics
- **GitHub Actions** → ECR → deploy

## Services mapping

| Component | AWS service |
|-----------|-------------|
| API | ECS Fargate / EKS Deployment |
| Database | RDS PostgreSQL |
| Queue | ElastiCache Redis |
| Secrets | AWS Secrets Manager |
| Logs | CloudWatch Logs |
| Metrics | CloudWatch + `/metrics` scrape |

## Environment variables (production)

```
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/workflows
REDIS_URL=redis://elasticache-endpoint:6379/0
CLOUD_PROVIDER=aws
AWS_REGION=us-east-1
```

## Deploy steps (summary)

1. Build image: `docker build -t cloud-ai-orchestration .`
2. Push to ECR
3. Create RDS + ElastiCache (Terraform templates in `infra/terraform/aws/`)
4. Deploy ECS service with env vars above
5. Health check: `/health` · Metrics: `/metrics`

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests; extend with `aws-actions/amazon-ecr-login` and ECS deploy for production.
