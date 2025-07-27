# Development Environment Configuration

terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket = "cloudwatch-pro-terraform-state"
    key    = "development/terraform.tfstate"
    region = "us-west-2"
  }
}

module "vpc" {
  source = "../../modules/aws/vpc"
  
  vpc_cidr             = "10.2.0.0/16"
  availability_zones   = ["us-west-2a"]
  public_subnet_cidrs  = ["10.2.1.0/24"]
  private_subnet_cidrs = ["10.2.11.0/24"]
  
  tags = {
    Environment = "development"
    Project     = "cloudwatch-pro"
  }
}

# Simplified development setup - single node EKS
module "eks" {
  source = "../../modules/aws/eks"
  
  cluster_name       = "cloudwatch-pro-dev"
  kubernetes_version = "1.28"
  subnet_ids         = concat(module.vpc.public_subnet_ids, module.vpc.private_subnet_ids)
  
  tags = {
    Environment = "development"
    Project     = "cloudwatch-pro"
  }
}

# Development uses smaller RDS instance
module "rds" {
  source = "../../modules/aws/rds"
  
  db_identifier       = "cloudwatch-pro-dev"
  database_name       = "cloudwatch_users"
  username           = "cloudwatch"
  password           = var.database_password
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [aws_security_group.rds.id]
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  backup_retention_period = 1
  
  tags = {
    Environment = "development"
    Project     = "cloudwatch-pro"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "cloudwatch-pro-dev-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # More permissive for development
  }

  tags = {
    Name        = "cloudwatch-pro-dev-rds-sg"
    Environment = "development"
    Project     = "cloudwatch-pro"
  }
}

