# ============================================================================
# Windows PowerShell Deployment Script for Sentiment Finance Pipeline
# ============================================================================

param(
    [Parameter()]
    [string]$StackName = "sentiment-finance-pipeline",
    
    [Parameter()]
    [string]$Region = "us-east-1",
    
    [Parameter()]
    [string]$Environment = "dev"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m" 
$Yellow = "`e[33m"
$Reset = "`e[0m"

Write-Host "${Green}🚀 Deploying Sentiment Finance Pipeline${Reset}"
Write-Host "Stack Name: $StackName"
Write-Host "Region: $Region"
Write-Host "Environment: $Environment"
Write-Host

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "${Green}✅ AWS CLI found${Reset}"
} catch {
    Write-Host "${Red}❌ AWS CLI is not installed. Please install it first.${Reset}"
    exit 1
}

# Check if SAM CLI is installed
try {
    sam --version | Out-Null
    Write-Host "${Green}✅ SAM CLI found${Reset}"
} catch {
    Write-Host "${Red}❌ SAM CLI is not installed. Install with: pip install aws-sam-cli${Reset}"
    exit 1
}

# Check AWS credentials
Write-Host "${Yellow}🔍 Checking AWS credentials...${Reset}"
try {
    $AccountId = (aws sts get-caller-identity --query Account --output text)
    Write-Host "${Green}✅ AWS credentials configured for account: $AccountId${Reset}"
} catch {
    Write-Host "${Red}❌ AWS credentials not configured. Run 'aws configure' first.${Reset}"
    exit 1
}

# Prompt for sensitive parameters
Write-Host
Write-Host "${Yellow}📝 Please provide the following parameters:${Reset}"

# Database password
do {
    $DbPassword = Read-Host "Enter RDS MySQL password (min 8 characters)" -AsSecureString
    $DbPasswordText = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($DbPassword))
} while ($DbPasswordText.Length -lt 8)

# News API key
$NewsApiKey = Read-Host "Enter News API key (get from https://newsapi.org)"

# Create S3 bucket for SAM artifacts if it doesn't exist
$BucketName = "sam-artifacts-$AccountId-$Region"
Write-Host "${Yellow}📦 Creating/checking S3 bucket for SAM artifacts...${Reset}"

try {
    aws s3 ls "s3://$BucketName" 2>$null | Out-Null
    Write-Host "S3 bucket $BucketName already exists"
} catch {
    Write-Host "Creating S3 bucket: $BucketName"
    if ($Region -eq "us-east-1") {
        aws s3 mb "s3://$BucketName" --region $Region
    } else {
        aws s3 mb "s3://$BucketName" --region $Region --create-bucket-configuration LocationConstraint=$Region
    }
}

# Build and package
Write-Host
Write-Host "${Yellow}🔨 Building SAM application...${Reset}"
sam build --template-file template.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "${Red}❌ SAM build failed!${Reset}"
    exit 1
}

# Deploy the stack
Write-Host
Write-Host "${Yellow}🚢 Deploying stack...${Reset}"
sam deploy `
    --template-file .aws-sam/build/template.yaml `
    --stack-name $StackName `
    --s3-bucket $BucketName `
    --region $Region `
    --capabilities CAPABILITY_IAM `
    --parameter-overrides `
        Environment=$Environment `
        DBPassword=$DbPasswordText `
        NewsAPIKey=$NewsApiKey `
    --confirm-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host
    Write-Host "${Green}✅ Deployment successful!${Reset}"
    
    # Get outputs
    Write-Host
    Write-Host "${Yellow}📋 Stack Outputs:${Reset}"
    aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region `
        --query 'Stacks[0].Outputs' `
        --output table
    
    # Get Lambda function name for GitHub Actions
    $LambdaFunctionName = (aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region `
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' `
        --output text)
    
    Write-Host
    Write-Host "${Green}🎉 Deployment complete!${Reset}"
    Write-Host
    Write-Host "${Yellow}Next steps:${Reset}"
    Write-Host "1. Set up GitHub Actions secrets in your repository:"
    Write-Host "   - AWS_ACCESS_KEY_ID"
    Write-Host "   - AWS_SECRET_ACCESS_KEY"
    Write-Host "   - AWS_REGION=$Region"
    Write-Host "   - LAMBDA_FUNCTION_NAME=$LambdaFunctionName"
    Write-Host
    Write-Host "2. Initialize the database by running the SQL schema:"
    Write-Host "   Connect to the RDS instance and run sql/schema.sql"
    Write-Host
    Write-Host "3. Test the Lambda function:"
    Write-Host "   aws lambda invoke --function-name $LambdaFunctionName response.json"
    Write-Host
    Write-Host "${Yellow}Database connection details:${Reset}"
    $DbEndpoint = (aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region `
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' `
        --output text)
    Write-Host "Endpoint: $DbEndpoint"
    Write-Host "Port: 3306"
    Write-Host "Database: sentiment_finance"
    Write-Host "Username: admin"
    Write-Host "Password: [the password you provided]"
    
} else {
    Write-Host "${Red}❌ Deployment failed!${Reset}"
    exit 1
}