-- =============================================================
-- Bluestock Mutual Fund Analytics - Analytical Queries
-- =============================================================

-- 1. Latest NAV for every fund
SELECT
    df.scheme_name,
    df.fund_house,
    fn.nav                      AS latest_nav,
    dd.full_date                AS nav_date
FROM fact_nav AS fn
JOIN dim_fund AS df ON fn.fund_key = df.fund_key
JOIN dim_date AS dd ON fn.date_key = dd.date_key
WHERE fn.date_key = (
    SELECT MAX(date_key)
    FROM fact_nav AS fn2
    WHERE fn2.fund_key = fn.fund_key
)
ORDER BY df.fund_house, df.scheme_name;


-- 2. Top 10 funds by 1-year return
SELECT
    df.scheme_name,
    df.fund_house,
    df.category,
    fp.return_1yr_pct
FROM fact_performance AS fp
JOIN dim_fund AS df ON fp.fund_key = df.fund_key
WHERE fp.return_1yr_pct IS NOT NULL
ORDER BY fp.return_1yr_pct DESC
LIMIT 10;


-- 3. Monthly SIP inflow trend (amount and transaction count)
SELECT
    dd.year_num,
    dd.month_num,
    dd.month_name,
    COUNT(*)                          AS sip_count,
    ROUND(SUM(ft.amount_inr), 2)      AS sip_inflow_inr
FROM fact_transactions AS ft
JOIN dim_date AS dd ON ft.date_key = dd.date_key
WHERE ft.transaction_type = 'SIP'
GROUP BY dd.year_num, dd.month_num, dd.month_name
ORDER BY dd.year_num, dd.month_num;


-- 4. Total AUM by fund house (latest snapshot per house)
SELECT
    fa.fund_house,
    ROUND(fa.aum_lakh_crore, 2)       AS aum_lakh_crore,
    fa.num_schemes
FROM fact_aum AS fa
WHERE fa.snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM fact_aum AS fa2
    WHERE fa2.fund_house = fa.fund_house
)
ORDER BY aum_lakh_crore DESC;


-- 5. NAV growth percentage (first vs latest NAV) per fund
WITH first_nav AS (
    SELECT fund_key, MIN(date_key) AS min_date_key FROM fact_nav GROUP BY fund_key
),
last_nav AS (
    SELECT fund_key, MAX(date_key) AS max_date_key FROM fact_nav GROUP BY fund_key
)
SELECT
    df.scheme_name,
    df.fund_house,
    ROUND(fn_first.nav, 4)            AS nav_start,
    ROUND(fn_last.nav, 4)             AS nav_end,
    ROUND(
        (fn_last.nav - fn_first.nav) * 100.0 / fn_first.nav, 2
    )                                 AS nav_growth_pct
FROM first_nav AS f
JOIN last_nav  AS l  ON f.fund_key    = l.fund_key
JOIN fact_nav  AS fn_first ON fn_first.fund_key = f.fund_key
                          AND fn_first.date_key  = f.min_date_key
JOIN fact_nav  AS fn_last  ON fn_last.fund_key  = l.fund_key
                          AND fn_last.date_key   = l.max_date_key
JOIN dim_fund  AS df ON df.fund_key   = f.fund_key
ORDER BY nav_growth_pct DESC;


-- 6. Transaction breakdown by type and KYC status
SELECT
    transaction_type,
    kyc_status,
    COUNT(*)                          AS txn_count,
    ROUND(SUM(amount_inr), 2)         AS total_inr,
    ROUND(AVG(amount_inr), 2)         AS avg_inr
FROM fact_transactions
GROUP BY transaction_type, kyc_status
ORDER BY transaction_type, kyc_status;


-- 7. State-wise total investment (SIP + Lumpsum only)
SELECT
    state,
    COUNT(*)                          AS txn_count,
    ROUND(SUM(amount_inr), 2)         AS total_invested_inr
FROM fact_transactions
WHERE transaction_type IN ('SIP', 'Lumpsum')
  AND state IS NOT NULL
GROUP BY state
ORDER BY total_invested_inr DESC;


-- 8. Risk-category-wise average expense ratio and Sharpe ratio
SELECT
    df.risk_category,
    COUNT(fp.fund_key)                AS fund_count,
    ROUND(AVG(fp.expense_ratio_pct), 4) AS avg_expense_ratio,
    ROUND(AVG(fp.sharpe_ratio), 4)    AS avg_sharpe_ratio,
    ROUND(AVG(fp.return_3yr_pct), 2)  AS avg_3yr_return_pct
FROM fact_performance AS fp
JOIN dim_fund AS df ON fp.fund_key = df.fund_key
GROUP BY df.risk_category
ORDER BY avg_3yr_return_pct DESC;


-- 9. Year-on-year SIP growth with percentage change
WITH yearly_sip AS (
    SELECT
        dd.year_num,
        SUM(ft.amount_inr) AS total_sip_inr
    FROM fact_transactions AS ft
    JOIN dim_date AS dd ON ft.date_key = dd.date_key
    WHERE ft.transaction_type = 'SIP'
    GROUP BY dd.year_num
)
SELECT
    year_num,
    ROUND(total_sip_inr, 2)           AS total_sip_inr,
    ROUND(
        (total_sip_inr - LAG(total_sip_inr) OVER (ORDER BY year_num))
        * 100.0
        / NULLIF(LAG(total_sip_inr) OVER (ORDER BY year_num), 0),
        2
    )                                 AS yoy_growth_pct
FROM yearly_sip
ORDER BY year_num;


-- 10. Funds with best alpha (outperformance vs benchmark)
SELECT
    df.scheme_name,
    df.fund_house,
    df.risk_category,
    fp.alpha,
    fp.beta,
    fp.sharpe_ratio,
    fp.return_3yr_pct,
    fp.benchmark_3yr_pct,
    ROUND(fp.return_3yr_pct - fp.benchmark_3yr_pct, 2) AS excess_return_pct
FROM fact_performance AS fp
JOIN dim_fund AS df ON fp.fund_key = df.fund_key
WHERE fp.alpha IS NOT NULL
ORDER BY fp.alpha DESC
LIMIT 10;
