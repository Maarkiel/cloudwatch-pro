# Google Cloud Platform Configuration Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cloudwatch-pro"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# GKE Configuration
variable "node_count" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-medium"
}

# Database Configuration
variable "database_password" {
  description = "Password for the PostgreSQL database"
  type        = string
  sensitive   = true
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

