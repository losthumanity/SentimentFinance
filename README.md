# SentimentFinance Pipeline

## Overview
Event-driven sentiment analysis pipeline for financial news using AWS services, Python OOP, and MySQL.

## Architecture
- **EventBridge**: Triggers Lambda function every 15 minutes
- **Lambda**: Serverless processing with Python OOP design
- **RDS MySQL**: Normalized database schema for articles, companies, and sentiment scores
- **Docker**: Containerized deployment environment
- **GitHub Actions**: Automated CI/CD pipeline

## Key Components
1. **DataFetcher**: Handles API calls to news sources
2. **DatabaseManager**: Manages SQL interactions and complex queries
3. **SentimentAnalyzer**: Performs sentiment analysis using NLTK/TextBlob

## Database Schema
- `companies`: Company information and sectors
- `articles`: Raw news articles with metadata
- `sentiment_scores`: Processed sentiment data with foreign keys

## Deployment
The project uses Docker for consistent environments and GitHub Actions for automated deployment to AWS Lambda.

## Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run tests
pytest tests/

# Build Docker image
docker-compose build

# Deploy to AWS
# Configure AWS credentials and run deployment scripts
```

## Usage
Once deployed, the pipeline automatically:
1. Fetches news data every 15 minutes via EventBridge
2. Processes and analyzes sentiment
3. Stores results in MySQL database
4. Provides complex SQL queries for reporting

## SQL Examples
```sql
-- Weekly sentiment report for a company
SELECT c.name, AVG(s.sentiment_score) as avg_sentiment
FROM companies c
JOIN articles a ON c.id = a.company_id
JOIN sentiment_scores s ON a.id = s.article_id
WHERE c.name = 'Apple Inc.' 
  AND a.published_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY c.name;
```