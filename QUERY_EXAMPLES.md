# Complex Query Examples - Verified Results

All queries in `sql/complex_queries.sql` have been tested and verified against live data (98 articles, 10 companies, 2025-11-18).

## ✅ Query 1: Weekly Sentiment Report
**Purpose:** Daily sentiment breakdown for a specific company

**Sample Result for Apple Inc.:**
```
Company: Apple Inc. (AAPL)
Date: 2025-11-18
Articles: 13
Avg Sentiment: 0.3344
Min: -0.2112 | Max: 0.7285
```

**Use Case:** Track daily sentiment trends for individual stocks

---

## ✅ Query 2: Sector Analysis with Rankings
**Purpose:** Rank companies within a sector by sentiment performance

**Sample Result (Technology Sector):**
```
1. NVIDIA Corporation (NVDA)  - 0.4435 sentiment (6 articles)
2. Apple Inc. (AAPL)          - 0.3344 sentiment (13 articles)
3. Meta Platforms Inc. (META) - 0.2502 sentiment (7 articles)
4. Amazon.com Inc. (AMZN)     - 0.1889 sentiment (10 articles)
5. Alphabet Inc. (GOOGL)      - 0.1095 sentiment (9 articles)
6. Microsoft Corporation (MSFT)- 0.0930 sentiment (10 articles)
```

**Use Case:** Identify top performers within a sector

---

## ✅ Query 4: Cross-Sector Comparison
**Purpose:** Compare sentiment across different business sectors

**Sample Results:**
```
Technology:         0.2285 sentiment (55 articles, 6 companies)
Healthcare:         0.2140 sentiment (10 articles, 1 company)
Financial Services: 0.2129 sentiment (23 articles, 2 companies)
Automotive:         0.0751 sentiment (10 articles, 1 company)
```

**Use Case:** Sector rotation strategies, identifying hot sectors

---

## ✅ Query 5: News Source Reliability
**Purpose:** Analyze consistency and sentiment bias by news source

**Sample Results:**
```
Thefly.com:         0.3096 avg (σ=0.0547) - Most positive, low volatility
GlobeNewswire:      0.2884 avg (σ=0.0847)
Yahoo Entertainment: 0.2841 avg (σ=0.3252) - High volatility
Fortune:            0.2057 avg (σ=0.2102)
```

**Use Case:** Identify reliable vs biased news sources

---

## ✅ Query 8: Company Performance Analysis
**Purpose:** Rank all companies by sentiment score

**Sample Results:**
```
1. NVIDIA Corporation     - 0.4435 (6 articles)
2. Apple Inc.             - 0.3344 (13 articles)
3. Meta Platforms Inc.    - 0.2502 (7 articles)
4. Berkshire Hathaway     - 0.2277 (7 articles)
5. Johnson & Johnson      - 0.2140 (10 articles)
6. JPMorgan Chase & Co.   - 0.2064 (16 articles)
7. Amazon.com Inc.        - 0.1889 (10 articles)
8. Alphabet Inc.          - 0.1095 (9 articles)
9. Microsoft Corporation  - 0.0930 (10 articles)
10. Tesla Inc.            - 0.0751 (10 articles)
```

**Use Case:** Overall market sentiment ranking

---

## ✅ Query 10: Portfolio Sentiment Report
**Purpose:** Risk-adjusted sentiment analysis for a portfolio

**Sample Results (Tech Portfolio):**
```
NVIDIA Corporation   - 0.4435 sentiment, volatility: 0.1149, risk-adj: 0.3977
Apple Inc.           - 0.3344 sentiment, volatility: 0.2575, risk-adj: 0.2660
Microsoft Corporation- 0.0930 sentiment, volatility: 0.1882, risk-adj: 0.0783
Tesla Inc.           - 0.0751 sentiment, volatility: 0.2105, risk-adj: 0.0620
```

**Insight:** NVIDIA has best risk-adjusted sentiment (high sentiment, low volatility)

**Use Case:** Portfolio optimization, risk management

---

## Additional Queries Available

- **Query 3:** Moving averages for trend analysis
- **Query 6:** Sentiment correlation between companies
- **Query 7:** Market momentum with shift detection
- **Query 9:** Time-based patterns (day of week, hour)

---

## How to Run Queries

### From MySQL Client:
```bash
docker exec -it sentiment_finance_db mysql -usentiment_app -psentiment_password sentiment_finance
```

Then paste any query from `sql/complex_queries.sql`

### From Python:
```python
from src.database_manager import DatabaseManager

db = DatabaseManager()
results = db.execute_query("YOUR_QUERY_HERE")
```

### From Command Line:
```bash
docker exec sentiment_finance_db mysql -usentiment_app -psentiment_password sentiment_finance -e "YOUR_QUERY_HERE"
```

---

## Key Insights from Current Data (2025-11-18)

✅ **Most articles:** JPMorgan Chase (16), Apple (13)
✅ **Best sentiment:** NVIDIA (0.44), Apple (0.33)
✅ **Best sector:** Technology (0.23 avg)
✅ **Most reliable source:** Thefly.com (low volatility)
✅ **Best risk-adjusted:** NVIDIA (high sentiment + low volatility)

---

## Advanced Features Demonstrated

- ✅ Common Table Expressions (CTEs)
- ✅ Window Functions (RANK, ROW_NUMBER, NTILE, LAG)
- ✅ Subqueries (correlated and non-correlated)
- ✅ Self-joins and Cross-joins
- ✅ Aggregation with GROUP BY and HAVING
- ✅ Date/time functions
- ✅ Statistical functions (AVG, STDDEV, MIN, MAX)
- ✅ Conditional aggregation (CASE WHEN in SUM)
- ✅ Multi-level aggregation
- ✅ Risk-adjusted metrics

All queries are production-ready and optimized with proper indexes!
