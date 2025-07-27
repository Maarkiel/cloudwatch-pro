# Google Cloud Platform Infrastructure Outputs

output "gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.main.name
}

output "gke_cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = google_container_cluster.main.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "CA certificate for the GKE cluster"
  value       = google_container_cluster.main.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

output "sql_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "sql_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "sql_public_ip" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.main.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.main.port
}

output "vpc_network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.main.name
}

output "subnet_name" {
  description = "Name of the subnet"
  value       = google_compute_subnetwork.main.name
}

