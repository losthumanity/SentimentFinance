"""
SentimentAnalyzer class for text processing and sentiment analysis.
Uses NLTK and TextBlob for natural language processing.
"""

import os
import re
import logging
from typing import Dict, Tuple, Optional, List
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Handles sentiment analysis using NLTK and TextBlob."""
    
    def __init__(self):
        """Initialize SentimentAnalyzer and download required NLTK data."""
        self._setup_nltk()
        self.lemmatizer = WordNetLemmatizer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            logger.warning("NLTK stopwords not found, downloading...")
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        
        # Financial keywords that might affect sentiment
        self.financial_keywords = {
            'positive': [
                'profit', 'growth', 'increase', 'gain', 'rise', 'bull', 'bullish',
                'up', 'surge', 'rally', 'outperform', 'beat', 'exceed', 'strong',
                'robust', 'solid', 'record', 'milestone', 'breakthrough', 'success'
            ],
            'negative': [
                'loss', 'decline', 'fall', 'drop', 'bear', 'bearish', 'down',
                'crash', 'plunge', 'underperform', 'miss', 'weak', 'poor',
                'disappointing', 'struggle', 'concern', 'risk', 'uncertainty'
            ]
        }
    
    def _setup_nltk(self):
        """Download and setup required NLTK resources."""
        required_nltk_data = [
            'punkt', 'stopwords', 'wordnet', 'vader_lexicon'
        ]
        
        for resource in required_nltk_data:
            try:
                nltk.data.find(f'tokenizers/{resource}')
            except LookupError:
                try:
                    nltk.data.find(f'corpora/{resource}')
                except LookupError:
                    try:
                        nltk.data.find(f'sentiment/{resource}')
                    except LookupError:
                        logger.info(f"Downloading NLTK resource: {resource}")
                        nltk.download(resource, quiet=True)
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of given text using multiple methods.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not text or not text.strip():
            return self._empty_sentiment_result()
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # TextBlob analysis
        textblob_result = self._analyze_with_textblob(cleaned_text)
        
        # NLTK VADER analysis
        vader_result = self._analyze_with_vader(cleaned_text)
        
        # Financial keyword analysis
        keyword_result = self._analyze_financial_keywords(cleaned_text)
        
        # Combine results with weighted average
        combined_result = self._combine_sentiment_results(
            textblob_result, vader_result, keyword_result
        )
        
        return combined_result
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text for sentiment analysis.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation that matters for sentiment
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        return text.strip()
    
    def _analyze_with_textblob(self, text: str) -> Dict:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Preprocessed text
            
        Returns:
            TextBlob sentiment results
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert polarity to label
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'method': 'textblob',
                'score': polarity,
                'confidence': 1 - subjectivity,  # More objective = higher confidence
                'label': label,
                'subjectivity': subjectivity
            }
        except Exception as e:
            logger.error(f"TextBlob analysis error: {str(e)}")
            return self._empty_sentiment_result('textblob')
    
    def _analyze_with_vader(self, text: str) -> Dict:
        """
        Analyze sentiment using NLTK's VADER.
        
        Args:
            text: Preprocessed text
            
        Returns:
            VADER sentiment results
        """
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            
            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(text)
            
            compound_score = scores['compound']
            
            # Convert compound score to label
            if compound_score >= 0.05:
                label = 'positive'
            elif compound_score <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'
            
            # Calculate confidence based on the strongest emotion
            confidence = max(scores['pos'], scores['neu'], scores['neg'])
            
            return {
                'method': 'vader',
                'score': compound_score,
                'confidence': confidence,
                'label': label,
                'pos': scores['pos'],
                'neu': scores['neu'],
                'neg': scores['neg']
            }
        except Exception as e:
            logger.error(f"VADER analysis error: {str(e)}")
            return self._empty_sentiment_result('vader')
    
    def _analyze_financial_keywords(self, text: str) -> Dict:
        """
        Analyze sentiment based on financial keywords.
        
        Args:
            text: Preprocessed text
            
        Returns:
            Financial keyword sentiment results
        """
        text_lower = text.lower()
        
        # Tokenize text
        tokens = word_tokenize(text_lower)
        tokens = [token for token in tokens if token not in self.stop_words and token.isalpha()]
        
        positive_count = 0
        negative_count = 0
        
        # Count financial sentiment keywords
        for token in tokens:
            if token in self.financial_keywords['positive']:
                positive_count += 1
            elif token in self.financial_keywords['negative']:
                negative_count += 1
        
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return self._empty_sentiment_result('financial_keywords')
        
        # Calculate score based on keyword ratio
        score = (positive_count - negative_count) / total_keywords
        
        # Determine label
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Confidence based on number of keywords found
        confidence = min(total_keywords / 10, 1.0)  # More keywords = higher confidence
        
        return {
            'method': 'financial_keywords',
            'score': score,
            'confidence': confidence,
            'label': label,
            'positive_keywords': positive_count,
            'negative_keywords': negative_count,
            'total_keywords': total_keywords
        }
    
    def _combine_sentiment_results(self, textblob_result: Dict, 
                                  vader_result: Dict, 
                                  keyword_result: Dict) -> Dict:
        """
        Combine multiple sentiment analysis results using weighted average.
        
        Args:
            textblob_result: TextBlob analysis results
            vader_result: VADER analysis results
            keyword_result: Financial keyword analysis results
            
        Returns:
            Combined sentiment analysis results
        """
        # Weights for different methods
        weights = {
            'textblob': 0.4,
            'vader': 0.4,
            'financial_keywords': 0.2
        }
        
        results = [textblob_result, vader_result, keyword_result]
        
        # Calculate weighted scores
        total_score = 0
        total_confidence = 0
        total_weight = 0
        
        label_votes = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for result in results:
            method = result['method']
            if method in weights and result['score'] is not None:
                weight = weights[method]
                total_score += result['score'] * weight
                total_confidence += result['confidence'] * weight
                total_weight += weight
                
                # Vote for label
                label_votes[result['label']] += weight
        
        if total_weight == 0:
            return self._empty_sentiment_result('combined')
        
        # Calculate final scores
        final_score = total_score / total_weight
        final_confidence = total_confidence / total_weight
        
        # Determine final label by majority vote
        final_label = max(label_votes, key=label_votes.get)
        
        return {
            'method': 'combined',
            'sentiment_score': final_score,
            'confidence': final_confidence,
            'sentiment_label': final_label,
            'individual_results': {
                'textblob': textblob_result,
                'vader': vader_result,
                'financial_keywords': keyword_result
            }
        }
    
    def _empty_sentiment_result(self, method: str = 'unknown') -> Dict:
        """
        Return empty/neutral sentiment result for error cases.
        
        Args:
            method: Analysis method name
            
        Returns:
            Neutral sentiment result
        """
        return {
            'method': method,
            'score': 0.0,
            'confidence': 0.0,
            'label': 'neutral'
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment for multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.analyze_sentiment(text)
                result['text_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing text {i}: {str(e)}")
                result = self._empty_sentiment_result('error')
                result['text_index'] = i
                result['error'] = str(e)
                results.append(result)
        
        return results
    
    def extract_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text using simple NLP techniques.
        
        Args:
            text: Text to extract phrases from
            num_phrases: Number of phrases to return
            
        Returns:
            List of key phrases
        """
        try:
            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Tokenize into sentences
            sentences = sent_tokenize(cleaned_text)
            
            # Extract noun phrases using TextBlob
            blob = TextBlob(cleaned_text)
            noun_phrases = blob.noun_phrases
            
            # Filter and rank phrases
            phrases = []
            for phrase in noun_phrases:
                # Skip very short or very long phrases
                if 2 <= len(phrase.split()) <= 4:
                    phrases.append(phrase)
            
            # Return top phrases (could be enhanced with TF-IDF or other ranking)
            return list(set(phrases))[:num_phrases]
            
        except Exception as e:
            logger.error(f"Error extracting key phrases: {str(e)}")
            return []