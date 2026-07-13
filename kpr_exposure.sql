/*
Convert trade-level FX notionals into key-point risk segment exposures.

Input table: my_table
Required columns:
  Ticker       - currency identifier
  ExpiryDays   - calendar days from the as-of date to maturity
  NetAmount1   - signed notional exposure

Day-count nodes use the existing 360-day convention:
  Spot = 0, 3M = 90, 6M = 180, 1Y = 360,
  3Y = 1080, 10Y = 3600.

Trades beyond 10Y receive full exposure in every displayed segment;
risk after 10Y is not represented. Trades with ExpiryDays <= 0 remain
in Spot Delta but receive zero forward-segment exposure.
*/

WITH buckets AS (
    SELECT 1 AS bucket_order, 'Spot Delta' AS bucket,
           NULL AS lower_days, NULL AS upper_days
    UNION ALL
    SELECT 2, 'Spot-3M',  0,    90
    UNION ALL
    SELECT 3, '3M-6M',    90,   180
    UNION ALL
    SELECT 4, '6M-1Y',    180,  360
    UNION ALL
    SELECT 5, '1Y-3Y',    360,  1080
    UNION ALL
    SELECT 6, '3Y-10Y',   1080, 3600
),
trades AS (
    SELECT
        Ticker,
        ExpiryDays,
        NetAmount1
    FROM my_table
    WHERE Ticker IS NOT NULL
      AND NetAmount1 IS NOT NULL
),
results AS (
    SELECT
        t.Ticker,
        b.bucket,
        b.bucket_order,
        COALESCE(
            SUM(
                t.NetAmount1 *
                CASE
                    -- Every trade contributes fully to spot delta.
                    WHEN b.bucket_order = 1
                        THEN 1.0

                    -- Missing or expired maturities have no forward risk.
                    WHEN t.ExpiryDays IS NULL
                      OR t.ExpiryDays <= b.lower_days
                        THEN 0.0

                    -- The trade passes through the entire segment.
                    WHEN t.ExpiryDays >= b.upper_days
                        THEN 1.0

                    -- The trade expires partway through the segment.
                    ELSE
                        1.0 * (t.ExpiryDays - b.lower_days)
                            / (b.upper_days - b.lower_days)
                END
            ),
            0
        ) AS Exposure
    FROM trades t
    CROSS JOIN buckets b
    GROUP BY
        t.Ticker,
        b.bucket,
        b.bucket_order
)
SELECT
    Ticker,
    bucket AS Bucket,
    Exposure
FROM results
ORDER BY
    Ticker,
    bucket_order;
