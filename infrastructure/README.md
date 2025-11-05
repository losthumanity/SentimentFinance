# Sentiment Finance Infrastructure

This directory contains AWS infrastructure as code (IaC) for the Sentiment Finance pipeline.

## Files

- `template.yaml` - AWS SAM CloudFormation template
- `deploy.sh` - Deployment script for Linux/macOS  
- `deploy.ps1` - Deployment script for Windows PowerShell
- `README.md` - This file

## Architecture

The infrastructure creates:

1. **VPC & Networking**
   - Private subnets for RDS
   - Public subnet with NAT Gateway for Lambda internet access
   - Security groups with least-privilege access

2. **RDS MySQL Database**
   - MySQL 8.0 in private subnets
   - Encrypted storage, automated backups
   - Security group allowing access only from Lambda

3. **Lambda Function**
   - Runs in VPC with access to RDS and internet
   - Triggered by EventBridge every 15 minutes
   - Environment variables for database connection

4. **EventBridge Schedule**
   - Triggers Lambda function every 15 minutes
   - Configurable schedule expression

## Prerequisites

1. **AWS CLI** - Install and configure with `aws configure`
2. **SAM CLI** - Install with `pip install aws-sam-cli`
3. **News API Key** - Get free key from https://newsapi.org

## Deployment

### Option 1: Using deployment script (recommended)

**Linux/macOS:**
```bash
cd infrastructure/
chmod +x deploy.sh
./deploy.sh
```

**Windows PowerShell:**
```powershell
cd infrastructure/
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1
```

### Option 2: Manual SAM deployment

```bash
# Build the application
sam build

# Deploy with guided prompts
sam deploy --guided

# Or deploy with parameters
sam deploy \
  --stack-name sentiment-finance-pipeline \
  --s3-bucket your-sam-artifacts-bucket \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=dev \
    DBPassword=YourSecurePassword123! \
    NewsAPIKey=your-news-api-key
```

## Post-Deployment

1. **Initialize Database Schema**
   ```bash
   # Connect to RDS and run the schema
   mysql -h <rds-endpoint> -u admin -p sentiment_finance < ../sql/schema.sql
   ```

2. **Test Lambda Function**
   ```bash
   aws lambda invoke --function-name <function-name> response.json
   cat response.json
   ```

3. **Set up GitHub Actions Secrets**
   Add these secrets to your GitHub repository:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `LAMBDA_FUNCTION_NAME` (from stack outputs)

## Cost Estimation

Monthly costs (us-east-1, approximate):
- RDS db.t3.micro: ~$13-15
- Lambda (assuming 2,880 invocations/month): ~$0.20
- VPC NAT Gateway: ~$32-45
- Data transfer, CloudWatch logs: ~$2-5

**Total: ~$47-67/month**

## Cleanup

To delete all resources:
```bash
sam delete --stack-name sentiment-finance-pipeline
```

## Customization

### Change Lambda Schedule
Edit the `ScheduleExpression` in `template.yaml`:
```yaml
ScheduleExpression: 'rate(30 minutes)'  # Every 30 minutes
# or
ScheduleExpression: 'cron(0 9 * * ? *)'  # Daily at 9 AM UTC
```

### Scale RDS Instance
Change the `DBInstanceClass`:
```yaml
DBInstanceClass: 'db.t3.small'  # More powerful instance
```

### Add Environment Variables
Add to the Lambda function's `Environment.Variables` section:
```yaml
Environment:
  Variables:
    YOUR_CUSTOM_VAR: 'value'
```