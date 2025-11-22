#!/bin/bash
# Deployment script for Gardenice Plant Monitoring Application
# Hỗ trợ: Linux, macOS, Windows (Git Bash/WSL)
# Includes: Frontend, Backend (2 Lambda functions), MQTT Bridge

set -e

echo "🌱 Gardenice Deployment Script v2.0"
echo "===================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Project Root: $PROJECT_ROOT${NC}"
echo ""

# ============================================
# Pre-flight Checks
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Pre-flight Checks${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check prerequisites
echo "Checking prerequisites..."
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}❌ Terraform is required but not installed.${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}❌ AWS CLI is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js is required but not installed.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ All prerequisites installed${NC}"

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity >/dev/null 2>&1 || { echo -e "${RED}❌ AWS credentials not configured.${NC}" >&2; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials configured (Account: $ACCOUNT_ID)${NC}"

# Check terraform.tfvars exists
if [ ! -f "$PROJECT_ROOT/terraform/terraform.tfvars" ]; then
    echo -e "${RED}❌ File terraform.tfvars not found!${NC}"
    echo "Please create it from terraform.tfvars.example"
    exit 1
fi
echo -e "${GREEN}✓ terraform.tfvars found${NC}"

# Check backend files exist
if [ ! -f "$PROJECT_ROOT/backend/get_plant_data.py" ]; then
    echo -e "${RED}❌ get_plant_data.py not found!${NC}"
    exit 1
fi
if [ ! -f "$PROJECT_ROOT/backend/hivemq_processor.py" ]; then
    echo -e "${RED}❌ hivemq_processor.py not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend Lambda functions found${NC}"

# Check frontend files exist
if [ ! -f "$PROJECT_ROOT/frontend/package.json" ]; then
    echo -e "${RED}❌ Frontend package.json not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Frontend files found${NC}"

# ============================================
# Step 1: Deploy Infrastructure
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Deploying Infrastructure (Terraform)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd "$PROJECT_ROOT/terraform"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate || { echo -e "${RED}❌ Terraform validation failed${NC}"; exit 1; }

# Plan
echo -e "${YELLOW}Running terraform plan...${NC}"
terraform plan -out=tfplan

# Apply
echo -e "${YELLOW}Applying terraform changes...${NC}"
terraform apply tfplan
rm -f tfplan

# Get outputs
echo "Retrieving Terraform outputs..."
API_ENDPOINT=$(terraform output -raw api_gateway_url)
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
WEBSITE_BUCKET=$(terraform output -raw website_bucket_name)
LAMBDA_FUNCTION=$(terraform output -raw lambda_function_name)
MQTT_LAMBDA_FUNCTION=$(terraform output -raw mqtt_lambda_function_name)
MQTT_INGEST_URL=$(terraform output -raw mqtt_ingest_url)

echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo "  Frontend API: $API_ENDPOINT"
echo "  MQTT Bridge: $MQTT_INGEST_URL"
echo "  CloudFront: $CLOUDFRONT_DOMAIN"
echo "  Website Bucket: $WEBSITE_BUCKET"

# ============================================
# Step 2: Deploy Lambda Functions
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Deploying Lambda Functions${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd "$PROJECT_ROOT/backend"

# Deploy GetPlantData Lambda
echo "Deploying GetPlantData Lambda..."
if [ -f get_plant_data.zip ]; then
    rm get_plant_data.zip
fi
zip -q get_plant_data.zip get_plant_data.py

aws lambda update-function-code \
  --function-name "$LAMBDA_FUNCTION" \
  --zip-file fileb://get_plant_data.zip \
  --no-cli-pager

echo "Waiting for GetPlantData Lambda update..."
aws lambda wait function-updated --function-name "$LAMBDA_FUNCTION"
rm get_plant_data.zip
echo -e "${GREEN}✓ GetPlantData Lambda deployed${NC}"

# Deploy HiveMQ Processor Lambda
echo "Deploying HiveMQ Processor Lambda..."
if [ -f hivemq_processor.zip ]; then
    rm hivemq_processor.zip
fi
zip -q hivemq_processor.zip hivemq_processor.py

aws lambda update-function-code \
  --function-name "$MQTT_LAMBDA_FUNCTION" \
  --zip-file fileb://hivemq_processor.zip \
  --no-cli-pager

echo "Waiting for HiveMQ Processor Lambda update..."
aws lambda wait function-updated --function-name "$MQTT_LAMBDA_FUNCTION"
rm hivemq_processor.zip
echo -e "${GREEN}✓ HiveMQ Processor Lambda deployed${NC}"

# ============================================
# Step 3: Build and Deploy Frontend
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Building and Deploying Frontend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd "$PROJECT_ROOT/frontend"

# Create .env file
echo "Creating .env file..."
cat > .env << EOF
REACT_APP_API_ENDPOINT=$API_ENDPOINT
REACT_APP_PLANT_ID=plant_001
EOF

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "npm dependencies already installed (skipping)"
fi

# Build
echo "Building React app..."
npm run build

# Deploy to S3
echo "Deploying to S3..."
aws s3 sync build/ s3://$WEBSITE_BUCKET --delete --no-progress

# Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)

echo "CloudFront invalidation created: $INVALIDATION_ID"
echo -e "${GREEN}✓ Frontend deployed${NC}"

# ============================================
# Summary
# ============================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📊 Deployment Summary:"
echo "  ✓ Infrastructure: Deployed"
echo "  ✓ Lambda Functions:"
echo "    - GetPlantData: $LAMBDA_FUNCTION"
echo "    - HiveMQ Processor: $MQTT_LAMBDA_FUNCTION"
echo "  ✓ API Endpoints:"
echo "    - Frontend API: $API_ENDPOINT"
echo "    - MQTT Bridge: $MQTT_INGEST_URL"
echo "  ✓ Frontend: Deployed to S3"
echo "  ✓ CloudFront: Cache invalidated"
echo ""
echo "🌐 Your application is available at:"
echo -e "${CYAN}   https://$CLOUDFRONT_DOMAIN${NC}"
echo ""
echo "🧪 Test Commands:"
echo ""
echo "  # Test Frontend API"
echo "  curl $API_ENDPOINT/plant_001"
echo ""
echo "  # Test MQTT Bridge (requires API Key)"
echo "  API_KEY=\$(cd $PROJECT_ROOT/terraform && terraform output -raw mqtt_api_key)"
echo "  curl -X POST $MQTT_INGEST_URL \\"
echo "    -H \"x-api-key: \$API_KEY\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"topic\":\"gardenice/plant_001/sensors\",\"payload\":{\"humidity\":55.2}}'"
echo ""
echo "📝 View Logs:"
echo "  # GetPlantData Lambda"
echo "  aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow"
echo ""
echo "  # HiveMQ Processor Lambda"
echo "  aws logs tail /aws/lambda/$MQTT_LAMBDA_FUNCTION --follow"
echo ""
echo "🔑 Get MQTT API Key:"
echo "  cd $PROJECT_ROOT/terraform && terraform output -raw mqtt_api_key"
echo ""
