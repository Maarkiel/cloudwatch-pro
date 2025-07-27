# CloudWatch Pro - AWS Infrastructure
# Terraform configuration for deploying CloudWatch Pro on AWS

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
  
  backend "s3" {
    bucket         = "cloudwatch-pro-terraform-state"
    key            = "aws/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "cloudwatch-pro-terraform-locks"
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "CloudWatch Pro"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOps Team"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  cluster_name = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "../modules/aws/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  
  availability_zones = data.aws_availability_zones.available.names
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "../modules/aws/eks"
  
  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  
  node_groups = var.node_groups
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# RDS Module
module "rds" {
  source = "../modules/aws/rds"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids
  
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  
  database_name = var.database_name
  username      = var.database_username
  password      = var.database_password
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# ElastiCache Module
module "elasticache" {
  source = "../modules/aws/elasticache"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_cache_nodes
  parameter_group   = var.redis_parameter_group
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# S3 Buckets
module "s3" {
  source = "../modules/aws/s3"
  
  project_name = var.project_name
  environment  = var.environment
  
  buckets = [
    {
      name        = "cloudwatch-pro-backups"
      versioning  = true
      encryption  = true
      lifecycle   = true
    },
    {
      name        = "cloudwatch-pro-logs"
      versioning  = false
      encryption  = true
      lifecycle   = true
    },
    {
      name        = "cloudwatch-pro-artifacts"
      versioning  = true
      encryption  = true
      lifecycle   = false
    }
  ]
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "../modules/aws/alb"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  
  certificate_arn = var.ssl_certificate_arn
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# Route53 DNS
module "route53" {
  source = "../modules/aws/route53"
  
  domain_name = var.domain_name
  
  alb_dns_name = module.alb.alb_dns_name
  alb_zone_id  = module.alb.alb_zone_id
  
  tags = local.common_tags
  
  depends_on = [module.alb]
}

# IAM Roles and Policies
module "iam" {
  source = "../modules/aws/iam"
  
  project_name = var.project_name
  environment  = var.environment
  
  eks_cluster_name = module.eks.cluster_name
  
  tags = local.common_tags
}

# CloudWatch Monitoring
module "cloudwatch" {
  source = "../modules/aws/cloudwatch"
  
  project_name = var.project_name
  environment  = var.environment
  
  eks_cluster_name = module.eks.cluster_name
  rds_instance_id  = module.rds.instance_id
  
  sns_topic_arn = var.sns_topic_arn
  
  tags = local.common_tags
  
  depends_on = [module.eks, module.rds]
}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Configure Helm provider
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Install essential Kubernetes addons
module "k8s_addons" {
  source = "../modules/kubernetes/addons"
  
  cluster_name = module.eks.cluster_name
  
  # NGINX Ingress Controller
  install_nginx_ingress = true
  
  # Cert Manager for SSL certificates
  install_cert_manager = true
  
  # Cluster Autoscaler
  install_cluster_autoscaler = true
  
  # AWS Load Balancer Controller
  install_aws_load_balancer_controller = true
  
  # Metrics Server
  install_metrics_server = true
  
  # Prometheus and Grafana
  install_monitoring_stack = true
  
  depends_on = [module.eks]
}

# Deploy CloudWatch Pro application
module "cloudwatch_pro_app" {
  source = "../modules/kubernetes/cloudwatch-pro"
  
  namespace = "cloudwatch-pro"
  
  # Database connections
  postgres_host     = module.rds.endpoint
  postgres_database = module.rds.database_name
  postgres_username = var.database_username
  postgres_password = var.database_password
  
  redis_host = module.elasticache.primary_endpoint
  
  # Application configuration
  environment = var.environment
  domain_name = var.domain_name
  
  # Container images
  image_tag = var.image_tag
  
  depends_on = [module.eks, module.k8s_addons, module.rds, module.elasticache]
}

