-- ============================================================================
-- Complex SQL Queries for Sentiment Finance Analysis
-- Demonstrates advanced SQL techniques: JOINs, subqueries, CTEs, window functions
-- ============================================================================

-- ============================================================================
-- 1. Weekly Sentiment Report for Specific Company
-- Uses JOINs, GROUP BY, date filtering, and aggregation functions
-- ============================================================================

-- Basic weekly sentiment report
SELECT 
    c.name as company_name,
    c.sector,
    c.symbol,
    DATE(a.published_at) as date,
    COUNT(a.id) as article_count,
    AVG(s.sentiment_score) as avg_sentiment,
    MIN(s.sentiment_score) as min_sentiment,
    MAX(s.sentiment_score) as max_sentiment,
    STDDEV(s.sentiment_score) as sentiment_volatility,
    AVG(s.confidence) as avg_confidence,
    SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
    SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
    -- Calculate sentiment momentum (positive - negative ratio)
    (SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) - 
     SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END)) / COUNT(a.id) as sentiment_momentum
FROM companies c
JOIN articles a ON c.id = a.company_id
JOIN sentiment_scores s ON a.id = s.article_id
WHERE c.name = 'Apple Inc.' 
  AND a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY c.name, c.sector, c.symbol, DATE(a.published_at)
ORDER BY DATE(a.published_at) DESC;

-- ============================================================================
-- 2. Sector Analysis with Subqueries and Rankings
-- Uses subqueries, window functions, and complex aggregations
-- ============================================================================

-- Find top-performing companies in technology sector with ranking
WITH sector_sentiment AS (
    SELECT 
        c.id as company_id,
        c.name as company_name,
        c.symbol,
        COUNT(a.id) as total_articles,
        AVG(s.sentiment_score) as avg_sentiment,
        AVG(s.confidence) as avg_confidence,
        -- Calculate weighted sentiment (sentiment * confidence)
        AVG(s.sentiment_score * s.confidence) as weighted_sentiment
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE c.sector = 'Technology' 
      AND a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY c.id, c.name, c.symbol
    HAVING total_articles >= 5  -- Only companies with substantial coverage
),
ranked_companies AS (
    SELECT *,
        RANK() OVER (ORDER BY weighted_sentiment DESC) as sentiment_rank,
        NTILE(4) OVER (ORDER BY weighted_sentiment DESC) as quartile
    FROM sector_sentiment
)
SELECT 
    company_name,
    symbol,
    total_articles,
    ROUND(avg_sentiment, 4) as avg_sentiment,
    ROUND(weighted_sentiment, 4) as weighted_sentiment,
    sentiment_rank,
    CASE quartile
        WHEN 1 THEN 'Top Quartile'
        WHEN 2 THEN 'Second Quartile'
        WHEN 3 THEN 'Third Quartile'
        ELSE 'Bottom Quartile'
    END as performance_tier
FROM ranked_companies
ORDER BY sentiment_rank;

-- ============================================================================
-- 3. Sentiment Trend Analysis with Moving Averages
-- Uses window functions for time-series analysis
-- ============================================================================

-- 7-day moving average of sentiment for a specific company
SELECT 
    date,
    daily_sentiment,
    article_count,
    -- 7-day moving average
    AVG(daily_sentiment) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as sentiment_7day_ma,
    -- Compare current sentiment to moving average
    CASE 
        WHEN daily_sentiment > AVG(daily_sentiment) OVER (
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) THEN 'Above Average'
        ELSE 'Below Average'
    END as trend_indicator
FROM (
    SELECT 
        DATE(a.published_at) as date,
        AVG(s.sentiment_score) as daily_sentiment,
        COUNT(a.id) as article_count
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE c.name = 'Tesla Inc.'
      AND a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY DATE(a.published_at)
) daily_data
ORDER BY date;

-- ============================================================================
-- 4. Cross-Sector Sentiment Comparison with Subqueries
-- Compares sentiment across different business sectors
-- ============================================================================

SELECT 
    sector_data.sector,
    sector_data.total_companies,
    sector_data.total_articles,
    sector_data.avg_sector_sentiment,
    sector_data.sentiment_volatility,
    -- Compare to overall market sentiment
    ROUND(
        sector_data.avg_sector_sentiment - market_data.market_avg, 4
    ) as vs_market_sentiment,
    -- Top company in sector
    top_companies.best_company,
    top_companies.best_company_sentiment
FROM (
    -- Sector aggregation
    SELECT 
        c.sector,
        COUNT(DISTINCT c.id) as total_companies,
        COUNT(a.id) as total_articles,
        AVG(s.sentiment_score) as avg_sector_sentiment,
        STDDEV(s.sentiment_score) as sentiment_volatility
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY c.sector
    HAVING total_articles >= 10
) sector_data
CROSS JOIN (
    -- Overall market sentiment
    SELECT AVG(s.sentiment_score) as market_avg
    FROM articles a
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) market_data
LEFT JOIN (
    -- Best performing company per sector
    SELECT 
        c.sector,
        c.name as best_company,
        AVG(s.sentiment_score) as best_company_sentiment,
        ROW_NUMBER() OVER (PARTITION BY c.sector ORDER BY AVG(s.sentiment_score) DESC) as rn
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY c.sector, c.id, c.name
) top_companies ON sector_data.sector = top_companies.sector AND top_companies.rn = 1
ORDER BY avg_sector_sentiment DESC;

-- ============================================================================
-- 5. News Source Reliability Analysis
-- Analyzes sentiment consistency across different news sources
-- ============================================================================

-- Compare sentiment scores across news sources
SELECT 
    a.source,
    COUNT(a.id) as total_articles,
    AVG(s.sentiment_score) as avg_sentiment,
    STDDEV(s.sentiment_score) as sentiment_std_dev,
    AVG(s.confidence) as avg_confidence,
    -- Calculate consistency score (inverse of standard deviation)
    1 / (1 + STDDEV(s.sentiment_score)) as consistency_score,
    -- Distribution of sentiment labels
    SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) / COUNT(*) as positive_ratio,
    SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) / COUNT(*) as negative_ratio,
    SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) / COUNT(*) as neutral_ratio
FROM articles a
JOIN sentiment_scores s ON a.id = s.article_id
WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY a.source
HAVING total_articles >= 20  -- Only sources with substantial coverage
ORDER BY consistency_score DESC, avg_confidence DESC;

-- ============================================================================
-- 6. Sentiment Correlation Between Companies
-- Find companies with similar sentiment patterns
-- ============================================================================

-- Compare sentiment correlation between two companies
WITH company_daily_sentiment AS (
    SELECT 
        c.name as company_name,
        DATE(a.published_at) as date,
        AVG(s.sentiment_score) as daily_sentiment
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
      AND c.name IN ('Apple Inc.', 'Microsoft Corporation')
    GROUP BY c.name, DATE(a.published_at)
),
apple_sentiment AS (
    SELECT date, daily_sentiment as apple_sentiment
    FROM company_daily_sentiment
    WHERE company_name = 'Apple Inc.'
),
microsoft_sentiment AS (
    SELECT date, daily_sentiment as microsoft_sentiment
    FROM company_daily_sentiment
    WHERE company_name = 'Microsoft Corporation'
)
SELECT 
    a.date,
    a.apple_sentiment,
    m.microsoft_sentiment,
    ABS(a.apple_sentiment - m.microsoft_sentiment) as sentiment_difference,
    CASE 
        WHEN ABS(a.apple_sentiment - m.microsoft_sentiment) < 0.1 THEN 'Highly Correlated'
        WHEN ABS(a.apple_sentiment - m.microsoft_sentiment) < 0.3 THEN 'Moderately Correlated'
        ELSE 'Divergent'
    END as correlation_level
FROM apple_sentiment a
JOIN microsoft_sentiment m ON a.date = m.date
ORDER BY a.date DESC;

-- ============================================================================
-- 7. Market Sentiment Momentum Analysis
-- Identify sentiment momentum shifts and market trends
-- ============================================================================

-- Daily market momentum with trend detection
WITH daily_market_sentiment AS (
    SELECT 
        DATE(a.published_at) as date,
        COUNT(a.id) as total_articles,
        AVG(s.sentiment_score) as avg_sentiment,
        SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_articles,
        SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_articles
    FROM articles a
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
    GROUP BY DATE(a.published_at)
),
momentum_analysis AS (
    SELECT 
        *,
        positive_articles - negative_articles as sentiment_momentum,
        LAG(avg_sentiment) OVER (ORDER BY date) as prev_day_sentiment,
        avg_sentiment - LAG(avg_sentiment) OVER (ORDER BY date) as sentiment_change
    FROM daily_market_sentiment
)
SELECT 
    date,
    avg_sentiment,
    sentiment_momentum,
    sentiment_change,
    CASE 
        WHEN sentiment_change > 0.05 THEN 'Strong Positive Shift'
        WHEN sentiment_change > 0.02 THEN 'Positive Shift'
        WHEN sentiment_change < -0.05 THEN 'Strong Negative Shift'
        WHEN sentiment_change < -0.02 THEN 'Negative Shift'
        ELSE 'Stable'
    END as momentum_trend,
    total_articles
FROM momentum_analysis
WHERE prev_day_sentiment IS NOT NULL
ORDER BY date DESC;

-- ============================================================================
-- 8. Advanced Subquery: Companies Outperforming Their Sector
-- Uses correlated subqueries and statistical comparisons
-- ============================================================================

-- Find companies performing better than their sector average
SELECT 
    c.name as company_name,
    c.sector,
    c.symbol,
    company_stats.avg_sentiment as company_sentiment,
    company_stats.article_count,
    sector_stats.sector_avg_sentiment,
    ROUND(
        company_stats.avg_sentiment - sector_stats.sector_avg_sentiment, 4
    ) as outperformance,
    CASE 
        WHEN company_stats.avg_sentiment > sector_stats.sector_avg_sentiment + 0.1 THEN 'Strong Outperformer'
        WHEN company_stats.avg_sentiment > sector_stats.sector_avg_sentiment + 0.05 THEN 'Outperformer'
        WHEN company_stats.avg_sentiment < sector_stats.sector_avg_sentiment - 0.05 THEN 'Underperformer'
        ELSE 'In Line'
    END as performance_category
FROM companies c
JOIN (
    -- Individual company sentiment stats
    SELECT 
        a.company_id,
        AVG(s.sentiment_score) as avg_sentiment,
        COUNT(a.id) as article_count
    FROM articles a
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY a.company_id
) company_stats ON c.id = company_stats.company_id
JOIN (
    -- Sector average sentiment
    SELECT 
        c2.sector,
        AVG(s2.sentiment_score) as sector_avg_sentiment
    FROM companies c2
    JOIN articles a2 ON c2.id = a2.company_id
    JOIN sentiment_scores s2 ON a2.id = s2.article_id
    WHERE a2.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY c2.sector
) sector_stats ON c.sector = sector_stats.sector
WHERE company_stats.article_count >= 3  -- Minimum coverage threshold
ORDER BY outperformance DESC;

-- ============================================================================
-- 9. Time-Based Sentiment Pattern Analysis
-- Analyze sentiment patterns by day of week and hour
-- ============================================================================

-- Sentiment patterns by day of week and time of day
SELECT 
    DAYNAME(a.published_at) as day_of_week,
    HOUR(a.published_at) as hour_of_day,
    COUNT(a.id) as article_count,
    AVG(s.sentiment_score) as avg_sentiment,
    CASE 
        WHEN HOUR(a.published_at) BETWEEN 9 AND 16 THEN 'Market Hours'
        WHEN HOUR(a.published_at) BETWEEN 17 AND 20 THEN 'After Hours'
        ELSE 'Off Hours'
    END as market_session
FROM articles a
JOIN sentiment_scores s ON a.id = s.article_id
WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DAYNAME(a.published_at), HOUR(a.published_at)
HAVING article_count >= 5
ORDER BY 
    FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
    hour_of_day;

-- ============================================================================
-- 10. Comprehensive Portfolio Sentiment Report
-- Multi-level aggregation for investment portfolio analysis
-- ============================================================================

-- Portfolio-level sentiment analysis with risk metrics
WITH portfolio_companies AS (
    SELECT * FROM companies 
    WHERE name IN ('Apple Inc.', 'Microsoft Corporation', 'Tesla Inc.', 'NVIDIA Corporation')
),
company_metrics AS (
    SELECT 
        pc.name as company_name,
        pc.sector,
        pc.symbol,
        COUNT(a.id) as article_count,
        AVG(s.sentiment_score) as avg_sentiment,
        STDDEV(s.sentiment_score) as sentiment_volatility,
        MIN(s.sentiment_score) as min_sentiment,
        MAX(s.sentiment_score) as max_sentiment,
        AVG(s.confidence) as avg_confidence
    FROM portfolio_companies pc
    JOIN articles a ON pc.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY pc.id, pc.name, pc.sector, pc.symbol
)
SELECT 
    -- Individual company metrics
    company_name,
    sector,
    symbol,
    article_count,
    ROUND(avg_sentiment, 4) as avg_sentiment,
    ROUND(sentiment_volatility, 4) as volatility,
    ROUND(avg_confidence, 4) as confidence,
    -- Risk-adjusted sentiment score
    ROUND(avg_sentiment / (1 + sentiment_volatility), 4) as risk_adjusted_sentiment,
    -- Portfolio weight (equal weight for simplicity)
    0.25 as portfolio_weight,
    -- Weighted contribution to portfolio sentiment
    ROUND(0.25 * avg_sentiment, 4) as portfolio_contribution
FROM company_metrics

UNION ALL

-- Portfolio summary
SELECT 
    'PORTFOLIO TOTAL' as company_name,
    'Mixed' as sector,
    'PORTFOLIO' as symbol,
    SUM(article_count) as article_count,
    ROUND(AVG(avg_sentiment), 4) as avg_sentiment,
    ROUND(AVG(sentiment_volatility), 4) as volatility,
    ROUND(AVG(avg_confidence), 4) as confidence,
    ROUND(AVG(avg_sentiment / (1 + sentiment_volatility)), 4) as risk_adjusted_sentiment,
    1.00 as portfolio_weight,
    ROUND(SUM(0.25 * avg_sentiment), 4) as portfolio_contribution
FROM company_metrics

ORDER BY FIELD(company_name, 'PORTFOLIO TOTAL', 'Apple Inc.', 'Microsoft Corporation', 'Tesla Inc.', 'NVIDIA Corporation');