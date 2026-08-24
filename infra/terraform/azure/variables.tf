variable "project" {
  default = "cloud-ai-orch"
}

variable "azure_region" {
  default = "eastus"
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}
