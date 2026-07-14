/*
SQL Server: expand each observed FX forward curve to every integer day
between its minimum and maximum nodes, using linear interpolation.

Replace fx_forward_rates with the source table name if necessary.

Required source columns:
  Date     - market-data date
  Ticker   - quoted curve node, such as CNH1W Curncy
  CurveId  - curve identifier
  Days     - integer days from spot to the node's expiry
  Value    - observed value at the node

Assumptions:
  Each Date + CurveId + Days combination is unique.
  Days and Value are non-NULL for usable nodes.
  No extrapolation is performed beyond the minimum and maximum nodes.

The SELECT INTO statement creates fx_forward_rates_daily. Use INSERT INTO
instead if the destination table already exists.
*/

WITH curve_bounds AS (
    SELECT
        [Date],
        CurveId,
        MIN(Days) AS MinDays,
        MAX(Days) AS MaxDays
    FROM fx_forward_rates
    WHERE Days IS NOT NULL
      AND [Value] IS NOT NULL
    GROUP BY
        [Date],
        CurveId
),
day_grid AS (
    -- Start each curve at its minimum observed node.
    SELECT
        [Date],
        CurveId,
        MinDays AS Days,
        MaxDays
    FROM curve_bounds

    UNION ALL

    -- Generate every integer day through the maximum observed node.
    SELECT
        [Date],
        CurveId,
        Days + 1,
        MaxDays
    FROM day_grid
    WHERE Days < MaxDays
),
interpolated AS (
    SELECT
        g.[Date],
        g.CurveId,
        g.Days,

        CASE
            -- Preserve the exact value at an original observed node.
            WHEN lower_node.Days = upper_node.Days
                THEN lower_node.[Value]

            -- Interpolate between the nearest surrounding nodes.
            ELSE
                lower_node.[Value]
                +
                (
                    1.0 * (g.Days - lower_node.Days)
                    / NULLIF(
                        upper_node.Days - lower_node.Days,
                        0
                    )
                )
                *
                (
                    upper_node.[Value]
                    - lower_node.[Value]
                )
        END AS InterpolatedValue,

        CASE
            WHEN lower_node.Days = upper_node.Days
                THEN 1
            ELSE 0
        END AS IsObservedNode

    FROM day_grid g

    CROSS APPLY (
        SELECT TOP (1)
            n.Days,
            CAST(n.[Value] AS DECIMAL(38, 12)) AS [Value]
        FROM fx_forward_rates n
        WHERE n.[Date] = g.[Date]
          AND n.CurveId = g.CurveId
          AND n.Days <= g.Days
          AND n.[Value] IS NOT NULL
        ORDER BY
            n.Days DESC
    ) lower_node

    CROSS APPLY (
        SELECT TOP (1)
            n.Days,
            CAST(n.[Value] AS DECIMAL(38, 12)) AS [Value]
        FROM fx_forward_rates n
        WHERE n.[Date] = g.[Date]
          AND n.CurveId = g.CurveId
          AND n.Days >= g.Days
          AND n.[Value] IS NOT NULL
        ORDER BY
            n.Days ASC
    ) upper_node
)
SELECT
    [Date],
    CurveId,
    Days,
    InterpolatedValue,
    IsObservedNode
INTO fx_forward_rates_daily
FROM interpolated
OPTION (MAXRECURSION 0);

/*
Recommended source index for repeated runs:

CREATE INDEX IX_fx_forward_rates_curve
ON fx_forward_rates ([Date], CurveId, Days)
INCLUDE ([Value]);
*/
