"""Currency universe for the USD correlation dashboard."""

USD_CURRENCIES = [
    # G10 / most liquid
    "EUR",
    "JPY",
    "GBP",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
    "SEK",
    "NOK",
    "DKK",
    # Asia
    "CNH",
    "CNY",
    "HKD",
    "SGD",
    "KRW",
    "TWD",
    "INR",
    "IDR",
    "THB",
    "MYR",
    "PHP",
    "VND",
    # EMEA
    "ZAR",
    "TRY",
    "PLN",
    "CZK",
    "HUF",
    "RON",
    "ILS",
    "AED",
    "SAR",
    "QAR",
    "KWD",
    "BHD",
    "OMR",
    "EGP",
    # Americas
    "MXN",
    "BRL",
    "CLP",
    "COP",
    "PEN",
]

EXTRA_INSTRUMENTS = [
    {
        "normalized_symbol": "DXY",
        "tradingview_symbol": "DXY",
        "exchange": "TVC",
    },
]
