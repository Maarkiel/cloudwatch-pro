# CloudWatch Pro - Google Cloud Platform Infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "main" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# GKE Cluster
resource "google_container_cluster" "main" {
  name     = "${var.project_name}-${var.environment}"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.main.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
}

# GKE Node Pool
resource "google_container_node_pool" "main" {
  name       = "${var.project_name}-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  node_config {
    preemptible  = false
    machine_type = var.machine_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = var.environment
      project     = var.project_name
    }

    tags = ["${var.project_name}-node"]
  }
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-postgres-${var.environment}"
  database_version = "POSTGRES_13"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = false
}

# Cloud SQL Database
resource "google_sql_database" "main" {
  name     = "cloudwatch_users"
  instance = google_sql_database_instance.main.name
}

# Cloud SQL User
resource "google_sql_user" "main" {
  name     = "cloudwatch"
  instance = google_sql_database_instance.main.name
  password = var.database_password
}

# Redis Instance
resource "google_redis_instance" "main" {
  name           = "${var.project_name}-redis-${var.environment}"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

