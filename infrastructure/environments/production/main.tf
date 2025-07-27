# Production Environment Configuration

terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket = "cloudwatch-pro-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
  }
}

module "vpc" {
  source = "../../modules/aws/vpc"
  
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-west-2a", "us-west-2b", "us-west-2c"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  
  tags = {
    Environment = "production"
    Project     = "cloudwatch-pro"
  }
}

module "eks" {
  source = "../../modules/aws/eks"
  
  cluster_name       = "cloudwatch-pro-production"
  kubernetes_version = "1.28"
  subnet_ids         = module.vpc.private_subnet_ids
  
  tags = {
    Environment = "production"
    Project     = "cloudwatch-pro"
  }
}

module "rds" {
  source = "../../modules/aws/rds"
  
  db_identifier       = "cloudwatch-pro-production"
  database_name       = "cloudwatch_users"
  username           = "cloudwatch"
  password           = var.database_password
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [aws_security_group.rds.id]
  
  tags = {
    Environment = "production"
    Project     = "cloudwatch-pro"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "cloudwatch-pro-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "cloudwatch-pro-rds-sg"
    Environment = "production"
    Project     = "cloudwatch-pro"
  }
}

