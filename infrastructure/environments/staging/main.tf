# Staging Environment Configuration

terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket = "cloudwatch-pro-terraform-state"
    key    = "staging/terraform.tfstate"
    region = "us-west-2"
  }
}

module "vpc" {
  source = "../../modules/aws/vpc"
  
  vpc_cidr             = "10.1.0.0/16"
  availability_zones   = ["us-west-2a", "us-west-2b"]
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]
  
  tags = {
    Environment = "staging"
    Project     = "cloudwatch-pro"
  }
}

module "eks" {
  source = "../../modules/aws/eks"
  
  cluster_name       = "cloudwatch-pro-staging"
  kubernetes_version = "1.28"
  subnet_ids         = module.vpc.private_subnet_ids
  
  tags = {
    Environment = "staging"
    Project     = "cloudwatch-pro"
  }
}

module "rds" {
  source = "../../modules/aws/rds"
  
  db_identifier       = "cloudwatch-pro-staging"
  database_name       = "cloudwatch_users"
  username           = "cloudwatch"
  password           = var.database_password
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [aws_security_group.rds.id]
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  
  tags = {
    Environment = "staging"
    Project     = "cloudwatch-pro"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "cloudwatch-pro-staging-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr]
  }

  tags = {
    Name        = "cloudwatch-pro-staging-rds-sg"
    Environment = "staging"
    Project     = "cloudwatch-pro"
  }
}

