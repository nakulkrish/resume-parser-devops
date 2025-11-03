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

# S3 bucket for storing parsed resumes and backups
resource "aws_s3_bucket" "resume_storage" {
  bucket = "resume-parser-storage-${random_id.bucket_id.hex}"

  tags = {
    Name        = "Resume Parser Storage"
    Environment = "Production"
    Project     = "DevOps-Resume-Parser"
  }
}

resource "aws_s3_bucket_versioning" "resume_storage_versioning" {
  bucket = aws_s3_bucket.resume_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket for Docker artifacts backup
resource "aws_s3_bucket" "docker_artifacts" {
  bucket = "resume-parser-artifacts-${random_id.bucket_id.hex}"

  tags = {
    Name        = "Docker Artifacts"
    Environment = "Production"
    Project     = "DevOps-Resume-Parser"
  }
}

resource "random_id" "bucket_id" {
  byte_length = 4
}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/resume-parser"
  retention_in_days = 7

  tags = {
    Application = "Resume Parser"
    Environment = "Production"
  }
}

# CloudWatch Metric Alarm - High CPU
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "resume-parser-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when CPU exceeds 80%"
  alarm_actions       = []

  dimensions = {
    InstanceId = var.app_server_instance_id
  }

  tags = {
    Name = "Resume Parser CPU Alarm"
  }
}

# CloudWatch Metric Alarm - High Memory (custom metric)
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "resume-parser-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "CWAgent"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "Alert when memory exceeds 85%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = var.app_server_instance_id
  }

  tags = {
    Name = "Resume Parser Memory Alarm"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "resume-parser-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { stat = "Average", label = "CPU Usage" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "EC2 CPU Utilization"
        }
      },
      {
        type = "log"
        properties = {
          query   = "SOURCE '/aws/ec2/resume-parser' | fields @timestamp, @message | sort @timestamp desc | limit 20"
          region  = var.aws_region
          title   = "Recent Application Logs"
        }
      }
    ]
  })
}

# IAM Role for EC2 to write CloudWatch logs
resource "aws_iam_role" "ec2_cloudwatch_role" {
  name = "resume-parser-ec2-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Resume Parser EC2 CloudWatch Role"
  }
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  name = "cloudwatch-logs-policy"
  role = aws_iam_role.ec2_cloudwatch_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:::*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "resume-parser-ec2-profile"
  role = aws_iam_role.ec2_cloudwatch_role.name
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_server_instance_id" {
  description = "EC2 Instance ID for App Server"
  type        = string
}

# Outputs
output "s3_resume_storage_bucket" {
  description = "S3 bucket for storing parsed resumes"
  value       = aws_s3_bucket.resume_storage.bucket
}

output "s3_artifacts_bucket" {
  description = "S3 bucket for Docker artifacts"
  value       = aws_s3_bucket.docker_artifacts.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "iam_instance_profile" {
  description = "IAM instance profile for EC2"
  value       = aws_iam_instance_profile.ec2_profile.name
}