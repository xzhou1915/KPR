/*
Convert bucketed FX exposure into approximate receive-positive USD DV01.

Input table: my_table
Required columns:
  Ticker   - six-character FX pair, such as USDCNH or AUDUSD
  Bucket   - Spot Delta, Spot-3M, 3M-6M, 6M-1Y, 1Y-3Y, or 3Y-10Y
  Exposure - signed millions of the ticker's base/first currency

Sign convention:
  Positive Exposure means long/receive the base currency.
  Positive USD_DV01 benefits when USD rates fall.

Replace the four NULL values in spot_rates with the desired spot-rate
proxies. Each rate must be quoted as USD per unit of base currency.
*/

WITH spot_rates AS (
    SELECT 'AUDUSD' AS Ticker,
           CAST(NULL AS DECIMAL(18, 8)) AS USDPerBase
    UNION ALL
    SELECT 'NZDUSD',
           CAST(NULL AS DECIMAL(18, 8))
    UNION ALL
    SELECT 'GBPUSD',
           CAST(NULL AS DECIMAL(18, 8))
    UNION ALL
    SELECT 'EURUSD',
           CAST(NULL AS DECIMAL(18, 8))
),
bucket_years AS (
    SELECT
        1 AS bucket_order,
        'Spot Delta' AS Bucket,
        CAST(NULL AS DECIMAL(10, 4)) AS SegmentYears

    UNION ALL
    SELECT 2, 'Spot-3M', 0.25

    UNION ALL
    SELECT 3, '3M-6M', 0.25

    UNION ALL
    SELECT 4, '6M-1Y', 0.50

    UNION ALL
    SELECT 5, '1Y-3Y', 2.00

    UNION ALL
    SELECT 6, '3Y-10Y', 7.00
),
normalized AS (
    SELECT
        t.Ticker,
        t.Bucket,
        t.Exposure AS BaseExposureMn,
        b.bucket_order,
        b.SegmentYears,
        s.USDPerBase AS SpotRateUsed,

        CASE
            /*
            USDXXX: Exposure is already millions of USD.
            Long base means receive USD.
            */
            WHEN LEFT(t.Ticker, 3) = 'USD'
                THEN t.Exposure

            /*
            XXXUSD: convert base-currency exposure into the signed USD leg.
            Long XXXUSD means receive XXX and pay USD, hence the minus sign.
            */
            WHEN RIGHT(t.Ticker, 3) = 'USD'
                THEN -t.Exposure * s.USDPerBase

            ELSE NULL
        END AS SignedUSDLegMn

    FROM my_table t
    INNER JOIN bucket_years b
        ON b.Bucket = t.Bucket
    LEFT JOIN spot_rates s
        ON s.Ticker = t.Ticker
)
SELECT
    Ticker,
    Bucket,
    BaseExposureMn,
    SpotRateUsed,
    SignedUSDLegMn,

    CASE
        /* Spot FX delta is not an interest-rate DV01. */
        WHEN SegmentYears IS NULL
            THEN NULL

        /* USD 1 million times 1 bp equals USD 100 per year. */
        ELSE SignedUSDLegMn
             * SegmentYears
             * 100.0
    END AS USD_DV01

FROM normalized
ORDER BY
    Ticker,
    bucket_order;
