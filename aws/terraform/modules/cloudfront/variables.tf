variable "distribution_name" {
  description = "CloudFront distribution name"
  type        = string
}

variable "distribution_comment" {
  description = "CloudFront distribution comment"
  type        = string
  default     = "Plant Monitor CDN"
}

variable "s3_bucket_regional_domain_name" {
  description = "S3 bucket regional domain name"
  type        = string
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "min_ttl" {
  description = "Minimum TTL for cache"
  type        = number
  default     = 0
}

variable "default_ttl" {
  description = "Default TTL for cache"
  type        = number
  default     = 3600
}

variable "max_ttl" {
  description = "Maximum TTL for cache"
  type        = number
  default     = 86400
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
