# ============================================
# S3 Module - Sử dụng existing bucket + Website
# ============================================

# Data source: Sử dụng S3 bucket hiện có cho plant data
data "aws_s3_bucket" "plant_data" {
  bucket = var.plant_data_bucket_name
}

# S3 Bucket MỚI cho Website Hosting
resource "aws_s3_bucket" "website" {
  bucket = var.website_bucket_name
  tags = merge(
    var.tags,
    {
      Name = "Plant Monitor Website"
      Type = "website"
    }
  )
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket                  = aws_s3_bucket.website.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Policy cho CloudFront
# Note: This will be applied after CloudFront distribution is created
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.website.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = var.cloudfront_distribution_arn
          }
        }
      }
    ]
  })
  
  depends_on = [
    aws_s3_bucket.website,
    aws_s3_bucket_public_access_block.website
  ]
}
