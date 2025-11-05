"""
AWS Lambda handler for the Sentiment Finance pipeline.
Event-driven processing orchestrating the entire data pipeline.
"""

import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

# Import our custom classes
from src.data_fetcher import DataFetcher
from src.database_manager import DatabaseManager
from src.sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentFinancePipeline:
    """Main pipeline orchestrator for sentiment analysis."""
    
    def __init__(self):
        """Initialize pipeline components."""
        self.data_fetcher = DataFetcher()
        self.db_manager = DatabaseManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Default companies to track (can be extended)
        self.tracked_companies = [
            {'name': 'Apple Inc.', 'sector': 'Technology', 'symbol': 'AAPL'},
            {'name': 'Microsoft Corporation', 'sector': 'Technology', 'symbol': 'MSFT'},
            {'name': 'Amazon.com Inc.', 'sector': 'Technology', 'symbol': 'AMZN'},
            {'name': 'Tesla Inc.', 'sector': 'Automotive', 'symbol': 'TSLA'},
            {'name': 'Alphabet Inc.', 'sector': 'Technology', 'symbol': 'GOOGL'},
            {'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'symbol': 'META'},
            {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'symbol': 'NVDA'},
            {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services', 'symbol': 'JPM'},
            {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'symbol': 'JNJ'},
            {'name': 'Berkshire Hathaway', 'sector': 'Financial Services', 'symbol': 'BRK.A'}
        ]
    
    def process_pipeline(self, event_type: str = 'scheduled') -> Dict[str, Any]:
        """
        Execute the complete sentiment analysis pipeline.
        
        Args:
            event_type: Type of event triggering the pipeline
            
        Returns:
            Pipeline execution results
        """
        start_time = datetime.now()
        results = {
            'event_type': event_type,
            'start_time': start_time.isoformat(),
            'companies_processed': 0,
            'articles_fetched': 0,
            'articles_processed': 0,
            'sentiment_scores_created': 0,
            'errors': [],
            'success': False
        }
        
        try:
            logger.info(f"Starting sentiment finance pipeline - Event: {event_type}")
            
            # Step 1: Ensure companies exist in database
            company_ids = self._setup_companies()
            results['companies_processed'] = len(company_ids)
            
            # Step 2: Fetch news articles for all companies
            articles = self._fetch_all_news_articles()
            results['articles_fetched'] = len(articles)
            
            if not articles:
                logger.warning("No articles fetched, ending pipeline execution")
                return results
            
            # Step 3: Process articles and perform sentiment analysis
            processed_count = self._process_articles(articles, company_ids)
            results['articles_processed'] = processed_count
            results['sentiment_scores_created'] = processed_count
            
            # Step 4: Cleanup old data (optional maintenance)
            if event_type == 'maintenance':
                deleted_count = self.db_manager.cleanup_old_articles(days_to_keep=90)
                results['old_articles_deleted'] = deleted_count
            
            results['success'] = True
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Pipeline completed successfully in {results['duration_seconds']:.2f} seconds")
            logger.info(f"Processed {processed_count} articles for {len(company_ids)} companies")
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            results['errors'].append(str(e))
            results['success'] = False
        
        return results
    
    def _setup_companies(self) -> Dict[str, int]:
        """
        Ensure all tracked companies exist in the database.
        
        Returns:
            Mapping of company names to their database IDs
        """
        company_ids = {}
        
        for company in self.tracked_companies:
            try:
                company_id = self.db_manager.insert_company(
                    name=company['name'],
                    sector=company['sector'],
                    symbol=company.get('symbol')
                )
                company_ids[company['name']] = company_id
                logger.debug(f"Company setup: {company['name']} -> ID: {company_id}")
            except Exception as e:
                logger.error(f"Error setting up company {company['name']}: {str(e)}")
                continue
        
        return company_ids
    
    def _fetch_all_news_articles(self) -> List[Dict]:
        """
        Fetch news articles for all tracked companies.
        
        Returns:
            List of all fetched articles
        """
        all_articles = []
        company_names = [company['name'] for company in self.tracked_companies]
        
        try:
            # Fetch articles for all companies
            articles = self.data_fetcher.fetch_financial_news(
                companies=company_names,
                hours_back=24  # Last 24 hours
            )
            all_articles.extend(articles)
            
            # Also fetch sector-based news for broader coverage
            sectors = list(set(company['sector'] for company in self.tracked_companies))
            for sector in sectors:
                try:
                    sector_articles = self.data_fetcher.fetch_sector_news(
                        sector=sector.lower(),
                        hours_back=24
                    )
                    all_articles.extend(sector_articles)
                except Exception as e:
                    logger.error(f"Error fetching sector news for {sector}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching news articles: {str(e)}")
            raise
        
        return all_articles
    
    def _process_articles(self, articles: List[Dict], company_ids: Dict[str, int]) -> int:
        """
        Process articles: store in database and perform sentiment analysis.
        
        Args:
            articles: List of articles to process
            company_ids: Mapping of company names to IDs
            
        Returns:
            Number of articles successfully processed
        """
        processed_count = 0
        
        for article in articles:
            try:
                # Determine which company this article relates to
                company_id = self._determine_company_id(article, company_ids)
                if not company_id:
                    logger.debug(f"Could not determine company for article: {article.get('title', '')}")
                    continue
                
                # Insert article into database
                article_id = self.db_manager.insert_article(
                    title=article['title'],
                    content=article.get('content', ''),
                    url=article['url'],
                    source=article['source'],
                    published_at=article['published_at'],
                    company_id=company_id,
                    description=article.get('description'),
                    author=article.get('author')
                )
                
                # Perform sentiment analysis
                text_for_analysis = self._prepare_text_for_analysis(article)
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(text_for_analysis)
                
                # Insert sentiment scores
                self.db_manager.insert_sentiment_score(
                    article_id=article_id,
                    sentiment_score=sentiment_result['sentiment_score'],
                    confidence=sentiment_result['confidence'],
                    sentiment_label=sentiment_result['sentiment_label'],
                    processing_method=sentiment_result['method']
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('url', 'unknown')}: {str(e)}")
                continue
        
        return processed_count
    
    def _determine_company_id(self, article: Dict, company_ids: Dict[str, int]) -> int:
        """
        Determine which company an article relates to.
        
        Args:
            article: Article data
            company_ids: Mapping of company names to IDs
            
        Returns:
            Company ID or None if not determined
        """
        # Check if article was fetched for a specific company
        search_term = article.get('company_search_term', '')
        if search_term in company_ids:
            return company_ids[search_term]
        
        # Check if company name appears in title or content
        article_text = (
            article.get('title', '') + ' ' + 
            article.get('description', '') + ' ' + 
            article.get('content', '')
        ).lower()
        
        for company_name, company_id in company_ids.items():
            # Simple keyword matching - could be enhanced with NER
            company_keywords = company_name.lower().split()
            if any(keyword in article_text for keyword in company_keywords):
                return company_id
        
        # Check for stock symbols
        for company in self.tracked_companies:
            if company.get('symbol') and company['symbol'].lower() in article_text:
                return company_ids.get(company['name'])
        
        return None
    
    def _prepare_text_for_analysis(self, article: Dict) -> str:
        """
        Prepare article text for sentiment analysis.
        
        Args:
            article: Article data
            
        Returns:
            Combined text for analysis
        """
        # Combine title, description, and content with appropriate weighting
        text_parts = []
        
        if article.get('title'):
            # Title is most important, so repeat it
            text_parts.append(article['title'])
            text_parts.append(article['title'])
        
        if article.get('description'):
            text_parts.append(article['description'])
        
        if article.get('content'):
            # Truncate content if too long to avoid token limits
            content = article['content']
            if len(content) > 2000:
                content = content[:2000] + '...'
            text_parts.append(content)
        
        return ' '.join(text_parts)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point for EventBridge triggers.
    
    Args:
        event: EventBridge event data
        context: Lambda runtime context
        
    Returns:
        Pipeline execution results
    """
    try:
        # Determine event type
        event_source = event.get('source', '')
        event_type = 'scheduled' if 'events' in event_source else 'manual'
        
        # Log event details
        logger.info(f"Lambda function triggered by: {event_source}")
        logger.info(f"Event type: {event_type}")
        
        # Initialize and run pipeline
        pipeline = SentimentFinancePipeline()
        results = pipeline.process_pipeline(event_type=event_type)
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'success': False
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }


def local_test_handler(event_type: str = 'scheduled') -> Dict[str, Any]:
    """
    Local testing function for development.
    
    Args:
        event_type: Type of event to simulate
        
    Returns:
        Pipeline execution results
    """
    pipeline = SentimentFinancePipeline()
    return pipeline.process_pipeline(event_type=event_type)


if __name__ == '__main__':
    # For local testing
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Run pipeline locally
    event_type = sys.argv[1] if len(sys.argv) > 1 else 'scheduled'
    results = local_test_handler(event_type)
    
    print(json.dumps(results, indent=2, default=str))