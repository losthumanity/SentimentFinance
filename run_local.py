"""
Local test script for Sentiment Finance Pipeline.
Run this to test the pipeline locally without AWS Lambda.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check required environment variables
required_vars = {
    'DB_HOST': 'Database host (should be localhost for local dev)',
    'DB_PASSWORD': 'Database password (from docker-compose.yml)',
    'NEWS_API_KEY': 'News API key from https://newsapi.org'
}

print("🔍 Checking environment variables...\n")
missing_vars = []
for var, description in required_vars.items():
    value = os.getenv(var)
    if not value or value.startswith('your_'):
        print(f"❌ {var}: MISSING or not set")
        print(f"   → {description}\n")
        missing_vars.append(var)
    else:
        masked_value = value if len(value) < 10 else f"{value[:4]}...{value[-4:]}"
        print(f"✅ {var}: {masked_value}")

if missing_vars:
    print("\n⚠️  Please set the missing environment variables in .env file")
    print("\nRequired API Keys:")
    print("1. NEWS_API_KEY - Get free key from https://newsapi.org/register")
    print("   - Sign up with email")
    print("   - Free tier: 1,000 requests/day")
    print("   - Copy API key to .env file\n")
    sys.exit(1)

print("\n" + "="*60)
print("✅ All environment variables are set!")
print("="*60 + "\n")

# Import and run the pipeline
from src.lambda_handler import local_test_handler
import json

try:
    print("🚀 Starting Sentiment Finance Pipeline (local test mode)...\n")

    # Run the pipeline
    results = local_test_handler(event_type='scheduled')

    # Print results
    print("\n" + "="*60)
    print("📊 PIPELINE EXECUTION RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2, default=str))
    print("="*60 + "\n")

    if results.get('success'):
        print("✅ Pipeline executed successfully!")
        print(f"   • Companies processed: {results.get('companies_processed', 0)}")
        print(f"   • Articles fetched: {results.get('articles_fetched', 0)}")
        print(f"   • Articles processed: {results.get('articles_processed', 0)}")
        print(f"   • Duration: {results.get('duration_seconds', 0):.2f} seconds")
    else:
        print("❌ Pipeline execution failed!")
        if results.get('errors'):
            print(f"   Errors: {results['errors']}")

except Exception as e:
    print(f"\n❌ Error running pipeline: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)