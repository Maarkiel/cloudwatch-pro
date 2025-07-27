# CloudWatch Pro - AWS Outputs

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

# EKS Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_ca_certificate" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_ca_certificate
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = module.eks.cluster_oidc_issuer_url
}

output "node_groups" {
  description = "EKS node groups"
  value       = module.eks.node_groups
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.port
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.instance_id
}

output "rds_instance_arn" {
  description = "RDS instance ARN"
  value       = module.rds.instance_arn
}

# ElastiCache Outputs
output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.primary_endpoint
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.port
}

output "redis_cluster_id" {
  description = "Redis cluster ID"
  value       = module.elasticache.cluster_id
}

# S3 Outputs
output "s3_bucket_names" {
  description = "Names of created S3 buckets"
  value       = module.s3.bucket_names
}

output "s3_bucket_arns" {
  description = "ARNs of created S3 buckets"
  value       = module.s3.bucket_arns
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = module.alb.alb_arn
}

# Route53 Outputs
output "domain_name" {
  description = "Domain name"
  value       = var.domain_name
}

output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = module.route53.hosted_zone_id
}

# Application URLs
output "application_url" {
  description = "URL to access the CloudWatch Pro application"
  value       = "https://${var.domain_name}"
}

output "api_url" {
  description = "URL to access the CloudWatch Pro API"
  value       = "https://api.${var.domain_name}"
}

output "grafana_url" {
  description = "URL to access Grafana dashboard"
  value       = "https://grafana.${var.domain_name}"
}

output "prometheus_url" {
  description = "URL to access Prometheus"
  value       = "https://prometheus.${var.domain_name}"
}

# Kubectl configuration
output "kubectl_config" {
  description = "kubectl config command to connect to the cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# Cost information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost (approximate)"
  value = {
    eks_cluster     = "$73"  # EKS control plane
    ec2_instances   = "$50-200"  # Depends on node configuration
    rds_instance    = "$15-50"   # Depends on instance type
    elasticache     = "$15-30"   # Depends on node type
    load_balancer   = "$20"      # ALB
    data_transfer   = "$10-50"   # Depends on usage
    storage         = "$10-30"   # EBS volumes and S3
    total_estimate  = "$193-453 per month"
  }
}

# Security information
output "security_groups" {
  description = "Security group IDs"
  value = {
    eks_cluster = module.eks.cluster_security_group_id
    rds         = module.rds.security_group_id
    alb         = module.alb.security_group_id
  }
}

# Monitoring information
output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value       = module.cloudwatch.log_group_names
}

output "cloudwatch_alarms" {
  description = "CloudWatch alarm names"
  value       = module.cloudwatch.alarm_names
}

# IAM information
output "iam_roles" {
  description = "IAM role ARNs"
  value       = module.iam.role_arns
}

# Backup information
output "backup_configuration" {
  description = "Backup configuration details"
  value = {
    rds_backup_retention_period = var.backup_retention_days
    rds_backup_window          = module.rds.backup_window
    rds_maintenance_window     = module.rds.maintenance_window
    s3_backup_bucket          = module.s3.bucket_names["backups"]
  }
}

