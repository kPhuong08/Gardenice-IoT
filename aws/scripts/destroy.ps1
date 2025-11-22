# PowerShell Destroy Script for Gardenice Plant Monitoring Application
# Xóa toàn bộ infrastructure (KHÔNG xóa S3 bucket iot-gardernice hiện có)

$ErrorActionPreference = "Stop"

Write-Host "🗑️  Gardenice Destroy Script" -ForegroundColor Red
Write-Host "=============================" -ForegroundColor Red
Write-Host ""
Write-Host "⚠️  WARNING: This will destroy all AWS resources!" -ForegroundColor Yellow
Write-Host "    - CloudFront distribution" -ForegroundColor Yellow
Write-Host "    - Lambda functions (2)" -ForegroundColor Yellow
Write-Host "    - API Gateway endpoints (2)" -ForegroundColor Yellow
Write-Host "    - S3 website bucket (NEW)" -ForegroundColor Yellow
Write-Host "    - IAM roles and policies" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Will NOT delete:" -ForegroundColor Green
Write-Host "    - S3 bucket: iot-gardernice (your existing data)" -ForegroundColor Green
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Confirmation
$confirmation = Read-Host "Are you sure you want to destroy all resources? Type 'yes' to confirm"
if ($confirmation -ne 'yes') {
    Write-Host "❌ Destroy cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Starting destruction process..." -ForegroundColor Red
Write-Host ""

# ============================================
# Step 1: Empty S3 Website Bucket
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Step 1: Emptying S3 Website Bucket" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Set-Location (Join-Path $ProjectRoot "terraform")

# Get website bucket name
$WEBSITE_BUCKET = terraform output -raw website_bucket_name 2>$null

if ($LASTEXITCODE -eq 0 -and $WEBSITE_BUCKET) {
    Write-Host "Emptying bucket: $WEBSITE_BUCKET" -ForegroundColor Cyan
    
    # Delete all objects
    aws s3 rm s3://$WEBSITE_BUCKET --recursive 2>$null
    
    # Delete all versions (if versioning enabled)
    $versions = aws s3api list-object-versions --bucket $WEBSITE_BUCKET --query 'Versions[].{Key:Key,VersionId:VersionId}' --output json 2>$null | ConvertFrom-Json
    if ($versions) {
        foreach ($version in $versions) {
            aws s3api delete-object --bucket $WEBSITE_BUCKET --key $version.Key --version-id $version.VersionId 2>$null
        }
    }
    
    # Delete all delete markers
    $deleteMarkers = aws s3api list-object-versions --bucket $WEBSITE_BUCKET --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output json 2>$null | ConvertFrom-Json
    if ($deleteMarkers) {
        foreach ($marker in $deleteMarkers) {
            aws s3api delete-object --bucket $WEBSITE_BUCKET --key $marker.Key --version-id $marker.VersionId 2>$null
        }
    }
    
    Write-Host "✓ Website bucket emptied" -ForegroundColor Green
} else {
    Write-Host "⚠️  Website bucket not found (may already be deleted)" -ForegroundColor Yellow
}

# ============================================
# Step 2: Destroy Infrastructure with Terraform
# ============================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Step 2: Destroying Infrastructure (Terraform)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host "Running terraform destroy..." -ForegroundColor Yellow
terraform destroy -auto-approve

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform destroy failed" -ForegroundColor Red
    Write-Host "You may need to manually delete some resources" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Infrastructure destroyed" -ForegroundColor Green

# ============================================
# Step 3: Clean up local files
# ============================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Step 3: Cleaning up local files" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Clean terraform files
if (Test-Path "terraform.tfstate") {
    Write-Host "Backing up terraform.tfstate..." -ForegroundColor Cyan
    Copy-Item "terraform.tfstate" "terraform.tfstate.destroyed.backup"
    Remove-Item "terraform.tfstate"
}

if (Test-Path "terraform.tfstate.backup") {
    Remove-Item "terraform.tfstate.backup"
}

if (Test-Path ".terraform") {
    Write-Host "Removing .terraform directory..." -ForegroundColor Cyan
    Remove-Item ".terraform" -Recurse -Force
}

if (Test-Path ".terraform.lock.hcl") {
    Remove-Item ".terraform.lock.hcl"
}

# Clean frontend build
$FrontendBuildPath = Join-Path $ProjectRoot "frontend\build"
if (Test-Path $FrontendBuildPath) {
    Write-Host "Removing frontend build..." -ForegroundColor Cyan
    Remove-Item $FrontendBuildPath -Recurse -Force
}

$FrontendEnvPath = Join-Path $ProjectRoot "frontend\.env"
if (Test-Path $FrontendEnvPath) {
    Remove-Item $FrontendEnvPath
}

# Clean backend zip files
$BackendPath = Join-Path $ProjectRoot "backend"
Get-ChildItem -Path $BackendPath -Filter "*.zip" | Remove-Item

Write-Host "✓ Local files cleaned" -ForegroundColor Green

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ Destruction Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Destroyed Resources:"
Write-Host "  ✓ CloudFront distribution"
Write-Host "  ✓ Lambda functions (GetPlantData, HiveMQ Processor)"
Write-Host "  ✓ API Gateway endpoints (Frontend API, MQTT Bridge)"
Write-Host "  ✓ S3 website bucket"
Write-Host "  ✓ IAM roles and policies"
Write-Host "  ✓ CloudWatch log groups"
Write-Host ""
Write-Host "✅ Preserved Resources:" -ForegroundColor Green
Write-Host "  ✓ S3 bucket: iot-gardernice (your plant data)" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Notes:"
Write-Host "  - terraform.tfstate backed up to: terraform.tfstate.destroyed.backup"
Write-Host "  - To redeploy, run: .\scripts\deploy.ps1"
Write-Host ""
