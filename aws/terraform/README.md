# Terraform Infrastructure - Gardenice Plant Monitoring

## Cấu trúc Modules

```
terraform/
├── main.tf              # Root module - gọi các modules con
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Giá trị cụ thể (không commit)
└── modules/
    ├── s3/              # S3 buckets (data + website)
    ├── cloudfront/      # CloudFront CDN
    ├── lambda/          # Lambda function
    └── api-gateway/     # API Gateway REST API
```

## Modules Chi Tiết

### 1. S3 Module (`modules/s3/`)
**Chức năng**: Tạo 2 S3 buckets
- **Plant Data Bucket**: Lưu trữ images và logs
- **Website Bucket**: Host React SPA

**Resources**:
- `aws_s3_bucket` x2
- `aws_s3_bucket_versioning`
- `aws_s3_bucket_public_access_block`
- `aws_s3_bucket_website_configuration`
- `aws_s3_bucket_policy`

### 2. CloudFront Module (`modules/cloudfront/`)
**Chức năng**: CDN distribution cho website

**Resources**:
- `aws_cloudfront_distribution`
- `aws_cloudfront_origin_access_control`

**Features**:
- HTTPS redirect
- SPA routing support (404 → index.html)
- Cache optimization
- Global edge locations

### 3. Lambda Module (`modules/lambda/`)
**Chức năng**: Serverless function để xử lý API requests

**Resources**:
- `aws_lambda_function`
- `aws_iam_role` (execution role)
- `aws_iam_role_policy` (S3 + CloudWatch)
- `aws_cloudwatch_log_group`

**Permissions**:
- `s3:GetObject`, `s3:ListBucket` trên plant data bucket
- `logs:*` cho CloudWatch

### 4. API Gateway Module (`modules/api-gateway/`)
**Chức năng**: REST API endpoint

**Resources**:
- `aws_api_gateway_rest_api`
- `aws_api_gateway_resource` (routes)
- `aws_api_gateway_method` (GET, OPTIONS)
- `aws_api_gateway_integration` (Lambda proxy)
- `aws_api_gateway_deployment`
- `aws_api_gateway_stage`

**Endpoints**:
- `GET /plant/{plant_id}` - Lấy thông tin plant
- `OPTIONS /plant/{plant_id}` - CORS preflight

## Cách Sử Dụng

### 1. Chuẩn bị

```bash
cd Gardenice-IoT/aws/terraform

# Copy file example và chỉnh sửa
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Chỉnh sửa `terraform.tfvars`:
```hcl
aws_region             = "us-east-1"
environment            = "dev"
project_name           = "gardenice"
plant_data_bucket_name = "gardenice-plant-data-dev"  # Phải unique
website_bucket_name    = "gardenice-website-dev"     # Phải unique
ec2_service_url        = "http://your-ec2-ip:8000"   # URL thực tế
```

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Xem plan trước khi apply
terraform plan

# Deploy
terraform apply

# Hoặc auto-approve
terraform apply -auto-approve
```

### 3. Lấy Outputs

```bash
# Xem tất cả outputs
terraform output

# Lấy giá trị cụ thể
terraform output cloudfront_domain_name
terraform output api_gateway_url
```

### 4. Deploy Frontend

```bash
cd ../frontend

# Tạo .env file với API endpoint
echo "REACT_APP_API_ENDPOINT=$(cd ../terraform && terraform output -raw api_gateway_url)" > .env

# Build và deploy
npm install
npm run build

# Upload lên S3
BUCKET_NAME=$(cd ../terraform && terraform output -raw website_bucket_name)
aws s3 sync build/ s3://$BUCKET_NAME --delete

# Invalidate CloudFront cache
DIST_ID=$(cd ../terraform && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

### 5. Upload Plant Data

```bash
# Upload images
aws s3 cp plant_001/images/ s3://gardenice-plant-data-dev/plant_001/images/ --recursive

# Upload logs
aws s3 cp plant_001/logs/ s3://gardenice-plant-data-dev/plant_001/logs/ --recursive
```

## Quản Lý Modules

### Thêm Module Mới

1. Tạo thư mục module:
```bash
mkdir -p modules/new-module
cd modules/new-module
```

2. Tạo 3 files cơ bản:
```bash
touch main.tf variables.tf outputs.tf
```

3. Gọi module trong `main.tf`:
```hcl
module "new_module" {
  source = "./modules/new-module"
  
  # Variables
  param1 = "value1"
  
  tags = local.common_tags
}
```

### Update Module

```bash
# Sau khi sửa code trong module
terraform init -upgrade
terraform plan
terraform apply
```

### Xóa Resources

```bash
# Xóa toàn bộ infrastructure
terraform destroy

# Xóa resource cụ thể
terraform destroy -target=module.lambda
```

## Best Practices

### 1. Module Design
- Mỗi module nên có 1 chức năng rõ ràng
- Luôn có `variables.tf`, `main.tf`, `outputs.tf`
- Sử dụng `tags` cho tất cả resources

### 2. Variables
- Đặt default values hợp lý
- Thêm description cho mọi variable
- Sử dụng type constraints

### 3. Outputs
- Export những giá trị cần thiết
- Thêm description rõ ràng
- Sử dụng outputs của module trong root

### 4. State Management
```hcl
# Nên dùng remote backend (S3 + DynamoDB)
terraform {
  backend "s3" {
    bucket         = "gardenice-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Troubleshooting

### Module not found
```bash
terraform init
```

### S3 bucket name already exists
Đổi tên bucket trong `terraform.tfvars`:
```hcl
plant_data_bucket_name = "gardenice-plant-data-dev-unique123"
```

### Lambda deployment package too large
Sử dụng Lambda layers hoặc container image:
```hcl
# Trong modules/lambda/main.tf
resource "aws_lambda_layer_version" "dependencies" {
  filename   = "layer.zip"
  layer_name = "python-dependencies"
}
```

### CloudFront cache không update
```bash
# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

## Cost Estimation

### Monthly Cost (1000 users, 10 requests/day)
- **Lambda**: ~$0.20 (300K requests)
- **API Gateway**: ~$3.50 (300K requests)
- **S3**: ~$1.00 (10GB storage)
- **CloudFront**: ~$5.00 (100GB transfer)
- **Total**: ~$10/month

### Cost Optimization
```hcl
# Trong modules/cloudfront/variables.tf
variable "price_class" {
  default = "PriceClass_100"  # Chỉ US, Canada, Europe
}

# Trong modules/lambda/variables.tf
variable "memory_size" {
  default = 128  # Minimum memory
}
```

## Security Checklist

- ✅ S3 buckets private (block public access)
- ✅ CloudFront OAC (không dùng OAI cũ)
- ✅ Lambda IAM role với least privilege
- ✅ API Gateway CORS configured
- ✅ Pre-signed URLs với expiration
- ✅ CloudWatch logs enabled
- ✅ S3 versioning enabled
- ✅ HTTPS only (CloudFront)

## Monitoring

### CloudWatch Dashboards
```bash
# Xem Lambda logs
aws logs tail /aws/lambda/gardenice-get-plant-data --follow

# Xem API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=gardenice-api \
  --start-time 2024-11-22T00:00:00Z \
  --end-time 2024-11-22T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
