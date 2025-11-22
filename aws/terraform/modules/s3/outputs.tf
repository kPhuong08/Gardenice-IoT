output "plant_data_bucket_id" {
  description = "Plant data bucket ID (existing bucket)"
  value       = data.aws_s3_bucket.plant_data.id
}

output "plant_data_bucket_arn" {
  description = "Plant data bucket ARN (existing bucket)"
  value       = data.aws_s3_bucket.plant_data.arn
}

output "website_bucket_id" {
  description = "Website bucket ID (newly created)"
  value       = aws_s3_bucket.website.id
}

output "website_bucket_arn" {
  description = "Website bucket ARN (newly created)"
  value       = aws_s3_bucket.website.arn
}

output "website_bucket_regional_domain_name" {
  description = "Website bucket regional domain name"
  value       = aws_s3_bucket.website.bucket_regional_domain_name
}
