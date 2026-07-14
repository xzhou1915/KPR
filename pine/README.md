# TradingView implementation

`directional_pressure_v01.pine` is a Pine Script v6 port of the frozen raw
Directional Pressure model. Paste the entire file into TradingView's Pine
Editor, choose **Save**, then **Add to chart**.

## Defaults and tuning

The defaults reproduce the research specification:

- horizons: 40, 60, and 80 chart bars;
- exponentially weighted volatility span: 20 bars, lagged one bar;
- efficiency segment: 5 bars and 0.50-volatility significance threshold;
- shock threshold: 1.0 volatility unit and response period: 5 bars;
- prior breakout range: 20 bars;
- minimum direction observations: 8 and minimum events: 3;
- trailing component scale: 126 bars with at least 30 valid values;
- component cap: plus/minus 3;
- neutral/strong pressure boundaries: plus/minus 0.20 and plus/minus 0.50;
- equal component and horizon weights.

All periods mean chart bars. On a daily chart, a response period of 5 means
five trading days. On a 60-minute chart, it means five 60-minute candles.

Every calculation parameter is available under the indicator's **Settings →
Inputs** tab. Changing the defaults produces a user-modified model that has not
been covered by the project's research validation.

## Reading the output

The main line is bounded near -1 to +1:

- `>= +0.50`: Strong up pressure
- `+0.20 to +0.50`: Up pressure
- `-0.20 to +0.20`: Neutral
- `-0.50 to -0.20`: Down pressure
- `<= -0.50`: Strong down pressure

Confidence measures sample sufficiency, component agreement, horizon agreement,
availability, and directional strength. It is not a probability of a profitable
trade.

Shock and breakout observations are recorded only after the response period has
finished. Public outputs update only on confirmed bars, so the indicator does
not use future bars or backfill a mature response onto its original event bar.

## Important research status

The Pine port implements the **raw OHLC-only pressure score**. It does not port
the Python research pipeline's rolling momentum-orthogonal diagnostic.

Model 0.1 did not pass the predeclared broad cross-asset holdout gate. The
breakout-acceptance family passed independently, while the full model and shock
family did not. The script is therefore labeled **Descriptive only** and should
not be treated as a validated strategy or next-return forecast.

TradingView's price feed, sessions, adjusted data, and available starting
history can differ from the Python research datasets, so exact numerical parity
is not guaranteed.
