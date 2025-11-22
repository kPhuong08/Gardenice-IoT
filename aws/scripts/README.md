# Deployment Scripts

## Available Scripts

### 1. Deploy Scripts
Deploy toàn bộ infrastructure và application

**Windows PowerShell:**
```powershell
cd Gardenice-IoT\aws
.\scripts\deploy.ps1
```

**Linux/macOS/Git Bash:**
```bash
cd Gardenice-IoT/aws
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 2. Destroy Scripts
Xóa toàn bộ infrastructure (KHÔNG xóa S3 bucket iot-gardernice)

**Windows PowerShell:**
```powershell
cd Gardenice-IoT\aws
.\scripts\destroy.ps1
```

**Linux/macOS/Git Bash:**
```bash
cd Gardenice-IoT/aws
chmod +x scripts/destroy.sh
./scripts/destroy.sh
```

## Script Features

### Deploy Script (`deploy.ps1` / `deploy.sh`)

**Pre-flight Checks:**
- ✅ Terraform installed
- ✅ AWS CLI installed
- ✅ Node.js installed
- ✅ AWS credentials configured
- ✅ terraform.tfvars exists
- ✅ Backend files exist
- ✅ Frontend files exist

**Deployment Steps:**
1. **Infrastructure** (Terraform)
   - Initialize Terraform
   - Validate configuration
   - Plan changes
   - Apply infrastructure
   - Get outputs

2. **Backend** (Lambda Functions)
   - Deploy GetPlantData Lambda
   - Deploy HiveMQ Processor Lambda
   - Wait for updates to complete

3. **Frontend** (React SPA)
   - Create .env file with API endpoint
   - Install npm dependencies
   - Build React app
   - Deploy to S3
   - Invalidate CloudFront cache

**Output:**
- CloudFront domain name (website URL)
- API Gateway endpoints (Frontend API, MQTT Bridge)
- Lambda function names
- Test commands
- Log viewing commands

### Destroy Script (`destroy.ps1` / `destroy.sh`)

**Safety Features:**
- ⚠️ Requires confirmation (type 'yes')
- ✅ Preserves S3 bucket: iot-gardernice
- ✅ Backs up terraform.tfstate

**Destruction Steps:**
1. **Empty S3 Website Bucket**
   - Delete all objects
   - Delete all versions (if versioning enabled)
   - Delete all delete markers

2. **Destroy Infrastructure** (Terraform)
   - Run terraform destroy
   - Remove all AWS resources

3. **Clean Local Files**
   - Backup terraform.tfstate
   - Remove .terraform directory
   - Remove frontend build
   - Remove backend zip files

**Destroyed Resources:**
- ✅ CloudFront distribution
- ✅ Lambda functions (2)
- ✅ API Gateway endpoints (2)
- ✅ S3 website bucket
- ✅ IAM roles and policies
- ✅ CloudWatch log groups

**Preserved Resources:**
- ✅ S3 bucket: iot-gardernice (your plant data)

## Prerequisites

### Required Tools
- **Terraform** >= 1.0
- **AWS CLI** configured
- **Node.js** >= 18
- **Git Bash** (Windows) or Terminal (Linux/macOS)

### AWS Configuration
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### Terraform Configuration
```bash
cd Gardenice-IoT/aws/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

## Usage Examples

### First Time Deployment
```powershell
# 1. Configure terraform.tfvars
cd Gardenice-IoT\aws\terraform
notepad terraform.tfvars

# 2. Deploy
cd ..
.\scripts\deploy.ps1
```

### Update Deployment
```powershell
# Just run deploy again
cd Gardenice-IoT\aws
.\scripts\deploy.ps1
```

### Destroy Everything
```powershell
cd Gardenice-IoT\aws
.\scripts\destroy.ps1
# Type 'yes' to confirm
```

### Redeploy After Destroy
```powershell
cd Gardenice-IoT\aws
.\scripts\deploy.ps1
```

## Troubleshooting

### Windows: Execution Policy Error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux/macOS: Permission Denied
```bash
chmod +x scripts/deploy.sh
chmod +x scripts/destroy.sh
```

### AWS Credentials Not Configured
```bash
aws configure
# Or check:
aws sts get-caller-identity
```

### Terraform State Locked
```bash
# If terraform is locked, force unlock
cd terraform
terraform force-unlock <LOCK_ID>
```

### S3 Bucket Name Already Exists
Edit `terraform.tfvars`:
```hcl
website_bucket_name = "gardenice-website-unique-12345"
```

### CloudFront Distribution Taking Long Time
CloudFront deployment can take 15-20 minutes. Be patient!

### Lambda Deployment Failed
```bash
# Check Lambda logs
aws logs tail /aws/lambda/gardenice-get-plant-data --since 10m
```

## Manual Operations

### Deploy Only Infrastructure
```bash
cd Gardenice-IoT/aws/terraform
terraform init
terraform apply
```

### Deploy Only Lambda
```bash
cd Gardenice-IoT/aws/backend
zip function.zip get_plant_data.py
aws lambda update-function-code \
  --function-name gardenice-get-plant-data \
  --zip-file fileb://function.zip
```

### Deploy Only Frontend
```bash
cd Gardenice-IoT/aws/frontend
npm run build
aws s3 sync build/ s3://$(cd ../terraform && terraform output -raw website_bucket_name) --delete
```

### Destroy Only Infrastructure
```bash
cd Gardenice-IoT/aws/terraform
terraform destroy
```

## Cost Estimates

### Deployment Costs
- Lambda: ~$0.40/month (2 functions)
- API Gateway: ~$7.00/month (2 APIs)
- S3: ~$1.00/month (storage + requests)
- CloudFront: ~$1.00/month (data transfer)
- **Total: ~$10/month**

### Destroy Costs
- No ongoing costs after destruction
- S3 bucket iot-gardernice still incurs storage costs

## Support

### View Logs
```bash
# GetPlantData Lambda
aws logs tail /aws/lambda/gardenice-get-plant-data --follow

# HiveMQ Processor Lambda
aws logs tail /aws/lambda/gardenice-hivemq-processor --follow
```

### Get Outputs
```bash
cd Gardenice-IoT/aws/terraform
terraform output

# Get specific output
terraform output -raw api_gateway_url
terraform output -raw mqtt_api_key
```

### Test Endpoints
```bash
# Test Frontend API
curl https://your-api-endpoint/plant/plant_001

# Test MQTT Bridge
curl -X POST https://your-mqtt-endpoint/mqtt-ingest \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"topic":"gardenice/plant_001/sensors","payload":{"humidity":55.2}}'
```

## Notes

1. **Backup Important Data**: Always backup your S3 data before destroying
2. **API Keys**: Save MQTT API key securely after deployment
3. **State Files**: Keep terraform.tfstate safe (contains sensitive data)
4. **Costs**: Monitor AWS costs regularly
5. **Updates**: Run deploy script to update code without destroying infrastructure
