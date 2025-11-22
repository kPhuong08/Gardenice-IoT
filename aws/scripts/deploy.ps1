# PowerShell Deployment Script for Gardenice Plant Monitoring Application
# Dành cho Windows PowerShell
# Includes: Frontend, Backend (2 Lambda functions), MQTT Bridge

$ErrorActionPreference = "Stop"

Write-Host " Gardenice Deployment Script v2.0 (PowerShell)" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# ============================================
# Pre-flight Checks
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pre-flight Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

Write-Host "Checking prerequisites..." -ForegroundColor Cyan

if (-not (Test-Command "terraform")) {
    Write-Host "Terraform is required but not installed." -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "aws")) {
    Write-Host "AWS CLI is required but not installed." -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "node")) {
    Write-Host "Node.js is required but not installed." -ForegroundColor Red
    exit 1
}

Write-Host "All prerequisites installed" -ForegroundColor Green

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Cyan
$AccountId = aws sts get-caller-identity --query Account --output text 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "AWS credentials not configured." -ForegroundColor Red
    Write-Host "Run: aws configure" -ForegroundColor Yellow
    exit 1
}
Write-Host "AWS credentials configured (Account: $AccountId)" -ForegroundColor Green

# Check terraform.tfvars
$TfVarsPath = Join-Path $ProjectRoot "terraform\terraform.tfvars"
if (-not (Test-Path $TfVarsPath)) {
    Write-Host "File terraform.tfvars not found!" -ForegroundColor Red
    Write-Host "Please create it from terraform.tfvars.example" -ForegroundColor Yellow
    exit 1
}
Write-Host "terraform.tfvars found" -ForegroundColor Green

# Check backend files
$GetPlantDataPath = Join-Path $ProjectRoot "backend\get_plant_data.py"
$HiveMQProcessorPath = Join-Path $ProjectRoot "backend\hivemq_processor.py"
if (-not (Test-Path $GetPlantDataPath)) {
    Write-Host "get_plant_data.py not found!" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $HiveMQProcessorPath)) {
    Write-Host "hivemq_processor.py not found!" -ForegroundColor Red
    exit 1
}
Write-Host "Backend Lambda functions found" -ForegroundColor Green

# Check frontend files
$PackageJsonPath = Join-Path $ProjectRoot "frontend\package.json"
if (-not (Test-Path $PackageJsonPath)) {
    Write-Host "Frontend package.json not found!" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend files found" -ForegroundColor Green

# ============================================
# Step 1: Deploy Infrastructure
# ============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Step 1: Deploying Infrastructure (Terraform)" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

Set-Location (Join-Path $ProjectRoot "terraform")

# Initialize Terraform
Write-Host "Initializing Terraform..." -ForegroundColor Cyan
terraform init -upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform init failed" -ForegroundColor Red
    exit 1
}

# Validate
Write-Host "Validating Terraform configuration..." -ForegroundColor Cyan
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform validation failed" -ForegroundColor Red
    exit 1
}

# Plan
Write-Host "Running terraform plan..." -ForegroundColor Yellow
terraform plan -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform plan failed" -ForegroundColor Red
    exit 1
}

# Apply
Write-Host "Applying terraform changes..." -ForegroundColor Yellow
terraform apply tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform apply failed" -ForegroundColor Red
    exit 1
}
Remove-Item tfplan -ErrorAction SilentlyContinue

# Get outputs
Write-Host "Retrieving Terraform outputs..." -ForegroundColor Cyan
$API_ENDPOINT = terraform output -raw api_gateway_url
$CLOUDFRONT_DOMAIN = terraform output -raw cloudfront_domain_name
$CLOUDFRONT_ID = terraform output -raw cloudfront_distribution_id
$WEBSITE_BUCKET = terraform output -raw website_bucket_name
$LAMBDA_FUNCTION = terraform output -raw lambda_function_name
$MQTT_LAMBDA_FUNCTION = terraform output -raw mqtt_lambda_function_name
$MQTT_INGEST_URL = terraform output -raw mqtt_ingest_url

Write-Host "Infrastructure deployed" -ForegroundColor Green
Write-Host "  Frontend API: $API_ENDPOINT"
Write-Host "  MQTT Bridge: $MQTT_INGEST_URL"
Write-Host "  CloudFront: $CLOUDFRONT_DOMAIN"
Write-Host "  Website Bucket: $WEBSITE_BUCKET"

# ============================================
# Step 2: Deploy Lambda Functions
# ============================================
Write-Host ""
Write-Host "=======================================" -ForegroundColor Blue
Write-Host "Step 2: Deploying Lambda Functions" -ForegroundColor Blue
Write-Host "=======================================" -ForegroundColor Blue

Set-Location (Join-Path $ProjectRoot "backend")

# Deploy GetPlantData Lambda
Write-Host "Deploying GetPlantData Lambda..." -ForegroundColor Cyan
if (Test-Path "get_plant_data.zip") {
    Remove-Item "get_plant_data.zip"
}
Compress-Archive -Path "get_plant_data.py" -DestinationPath "get_plant_data.zip" -Force

aws lambda update-function-code `
  --function-name $LAMBDA_FUNCTION `
  --zip-file fileb://get_plant_data.zip `
  --no-cli-pager

if ($LASTEXITCODE -ne 0) {
    Write-Host "GetPlantData Lambda deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "Waiting for GetPlantData Lambda update..." -ForegroundColor Cyan
aws lambda wait function-updated --function-name $LAMBDA_FUNCTION
Remove-Item "get_plant_data.zip"
Write-Host "GetPlantData Lambda deployed" -ForegroundColor Green

# Deploy HiveMQ Processor Lambda
Write-Host "Deploying HiveMQ Processor Lambda..." -ForegroundColor Cyan
if (Test-Path "hivemq_processor.zip") {
    Remove-Item "hivemq_processor.zip"
}
Compress-Archive -Path "hivemq_processor.py" -DestinationPath "hivemq_processor.zip" -Force

aws lambda update-function-code `
  --function-name $MQTT_LAMBDA_FUNCTION `
  --zip-file fileb://hivemq_processor.zip `
  --no-cli-pager

if ($LASTEXITCODE -ne 0) {
    Write-Host "HiveMQ Processor Lambda deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "Waiting for HiveMQ Processor Lambda update..." -ForegroundColor Cyan
aws lambda wait function-updated --function-name $MQTT_LAMBDA_FUNCTION
Remove-Item "hivemq_processor.zip"
Write-Host "HiveMQ Processor Lambda deployed" -ForegroundColor Green

# ============================================
# Step 3: Build and Deploy Frontend
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Step 3: Building and Deploying Frontend" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

Set-Location (Join-Path $ProjectRoot "frontend")

# Create .env file
Write-Host "Creating .env file..." -ForegroundColor Cyan
@"
REACT_APP_API_ENDPOINT=$API_ENDPOINT
REACT_APP_PLANT_ID=plant_001
"@ | Out-File -FilePath ".env" -Encoding utf8

# Install dependencies
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "npm install failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "npm dependencies already installed (skipping)" -ForegroundColor Cyan
}

# Build
Write-Host "Building React app..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm build failed" -ForegroundColor Red
    exit 1
}

# Deploy to S3
Write-Host "Deploying to S3..." -ForegroundColor Cyan
aws s3 sync build/ s3://$WEBSITE_BUCKET --delete
if ($LASTEXITCODE -ne 0) {
    Write-Host "S3 sync failed" -ForegroundColor Red
    exit 1
}

# Invalidate CloudFront cache
Write-Host "Invalidating CloudFront cache..." -ForegroundColor Cyan
$INVALIDATION_ID = aws cloudfront create-invalidation `
  --distribution-id $CLOUDFRONT_ID `
  --paths "/*" `
  --query 'Invalidation.Id' `
  --output text

Write-Host "CloudFront invalidation created: $INVALIDATION_ID" -ForegroundColor Cyan
Write-Host "Frontend deployed" -ForegroundColor Green

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Detployment Summary:"
Write-Host "  Infrastructure: Deployed"
Write-Host "  Lambda Functions:"
Write-Host "    - GetPlantData: $LAMBDA_FUNCTION"
Write-Host "    - HiveMQ Processor: $MQTT_LAMBDA_FUNCTION"
Write-Host "  API Endpoints:"
Write-Host "    - Frontend API: $API_ENDPOINT"
Write-Host "    - MQTT Bridge: $MQTT_INGEST_URL"
Write-Host "  Frontend: Deployed to S3"
Write-Host "  CloudFront: Cache invalidated"
Write-Host ""
Write-Host "Your application is available at:" -ForegroundColor Cyan
Write-Host "   https://$CLOUDFRONT_DOMAIN" -ForegroundColor Blue
Write-Host ""
Write-Host "Test Commands:"
Write-Host ""
Write-Host "  # Test Frontend API"
Write-Host "  curl $API_ENDPOINT/plant_001"
Write-Host ""
Write-Host "  # Test MQTT Bridge (requires API Key)"
Write-Host "  `$API_KEY = terraform output -raw mqtt_api_key"
Write-Host "  curl -X POST $MQTT_INGEST_URL ``"
Write-Host "    -H `"x-api-key: `$API_KEY`" ``"
Write-Host "    -H `"Content-Type: application/json`" ``"
Write-Host "    -d '{`"topic`":`"gardenice/plant_001/sensors`",`"payload`":{`"humidity`":55.2}}'"
Write-Host ""
Write-Host "View Logs:"
Write-Host "  aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow"
Write-Host "  aws logs tail /aws/lambda/$MQTT_LAMBDA_FUNCTION --follow"
Write-Host ""
Write-Host "Get MQTT API Key:"
Write-Host "  cd terraform"
Write-Host "  terraform output -raw mqtt_api_key"
Write-Host ""
