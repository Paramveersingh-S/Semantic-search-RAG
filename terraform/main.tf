terraform {
  required_version = ">= 1.8.0"
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

# 1. VPC and Subnets (Assuming basic usage or leveraging an existing module)
# Here using AWS official VPC module for a standard multi-AZ setup
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "search-platform-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

# 2. EKS Cluster
module "eks" {
  source       = "./modules/eks"
  cluster_name = "search-platform-${var.environment}"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnets

  node_groups = {
    cpu_workers = { instance_type = "m5.2xlarge", min_size = 2, max_size = 10 }
    gpu_workers = { instance_type = "g4dn.xlarge", min_size = 0, max_size = 4 }
    inference   = { instance_type = "c6i.2xlarge", min_size = 1, max_size = 5 }
  }
}

# 3. RDS PostgreSQL with pgvector
module "rds" {
  source = "./modules/rds"
  
  identifier = "searchdb-${var.environment}"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  instance_class = "db.m6g.xlarge"
  engine_version = "16.1"
}

# 4. ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id = "search-redis-${var.environment}"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  node_type  = "cache.m6g.large"
}

# 5. MSK (Managed Kafka)
# 6. ECR Repositories
# 7. S3 Buckets
resource "aws_s3_bucket" "document_storage" {
  bucket = "search-platform-docs-${var.environment}-${var.aws_region}"
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket = "search-platform-models-${var.environment}-${var.aws_region}"
}
