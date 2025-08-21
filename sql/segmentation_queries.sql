-- Advanced Customer Segmentation Queries
-- Author: Sahil Hansa
-- Email: sahilhansa007@gmail.com
-- Description: Advanced SQL queries for customer segmentation logic and business rules
-- Location: Jammu, J&K, India

-- =============================================
-- Advanced Customer Segmentation Logic
-- =============================================

-- Dynamic RFM Segmentation with Business Rules
WITH customer_rfm AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.location,
        c.registration_date,
        
        -- Dynamic date calculations
        DATEDIFF(CURDATE(), MAX(t.transaction_date)) as recency_days,
        COUNT(t.transaction_id) as frequency_count,
        SUM(t.transaction_amount) as monetary_total,
        AVG(t.transaction_amount) as avg_order_value,
        
        -- Customer lifecycle metrics
        DATEDIFF(MAX(t.transaction_date), MIN(t.transaction_date)) as customer_lifespan_days,
        COUNT(DISTINCT DATE_FORMAT(t.transaction_date, '%Y-%m')) as active_months,
        COUNT(DISTINCT t.product_category) as category_diversity,
        
        -- Behavioral indicators
        STDDEV(t.transaction_amount) as spending_consistency,
        MAX(t.transaction_amount) as highest_purchase,
        MIN(t.transaction_date) as first_purchase_date,
        MAX(t.transaction_date) as last_purchase_date
        
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    GROUP BY c.customer_id, c.customer_name, c.location, c.registration_date
),

-- Dynamic RFM Scoring based on data distribution
rfm_scoring AS (
    SELECT *,
        -- Dynamic recency scoring (quintiles)
        CASE 
            WHEN recency_days <= (SELECT PERCENTILE_CONT(0.2) WITHIN GROUP (ORDER BY recency_days) FROM customer_rfm) THEN 5
            WHEN recency_days <= (SELECT PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY recency_days) FROM customer_rfm) THEN 4
            WHEN recency_days <= (SELECT PERCENTILE_CONT(0.6) WITHIN GROUP (ORDER BY recency_days) FROM customer_rfm) THEN 3
            WHEN recency_days <= (SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY recency_days) FROM customer_rfm) THEN 2
            ELSE 1
        END as recency_score,
        
        -- Dynamic frequency scoring (quintiles)
        CASE 
            WHEN frequency_count >= (SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY frequency_count) FROM customer_rfm) THEN 5
            WHEN frequency_count >= (SELECT PERCENTILE_CONT(0.6) WITHIN GROUP (ORDER BY frequency_count) FROM customer_rfm) THEN 4
            WHEN frequency_count >= (SELECT PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY frequency_count) FROM customer_rfm) THEN 3
            WHEN frequency_count >= (SELECT PERCENTILE_CONT(0.2) WITHIN GROUP (ORDER BY frequency_count) FROM customer_rfm) THEN 2
            ELSE 1
        END as frequency_score,
        
        -- Dynamic monetary scoring (quintiles)
        CASE 
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY monetary_total) FROM customer_rfm) THEN 5
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.6) WITHIN GROUP (ORDER BY monetary_total) FROM customer_rfm) THEN 4
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY monetary_total) FROM customer_rfm) THEN 3
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.2) WITHIN GROUP (ORDER BY monetary_total) FROM customer_rfm) THEN 2
            ELSE 1
        END as monetary_score
        
    FROM customer_rfm
    WHERE frequency_count > 0
),

-- Advanced customer segmentation with business logic
advanced_segmentation AS (
    SELECT *,
        ROUND((recency_score + frequency_score + monetary_score) / 3.0, 2) as rfm_score,
        
        -- Advanced segment classification
        CASE 
            -- VIP Champions (Best customers)
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'VIP Champions'
            
            -- Loyal Customers (High frequency and monetary)
            WHEN frequency_score >= 4 AND monetary_score >= 4 THEN 'Loyal Customers'
            
            -- Big Spenders (High monetary, varying frequency)
            WHEN monetary_score >= 4 AND frequency_score >= 2 THEN 'Big Spenders'
            
            -- Potential Loyalists (Recent customers with good activity)
            WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'Potential Loyalists'
            
            -- New Customers (Recent but low frequency)
            WHEN recency_score >= 4 AND frequency_score <= 2 AND customer_lifespan_days <= 90 THEN 'New Customers'
            
            -- Promising (Recent with medium engagement)
            WHEN recency_score >= 3 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'Promising'
            
            -- Need Attention (Above average but declining)
            WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'Need Attention'
            
            -- About to Sleep (Declining recent activity)
            WHEN recency_score = 2 AND frequency_score >= 2 AND monetary_score >= 2 THEN 'About to Sleep'
            
            -- At Risk (Good monetary but declining activity)
            WHEN monetary_score >= 3 AND recency_score <= 2 AND frequency_score <= 2 THEN 'At Risk'
            
            -- Cannot Lose Them (High value but very low activity)
            WHEN monetary_score >= 4 AND recency_score = 1 THEN 'Cannot Lose Them'
            
            -- Hibernating (Previously active, now dormant)
            WHEN recency_score <= 2 AND frequency_score >= 2 AND customer_lifespan_days > 180 THEN 'Hibernating'
            
            -- Lost Customers (No recent activity)
            WHEN recency_score = 1 AND frequency_score <= 2 THEN 'Lost Customers'
            
            ELSE 'Undefined'
        END as segment,
        
        -- Customer value tier
        CASE 
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY monetary_total) FROM rfm_scoring) THEN 'Platinum'
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.7) WITHIN GROUP (ORDER BY monetary_total) FROM rfm_scoring) THEN 'Gold'
            WHEN monetary_total >= (SELECT PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY monetary_total) FROM rfm_scoring) THEN 'Silver'
            ELSE 'Bronze'
        END as value_tier,
        
        -- Engagement level
        CASE 
            WHEN frequency_score >= 4 AND recency_score >= 4 THEN 'Highly Engaged'
            WHEN frequency_score >= 3 AND recency_score >= 3 THEN 'Moderately Engaged'
            WHEN frequency_score >= 2 OR recency_score >= 2 THEN 'Low Engagement'
            ELSE 'Disengaged'
        END as engagement_level,
        
        -- Churn risk assessment
        CASE 
            WHEN recency_days > 365 AND frequency_score <= 2 THEN 'High Risk'
            WHEN recency_days > 180 AND frequency_score <= 3 THEN 'Medium Risk'
            WHEN recency_days > 90 AND frequency_score <= 2 THEN 'Low Risk'
            ELSE 'Active'
        END as churn_risk
        
    FROM rfm_scoring
)

-- Final segmentation results with business metrics
SELECT 
    customer_id,
    customer_name,
    location,
    registration_date,
    recency_days,
    frequency_count,
    monetary_total,
    avg_order_value,
    customer_lifespan_days,
    active_months,
    category_diversity,
    spending_consistency,
    highest_purchase,
    first_purchase_date,
    last_purchase_date,
    recency_score,
    frequency_score,
    monetary_score,
    rfm_score,
    segment,
    value_tier,
    engagement_level,
    churn_risk,
    
    -- Business priority scoring
    CASE 
        WHEN segment IN ('VIP Champions', 'Cannot Lose Them') THEN 'Critical'
        WHEN segment IN ('Loyal Customers', 'Big Spenders', 'At Risk') THEN 'High'
        WHEN segment IN ('Potential Loyalists', 'Need Attention', 'About to Sleep') THEN 'Medium'
        ELSE 'Low'
    END as business_priority
    
FROM advanced_segmentation
ORDER BY rfm_score DESC, monetary_total DESC;

-- =============================================
-- Customer Segment Performance Analysis
-- =============================================

-- Comprehensive segment analysis with KPIs
WITH segment_performance AS (
    SELECT 
        segment,
        value_tier,
        COUNT(*) as customer_count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM advanced_segmentation), 2) as customer_percentage,
        
        -- Revenue metrics
        SUM(monetary_total) as total_revenue,
        AVG(monetary_total) as avg_customer_value,
        ROUND(SUM(monetary_total) * 100.0 / (SELECT SUM(monetary_total) FROM advanced_segmentation), 2) as revenue_contribution,
        
        -- Behavioral metrics
        AVG(recency_days) as avg_recency,
        AVG(frequency_count) as avg_frequency,
        AVG(avg_order_value) as avg_order_value,
        AVG(customer_lifespan_days) as avg_customer_lifespan,
        AVG(category_diversity) as avg_category_diversity,
        
        -- Engagement metrics
        AVG(rfm_score) as avg_rfm_score,
        COUNT(CASE WHEN churn_risk = 'High Risk' THEN 1 END) as high_risk_customers,
        COUNT(CASE WHEN engagement_level = 'Highly Engaged' THEN 1 END) as highly_engaged_customers
        
    FROM advanced_segmentation
    GROUP BY segment, value_tier
)
SELECT *,
    ROUND(revenue_contribution / customer_percentage, 2) as revenue_efficiency_ratio,
    ROUND(high_risk_customers * 100.0 / customer_count, 2) as churn_risk_percentage,
    ROUND(highly_engaged_customers * 100.0 / customer_count, 2) as engagement_percentage
FROM segment_performance
ORDER BY total_revenue DESC;

-- =============================================
-- Marketing Campaign Targeting Queries
-- =============================================

-- High-value customer retention campaign targets
SELECT 
    customer_id,
    customer_name,
    location,
    segment,
    value_tier,
    monetary_total,
    recency_days,
    churn_risk,
    'Retention Campaign' as campaign_type,
    CASE 
        WHEN segment = 'Cannot Lose Them' THEN 'Personal outreach with exclusive offers'
        WHEN segment = 'At Risk' THEN 'Win-back campaign with discounts'
        WHEN segment = 'About to Sleep' THEN 'Re-engagement with new product showcase'
        ELSE 'Standard retention offer'
    END as recommended_action
FROM advanced_segmentation
WHERE value_tier IN ('Platinum', 'Gold') 
  AND churn_risk IN ('High Risk', 'Medium Risk')
ORDER BY monetary_total DESC;

-- Customer acquisition campaign (lookalike targeting)
SELECT 
    segment,
    value_tier,
    COUNT(*) as segment_size,
    AVG(monetary_total) as avg_value,
    AVG(frequency_count) as avg_frequency,
    AVG(category_diversity) as avg_categories,
    
    -- Lookalike profile characteristics
    GROUP_CONCAT(DISTINCT location) as common_locations,
    AVG(DATEDIFF(CURDATE(), registration_date)) as avg_customer_age_days,
    
    'Lookalike Acquisition' as campaign_type
FROM advanced_segmentation
WHERE segment IN ('VIP Champions', 'Loyal Customers', 'Big Spenders')
GROUP BY segment, value_tier
ORDER BY avg_value DESC;

-- Cross-sell and upsell opportunities
SELECT 
    a.customer_id,
    a.customer_name,
    a.segment,
    a.value_tier,
    a.category_diversity,
    a.avg_order_value,
    
    -- Identify customers with low category diversity but high spend
    CASE 
        WHEN a.category_diversity <= 2 AND a.monetary_total >= 1000 THEN 'Cross-sell Opportunity'
        WHEN a.avg_order_value < (SELECT AVG(avg_order_value) FROM advanced_segmentation WHERE segment = a.segment) 
             AND a.frequency_count >= 5 THEN 'Upsell Opportunity'
        ELSE 'No immediate opportunity'
    END as opportunity_type,
    
    -- Recommended categories based on similar customers
    (SELECT GROUP_CONCAT(DISTINCT product_category)
     FROM transactions t2 
     JOIN customers c2 ON t2.customer_id = c2.customer_id
     WHERE c2.location = a.location 
       AND t2.customer_id != a.customer_id
     LIMIT 3) as recommended_categories
     
FROM advanced_segmentation a
WHERE a.segment IN ('Loyal Customers', 'Big Spenders', 'Potential Loyalists')
  AND (a.category_diversity <= 2 OR a.avg_order_value < 200)
ORDER BY a.monetary_total DESC;

-- =============================================
-- Customer Lifetime Value Prediction
-- =============================================

-- CLV calculation and prediction model
WITH clv_calculation AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        
        -- Historical metrics
        frequency_count,
        avg_order_value,
        customer_lifespan_days,
        monetary_total as historical_clv,
        
        -- Predicted metrics (simplified model)
        CASE 
            WHEN customer_lifespan_days > 0 THEN 
                ROUND((frequency_count / (customer_lifespan_days / 365.0)) * avg_order_value * 3, 2) -- 3-year projection
            ELSE avg_order_value * frequency_count * 2
        END as predicted_clv_3year,
        
        -- Customer health score (0-100)
        ROUND(
            (recency_score * 0.3 + frequency_score * 0.4 + monetary_score * 0.3) * 20, 0
        ) as customer_health_score,
        
        -- Risk-adjusted CLV
        CASE churn_risk
            WHEN 'High Risk' THEN 0.3
            WHEN 'Medium Risk' THEN 0.6
            WHEN 'Low Risk' THEN 0.8
            ELSE 1.0
        END as risk_multiplier
        
    FROM advanced_segmentation
)
SELECT *,
    ROUND(predicted_clv_3year * risk_multiplier, 2) as risk_adjusted_clv,
    CASE 
        WHEN predicted_clv_3year * risk_multiplier >= 5000 THEN 'Very High'
        WHEN predicted_clv_3year * risk_multiplier >= 2000 THEN 'High'
        WHEN predicted_clv_3year * risk_multiplier >= 1000 THEN 'Medium'
        ELSE 'Low'
    END as clv_tier
FROM clv_calculation
ORDER BY risk_adjusted_clv DESC;

-- =============================================
-- Cohort Analysis for Segmentation Trends
-- =============================================

-- Monthly cohort analysis by segment
WITH customer_cohorts AS (
    SELECT 
        customer_id,
        DATE_FORMAT(MIN(transaction_date), '%Y-%m') as cohort_month,
        MIN(transaction_date) as first_purchase_date
    FROM transactions
    GROUP BY customer_id
),
cohort_segments AS (
    SELECT 
        cc.cohort_month,
        COUNT(DISTINCT cc.customer_id) as cohort_size,
        
        -- Current segment distribution
        SUM(CASE WHEN ads.segment = 'VIP Champions' THEN 1 ELSE 0 END) as vip_champions,
        SUM(CASE WHEN ads.segment = 'Loyal Customers' THEN 1 ELSE 0 END) as loyal_customers,
        SUM(CASE WHEN ads.segment = 'At Risk' THEN 1 ELSE 0 END) as at_risk,
        SUM(CASE WHEN ads.segment = 'Lost Customers' THEN 1 ELSE 0 END) as lost_customers,
        
        AVG(ads.monetary_total) as avg_cohort_value,
        AVG(ads.rfm_score) as avg_rfm_score
        
    FROM customer_cohorts cc
    LEFT JOIN advanced_segmentation ads ON cc.customer_id = ads.customer_id
    WHERE cc.cohort_month >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 12 MONTH), '%Y-%m')
    GROUP BY cc.cohort_month
)
SELECT 
    cohort_month,
    cohort_size,
    vip_champions,
    loyal_customers,
    at_risk,
    lost_customers,
    ROUND(avg_cohort_value, 2) as avg_cohort_value,
    ROUND(avg_rfm_score, 2) as avg_rfm_score,
    
    -- Percentage distributions
    ROUND(vip_champions * 100.0 / cohort_size, 1) as vip_champions_pct,
    ROUND(loyal_customers * 100.0 / cohort_size, 1) as loyal_customers_pct,
    ROUND(at_risk * 100.0 / cohort_size, 1) as at_risk_pct,
    ROUND(lost_customers * 100.0 / cohort_size, 1) as lost_customers_pct
    
FROM cohort_segments
ORDER BY cohort_month DESC;