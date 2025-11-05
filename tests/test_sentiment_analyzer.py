import pytest
from src.sentiment_analyzer import SentimentAnalyzer


def test_sentiment_analyzer_positive():
    sa = SentimentAnalyzer()
    text = "The company reported record profits and strong growth this quarter. Investors are optimistic."
    result = sa.analyze_sentiment(text)
    assert 'sentiment_label' in result
    assert result['sentiment_label'] in ('positive', 'neutral')
    assert isinstance(result['sentiment_score'], float)


def test_sentiment_analyzer_negative():
    sa = SentimentAnalyzer()
    text = "The company missed earnings, issued a weak outlook and faces significant risk ahead."
    result = sa.analyze_sentiment(text)
    assert 'sentiment_label' in result
    assert result['sentiment_label'] in ('negative', 'neutral')
    assert isinstance(result['sentiment_score'], float)


def test_sentiment_analyzer_empty():
    sa = SentimentAnalyzer()
    text = ""
    result = sa.analyze_sentiment(text)
    assert result['sentiment_label'] == 'neutral'
    assert result['sentiment_score'] == 0.0
