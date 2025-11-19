# 📊 SentimentFinance Pipeline

> Event-driven financial news sentiment analysis using AWS Lambda, Python OOP, and MySQL

[![Tests](https://github.com/losthumanity/SentimentFinance/workflows/CI/badge.svg)](https://github.com/losthumanity/SentimentFinance/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

Automated pipeline that fetches financial news, analyzes sentiment using NLP, and stores results in MySQL for comprehensive market sentiment tracking.

**Key Features:**
- 🤖 Automated news fetching from 80,000+ sources via News API
- 📈 Multi-method sentiment analysis (TextBlob + NLTK VADER + Financial Keywords)
- 💾 Normalized MySQL database with complex analytics queries
- ⚡ Event-driven architecture with AWS Lambda + EventBridge
- 🐳 Docker containerization for consistent environments
- 🧪 37+ unit tests with 90%+ code coverage

## 🏗️ Architecture

```
EventBridge (7 Days) → Lambda Function → RDS MySQL
                          ↓
                    News API Fetch
                          ↓
                  Sentiment Analysis
                          ↓
                    Store Results
```

**Components:**
- **DataFetcher**: News API integration, article deduplication
- **SentimentAnalyzer**: Multi-model sentiment scoring (TextBlob 40% + VADER 40% + Keywords 20%)
- **DatabaseManager**: Complex SQL queries, connection pooling, transaction management
- **Lambda Handler**: Event-driven orchestration, error handling

## 📊 Sentiment Scoring

Sentiment scores range from **-1 (most negative)** to **+1 (most positive)**:
- `+0.5 to +1.0`: Strong positive sentiment
- `+0.2 to +0.5`: Moderately positive
- `-0.2 to +0.2`: Neutral
- `-0.5 to -0.2`: Moderately negative
- `-1.0 to -0.5`: Strong negative sentiment

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Docker Desktop
- News API key (free at https://newsapi.org/register)

### Setup
```powershell
# 1. Clone and navigate
git clone https://github.com/losthumanity/SentimentFinance.git
cd SentimentFinance

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('vader_lexicon')"

# 5. Configure environment
# Edit .env file and add your NEWS_API_KEY

# 6. Start MySQL database
docker-compose up -d

# 7. Run the pipeline
python run_local.py
```

## 📁 Project Structure

```
SentimentFinance/
├── src/                          # Core application code
│   ├── data_fetcher.py          # News API
│   ├── sentiment_analyzer.py    # NLP sentiment analysis
│   ├── database_manager.py      # MySQL operations
│   └── lambda_handler.py        # AWS Lambda
├── tests/                        # Unit tests
│   ├── test_data_fetcher.py
│   ├── test_sentiment_analyzer.py
│   ├── test_database_manager.py
│   └── test_lambda_handler.py
├── sql/
│   ├── schema.sql               # Normalized database design
│   └── complex_queries.sql
├── infrastructure/               # AWS deployment
│   ├── template.yaml            # AWS SAM CloudFormation
│   ├── deploy.sh                # Linux/macOS deployment
│   └── deploy.ps1               # Windows deployment
├── .github/workflows/            # CI/CD pipeline
│   └── ci-cd.yml                # Automated testing & deployment
├── docker-compose.yml            # Local MySQL setup
├── Dockerfile                    # Lambda container image
├── requirements.txt              # Python dependencies
└── run_local.py                 # Local testing
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_database_manager.py -v

# View coverage
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

**Test Coverage:**
- DataFetcher: API mocking, error handling, deduplication
- SentimentAnalyzer: Positive/negative/neutral detection, edge cases
- DatabaseManager: CRUD operations, complex queries, transactions
- Lambda Handler: Pipeline orchestration, event handling

## 📊 Database Schema

**3 Tables + 2 Views + 1 Stored Procedure:**

```sql
companies          # Company master data
├── id (PK)
├── name, symbol, sector
└── timestamps

articles           # Raw news articles
├── id (PK)
├── company_id (FK)
├── title, content, url
└── published_at

sentiment_scores   # Sentiment analysis results
├── id (PK)
├── article_id (FK)
├── sentiment_score (-1 to +1)
├── sentiment_label (positive/negative/neutral)
└── confidence
```

## 📈 Sample Analytics Queries

See `QUERY_EXAMPLES.md` for complete query documentation with sample results.

**Top performers by sentiment:**
```sql
SELECT c.name, c.symbol, AVG(s.sentiment_score) as avg_sentiment
FROM companies c
JOIN articles a ON c.id = a.company_id
JOIN sentiment_scores s ON a.id = s.article_id
WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY c.id, c.name, c.symbol
ORDER BY avg_sentiment DESC;
```

**Sector analysis:**
```sql
SELECT c.sector, COUNT(DISTINCT c.id) as companies,
       AVG(s.sentiment_score) as avg_sentiment
FROM companies c
JOIN articles a ON c.id = a.company_id
JOIN sentiment_scores s ON a.id = s.article_id
GROUP BY c.sector
ORDER BY avg_sentiment DESC;
```

## ☁️ AWS Deployment

Deploy to AWS Lambda + RDS using AWS SAM:

```bash
# Navigate to infrastructure directory
cd infrastructure/

# Deploy (Windows)
.\deploy.ps1

# Deploy (Linux/macOS)
chmod +x deploy.sh
./deploy.sh
```

**Deployed Resources:**
- Lambda Function (Python 3.11, 1024MB, 900s timeout)
- EventBridge Schedule (every 15 minutes)
- RDS MySQL (db.t3.micro)
- VPC with private/public subnets
- NAT Gateway, Security Groups

**Estimated Cost:** $47-67/month (mostly RDS + NAT Gateway)

## 🔧 Configuration

**Environment Variables:**
```env
# Database (required)
DB_HOST=localhost
DB_PORT=3308
DB_NAME=sentiment_finance
DB_USER=sentiment_app
DB_PASSWORD=sentiment_password

# News API (required)
NEWS_API_KEY=your_key_here

# AWS (optional, for deployment)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

## 📚 Advanced Features

- **Complex SQL Queries**: 10 advanced queries demonstrating JOINs, CTEs, window functions, subqueries
- **Risk-Adjusted Metrics**: Sentiment scores adjusted for volatility
- **Sector Correlation**: Track sentiment patterns across industries
- **Time-Series Analysis**: Moving averages, trend detection
- **Source Reliability**: Analyze consistency by news source

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- News API for financial news data
- NLTK & TextBlob for NLP capabilities
- AWS for serverless infrastructure