-- 1. Top 5 funds by AUM
SELECT
    df.scheme_name,
    fa.aum
FROM fact_aum AS fa
JOIN dim_fund AS df
    ON fa.fund_key = df.fund_key
ORDER BY fa.aum DESC
LIMIT 5;

-- 2. Average NAV by month
SELECT
    dd.year_num,
    dd.month_num,
    ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav AS fn
JOIN dim_date AS dd
    ON fn.date_key = dd.date_key
GROUP BY dd.year_num, dd.month_num
ORDER BY dd.year_num, dd.month_num;

-- 3. Average NAV by year
SELECT
    dd.year_num,
    ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav AS fn
JOIN dim_date AS dd
    ON fn.date_key = dd.date_key
GROUP BY dd.year_num
ORDER BY dd.year_num;

-- 4. SIP transaction growth YoY
WITH sip_yearly AS (
    SELECT
        dd.year_num,
        SUM(ft.amount) AS sip_amount
    FROM fact_transactions AS ft
    JOIN dim_date AS dd
        ON ft.date_key = dd.date_key
    WHERE ft.transaction_type = 'SIP'
    GROUP BY dd.year_num
)
SELECT
    year_num,
    ROUND(sip_amount, 2) AS sip_amount,
    ROUND(
        (
            sip_amount - LAG(sip_amount) OVER (ORDER BY year_num)
        ) * 100.0
        / NULLIF(LAG(sip_amount) OVER (ORDER BY year_num), 0),
        2
    ) AS yoy_growth_pct
FROM sip_yearly
ORDER BY year_num;

-- 5. Transactions by state
SELECT
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY transaction_count DESC, total_amount DESC;

-- 6. Funds with expense ratio below 1%
SELECT
    df.scheme_name,
    fp.expense_ratio
FROM fact_performance AS fp
JOIN dim_fund AS df
    ON fp.fund_key = df.fund_key
WHERE fp.expense_ratio < 1.0
ORDER BY fp.expense_ratio ASC, df.scheme_name;

-- 7. Highest 1-year return funds
SELECT
    df.scheme_name,
    fp.return_1y
FROM fact_performance AS fp
JOIN dim_fund AS df
    ON fp.fund_key = df.fund_key
ORDER BY fp.return_1y DESC
LIMIT 5;

-- 8. Total investment amount by fund
SELECT
    df.scheme_name,
    ROUND(SUM(ft.amount), 2) AS total_investment_amount
FROM fact_transactions AS ft
JOIN dim_fund AS df
    ON ft.fund_key = df.fund_key
WHERE ft.transaction_type IN ('SIP', 'Lumpsum')
GROUP BY df.scheme_name
ORDER BY total_investment_amount DESC;

-- 9. Total redemptions by fund
SELECT
    df.scheme_name,
    ROUND(SUM(ft.amount), 2) AS total_redemption_amount
FROM fact_transactions AS ft
JOIN dim_fund AS df
    ON ft.fund_key = df.fund_key
WHERE ft.transaction_type = 'Redemption'
GROUP BY df.scheme_name
ORDER BY total_redemption_amount DESC;

-- 10. Monthly transaction trend
SELECT
    dd.year_num,
    dd.month_num,
    COUNT(*) AS transaction_count,
    ROUND(SUM(ft.amount), 2) AS total_amount
FROM fact_transactions AS ft
JOIN dim_date AS dd
    ON ft.date_key = dd.date_key
GROUP BY dd.year_num, dd.month_num
ORDER BY dd.year_num, dd.month_num;
