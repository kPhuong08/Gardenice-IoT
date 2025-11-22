variable "plant_data_bucket_name" {
  description = "S3 bucket name for plant data (images and logs)"
  type        = string
}

variable "website_bucket_name" {
  description = "S3 bucket name for website hosting"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN for bucket policy"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
