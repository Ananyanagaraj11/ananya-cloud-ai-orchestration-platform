variable "project" {
  default = "cloud-ai-orchestration"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "db_instance_class" {
  default = "db.t3.micro"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "redis_node_type" {
  default = "cache.t3.micro"
}
