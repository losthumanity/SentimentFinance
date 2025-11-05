-- ============================================================================
-- Sentiment Finance Database Schema
-- Normalized MySQL database design for financial news sentiment analysis
-- ============================================================================

-- Create database (run this separately if needed)
-- CREATE DATABASE IF NOT EXISTS sentiment_finance 
-- CHARACTER SET utf8mb4 
-- COLLATE utf8mb4_unicode_ci;

-- USE sentiment_finance;

-- Drop tables in reverse order of dependencies for clean setup
DROP TABLE IF EXISTS sentiment_scores;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS companies;

-- ============================================================================
-- Table: companies
-- Stores company information and business sectors
-- ============================================================================
CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    sector VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NULL,
    description TEXT NULL,
    market_cap BIGINT NULL,
    employees INT NULL,
    founded_year YEAR NULL,
    headquarters VARCHAR(255) NULL,
    website VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_sector (sector),
    INDEX idx_symbol (symbol),
    INDEX idx_name_sector (name, sector)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Company master data with sector classification';

-- ============================================================================
-- Table: articles
-- Stores raw news articles with metadata and company associations
-- ============================================================================
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT NULL,
    content LONGTEXT NULL,
    url VARCHAR(1000) NOT NULL UNIQUE,
    source VARCHAR(255) NOT NULL,
    author VARCHAR(255) NULL,
    published_at TIMESTAMP NOT NULL,
    company_id INT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    category VARCHAR(100) NULL,
    tags JSON NULL,
    word_count INT NULL,
    reading_time_minutes INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (company_id) REFERENCES companies(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    -- Indexes for performance
    INDEX idx_published_at (published_at),
    INDEX idx_company_published (company_id, published_at),
    INDEX idx_source (source),
    INDEX idx_url_hash (url(255)),
    INDEX idx_title_fulltext (title),
    
    -- Full-text search indexes
    FULLTEXT INDEX ft_title_content (title, content)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='News articles with company associations and metadata';

-- ============================================================================
-- Table: sentiment_scores
-- Stores sentiment analysis results with confidence metrics
-- ============================================================================
CREATE TABLE sentiment_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    sentiment_score DECIMAL(5,4) NOT NULL COMMENT 'Sentiment score from -1.0000 to 1.0000',
    confidence DECIMAL(5,4) NOT NULL COMMENT 'Confidence level from 0.0000 to 1.0000',
    sentiment_label ENUM('positive', 'negative', 'neutral') NOT NULL,
    processing_method VARCHAR(50) NOT NULL DEFAULT 'textblob',
    processing_version VARCHAR(20) NULL,
    subjectivity DECIMAL(5,4) NULL COMMENT 'Subjectivity score from 0.0000 to 1.0000',
    keywords JSON NULL COMMENT 'Key phrases or words that influenced sentiment',
    processing_time_ms INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (article_id) REFERENCES articles(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    -- Unique constraint - one sentiment score per article per method
    UNIQUE KEY unique_article_method (article_id, processing_method),
    
    -- Indexes for performance
    INDEX idx_sentiment_score (sentiment_score),
    INDEX idx_sentiment_label (sentiment_label),
    INDEX idx_confidence (confidence),
    INDEX idx_article_sentiment (article_id, sentiment_score),
    INDEX idx_created_at (created_at),
    
    -- Check constraints for data validation
    CHECK (sentiment_score >= -1.0000 AND sentiment_score <= 1.0000),
    CHECK (confidence >= 0.0000 AND confidence <= 1.0000),
    CHECK (subjectivity IS NULL OR (subjectivity >= 0.0000 AND subjectivity <= 1.0000))
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Sentiment analysis results with confidence metrics';

-- ============================================================================
-- Insert sample companies for testing
-- ============================================================================
INSERT INTO companies (name, sector, symbol, description, market_cap, employees, founded_year, headquarters) VALUES
('Apple Inc.', 'Technology', 'AAPL', 'Consumer electronics, software, and services', 3000000000000, 154000, 1976, 'Cupertino, CA'),
('Microsoft Corporation', 'Technology', 'MSFT', 'Software, cloud computing, and productivity services', 2800000000000, 221000, 1975, 'Redmond, WA'),
('Amazon.com Inc.', 'Technology', 'AMZN', 'E-commerce, cloud computing, and digital services', 1500000000000, 1540000, 1994, 'Seattle, WA'),
('Tesla Inc.', 'Automotive', 'TSLA', 'Electric vehicles and clean energy solutions', 800000000000, 140473, 2003, 'Austin, TX'),
('Alphabet Inc.', 'Technology', 'GOOGL', 'Internet services, advertising, and cloud computing', 1700000000000, 190000, 1998, 'Mountain View, CA'),
('Meta Platforms Inc.', 'Technology', 'META', 'Social media and virtual reality platforms', 750000000000, 86482, 2004, 'Menlo Park, CA'),
('NVIDIA Corporation', 'Technology', 'NVDA', 'Graphics processing and artificial intelligence', 1200000000000, 29600, 1993, 'Santa Clara, CA'),
('JPMorgan Chase & Co.', 'Financial Services', 'JPM', 'Investment banking and financial services', 500000000000, 288474, 1799, 'New York, NY'),
('Johnson & Johnson', 'Healthcare', 'JNJ', 'Pharmaceuticals, medical devices, and consumer products', 450000000000, 152700, 1886, 'New Brunswick, NJ'),
('Berkshire Hathaway', 'Financial Services', 'BRK.A', 'Diversified holding company', 750000000000, 383000, 1839, 'Omaha, NE');

-- ============================================================================
-- Create views for common queries
-- ============================================================================

-- View: Recent sentiment summary by company
CREATE VIEW v_recent_company_sentiment AS
SELECT 
    c.name AS company_name,
    c.sector,
    c.symbol,
    COUNT(a.id) AS article_count,
    AVG(s.sentiment_score) AS avg_sentiment,
    MIN(s.sentiment_score) AS min_sentiment,
    MAX(s.sentiment_score) AS max_sentiment,
    AVG(s.confidence) AS avg_confidence,
    SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
    MAX(a.published_at) AS latest_article_date
FROM companies c
LEFT JOIN articles a ON c.id = a.company_id 
LEFT JOIN sentiment_scores s ON a.id = s.article_id
WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY c.id, c.name, c.sector, c.symbol
HAVING article_count > 0
ORDER BY avg_sentiment DESC;

-- View: Daily sentiment trends
CREATE VIEW v_daily_sentiment_trends AS
SELECT 
    DATE(a.published_at) AS date,
    c.sector,
    COUNT(a.id) AS total_articles,
    AVG(s.sentiment_score) AS avg_sentiment,
    SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_articles,
    SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_articles,
    SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_articles
FROM articles a
JOIN companies c ON a.company_id = c.id
JOIN sentiment_scores s ON a.id = s.article_id
WHERE a.published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(a.published_at), c.sector
ORDER BY date DESC, c.sector;

-- ============================================================================
-- Create stored procedures for common operations
-- ============================================================================

DELIMITER //

-- Procedure: Get company sentiment report
CREATE PROCEDURE GetCompanySentimentReport(
    IN company_name_param VARCHAR(255),
    IN days_back INT DEFAULT 7
)
BEGIN
    SELECT 
        c.name AS company_name,
        c.sector,
        c.symbol,
        DATE(a.published_at) AS date,
        COUNT(a.id) AS article_count,
        AVG(s.sentiment_score) AS avg_sentiment,
        MIN(s.sentiment_score) AS min_sentiment,
        MAX(s.sentiment_score) AS max_sentiment,
        AVG(s.confidence) AS avg_confidence,
        SUM(CASE WHEN s.sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN s.sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN s.sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_count
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE c.name = company_name_param
      AND a.published_at >= DATE_SUB(NOW(), INTERVAL days_back DAY)
    GROUP BY c.name, c.sector, c.symbol, DATE(a.published_at)
    ORDER BY DATE(a.published_at) DESC;
END //

-- Procedure: Get sector analysis
CREATE PROCEDURE GetSectorAnalysis(
    IN sector_param VARCHAR(100),
    IN days_back INT DEFAULT 30
)
BEGIN
    SELECT 
        c.name AS company_name,
        COUNT(a.id) AS article_count,
        AVG(s.sentiment_score) AS avg_sentiment,
        CASE 
            WHEN AVG(s.sentiment_score) > 0.1 THEN 'Positive'
            WHEN AVG(s.sentiment_score) < -0.1 THEN 'Negative'
            ELSE 'Neutral'
        END AS sentiment_trend,
        AVG(s.confidence) AS avg_confidence
    FROM companies c
    JOIN articles a ON c.id = a.company_id
    JOIN sentiment_scores s ON a.id = s.article_id
    WHERE c.sector = sector_param
      AND a.published_at >= DATE_SUB(NOW(), INTERVAL days_back DAY)
    GROUP BY c.id, c.name
    HAVING article_count >= 1
    ORDER BY avg_sentiment DESC;
END //

DELIMITER ;

-- ============================================================================
-- Create indexes for optimization
-- ============================================================================

-- Composite index for time-series queries
CREATE INDEX idx_articles_company_date_sentiment ON articles(company_id, published_at);

-- Index for sentiment analysis queries
CREATE INDEX idx_sentiment_article_score ON sentiment_scores(article_id, sentiment_score, confidence);

-- ============================================================================
-- Grant permissions (adjust as needed for your environment)
-- ============================================================================

-- Example permissions for application user
-- CREATE USER IF NOT EXISTS 'sentiment_app'@'%' IDENTIFIED BY 'secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sentiment_finance.* TO 'sentiment_app'@'%';
-- GRANT EXECUTE ON PROCEDURE sentiment_finance.GetCompanySentimentReport TO 'sentiment_app'@'%';
-- GRANT EXECUTE ON PROCEDURE sentiment_finance.GetSectorAnalysis TO 'sentiment_app'@'%';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- Sample data validation queries
-- ============================================================================

-- Verify foreign key constraints are working
-- INSERT INTO articles (title, url, source, published_at, company_id) 
-- VALUES ('Test', 'http://test.com', 'Test Source', NOW(), 999); -- Should fail

-- Verify check constraints are working
-- INSERT INTO sentiment_scores (article_id, sentiment_score, confidence, sentiment_label)
-- VALUES (1, 2.0, 0.5, 'positive'); -- Should fail due to sentiment_score > 1.0

-- ============================================================================
-- Performance monitoring queries
-- ============================================================================

-- Check table sizes
-- SELECT 
--     table_name,
--     ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
--     table_rows
-- FROM information_schema.tables 
-- WHERE table_schema = 'sentiment_finance'
-- ORDER BY size_mb DESC;

-- Check index usage
-- SHOW INDEX FROM articles;
-- SHOW INDEX FROM sentiment_scores;
-- SHOW INDEX FROM companies;