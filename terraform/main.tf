# Household Management App - Infrastructure Configuration
# This Terraform configuration defines the infrastructure needed to deploy the application
#
# Note: Railway.app and Render.com don't use Terraform natively, but this serves as
# infrastructure documentation. For AWS deployment, this can be adapted.
#
# For Railway/Render: Use their web UI or CLI tools
# For AWS: Adapt this configuration to use AWS provider

terraform {
  required_version = ">= 1.0"

  # Uncomment and configure for remote state storage (recommended for production)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "household-app/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Provider Configuration
# Choose based on your cloud provider preference

# Option 1: AWS Configuration
provider "aws" {
  region = var.aws_region

  # Credentials should be set via environment variables:
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  # Or use AWS CLI configuration
}

# Option 2: For Railway/Render, infrastructure is managed through their platforms
# This file serves as documentation of required components

# Variables
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "household-manager"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

# Data Sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Configuration (for AWS deployment)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.app_name}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.app_name}-igw"
    Environment = var.environment
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.app_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.app_name}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for Application
resource "aws_security_group" "app" {
  name        = "${var.app_name}-app-sg"
  description = "Security group for application"
  vpc_id      = aws_vpc.main.id

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Application port (FastAPI default 8000)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-app-sg"
    Environment = var.environment
  }
}

# Security Group for Database
resource "aws_security_group" "db" {
  name        = "${var.app_name}-db-sg"
  description = "Security group for PostgreSQL database"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-db-sg"
    Environment = var.environment
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name        = "${var.app_name}-db-subnet-group"
    Environment = var.environment
  }
}

# RDS PostgreSQL Instance (Free Tier)
resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro" # Free tier eligible

  allocated_storage     = 20 # GB (free tier: 20GB)
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "householddb"
  username = "household_admin"
  # Password should be stored in AWS Secrets Manager in production
  # For now, use a variable (NOT RECOMMENDED FOR PRODUCTION)
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false # Set to true only for development

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  skip_final_snapshot = var.environment != "prod"

  tags = {
    Name        = "${var.app_name}-db"
    Environment = var.environment
  }
}

# ECR Repository for Docker Images (optional, for containerized deployment)
resource "aws_ecr_repository" "app" {
  name                 = "${var.app_name}-app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.app_name}-ecr"
    Environment = var.environment
  }
}

# Application Load Balancer (for production)
resource "aws_lb" "main" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.app.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name        = "${var.app_name}-alb"
    Environment = var.environment
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.main.dns_name
}

# Variables file (create terraform/terraform.tfvars)
# db_password = "your-secure-password-here"
# aws_region  = "us-east-1"
# environment = "dev"

