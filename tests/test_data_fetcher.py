from unittest.mock import patch, Mock
from src.data_fetcher import DataFetcher
from datetime import datetime


def make_fake_response(articles):
    mock = Mock()
    mock.raise_for_status = Mock()
    mock.json = Mock(return_value={
        'status': 'ok',
        'totalResults': len(articles),
        'articles': articles
    })
    return mock


@patch('src.data_fetcher.requests.get')
def test_fetch_financial_news(mock_get):
    # Create a fake article
    article = {
        'title': 'TestCo posts better than expected revenue',
        'description': 'Quarterly revenue beats estimates',
        'content': 'TestCo has posted strong revenue driven by product sales',
        'url': 'http://example.com/testco',
        'source': {'name': 'Example News'},
        'publishedAt': datetime.utcnow().isoformat() + 'Z',
        'author': 'Reporter'
    }

    mock_get.return_value = make_fake_response([article])

    df = DataFetcher(api_key='fake-key', base_url='https://fake-api')
    results = df.fetch_financial_news(['TestCo'], hours_back=1)

    assert isinstance(results, list)
    assert len(results) == 1
    a = results[0]
    assert a['title'] == article['title']
    assert 'company_search_term' in a
