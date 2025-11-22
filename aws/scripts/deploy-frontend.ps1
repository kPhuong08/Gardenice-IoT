# Quick Frontend Deployment Script
# Deploy chỉ frontend (CSS, JS changes)

$ErrorActionPreference = "Stop"

Write-Host "[*] Deploying Frontend..." -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Step 1: Build
Write-Host "Step 1: Building React app..." -ForegroundColor Yellow
Set-Location (Join-Path $ProjectRoot "frontend")
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Build completed" -ForegroundColor Green
Write-Host ""

# Step 2: Get bucket info
Write-Host "Step 2: Getting S3 bucket info..." -ForegroundColor Yellow
Set-Location (Join-Path $ProjectRoot "terraform")
$WEBSITE_BUCKET = terraform output -raw website_bucket_name
$CLOUDFRONT_ID = terraform output -raw cloudfront_distribution_id

Write-Host "  Bucket: $WEBSITE_BUCKET" -ForegroundColor Cyan
Write-Host "  CloudFront: $CLOUDFRONT_ID" -ForegroundColor Cyan
Write-Host ""

# Step 3: Upload to S3
Write-Host "Step 3: Uploading to S3..." -ForegroundColor Yellow
Set-Location (Join-Path $ProjectRoot "frontend")
aws s3 sync build/ s3://$WEBSITE_BUCKET --delete

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] S3 upload failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Uploaded to S3" -ForegroundColor Green
Write-Host ""

# Step 4: Invalidate CloudFront cache
Write-Host "Step 4: Invalidating CloudFront cache..." -ForegroundColor Yellow
$INVALIDATION = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_ID `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

Write-Host "  Invalidation ID: $INVALIDATION" -ForegroundColor Cyan
Write-Host "[OK] Cache invalidated" -ForegroundColor Green
Write-Host ""

# Summary
Set-Location (Join-Path $ProjectRoot "terraform")
$CLOUDFRONT_URL = terraform output -raw cloudfront_domain_name

Write-Host "========================================" -ForegroundColor Green
Write-Host "[SUCCESS] Frontend Deployed Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Website URL:" -ForegroundColor Cyan
Write-Host "   https://$CLOUDFRONT_URL" -ForegroundColor Blue
Write-Host ""
Write-Host "CloudFront cache invalidation in progress..." -ForegroundColor Yellow
Write-Host "   Changes will be visible in 1-5 minutes" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tip: Hard refresh browser (Ctrl+Shift+R) to see changes immediately" -ForegroundColor Cyan
Write-Host ""
