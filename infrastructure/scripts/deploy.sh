#!/bin/bash

# CloudWatch Pro - Infrastructure Deployment Script
# This script automates the deployment of CloudWatch Pro infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-production}
CLOUD_PROVIDER=${2:-aws}
ACTION=${3:-plan}

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if AWS CLI is installed (for AWS deployment)
    if [[ "$CLOUD_PROVIDER" == "aws" ]] && ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed. Please install Helm first."
        exit 1
    fi
    
    log_success "All prerequisites are met."
}

setup_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    local backend_dir="$PROJECT_ROOT/$CLOUD_PROVIDER/backend"
    
    if [[ ! -d "$backend_dir" ]]; then
        log_warning "Backend directory not found. Creating backend resources..."
        
        # Create backend directory
        mkdir -p "$backend_dir"
        
        # Create backend configuration
        cat > "$backend_dir/main.tf" << EOF
# Terraform Backend Resources for CloudWatch Pro

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloudwatch-pro"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "\${var.project_name}-terraform-state"
  
  tags = {
    Name        = "\${var.project_name}-terraform-state"
    Environment = "shared"
    Purpose     = "Terraform State"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "\${var.project_name}-terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "\${var.project_name}-terraform-locks"
    Environment = "shared"
    Purpose     = "Terraform State Locking"
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.terraform_state.bucket
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
EOF
        
        # Initialize and apply backend
        cd "$backend_dir"
        terraform init
        terraform plan
        terraform apply -auto-approve
        cd "$PROJECT_ROOT"
        
        log_success "Terraform backend created successfully."
    else
        log_info "Terraform backend already exists."
    fi
}

validate_terraform() {
    log_info "Validating Terraform configuration..."
    
    cd "$PROJECT_ROOT/$CLOUD_PROVIDER"
    
    # Check if terraform.tfvars exists
    if [[ ! -f "terraform.tfvars" ]]; then
        log_warning "terraform.tfvars not found. Please copy terraform.tfvars.example to terraform.tfvars and update the values."
        exit 1
    fi
    
    # Validate Terraform configuration
    terraform validate
    
    log_success "Terraform configuration is valid."
}

deploy_infrastructure() {
    log_info "Deploying infrastructure for environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT/$CLOUD_PROVIDER"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Select or create workspace
    log_info "Setting up Terraform workspace: $ENVIRONMENT"
    terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"
    
    case "$ACTION" in
        "plan")
            log_info "Running Terraform plan..."
            terraform plan -var="environment=$ENVIRONMENT" -out="tfplan-$ENVIRONMENT"
            ;;
        "apply")
            log_info "Applying Terraform configuration..."
            terraform apply -var="environment=$ENVIRONMENT" -auto-approve
            
            # Save outputs
            terraform output -json > "outputs-$ENVIRONMENT.json"
            
            log_success "Infrastructure deployed successfully!"
            
            # Configure kubectl
            configure_kubectl
            
            # Deploy applications
            deploy_applications
            ;;
        "destroy")
            log_warning "Destroying infrastructure for environment: $ENVIRONMENT"
            read -p "Are you sure you want to destroy the infrastructure? (yes/no): " confirm
            if [[ "$confirm" == "yes" ]]; then
                terraform destroy -var="environment=$ENVIRONMENT" -auto-approve
                log_success "Infrastructure destroyed successfully!"
            else
                log_info "Destruction cancelled."
            fi
            ;;
        *)
            log_error "Invalid action: $ACTION. Use 'plan', 'apply', or 'destroy'."
            exit 1
            ;;
    esac
}

configure_kubectl() {
    log_info "Configuring kubectl..."
    
    # Get cluster name from Terraform output
    local cluster_name=$(terraform output -raw cluster_id 2>/dev/null || echo "")
    local aws_region=$(terraform output -raw aws_region 2>/dev/null || echo "us-west-2")
    
    if [[ -n "$cluster_name" ]]; then
        aws eks update-kubeconfig --region "$aws_region" --name "$cluster_name"
        log_success "kubectl configured successfully."
    else
        log_warning "Could not configure kubectl. Cluster name not found in Terraform outputs."
    fi
}

deploy_applications() {
    log_info "Deploying CloudWatch Pro applications..."
    
    local k8s_dir="$PROJECT_ROOT/../k8s"
    
    if [[ -d "$k8s_dir" ]]; then
        # Apply Kubernetes manifests
        kubectl apply -f "$k8s_dir/namespaces/"
        kubectl apply -f "$k8s_dir/storage/"
        kubectl apply -f "$k8s_dir/configmaps/"
        kubectl apply -f "$k8s_dir/secrets/"
        kubectl apply -f "$k8s_dir/deployments/"
        kubectl apply -f "$k8s_dir/services/"
        kubectl apply -f "$k8s_dir/ingress/"
        kubectl apply -f "$k8s_dir/monitoring/"
        
        log_success "Applications deployed successfully!"
        
        # Show application URLs
        show_application_urls
    else
        log_warning "Kubernetes manifests directory not found: $k8s_dir"
    fi
}

show_application_urls() {
    log_info "Application URLs:"
    
    local domain_name=$(terraform output -raw domain_name 2>/dev/null || echo "cloudwatch-pro.example.com")
    
    echo ""
    echo "🌐 CloudWatch Pro Dashboard: https://$domain_name"
    echo "🔧 API Gateway: https://api.$domain_name"
    echo "📊 Grafana: https://grafana.$domain_name"
    echo "📈 Prometheus: https://prometheus.$domain_name"
    echo ""
    
    log_info "It may take a few minutes for the DNS and SSL certificates to propagate."
}

show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [CLOUD_PROVIDER] [ACTION]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT      Environment to deploy (default: production)"
    echo "  CLOUD_PROVIDER   Cloud provider (aws, azure, gcp) (default: aws)"
    echo "  ACTION          Action to perform (plan, apply, destroy) (default: plan)"
    echo ""
    echo "Examples:"
    echo "  $0 production aws plan     # Plan production deployment on AWS"
    echo "  $0 staging aws apply       # Deploy staging environment on AWS"
    echo "  $0 production aws destroy  # Destroy production environment on AWS"
    echo ""
}

main() {
    echo "🚀 CloudWatch Pro Infrastructure Deployment"
    echo "============================================"
    echo ""
    
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        show_usage
        exit 0
    fi
    
    log_info "Environment: $ENVIRONMENT"
    log_info "Cloud Provider: $CLOUD_PROVIDER"
    log_info "Action: $ACTION"
    echo ""
    
    check_prerequisites
    
    if [[ "$CLOUD_PROVIDER" == "aws" ]]; then
        setup_terraform_backend
    fi
    
    validate_terraform
    deploy_infrastructure
    
    log_success "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"

