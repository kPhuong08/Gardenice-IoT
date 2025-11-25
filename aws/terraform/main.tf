terraform {
  required_version = ">= 1.0"
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

# Common tags cho tất cả resources
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================
# Module: S3 Buckets
# Sử dụng existing bucket cho data, tạo mới cho website
# ============================================
module "s3" {
  source = "./modules/s3"

  plant_data_bucket_name        = var.plant_data_bucket_name  # Bucket hiện có
  website_bucket_name           = var.website_bucket_name     # Bucket mới
  cloudfront_distribution_arn   = module.cloudfront.distribution_arn
  tags                          = local.common_tags
}

# ============================================
# Module: CloudFront Distribution
# ============================================
module "cloudfront" {
  source = "./modules/cloudfront"

  distribution_name               = "${var.project_name}-website"
  distribution_comment            = "Plant Monitor CDN - ${var.environment}"
  s3_bucket_regional_domain_name  = module.s3.website_bucket_regional_domain_name
  price_class                     = "PriceClass_100"
  
  # Cache settings
  min_ttl     = 0
  default_ttl = 3600
  max_ttl     = 86400

  tags = local.common_tags
}

# ============================================
# Module: Lambda Function
# ============================================
module "lambda" {
  source = "./modules/lambda"

  function_name           = "${var.project_name}-get-plant-data"
  handler                 = "get_plant_data.lambda_handler"
  runtime                 = "python3.11"
  timeout                 = 30
  memory_size             = 128
  source_file             = "${path.module}/../backend/get_plant_data.py"
  plant_data_bucket_arn   = module.s3.plant_data_bucket_arn
  log_retention_days      = 7

  environment_variables = {
    PLANT_DATA_BUCKET = module.s3.plant_data_bucket_id
    EC2_SERVICE_URL   = var.ec2_service_url
    PLANT_ID          = var.plant_id
    DATA_PATH_PREFIX  = var.data_path_prefix
    MQTT_TOPIC        = "esp32s3/soil"  # MQTT topic for sensor data
  }

  tags = local.common_tags
}

# ============================================
# Module: API Gateway (Frontend API)
# ============================================
module "api_gateway" {
  source = "./modules/api-gateway"

  api_name             = "${var.project_name}-api"
  api_description      = "Plant Monitoring API - ${var.environment}"
  stage_name           = var.environment
  lambda_invoke_arn    = module.lambda.invoke_arn
  lambda_function_name = module.lambda.function_name

  tags = local.common_tags
}

# # ============================================
# # Module: MQTT Bridge (HiveMQ Webhook)
# # ============================================
module "mqtt_bridge" {
  source = "./modules/mqtt-bridge"

  api_name                = "${var.project_name}-mqtt-bridge"
  stage_name              = "prod"
  lambda_function_name    = "${var.project_name}-hivemq-processor"
  lambda_handler          = "hivemq_processor.lambda_handler"
  lambda_runtime          = "python3.11"
  lambda_timeout          = 30
  lambda_memory_size      = 128
  source_file             = "${path.module}/../backend/hivemq_processor.py"
  plant_data_bucket_name  = module.s3.plant_data_bucket_id
  plant_data_bucket_arn   = module.s3.plant_data_bucket_arn
  log_retention_days      = 7
  api_key_name            = "hivemq-webhook-key"
  rate_limit              = 1000
  burst_limit             = 2000

  tags = local.common_tags
}
