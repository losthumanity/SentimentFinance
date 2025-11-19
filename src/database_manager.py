"""
DatabaseManager class for handling all SQL interactions.
Implements complex queries, JOINs, and database operations.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations with MySQL RDS."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 database: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize DatabaseManager with connection parameters.

        Args:
            host: Database host, defaults to environment variable
            port: Database port, defaults to environment variable
            database: Database name, defaults to environment variable
            user: Database user, defaults to environment variable
            password: Database password, defaults to environment variable
        """
        self.host = host or os.getenv('DB_HOST')
        self.port = port or int(os.getenv('DB_PORT', '3306'))
        self.database = database or os.getenv('DB_NAME')
        self.user = user or os.getenv('DB_USER')
        self.password = password or os.getenv('DB_PASSWORD')

        # Validate required connection parameters
        required_params = [self.host, self.database, self.user, self.password]
        if not all(required_params):
            raise ValueError("All database connection parameters must be provided")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            MySQL connection object
        """
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=False,
                charset='utf8mb4',
                use_unicode=True
            )
            yield connection
        except Error as e:
            logger.error(f"Database connection error: {str(e)}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def insert_company(self, name: str, sector: str, symbol: Optional[str] = None) -> int:
        """
        Insert a new company or return existing ID.

        Args:
            name: Company name
            sector: Business sector
            symbol: Stock symbol (optional)

        Returns:
            Company ID
        """
        # First check if company exists
        existing_id = self.get_company_id(name)
        if existing_id:
            return existing_id

        insert_query = """
        INSERT INTO companies (name, sector, symbol, created_at)
        VALUES (%s, %s, %s, %s)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(insert_query, (name, sector, symbol, datetime.now()))
                conn.commit()
                company_id = cursor.lastrowid
                logger.info(f"Inserted company: {name} with ID: {company_id}")
                return company_id
            except Error as e:
                conn.rollback()
                logger.error(f"Error inserting company {name}: {str(e)}")
                raise
            finally:
                cursor.close()

    def get_company_id(self, name: str) -> Optional[int]:
        """
        Get company ID by name.

        Args:
            name: Company name

        Returns:
            Company ID or None if not found
        """
        query = "SELECT id FROM companies WHERE name = %s"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (name,))
                result = cursor.fetchone()
                return result[0] if result else None
            finally:
                cursor.close()

    def insert_article(self, title: str, content: str, url: str, source: str,
                      published_at: datetime, company_id: int,
                      description: Optional[str] = None,
                      author: Optional[str] = None) -> int:
        """
        Insert a new article.

        Args:
            title: Article title
            content: Article content
            url: Article URL
            source: News source
            published_at: Publication datetime
            company_id: Associated company ID
            description: Article description (optional)
            author: Author name (optional)

        Returns:
            Article ID
        """
        # Check if article already exists (by URL)
        if self.article_exists(url):
            logger.info(f"Article already exists: {url}")
            return self.get_article_id_by_url(url)

        insert_query = """
        INSERT INTO articles (title, description, content, url, source,
                             published_at, company_id, author, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(insert_query, (
                    title, description, content, url, source,
                    published_at, company_id, author, datetime.now()
                ))
                conn.commit()
                article_id = cursor.lastrowid
                logger.info(f"Inserted article: {title[:50]}... with ID: {article_id}")
                return article_id
            except Error as e:
                conn.rollback()
                logger.error(f"Error inserting article {title}: {str(e)}")
                raise
            finally:
                cursor.close()

    def article_exists(self, url: str) -> bool:
        """
        Check if article exists by URL.

        Args:
            url: Article URL

        Returns:
            True if article exists
        """
        query = "SELECT 1 FROM articles WHERE url = %s"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (url,))
                return cursor.fetchone() is not None
            finally:
                cursor.close()

    def get_article_id_by_url(self, url: str) -> Optional[int]:
        """
        Get article ID by URL.

        Args:
            url: Article URL

        Returns:
            Article ID or None
        """
        query = "SELECT id FROM articles WHERE url = %s"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (url,))
                result = cursor.fetchone()
                return result[0] if result else None
            finally:
                cursor.close()

    def insert_sentiment_score(self, article_id: int, sentiment_score: float,
                              confidence: float, sentiment_label: str,
                              processing_method: str = 'textblob') -> int:
        """
        Insert sentiment analysis results.

        Args:
            article_id: Associated article ID
            sentiment_score: Numerical sentiment score (-1 to 1)
            confidence: Confidence level (0 to 1)
            sentiment_label: Text label (positive/negative/neutral)
            processing_method: Method used for analysis

        Returns:
            Sentiment score ID
        """
        insert_query = """
        INSERT INTO sentiment_scores (article_id, sentiment_score, confidence,
                                    sentiment_label, processing_method, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(insert_query, (
                    article_id, sentiment_score, confidence,
                    sentiment_label, processing_method, datetime.now()
                ))
                conn.commit()
                sentiment_id = cursor.lastrowid
                logger.info(f"Inserted sentiment score for article {article_id}: {sentiment_score}")
                return sentiment_id
            except Error as e:
                conn.rollback()
                logger.error(f"Error inserting sentiment score: {str(e)}")
                raise
            finally:
                cursor.close()

    def get_weekly_sentiment_report(self, company_name: str) -> List[Dict]:
        """
        Generate weekly sentiment report for a company using complex SQL with JOINs.

        Args:
            company_name: Company name to analyze

        Returns:
            List of sentiment report data
        """
        query = """
        SELECT
            c.name as company_name,
            c.sector,
            DATE(a.published_at) as date,
            COUNT(a.id) as article_count,
            AVG(s.sentiment_score) as avg_sentiment,
            MIN(s.sentiment_score) as min_sentiment,
            MAX(s.sentiment_score) as max_sentiment,
            AVG(s.confidence) as avg_confidence,
            SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
        FROM companies c
        JOIN articles a ON c.id = a.company_id
        JOIN sentiment_scores s ON a.id = s.article_id
        WHERE c.name = %s
          AND a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY c.name, c.sector, DATE(a.published_at)
        ORDER BY DATE(a.published_at) DESC
        """

        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, (company_name,))
                results = cursor.fetchall()
                logger.info(f"Generated weekly report for {company_name}: {len(results)} days")
                return results
            finally:
                cursor.close()

    def get_sector_sentiment_analysis(self, sector: str, days_back: int = 30) -> List[Dict]:
        """
        Analyze sentiment for an entire sector using subqueries.

        Args:
            sector: Business sector to analyze
            days_back: Number of days to look back

        Returns:
            Sector sentiment analysis results
        """
        query = """
        SELECT
            sector_data.sector,
            sector_data.total_articles,
            sector_data.avg_sentiment,
            sector_data.sentiment_trend,
            company_rankings.top_company,
            company_rankings.top_company_sentiment
        FROM (
            SELECT
                c.sector,
                COUNT(a.id) as total_articles,
                AVG(s.sentiment_score) as avg_sentiment,
                CASE
                    WHEN AVG(s.sentiment_score) > 0.1 THEN 'Positive'
                    WHEN AVG(s.sentiment_score) < -0.1 THEN 'Negative'
                    ELSE 'Neutral'
                END as sentiment_trend
            FROM companies c
            JOIN articles a ON c.id = a.company_id
            JOIN sentiment_scores s ON a.id = s.article_id
            WHERE c.sector = %s
              AND a.published_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY c.sector
        ) as sector_data
        LEFT JOIN (
            SELECT
                c.sector,
                c.name as top_company,
                AVG(s.sentiment_score) as top_company_sentiment,
                ROW_NUMBER() OVER (PARTITION BY c.sector ORDER BY AVG(s.sentiment_score) DESC) as rn
            FROM companies c
            JOIN articles a ON c.id = a.company_id
            JOIN sentiment_scores s ON a.id = s.article_id
            WHERE c.sector = %s
              AND a.published_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY c.sector, c.name
        ) as company_rankings ON sector_data.sector = company_rankings.sector AND company_rankings.rn = 1
        """

        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, (sector, days_back, sector, days_back))
                results = cursor.fetchall()
                logger.info(f"Generated sector analysis for {sector}: {len(results)} records")
                return results
            finally:
                cursor.close()

    def get_trending_companies(self, limit: int = 10) -> List[Dict]:
        """
        Get companies with most articles in the last 24 hours.

        Args:
            limit: Number of companies to return

        Returns:
            List of trending companies with article counts
        """
        query = """
        SELECT
            c.name,
            c.sector,
            COUNT(a.id) as article_count,
            AVG(s.sentiment_score) as avg_sentiment
        FROM companies c
        JOIN articles a ON c.id = a.company_id
        JOIN sentiment_scores s ON a.id = s.article_id
        WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        GROUP BY c.id, c.name, c.sector
        ORDER BY article_count DESC, avg_sentiment DESC
        LIMIT %s
        """

        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                logger.info(f"Retrieved {len(results)} trending companies")
                return results
            finally:
                cursor.close()

    def execute_custom_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """
        Execute a custom SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return [{'affected_rows': cursor.rowcount}]
            except Error as e:
                conn.rollback()
                logger.error(f"Error executing custom query: {str(e)}")
                raise
            finally:
                cursor.close()

    def cleanup_old_articles(self, days_to_keep: int = 90) -> int:
        """
        Remove articles older than specified days.

        Args:
            days_to_keep: Number of days to keep

        Returns:
            Number of articles deleted
        """
        query = """
        DELETE a, s FROM articles a
        LEFT JOIN sentiment_scores s ON a.id = s.article_id
        WHERE a.published_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (days_to_keep,))
                conn.commit()
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old articles")
                return deleted_count
            except Error as e:
                conn.rollback()
                logger.error(f"Error cleaning up articles: {str(e)}")
                raise
            finally:
                cursor.close()