-- Customer Segmentation SQL Analysis
-- Author: Sahil Hansa
-- Email: sahilhansa007@gmail.com
-- Description: Advanced SQL queries for customer behavior analysis and segmentation
-- Location: Jammu, J&K, India

-- =============================================
-- Customer Behavior Analysis - Main Query
-- =============================================

-- Comprehensive customer metrics calculation
SELECT 
    c.customer_id,
    c.customer_name,
    c.registration_date,
    c.customer_type,
    c.location,
    
    -- Transaction Metrics
    COUNT(t.transaction_id) as total_transactions,
    SUM(t.transaction_amount) as total_spent,
    AVG(t.transaction_amount) as avg_transaction_value,
    MIN(t.transaction_date) as first_purchase_date,
    MAX(t.transaction_date) as last_purchase_date,
    
    -- Recency, Frequency, Monetary (RFM) Calculations
    DATEDIFF(CURDATE(), MAX(t.transaction_date)) as days_since_last_purchase,
    COUNT(t.transaction_id) as purchase_frequency,
    SUM(t.transaction_amount) as monetary_value,
    
    -- Customer Lifetime Metrics
    DATEDIFF(MAX(t.transaction_date), MIN(t.transaction_date)) as customer_lifespan_days,
    SUM(t.transaction_amount) / COUNT(DISTINCT YEAR(t.transaction_date)) as avg_annual_spend,
    
    -- Purchase Pattern Analysis
    COUNT(DISTINCT t.product_category) as categories_purchased,
    COUNT(DISTINCT MONTH(t.transaction_date)) as active_months,
    
    -- Seasonal Analysis
    AVG(CASE WHEN QUARTER(t.transaction_date) = 1 THEN t.transaction_amount END) as q1_avg_spend,
    AVG(CASE WHEN QUARTER(t.transaction_date) = 2 THEN t.transaction_amount END) as q2_avg_spend,
    AVG(CASE WHEN QUARTER(t.transaction_date) = 3 THEN t.transaction_amount END) as q3_avg_spend,
    AVG(CASE WHEN QUARTER(t.transaction_date) = 4 THEN t.transaction_amount END) as q4_avg_spend

FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
GROUP BY c.customer_id, c.customer_name, c.registration_date, c.customer_type, c.location
ORDER BY total_spent DESC;

-- =============================================
-- Customer Journey Analysis
-- =============================================

-- Analyze customer purchase journey and patterns
WITH customer_journey AS (
    SELECT 
        customer_id,
        transaction_id,
        transaction_date,
        transaction_amount,
        product_category,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY transaction_date) as purchase_sequence,
        LAG(transaction_date) OVER (PARTITION BY customer_id ORDER BY transaction_date) as previous_purchase_date,
        LAG(transaction_amount) OVER (PARTITION BY customer_id ORDER BY transaction_date) as previous_amount
    FROM transactions
    WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
),
journey_metrics AS (
    SELECT 
        customer_id,
        purchase_sequence,
        transaction_date,
        transaction_amount,
        product_category,
        CASE 
            WHEN previous_purchase_date IS NULL THEN NULL
            ELSE DATEDIFF(transaction_date, previous_purchase_date)
        END as days_between_purchases,
        CASE 
            WHEN previous_amount IS NULL THEN NULL
            ELSE transaction_amount - previous_amount
        END as amount_change_from_previous
    FROM customer_journey
)
SELECT 
    customer_id,
    COUNT(*) as total_purchases,
    MIN(transaction_date) as first_purchase,
    MAX(transaction_date) as latest_purchase,
    AVG(days_between_purchases) as avg_days_between_purchases,
    STDDEV(days_between_purchases) as purchase_regularity_score,
    AVG(amount_change_from_previous) as avg_spend_trend,
    COUNT(DISTINCT product_category) as category_diversity
FROM journey_metrics
GROUP BY customer_id;

-- =============================================
-- Product Affinity Analysis
-- =============================================

-- Customer product preferences and cross-selling opportunities
SELECT 
    c.customer_id,
    c.customer_name,
    t.product_category,
    COUNT(t.transaction_id) as category_purchases,
    SUM(t.transaction_amount) as category_spend,
    AVG(t.transaction_amount) as avg_category_spend,
    ROUND(
        (COUNT(t.transaction_id) * 100.0 / 
         (SELECT COUNT(*) FROM transactions t2 WHERE t2.customer_id = c.customer_id)), 2
    ) as category_purchase_percentage
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY c.customer_id, c.customer_name, t.product_category
HAVING category_purchases >= 2
ORDER BY c.customer_id, category_spend DESC;

-- =============================================
-- Cohort Analysis for Customer Retention
-- =============================================

-- Monthly cohort analysis to track customer retention
WITH customer_cohorts AS (
    SELECT 
        customer_id,
        DATE_FORMAT(MIN(transaction_date), '%Y-%m') as cohort_month,
        MIN(transaction_date) as first_purchase_date
    FROM transactions
    GROUP BY customer_id
),
customer_activities AS (
    SELECT 
        t.customer_id,
        cc.cohort_month,
        DATE_FORMAT(t.transaction_date, '%Y-%m') as activity_month,
        PERIOD_DIFF(
            EXTRACT(YEAR_MONTH FROM t.transaction_date),
            EXTRACT(YEAR_MONTH FROM cc.first_purchase_date)
        ) as period_number
    FROM transactions t
    JOIN customer_cohorts cc ON t.customer_id = cc.customer_id
),
cohort_table AS (
    SELECT 
        cohort_month,
        period_number,
        COUNT(DISTINCT customer_id) as customers
    FROM customer_activities
    GROUP BY cohort_month, period_number
),
cohort_sizes AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) as cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT 
    ct.cohort_month,
    cs.cohort_size,
    ct.period_number,
    ct.customers,
    ROUND(ct.customers * 100.0 / cs.cohort_size, 2) as retention_rate
FROM cohort_table ct
JOIN cohort_sizes cs ON ct.cohort_month = cs.cohort_month
ORDER BY ct.cohort_month, ct.period_number;

-- =============================================
-- Customer Churn Risk Assessment
-- =============================================

-- Identify customers at risk of churning
WITH customer_metrics AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.registration_date,
        DATEDIFF(CURDATE(), MAX(t.transaction_date)) as days_since_last_purchase,
        COUNT(t.transaction_id) as total_transactions,
        SUM(t.transaction_amount) as total_spent,
        AVG(DATEDIFF(t.transaction_date, 
            LAG(t.transaction_date) OVER (PARTITION BY c.customer_id ORDER BY t.transaction_date))
        ) as avg_days_between_purchases
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id, c.customer_name, c.registration_date
),
churn_risk AS (
    SELECT *,
        CASE 
            WHEN days_since_last_purchase > (avg_days_between_purchases * 2) 
                AND total_spent > 1000 THEN 'High Risk - High Value'
            WHEN days_since_last_purchase > (avg_days_between_purchases * 2) THEN 'High Risk - Low Value'
            WHEN days_since_last_purchase > avg_days_between_purchases THEN 'Medium Risk'
            WHEN days_since_last_purchase <= avg_days_between_purchases THEN 'Low Risk'
            ELSE 'New Customer'
        END as churn_risk_level,
        CASE 
            WHEN total_spent >= 5000 THEN 'High Value'
            WHEN total_spent >= 1000 THEN 'Medium Value'
            ELSE 'Low Value'
        END as customer_value_tier
    FROM customer_metrics
    WHERE total_transactions > 0
)
SELECT 
    churn_risk_level,
    customer_value_tier,
    COUNT(*) as customer_count,
    AVG(total_spent) as avg_customer_value,
    SUM(total_spent) as total_at_risk_value
FROM churn_risk
GROUP BY churn_risk_level, customer_value_tier
ORDER BY 
    CASE churn_risk_level 
        WHEN 'High Risk - High Value' THEN 1
        WHEN 'High Risk - Low Value' THEN 2
        WHEN 'Medium Risk' THEN 3
        WHEN 'Low Risk' THEN 4
        WHEN 'New Customer' THEN 5
    END;

-- =============================================
-- Geographic Customer Analysis
-- =============================================

-- Regional customer behavior analysis
SELECT 
    c.location as region,
    COUNT(DISTINCT c.customer_id) as total_customers,
    AVG(customer_metrics.total_spent) as avg_customer_value,
    AVG(customer_metrics.total_transactions) as avg_transactions_per_customer,
    AVG(customer_metrics.avg_transaction_value) as avg_transaction_size,
    SUM(customer_metrics.total_spent) as total_regional_revenue,
    ROUND(
        SUM(customer_metrics.total_spent) * 100.0 / 
        (SELECT SUM(total_spent) FROM (
            SELECT c2.customer_id, SUM(t2.transaction_amount) as total_spent
            FROM customers c2 
            JOIN transactions t2 ON c2.customer_id = t2.customer_id
            WHERE t2.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            GROUP BY c2.customer_id
        ) as all_customers), 2
    ) as revenue_percentage
FROM customers c
JOIN (
    SELECT 
        customer_id,
        COUNT(transaction_id) as total_transactions,
        SUM(transaction_amount) as total_spent,
        AVG(transaction_amount) as avg_transaction_value
    FROM transactions 
    WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    GROUP BY customer_id
) customer_metrics ON c.customer_id = customer_metrics.customer_id
GROUP BY c.location
ORDER BY total_regional_revenue DESC;

-- =============================================
-- Customer Segment Performance Comparison
-- =============================================

-- Compare different customer segments performance
SELECT 
    CASE 
        WHEN total_spent >= 10000 AND purchase_frequency >= 20 THEN 'VIP Customers'
        WHEN total_spent >= 5000 AND purchase_frequency >= 10 THEN 'Loyal Customers'
        WHEN days_since_last_purchase <= 30 AND total_spent >= 1000 THEN 'Potential Loyalists'
        WHEN days_since_last_purchase BETWEEN 31 AND 90 THEN 'At Risk'
        WHEN days_since_last_purchase BETWEEN 91 AND 180 THEN 'Hibernating'
        WHEN days_since_last_purchase > 180 THEN 'Lost Customers'
        ELSE 'New Customers'
    END as customer_segment,
    
    COUNT(*) as segment_size,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers), 2) as segment_percentage,
    AVG(total_spent) as avg_segment_value,
    AVG(purchase_frequency) as avg_purchase_frequency,
    AVG(days_since_last_purchase) as avg_days_since_last_purchase,
    SUM(total_spent) as total_segment_value,
    ROUND(
        SUM(total_spent) * 100.0 / 
        (SELECT SUM(total_spent) FROM (
            SELECT customer_id, SUM(transaction_amount) as total_spent
            FROM transactions 
            WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
            GROUP BY customer_id
        ) as all_revenue), 2
    ) as revenue_contribution

FROM (
    SELECT 
        c.customer_id,
        COALESCE(SUM(t.transaction_amount), 0) as total_spent,
        COALESCE(COUNT(t.transaction_id), 0) as purchase_frequency,
        COALESCE(DATEDIFF(CURDATE(), MAX(t.transaction_date)), 999) as days_since_last_purchase
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id 
        AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id
) customer_summary

GROUP BY customer_segment
ORDER BY total_segment_value DESC;