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
    # Empty text returns an empty result with basic keys
    assert result['label'] == 'neutral'
    assert result['score'] == 0.0
    assert result['confidence'] == 0.0
