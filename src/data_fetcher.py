"""
DataFetcher class for handling API calls to news sources.
Implements clean OOP design for data ingestion.
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataFetcher:
    """Handles fetching news data from various API sources."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize DataFetcher with API credentials.

        Args:
            api_key: News API key, defaults to environment variable
            base_url: Base URL for news API, defaults to environment variable
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = base_url or os.getenv('NEWS_API_BASE_URL', 'https://newsapi.org/v2')

        if not self.api_key:
            raise ValueError("NEWS_API_KEY must be provided or set in environment")

    def fetch_financial_news(self, companies: List[str], hours_back: int = 24) -> List[Dict]:
        """
        Fetch recent financial news for specified companies.

        Args:
            companies: List of company names to search for
            hours_back: How many hours back to fetch news

        Returns:
            List of article dictionaries
        """
        articles = []

        for company in companies:
            try:
                company_articles = self._fetch_company_news(company, hours_back)
                articles.extend(company_articles)
                logger.info(f"Fetched {len(company_articles)} articles for {company}")
            except Exception as e:
                logger.error(f"Error fetching news for {company}: {str(e)}")
                continue

        return self._deduplicate_articles(articles)

    def _fetch_company_news(self, company: str, hours_back: int) -> List[Dict]:
        """
        Fetch news for a specific company.

        Args:
            company: Company name to search for
            hours_back: Hours to look back for news

        Returns:
            List of article dictionaries
        """
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(hours=hours_back)

        # Build query parameters - use broader search for free tier
        # Extract key terms from company name (e.g., "Apple" from "Apple Inc.")
        search_term = company.split()[0]  # Get first word (main company name)

        params = {
            'q': f'{search_term} AND (stock OR market OR business)',
            'from': from_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,  # Limit to 10 articles per company
            'apiKey': self.api_key
        }

        response = requests.get(f"{self.base_url}/everything", params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'ok':
            raise Exception(f"API error: {data.get('message', 'Unknown error')}")

        return self._process_articles(data.get('articles', []), company)

    def _process_articles(self, raw_articles: List[Dict], company: str) -> List[Dict]:
        """
        Process raw API articles into standardized format.

        Args:
            raw_articles: Raw articles from API
            company: Company name this search was for

        Returns:
            Processed articles
        """
        processed = []

        for article in raw_articles:
            # Skip articles without required fields
            if not all([article.get('title'), article.get('publishedAt'), article.get('url')]):
                continue

            processed_article = {
                'title': article.get('title', '').strip(),
                'description': article.get('description', '').strip(),
                'content': article.get('content', '').strip(),
                'url': article.get('url').strip(),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': self._parse_date(article.get('publishedAt')),
                'company_search_term': company,
                'author': article.get('author', '').strip() if article.get('author') else None
            }

            processed.append(processed_article)

        return processed

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse ISO date string to datetime object.

        Args:
            date_str: ISO format date string

        Returns:
            Parsed datetime object
        """
        try:
            # Handle timezone info by removing it (News API uses UTC)
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Remove duplicate articles based on URL.

        Args:
            articles: List of articles

        Returns:
            Deduplicated articles
        """
        seen_urls = set()
        unique_articles = []

        for article in articles:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        return unique_articles

    def fetch_sector_news(self, sector: str, hours_back: int = 24) -> List[Dict]:
        """
        Fetch news for a specific sector (e.g., 'technology', 'healthcare').

        Args:
            sector: Sector name to search for
            hours_back: Hours to look back for news

        Returns:
            List of article dictionaries
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(hours=hours_back)

        params = {
            'q': f'{sector} AND (stock OR market)',
            'from': from_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,  # Limit results
            'apiKey': self.api_key
        }

        try:
            response = requests.get(f"{self.base_url}/everything", params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'ok':
                raise Exception(f"API error: {data.get('message', 'Unknown error')}")

            articles = self._process_articles(data.get('articles', []), f"sector:{sector}")
            logger.info(f"Fetched {len(articles)} articles for {sector} sector")

            return articles

        except Exception as e:
            logger.error(f"Error fetching sector news for {sector}: {str(e)}")
            return []