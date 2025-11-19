import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.lambda_handler import SentimentFinancePipeline, lambda_handler, local_test_handler


@pytest.fixture
def mock_pipeline_components():
    """Create mocks for all pipeline components."""
    with patch('src.lambda_handler.DataFetcher') as mock_fetcher, \
         patch('src.lambda_handler.DatabaseManager') as mock_db, \
         patch('src.lambda_handler.SentimentAnalyzer') as mock_analyzer:

        yield {
            'fetcher': mock_fetcher,
            'db': mock_db,
            'analyzer': mock_analyzer
        }


def test_pipeline_initialization(mock_pipeline_components):
    """Test pipeline initializes with all components."""
    pipeline = SentimentFinancePipeline()

    assert pipeline.data_fetcher is not None
    assert pipeline.db_manager is not None
    assert pipeline.sentiment_analyzer is not None
    assert len(pipeline.tracked_companies) == 10


def test_pipeline_process_success(mock_pipeline_components):
    """Test successful pipeline execution."""
    pipeline = SentimentFinancePipeline()

    # Mock database operations
    pipeline.db_manager.insert_company = Mock(return_value=1)
    pipeline.db_manager.insert_article = Mock(return_value=100)
    pipeline.db_manager.insert_sentiment_score = Mock(return_value=200)

    # Mock data fetcher
    mock_article = {
        'title': 'Test Article',
        'content': 'Test content',
        'url': 'https://example.com/test',
        'source': 'Test Source',
        'published_at': datetime.now(),
        'company_search_term': 'Apple Inc.',
        'description': 'Test description',
        'author': 'Test Author'
    }
    pipeline.data_fetcher.fetch_financial_news = Mock(return_value=[mock_article])
    pipeline.data_fetcher.fetch_sector_news = Mock(return_value=[])

    # Mock sentiment analyzer
    pipeline.sentiment_analyzer.analyze_sentiment = Mock(return_value={
        'sentiment_score': 0.5,
        'confidence': 0.8,
        'sentiment_label': 'positive',
        'method': 'combined'
    })

    result = pipeline.process_pipeline('scheduled')

    assert result['success'] is True
    assert result['companies_processed'] == 10
    assert result['articles_fetched'] > 0
    assert result['articles_processed'] > 0


def test_pipeline_process_no_articles(mock_pipeline_components):
    """Test pipeline when no articles are fetched."""
    pipeline = SentimentFinancePipeline()

    pipeline.db_manager.insert_company = Mock(return_value=1)
    pipeline.data_fetcher.fetch_financial_news = Mock(return_value=[])
    pipeline.data_fetcher.fetch_sector_news = Mock(return_value=[])

    result = pipeline.process_pipeline('scheduled')

    assert result['articles_fetched'] == 0
    assert result['articles_processed'] == 0


def test_pipeline_setup_companies(mock_pipeline_components):
    """Test company setup creates all tracked companies."""
    pipeline = SentimentFinancePipeline()

    pipeline.db_manager.insert_company = Mock(side_effect=range(1, 11))

    company_ids = pipeline._setup_companies()

    assert len(company_ids) == 10
    assert 'Apple Inc.' in company_ids
    assert 'Tesla Inc.' in company_ids


def test_pipeline_fetch_all_news_articles(mock_pipeline_components):
    """Test fetching news from multiple sources."""
    pipeline = SentimentFinancePipeline()

    mock_article_1 = {'title': 'Article 1', 'url': 'https://example.com/1'}
    mock_article_2 = {'title': 'Article 2', 'url': 'https://example.com/2'}

    pipeline.data_fetcher.fetch_financial_news = Mock(return_value=[mock_article_1])
    pipeline.data_fetcher.fetch_sector_news = Mock(return_value=[mock_article_2])

    articles = pipeline._fetch_all_news_articles()

    assert len(articles) >= 2


def test_pipeline_determine_company_id_by_search_term(mock_pipeline_components):
    """Test determining company ID from search term."""
    pipeline = SentimentFinancePipeline()

    company_ids = {'Apple Inc.': 1, 'Tesla Inc.': 2}
    article = {'company_search_term': 'Apple Inc.'}

    company_id = pipeline._determine_company_id(article, company_ids)

    assert company_id == 1


def test_pipeline_determine_company_id_by_content(mock_pipeline_components):
    """Test determining company ID from article content."""
    pipeline = SentimentFinancePipeline()

    company_ids = {'Apple Inc.': 1, 'Tesla Inc.': 2}
    article = {
        'company_search_term': '',
        'title': 'Apple releases new iPhone',
        'description': 'The tech giant unveils new products',
        'content': 'Apple Inc. announced today...'
    }

    company_id = pipeline._determine_company_id(article, company_ids)

    assert company_id == 1


def test_pipeline_determine_company_id_by_symbol(mock_pipeline_components):
    """Test determining company ID from stock symbol."""
    pipeline = SentimentFinancePipeline()

    company_ids = {'Tesla Inc.': 2}
    article = {
        'company_search_term': '',
        'title': 'TSLA stock rises',
        'description': 'Tesla shares up',
        'content': 'TSLA is trading higher'
    }

    company_id = pipeline._determine_company_id(article, company_ids)

    assert company_id == 2


def test_pipeline_prepare_text_for_analysis(mock_pipeline_components):
    """Test text preparation for sentiment analysis."""
    pipeline = SentimentFinancePipeline()

    article = {
        'title': 'Great earnings report',
        'description': 'Company beats expectations',
        'content': 'The company reported strong revenue growth and profitability.'
    }

    text = pipeline._prepare_text_for_analysis(article)

    assert 'Great earnings report' in text
    assert text.count('Great earnings report') == 2  # Title repeated for emphasis
    assert 'Company beats expectations' in text
    assert 'revenue growth' in text


def test_pipeline_prepare_text_truncates_long_content(mock_pipeline_components):
    """Test that long content is truncated."""
    pipeline = SentimentFinancePipeline()

    article = {
        'title': 'Title',
        'description': 'Description',
        'content': 'A' * 3000  # Very long content
    }

    text = pipeline._prepare_text_for_analysis(article)

    assert len(text) < 3000
    assert '...' in text


def test_lambda_handler_scheduled_event():
    """Test Lambda handler with scheduled event."""
    event = {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event'
    }
    context = Mock()

    with patch('src.lambda_handler.SentimentFinancePipeline') as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline.process_pipeline.return_value = {
            'success': True,
            'articles_processed': 5
        }
        mock_pipeline_class.return_value = mock_pipeline

        response = lambda_handler(event, context)

        assert response['statusCode'] == 200
        mock_pipeline.process_pipeline.assert_called_once_with(event_type='scheduled')


def test_lambda_handler_manual_event():
    """Test Lambda handler with manual invocation."""
    event = {
        'source': 'manual',
        'detail-type': 'Manual Test'
    }
    context = Mock()

    with patch('src.lambda_handler.SentimentFinancePipeline') as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline.process_pipeline.return_value = {'success': True}
        mock_pipeline_class.return_value = mock_pipeline

        response = lambda_handler(event, context)

        assert response['statusCode'] == 200
        mock_pipeline.process_pipeline.assert_called_once_with(event_type='manual')


def test_lambda_handler_error():
    """Test Lambda handler error handling."""
    event = {'source': 'aws.events'}
    context = Mock()

    with patch('src.lambda_handler.SentimentFinancePipeline') as mock_pipeline_class:
        mock_pipeline_class.side_effect = Exception('Pipeline error')

        response = lambda_handler(event, context)

        assert response['statusCode'] == 500
        assert 'error' in response['body']


def test_pipeline_process_with_maintenance_cleanup(mock_pipeline_components):
    """Test pipeline cleanup in maintenance mode."""
    pipeline = SentimentFinancePipeline()

    pipeline.db_manager.insert_company = Mock(return_value=1)
    # Return some articles so maintenance cleanup runs
    pipeline.data_fetcher.fetch_financial_news = Mock(return_value=[{
        'title': 'Test',
        'url': 'http://test.com',
        'published_at': datetime.now(),
        'source': 'Test',
        'company_search_term': 'Apple Inc.'
    }])
    pipeline.data_fetcher.fetch_sector_news = Mock(return_value=[])
    pipeline.db_manager.insert_article = Mock(return_value=1)
    pipeline.sentiment_analyzer.analyze_sentiment = Mock(return_value={
        'sentiment_score': 0.5,
        'confidence': 0.8,
        'sentiment_label': 'positive'
    })
    pipeline.db_manager.insert_sentiment_score = Mock()
    pipeline.db_manager.cleanup_old_articles = Mock(return_value=25)

    result = pipeline.process_pipeline('maintenance')

    assert 'old_articles_deleted' in result
    assert result['old_articles_deleted'] == 25
    assert result['old_articles_deleted'] == 25
    pipeline.db_manager.cleanup_old_articles.assert_called_once_with(days_to_keep=90)


def test_pipeline_error_handling_in_article_processing(mock_pipeline_components):
    """Test error handling when processing individual articles fails."""
    pipeline = SentimentFinancePipeline()

    pipeline.db_manager.insert_article = Mock(side_effect=Exception('DB error'))
    pipeline.sentiment_analyzer.analyze_sentiment = Mock(return_value={
        'sentiment_score': 0.5,
        'confidence': 0.8,
        'sentiment_label': 'positive',
        'method': 'combined'
    })

    articles = [
        {
            'title': 'Test',
            'content': 'Test content',
            'url': 'https://example.com/test',
            'source': 'Test',
            'published_at': datetime.now(),
            'company_search_term': 'Apple Inc.'
        }
    ]
    company_ids = {'Apple Inc.': 1}

    # Should not raise exception, just log error
    processed = pipeline._process_articles(articles, company_ids)

    assert processed == 0  # No articles successfully processed


def test_local_test_handler():
    """Test local test handler function."""
    with patch('src.lambda_handler.SentimentFinancePipeline') as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline.process_pipeline.return_value = {'success': True}
        mock_pipeline_class.return_value = mock_pipeline

        result = local_test_handler('scheduled')

        assert result['success'] is True
        mock_pipeline.process_pipeline.assert_called_once_with(event_type='scheduled')