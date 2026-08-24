# Azure — Cloud AI Orchestration Platform
# Usage: terraform init && terraform plan
# Requires: az login, terraform >= 1.5

terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "${var.project}-rg"
  location = var.azure_region
}

# Container Registry
resource "azurerm_container_registry" "acr" {
  name                = replace("${var.project}acr", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "workflows" {
  name                   = "${var.project}-pg"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  administrator_login    = var.db_username
  administrator_password = var.db_password
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  zone                   = "1"
}

resource "azurerm_postgresql_flexible_server_database" "workflows" {
  name      = "workflows"
  server_id = azurerm_postgresql_flexible_server.workflows.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "queue" {
  name                = "${var.project}-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
}

# Log Analytics + Container Apps Environment
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project}-env"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

resource "azurerm_container_app" "api" {
  name                         = "${var.project}-api"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "api"
      image  = "${azurerm_container_registry.acr.login_server}/api:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_username}:${var.db_password}@${azurerm_postgresql_flexible_server.workflows.fqdn}:5432/workflows"
      }
      env {
        name  = "REDIS_URL"
        value = "rediss://${azurerm_redis_cache.queue.hostname}:6380/0"
      }
      env {
        name  = "CLOUD_PROVIDER"
        value = "azure"
      }
      env {
        name  = "AZURE_REGION"
        value = var.azure_region
      }

      liveness_probe {
        transport = "HTTP"
        port      = 8040
        path      = "/health"
      }
    }

    min_replicas = 1
    max_replicas = 5
  }

  ingress {
    external_enabled = true
    target_port      = 8040
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

# Blob Storage (workflow exports)
resource "azurerm_storage_account" "exports" {
  name                     = replace("${var.project}exports", "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.workflows.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.queue.hostname
}

output "container_app_url" {
  value = "https://${azurerm_container_app.api.latest_revision_fqdn}"
}

output "storage_account" {
  value = azurerm_storage_account.exports.name
}
