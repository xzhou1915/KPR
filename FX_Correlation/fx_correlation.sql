-- Full N x N pairwise Pearson correlation matrix of simple percentage returns.
-- Replace dbo.FX_Prices with the name of the source table.
-- The source is expected to contain one row per [Date] and Ticker.

;WITH price_lags AS (
    SELECT
        [Date],
        Ticker,
        CAST([Value] AS float) AS current_value,
        LAG(CAST([Value] AS float)) OVER (
            PARTITION BY Ticker
            ORDER BY [Date]
        ) AS previous_value
    FROM dbo.FX_Prices
),
ticker_universe AS (
    SELECT DISTINCT
        Ticker
    FROM price_lags
    WHERE Ticker IS NOT NULL
),
ticker_pairs AS (
    SELECT
        t1.Ticker AS CCY_1,
        t2.Ticker AS CCY_2
    FROM ticker_universe AS t1
    CROSS JOIN ticker_universe AS t2
),
returns AS (
    SELECT
        [Date],
        Ticker,
        current_value / NULLIF(previous_value, 0.0) - 1.0 AS pct_return
    FROM price_lags
    WHERE previous_value IS NOT NULL
),
paired_returns AS (
    SELECT
        r1.Ticker AS CCY_1,
        r2.Ticker AS CCY_2,
        r1.pct_return AS return_1,
        r2.pct_return AS return_2
    FROM returns AS r1
    INNER JOIN returns AS r2
        ON r2.[Date] = r1.[Date]
    WHERE r1.pct_return IS NOT NULL
      AND r2.pct_return IS NOT NULL
),
pair_means AS (
    SELECT
        CCY_1,
        CCY_2,
        AVG(return_1) AS mean_1,
        AVG(return_2) AS mean_2,
        COUNT_BIG(*) AS observations
    FROM paired_returns
    GROUP BY
        CCY_1,
        CCY_2
),
correlation_components AS (
    SELECT
        p.CCY_1,
        p.CCY_2,
        m.observations,
        SUM(
            (p.return_1 - m.mean_1) *
            (p.return_2 - m.mean_2)
        ) AS numerator,
        SQRT(
            SUM((p.return_1 - m.mean_1) * (p.return_1 - m.mean_1)) *
            SUM((p.return_2 - m.mean_2) * (p.return_2 - m.mean_2))
        ) AS denominator
    FROM paired_returns AS p
    INNER JOIN pair_means AS m
        ON m.CCY_1 = p.CCY_1
       AND m.CCY_2 = p.CCY_2
    GROUP BY
        p.CCY_1,
        p.CCY_2,
        m.observations
)
SELECT
    p.CCY_1,
    p.CCY_2,
    CAST(
        CASE
            WHEN ISNULL(c.observations, 0) < 2 THEN NULL
            ELSE ROUND(c.numerator / NULLIF(c.denominator, 0.0), 2)
        END
        AS decimal(4, 2)
    ) AS Correlation
FROM ticker_pairs AS p
LEFT JOIN correlation_components AS c
    ON c.CCY_1 = p.CCY_1
   AND c.CCY_2 = p.CCY_2
ORDER BY
    p.CCY_1,
    p.CCY_2;
