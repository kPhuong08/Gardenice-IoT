#!/bin/bash
# Destroy Script for Gardenice Plant Monitoring Application
# Xóa toàn bộ infrastructure (KHÔNG xóa S3 bucket iot-gardernice hiện có)

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${RED}🗑️  Gardenice Destroy Script${NC}"
echo -e "${RED}=============================${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will destroy all AWS resources!${NC}"
echo -e "${YELLOW}    - CloudFront distribution${NC}"
echo -e "${YELLOW}    - Lambda functions (2)${NC}"
echo -e "${YELLOW}    - API Gateway endpoints (2)${NC}"
echo -e "${YELLOW}    - S3 website bucket (NEW)${NC}"
echo -e "${YELLOW}    - IAM roles and policies${NC}"
echo ""
echo -e "${GREEN}✅ Will NOT delete:${NC}"
echo -e "${GREEN}    - S3 bucket: iot-gardernice (your existing data)${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Confirmation
read -p "Are you sure you want to destroy all resources? Type 'yes' to confirm: " confirmation
if [ "$confirmation" != "yes" ]; then
    echo -e "${YELLOW}❌ Destroy cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}Starting destruction process...${NC}"
echo ""

# ============================================
# Step 1: Empty S3 Website Bucket
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 1: Emptying S3 Website Bucket${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_ROOT/terraform"

# Get website bucket name
WEBSITE_BUCKET=$(terraform output -raw website_bucket_name 2>/dev/null || echo "")

if [ -n "$WEBSITE_BUCKET" ]; then
    echo "Emptying bucket: $WEBSITE_BUCKET"
    
    # Delete all objects
    aws s3 rm s3://$WEBSITE_BUCKET --recursive 2>/dev/null || true
    
    # Delete all versions (if versioning enabled)
    aws s3api list-object-versions \
        --bucket $WEBSITE_BUCKET \
        --query 'Versions[].{Key:Key,VersionId:VersionId}' \
        --output json 2>/dev/null | \
    jq -r '.[] | "--key \(.Key) --version-id \(.VersionId)"' | \
    while read -r args; do
        aws s3api delete-object --bucket $WEBSITE_BUCKET $args 2>/dev/null || true
    done
    
    # Delete all delete markers
    aws s3api list-object-versions \
        --bucket $WEBSITE_BUCKET \
        --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' \
        --output json 2>/dev/null | \
    jq -r '.[] | "--key \(.Key) --version-id \(.VersionId)"' | \
    while read -r args; do
        aws s3api delete-object --bucket $WEBSITE_BUCKET $args 2>/dev/null || true
    done
    
    echo -e "${GREEN}✓ Website bucket emptied${NC}"
else
    echo -e "${YELLOW}⚠️  Website bucket not found (may already be deleted)${NC}"
fi

# ============================================
# Step 2: Destroy Infrastructure with Terraform
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 2: Destroying Infrastructure (Terraform)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Running terraform destroy...${NC}"
terraform destroy -auto-approve

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform destroy failed${NC}"
    echo -e "${YELLOW}You may need to manually delete some resources${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Infrastructure destroyed${NC}"

# ============================================
# Step 3: Clean up local files
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 3: Cleaning up local files${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Clean terraform files
if [ -f "terraform.tfstate" ]; then
    echo "Backing up terraform.tfstate..."
    cp terraform.tfstate terraform.tfstate.destroyed.backup
    rm terraform.tfstate
fi

if [ -f "terraform.tfstate.backup" ]; then
    rm terraform.tfstate.backup
fi

if [ -d ".terraform" ]; then
    echo "Removing .terraform directory..."
    rm -rf .terraform
fi

if [ -f ".terraform.lock.hcl" ]; then
    rm .terraform.lock.hcl
fi

# Clean frontend build
if [ -d "$PROJECT_ROOT/frontend/build" ]; then
    echo "Removing frontend build..."
    rm -rf "$PROJECT_ROOT/frontend/build"
fi

if [ -f "$PROJECT_ROOT/frontend/.env" ]; then
    rm "$PROJECT_ROOT/frontend/.env"
fi

# Clean backend zip files
rm -f "$PROJECT_ROOT/backend"/*.zip

echo -e "${GREEN}✓ Local files cleaned${NC}"

# ============================================
# Summary
# ============================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Destruction Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📊 Destroyed Resources:"
echo "  ✓ CloudFront distribution"
echo "  ✓ Lambda functions (GetPlantData, HiveMQ Processor)"
echo "  ✓ API Gateway endpoints (Frontend API, MQTT Bridge)"
echo "  ✓ S3 website bucket"
echo "  ✓ IAM roles and policies"
echo "  ✓ CloudWatch log groups"
echo ""
echo -e "${GREEN}✅ Preserved Resources:${NC}"
echo -e "${GREEN}  ✓ S3 bucket: iot-gardernice (your plant data)${NC}"
echo ""
echo "📝 Notes:"
echo "  - terraform.tfstate backed up to: terraform.tfstate.destroyed.backup"
echo "  - To redeploy, run: ./scripts/deploy.sh"
echo ""
