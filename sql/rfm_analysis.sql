-- RFM Analysis SQL Queries
-- Author: Sahil Hansa
-- Email: sahilhansa007@gmail.com
-- Description: Recency, Frequency, Monetary analysis for customer segmentation
-- Location: Jammu, J&K, India

-- =============================================
-- RFM Analysis - Complete Implementation
-- =============================================

-- Step 1: Calculate RFM Metrics for each customer
WITH customer_rfm AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.registration_date,
        c.location,
        
        -- Recency: Days since last purchase (lower is better)
        DATEDIFF(CURDATE(), MAX(t.transaction_date)) as recency,
        
        -- Frequency: Number of transactions (higher is better)
        COUNT(t.transaction_id) as frequency,
        
        -- Monetary: Total amount spent (higher is better)
        SUM(t.transaction_amount) as monetary,
        
        -- Additional metrics
        AVG(t.transaction_amount) as avg_order_value,
        MIN(t.transaction_date) as first_purchase_date,
        MAX(t.transaction_date) as last_purchase_date,
        DATEDIFF(MAX(t.transaction_date), MIN(t.transaction_date)) as customer_lifespan
        
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id, c.customer_name, c.registration_date, c.location
),

-- Step 2: Calculate RFM Scores (1-5 scale)
rfm_scores AS (
    SELECT *,
        -- Recency Score (5 = most recent, 1 = least recent)
        CASE 
            WHEN recency <= 30 THEN 5
            WHEN recency <= 60 THEN 4
            WHEN recency <= 90 THEN 3
            WHEN recency <= 180 THEN 2
            ELSE 1
        END as recency_score,
        
        -- Frequency Score (5 = highest frequency, 1 = lowest frequency)
        NTILE(5) OVER (ORDER BY frequency) as frequency_score,
        
        -- Monetary Score (5 = highest spend, 1 = lowest spend)
        NTILE(5) OVER (ORDER BY monetary) as monetary_score
        
    FROM customer_rfm
    WHERE frequency > 0  -- Only customers with transactions
),

-- Step 3: Create RFM Segments
rfm_segments AS (
    SELECT *,
        CONCAT(recency_score, frequency_score, monetary_score) as rfm_code,
        
        -- Overall RFM Score (average of three components)
        ROUND((recency_score + frequency_score + monetary_score) / 3.0, 1) as rfm_score,
        
        -- Customer Segmentation based on RFM
        CASE 
            -- Champions: Best customers (high RFM scores)
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            
            -- Loyal Customers: High frequency and monetary, but not recent
            WHEN frequency_score >= 4 AND monetary_score >= 4 THEN 'Loyal Customers'
            
            -- Potential Loyalists: Recent customers with good frequency
            WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'Potential Loyalists'
            
            -- New Customers: Recent but low frequency/monetary
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
            
            -- Promising: Recent with medium frequency
            WHEN recency_score >= 3 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'Promising'
            
            -- Need Attention: Above average recency, frequency & monetary
            WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Need Attention'
            
            -- About to Sleep: Below average recency but good frequency/monetary
            WHEN recency_score = 2 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'About to Sleep'
            
            -- At Risk: Good monetary but low recency/frequency
            WHEN monetary_score >= 4 AND recency_score <= 2 THEN 'At Risk'
            
            -- Cannot Lose Them: High monetary but very low recency
            WHEN monetary_score >= 4 AND recency_score = 1 THEN 'Cannot Lose Them'
            
            -- Hibernating: Low recency but medium frequency/monetary
            WHEN recency_score <= 2 AND frequency_score >= 2 THEN 'Hibernating'
            
            -- Lost: Lowest RFM scores
            ELSE 'Lost'
        END as customer_segment
        
    FROM rfm_scores
)

-- Final RFM Analysis Results
SELECT 
    customer_id,
    customer_name,
    location,
    recency,
    frequency, 
    monetary,
    avg_order_value,
    customer_lifespan,
    recency_score,
    frequency_score,
    monetary_score,
    rfm_code,
    rfm_score,
    customer_segment
FROM rfm_segments
ORDER BY rfm_score DESC, monetary DESC;

-- =============================================
-- RFM Segment Analysis Summary
-- =============================================

-- Segment performance overview
WITH rfm_analysis AS (
    -- (Include the complete CTE from above)
    SELECT 
        c.customer_id,
        c.customer_name,
        c.location,
        DATEDIFF(CURDATE(), MAX(t.transaction_date)) as recency,
        COUNT(t.transaction_id) as frequency,
        SUM(t.transaction_amount) as monetary,
        AVG(t.transaction_amount) as avg_order_value,
        CASE 
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 30 THEN 5
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 60 THEN 4
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 90 THEN 3
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 180 THEN 2
            ELSE 1
        END as recency_score,
        NTILE(5) OVER (ORDER BY COUNT(t.transaction_id)) as frequency_score,
        NTILE(5) OVER (ORDER BY SUM(t.transaction_amount)) as monetary_score
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id, c.customer_name, c.location
    HAVING frequency > 0
),
segments AS (
    SELECT *,
        CASE 
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            WHEN frequency_score >= 4 AND monetary_score >= 4 THEN 'Loyal Customers'
            WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'Potential Loyalists'
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
            WHEN recency_score >= 3 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'Promising'
            WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Need Attention'
            WHEN recency_score = 2 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'About to Sleep'
            WHEN monetary_score >= 4 AND recency_score <= 2 THEN 'At Risk'
            WHEN monetary_score >= 4 AND recency_score = 1 THEN 'Cannot Lose Them'
            WHEN recency_score <= 2 AND frequency_score >= 2 THEN 'Hibernating'
            ELSE 'Lost'
        END as customer_segment
    FROM rfm_analysis
)
SELECT 
    customer_segment,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM segments), 2) as percentage_of_customers,
    AVG(recency) as avg_recency,
    AVG(frequency) as avg_frequency,
    AVG(monetary) as avg_monetary,
    SUM(monetary) as total_revenue,
    AVG(avg_order_value) as avg_order_value,
    MIN(monetary) as min_monetary,
    MAX(monetary) as max_monetary
FROM segments
GROUP BY customer_segment
ORDER BY total_revenue DESC;

-- =============================================
-- RFM Score Distribution Analysis
-- =============================================

-- Analyze distribution of RFM scores
WITH rfm_distribution AS (
    SELECT 
        c.customer_id,
        CASE 
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 30 THEN 5
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 60 THEN 4
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 90 THEN 3
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 180 THEN 2
            ELSE 1
        END as recency_score,
        NTILE(5) OVER (ORDER BY COUNT(t.transaction_id)) as frequency_score,
        NTILE(5) OVER (ORDER BY SUM(t.transaction_amount)) as monetary_score
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id
    HAVING COUNT(t.transaction_id) > 0
)
SELECT 
    'Recency Distribution' as metric_type,
    recency_score as score,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_distribution), 2) as percentage
FROM rfm_distribution
GROUP BY recency_score

UNION ALL

SELECT 
    'Frequency Distribution' as metric_type,
    frequency_score as score,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_distribution), 2) as percentage
FROM rfm_distribution
GROUP BY frequency_score

UNION ALL

SELECT 
    'Monetary Distribution' as metric_type,
    monetary_score as score,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_distribution), 2) as percentage
FROM rfm_distribution
GROUP BY monetary_score

ORDER BY metric_type, score DESC;

-- =============================================
-- Marketing Action Recommendations
-- =============================================

-- Generate marketing recommendations for each segment
WITH segment_recommendations AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.location,
        DATEDIFF(CURDATE(), MAX(t.transaction_date)) as recency,
        COUNT(t.transaction_id) as frequency,
        SUM(t.transaction_amount) as monetary,
        CASE 
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 30 THEN 5
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 60 THEN 4
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 90 THEN 3
            WHEN DATEDIFF(CURDATE(), MAX(t.transaction_date)) <= 180 THEN 2
            ELSE 1
        END as recency_score,
        NTILE(5) OVER (ORDER BY COUNT(t.transaction_id)) as frequency_score,
        NTILE(5) OVER (ORDER BY SUM(t.transaction_amount)) as monetary_score
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id, c.customer_name, c.location
    HAVING frequency > 0
),
actionable_segments AS (
    SELECT *,
        CASE 
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            WHEN frequency_score >= 4 AND monetary_score >= 4 THEN 'Loyal Customers'
            WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'Potential Loyalists'
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
            WHEN recency_score >= 3 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'Promising'
            WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Need Attention'
            WHEN recency_score = 2 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'About to Sleep'
            WHEN monetary_score >= 4 AND recency_score <= 2 THEN 'At Risk'
            WHEN monetary_score >= 4 AND recency_score = 1 THEN 'Cannot Lose Them'
            WHEN recency_score <= 2 AND frequency_score >= 2 THEN 'Hibernating'
            ELSE 'Lost'
        END as customer_segment,
        
        CASE 
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 
            THEN 'VIP treatment, exclusive offers, loyalty rewards'
            
            WHEN frequency_score >= 4 AND monetary_score >= 4 
            THEN 'Upsell premium products, cross-sell, loyalty program'
            
            WHEN recency_score >= 4 AND frequency_score >= 3 
            THEN 'Membership offers, engagement campaigns, product recommendations'
            
            WHEN recency_score >= 4 AND frequency_score <= 2 
            THEN 'Onboarding sequence, product education, welcome offers'
            
            WHEN recency_score >= 3 AND frequency_score >= 2 AND monetary_score >= 2 
            THEN 'Targeted promotions, engagement campaigns'
            
            WHEN recency_score >= 3 AND frequency_score >= 3 
            THEN 'Limited-time offers, personalized recommendations'
            
            WHEN recency_score = 2 AND frequency_score >= 2 AND monetary_score >= 2 
            THEN 'Reactivation campaigns, special discounts'
            
            WHEN monetary_score >= 4 AND recency_score <= 2 
            THEN 'Win-back campaigns, premium support, exclusive previews'
            
            WHEN monetary_score >= 4 AND recency_score = 1 
            THEN 'Immediate intervention, personal outreach, special offers'
            
            WHEN recency_score <= 2 AND frequency_score >= 2 
            THEN 'Win-back series, surveys, incentive offers'
            
            ELSE 'Re-engagement surveys, basic promotional offers'
        END as marketing_action
        
    FROM segment_recommendations
)
SELECT 
    customer_segment,
    marketing_action,
    COUNT(*) as customers_in_segment,
    AVG(monetary) as avg_customer_value,
    SUM(monetary) as total_segment_value
FROM actionable_segments
GROUP BY customer_segment, marketing_action
ORDER BY total_segment_value DESC;

-- =============================================
-- RFM Trend Analysis
-- =============================================

-- Track RFM changes over time
WITH monthly_rfm AS (
    SELECT 
        DATE_FORMAT(t.transaction_date, '%Y-%m') as month_year,
        c.customer_id,
        COUNT(t.transaction_id) as monthly_frequency,
        SUM(t.transaction_amount) as monthly_monetary
    FROM customers c
    JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
    GROUP BY DATE_FORMAT(t.transaction_date, '%Y-%m'), c.customer_id
),
monthly_segments AS (
    SELECT 
        month_year,
        customer_id,
        monthly_frequency,
        monthly_monetary,
        NTILE(5) OVER (PARTITION BY month_year ORDER BY monthly_frequency) as freq_score,
        NTILE(5) OVER (PARTITION BY month_year ORDER BY monthly_monetary) as monetary_score
    FROM monthly_rfm
)
SELECT 
    month_year,
    CASE 
        WHEN freq_score >= 4 AND monetary_score >= 4 THEN 'High Value'
        WHEN freq_score >= 3 AND monetary_score >= 3 THEN 'Medium Value'
        ELSE 'Low Value'
    END as segment,
    COUNT(*) as customer_count,
    AVG(monthly_monetary) as avg_monthly_spend
FROM monthly_segments
GROUP BY month_year, 
    CASE 
        WHEN freq_score >= 4 AND monetary_score >= 4 THEN 'High Value'
        WHEN freq_score >= 3 AND monetary_score >= 3 THEN 'Medium Value'
        ELSE 'Low Value'
    END
ORDER BY month_year, segment;