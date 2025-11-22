variable "api_name" {
  description = "MQTT Bridge API Gateway name"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "lambda_function_name" {
  description = "HiveMQ Processor Lambda function name"
  type        = string
}

variable "lambda_handler" {
  description = "Lambda function handler"
  type        = string
  default     = "hivemq_processor.lambda_handler"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 128
}

variable "source_file" {
  description = "Path to Lambda source file"
  type        = string
}

variable "plant_data_bucket_name" {
  description = "S3 bucket name for plant data"
  type        = string
}

variable "plant_data_bucket_arn" {
  description = "S3 bucket ARN for plant data"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "api_key_name" {
  description = "API Gateway API Key name"
  type        = string
  default     = "hivemq-webhook-key"
}

variable "rate_limit" {
  description = "API Gateway rate limit (requests per second)"
  type        = number
  default     = 1000
}

variable "burst_limit" {
  description = "API Gateway burst limit"
  type        = number
  default     = 2000
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
