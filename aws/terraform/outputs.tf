# ============================================
# Outputs - Thông tin quan trọng sau khi deploy
# ============================================

# CloudFront Outputs
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name - URL để truy cập website"
  value       = module.cloudfront.distribution_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID - Dùng để invalidate cache"
  value       = module.cloudfront.distribution_id
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "API Gateway endpoint URL - Dùng trong React app"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

# S3 Outputs
output "plant_data_bucket_name" {
  description = "S3 bucket name cho plant data (EXISTING BUCKET)"
  value       = module.s3.plant_data_bucket_id
}

output "website_bucket_name" {
  description = "S3 bucket name cho website hosting (NEW BUCKET)"
  value       = module.s3.website_bucket_id
}

# Lambda Outputs
output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = module.lambda.function_arn
}

# Plant Configuration
output "plant_id" {
  description = "Plant ID được cấu hình"
  value       = var.plant_id
}

output "data_path_prefix" {
  description = "Data path prefix trong S3"
  value       = var.data_path_prefix
}

# ============================================
# MQTT Bridge Outputs
# ============================================

output "mqtt_ingest_url" {
  description = "MQTT Bridge webhook URL - Configure this in HiveMQ"
  value       = module.mqtt_bridge.api_endpoint
}

output "mqtt_api_key" {
  description = "API Key for HiveMQ webhook (SENSITIVE)"
  value       = module.mqtt_bridge.api_key_value
  sensitive   = true
}

output "mqtt_lambda_function_name" {
  description = "HiveMQ Processor Lambda function name"
  value       = module.mqtt_bridge.lambda_function_name
}

# Deployment Instructions
output "deployment_instructions" {
  description = "Hướng dẫn deploy sau khi chạy Terraform"
  value = <<-EOT
  
  Infrastructure đã được tạo thành công!
  
    S3 Buckets:
     - Plant Data (EXISTING): ${module.s3.plant_data_bucket_id}
     - Website (NEW):         ${module.s3.website_bucket_id}
  
    Plant Configuration:
     - Plant ID:      ${var.plant_id}
     - Data Path:     ${var.data_path_prefix}
     - Images Path:   s3://${module.s3.plant_data_bucket_id}/${var.data_path_prefix}images/
     - Logs Path:     s3://${module.s3.plant_data_bucket_id}/${var.data_path_prefix}logs/
  
  Các bước tiếp theo:
  
  1. Deploy Frontend:
     cd ../frontend
     cat > .env << EOF
REACT_APP_API_ENDPOINT=${module.api_gateway.api_endpoint}
REACT_APP_PLANT_ID=${var.plant_id}
EOF
     npm install
     npm run build
     aws s3 sync build/ s3://${module.s3.website_bucket_id} --delete
     aws cloudfront create-invalidation --distribution-id ${module.cloudfront.distribution_id} --paths "/*"
  
  2. Kiểm tra dữ liệu trong S3 bucket hiện có:
     aws s3 ls s3://${module.s3.plant_data_bucket_id}/${var.data_path_prefix}images/ --recursive
  
  3. Truy cập website:
     https://${module.cloudfront.distribution_domain_name}
  
  4. Test API:
     curl ${module.api_gateway.api_endpoint}/${var.plant_id}
  
  EOT
}
