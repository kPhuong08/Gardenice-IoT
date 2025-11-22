variable "api_name" {
  description = "API Gateway name"
  type        = string
}

variable "api_description" {
  description = "API Gateway description"
  type        = string
  default     = "Plant Monitoring API"
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
