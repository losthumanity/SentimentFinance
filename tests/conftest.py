"""
Test configuration and fixtures for pytest.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ['DB_HOST'] = 'test-host'
os.environ['DB_PORT'] = '3306'
os.environ['DB_NAME'] = 'test_db'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_password'
os.environ['NEWS_API_KEY'] = 'test-api-key'
os.environ['NEWS_API_BASE_URL'] = 'https://test-api.example.com'
os.environ['ENVIRONMENT'] = 'test'
os.environ['LOG_LEVEL'] = 'DEBUG'