# USD FX Correlation Dashboard

Builds a static HTML and Excel dashboard from TradingView daily FX data.

The dashboard normalizes every FX pair as `XXXUSD`. If TradingView only has the inverse quote, for example `USDJPY`, the script retrieves `USDJPY` and stores the normalized price as `JPYUSD = 1 / USDJPY`. Extra instruments such as `DXY` can also be included without FX inversion.

## Install

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python .\build_correlation_dashboard.py
```

Outputs:

- `output\usd_fx_correlation.html`
- `output\usd_fx_correlation.xlsx`

## Optional TradingView Login

The script can run without a login. If you want to use TradingView credentials, set:

```powershell
$env:TV_USERNAME="your_username"
$env:TV_PASSWORD="your_password"
python .\build_correlation_dashboard.py
```

## Method

- Data source: TradingView via `tvDatafeed`
- Exchange/feed: `FX_IDC` for FX, `TVC:DXY` for DXY
- Frequency: daily
- Default history: 250 candles
- Return method: log returns, `ln(close_today / close_yesterday)`
- Short-term correlation: latest 30 daily log-return observations
- Long-term correlation: latest 180 daily log-return observations
- Divergence matrix: `30D correlation - 180D correlation`
- Correlation method: Pearson correlation on aligned log returns

## Customize

Edit `currency_universe.py` to add or remove currencies. The script tries `XXXUSD` first, then `USDXXX`, and records unavailable symbols in the Excel `metadata` sheet. Add non-FX instruments such as indices to `EXTRA_INSTRUMENTS`.

Change the windows from the command line:

```powershell
python .\build_correlation_dashboard.py --st-window 30 --lt-window 180
```

If you only changed dashboard logic and want to reuse the existing downloaded prices:

```powershell
python .\build_correlation_dashboard.py --use-existing-output
```
