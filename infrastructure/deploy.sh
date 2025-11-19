#!/bin/bash

# ============================================================================
# AWS SAM Deployment Script for Sentiment Finance Pipeline
# ============================================================================

set -e

# Configuration
STACK_NAME="sentiment-finance-pipeline"
REGION="us-east-1"
ENVIRONMENT="dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Sentiment Finance Pipeline${NC}"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed. Please install it first.${NC}"
    echo "Install with: pip install aws-sam-cli"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}🔍 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials configured for account: $ACCOUNT_ID${NC}"

# Prompt for sensitive parameters
echo
echo -e "${YELLOW}📝 Please provide the following parameters:${NC}"

# Database password
while true; do
    echo -n "Enter RDS MySQL password (min 8 characters): "
    read -s DB_PASSWORD
    echo
    if [[ ${#DB_PASSWORD} -ge 8 ]]; then
        break
    else
        echo -e "${RED}Password must be at least 8 characters long${NC}"
    fi
done

# News API key
echo -n "Enter News API key (get from https://newsapi.org): "
read NEWS_API_KEY
echo

# Create S3 bucket for SAM artifacts if it doesn't exist
BUCKET_NAME="sam-artifacts-${ACCOUNT_ID}-${REGION}"
echo -e "${YELLOW}📦 Creating/checking S3 bucket for SAM artifacts...${NC}"

if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: $BUCKET_NAME"
    if [[ "$REGION" == "us-east-1" ]]; then
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
    else
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
    fi
else
    echo "S3 bucket $BUCKET_NAME already exists"
fi

# Build and package
echo
echo -e "${YELLOW}🔨 Building SAM application...${NC}"
sam build --template-file template.yaml

# Deploy the stack
echo
echo -e "${YELLOW}🚢 Deploying stack...${NC}"
sam deploy \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "$STACK_NAME" \
    --s3-bucket "$BUCKET_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        DBPassword="$DB_PASSWORD" \
        NewsAPIKey="$NEWS_API_KEY" \
    --confirm-changeset

if [[ $? -eq 0 ]]; then
    echo
    echo -e "${GREEN}✅ Deployment successful!${NC}"

    # Get outputs
    echo
    echo -e "${YELLOW}📋 Stack Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table

    # Get Lambda function name for GitHub Actions
    LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
        --output text)

    echo
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Set up GitHub Actions secrets in your repository:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - AWS_REGION=$REGION"
    echo "   - LAMBDA_FUNCTION_NAME=$LAMBDA_FUNCTION_NAME"
    echo
    echo "2. Initialize the database by running the SQL schema:"
    echo "   Connect to the RDS instance and run sql/schema.sql"
    echo
    echo "3. Test the Lambda function:"
    echo "   aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME response.json"
    echo
    echo -e "${YELLOW}Database connection details:${NC}"
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text)
    echo "Endpoint: $DB_ENDPOINT"
    echo "Port: 3306"
    echo "Database: sentiment_finance"
    echo "Username: admin"
    echo "Password: [the password you provided]"

else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi