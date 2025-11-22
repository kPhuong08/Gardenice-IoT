variable "aws_region" {
  description = "AWS region cho resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name prefix cho resources"
  type        = string
  default     = "iot-gardenice"
}

variable "plant_data_bucket_name" {
  description = "Tên S3 bucket HIỆN CÓ chứa plant data (images và logs)"
  type        = string
  #tên bucket thực tế trong terraform.tfvars
}

variable "website_bucket_name" {
  description = "Tên S3 bucket MỚI cho website hosting"
  type        = string
  default     = "gardenice-website"
}

variable "ec2_service_url" {
  description = "URL của EC2 service cho real-time plant metrics"
  type        = string
}

variable "plant_id" {
  description = "ID của plant duy nhất (vì chỉ có 1 plant)"
  type        = string
  default     = "plant_001"
}

variable "data_path_prefix" {
  description = "Prefix path trong S3 bucket (ví dụ: 'plant_001/' hoặc '' nếu ở root)"
  type        = string
  default     = ""
}
