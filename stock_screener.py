import yfinance as yf

# 20 companies listed on the Oslo Stock Exchange
tickers = [
    "NORBT.OL",  # Norbit
    "PROT.OL",  # Protector Forsikring
    "EQNR.OL",  # Equinor
    "DNB.OL",  # DNB
    "NHY.OL",  # Norsk Hydro
    "ORK.OL",  # Orkla
    "KOG.OL",  # Kongsberg Gruppen
    "KIT.OL",  # Kitron
    "PARB.OL",  # Pareto Bank
    "BOUV.OL",  # Bouvet
    "FRO.OL",  # Frontline
    "SATS.OL",  # Sats
    "AFG.OL",  # AF Gruppen
    "VEI.OL",  # Veidekke
    "TEL.OL",  # Telenor
    "MOWI.OL",  # Mowi
    "YAR.OL",  # Yara
    "TOM.OL",  # Tomra
    "KID.OL",  # Kid
    "MEDI.OL",  # Medistim
]

# Download historical prices for momentum calculation
data = yf.download(tickers, period="1y", auto_adjust=True, progress=False)["Close"]


betas = {}
market_caps = {}
profitability = {}
momentum = {}
valuation = {}


for ticker in tickers:
    stock = yf.Ticker(ticker)

    # beta
    beta = stock.info.get("beta")
    if beta is not None:
        betas[ticker] = beta

    # size
    market_cap = stock.info.get("marketCap")
    if market_cap is not None:
        market_caps[ticker] = market_cap

    # Profitability
    roe = stock.info.get("returnOnEquity")
    if roe is not None:
        profitability[ticker] = roe
    # todo: do a composite score with roce

    # Momentum (12–2 month momentum)
    prices = data[ticker].dropna()  # Remove missing price data
    if len(prices) >= 230:
        price_12m = prices.iloc[0]
        price_1m = prices.iloc[-22]

        momentum[ticker] = (price_1m / price_12m) - 1

    # value
    pe = stock.info.get("trailingPE")
    pb = stock.info.get("priceToBook")
    ps = stock.info.get("priceToSalesTrailing12Months")
    ev_ebitda = stock.info.get("enterpriseToEbitda")
    # todo: add EV/EBIT and EV/Gross Profit

    if all(x is not None and x > 0 for x in [pe, pb, ps, ev_ebitda]):
        valuation[ticker] = {"PE": pe, "PB": pb, "PS": ps, "EV_EBITDA": ev_ebitda}

# Make a composite value score for value/pricing
value_scores = {}

for ticker in valuation:
    pe_rank = sorted(valuation, key=lambda t: valuation[t]["PE"]).index(ticker) + 1
    pb_rank = sorted(valuation, key=lambda t: valuation[t]["PB"]).index(ticker) + 1
    ps_rank = sorted(valuation, key=lambda t: valuation[t]["PS"]).index(ticker) + 1
    ev_rank = (
        sorted(valuation, key=lambda t: valuation[t]["EV_EBITDA"]).index(ticker) + 1
    )

    value_scores[ticker] = (pe_rank + pb_rank + ps_rank + ev_rank) / 4


# Include only stocks with data for all five factors
valid_tickers = [
    ticker
    for ticker in tickers
    if ticker in betas
    and ticker in market_caps
    and ticker in profitability
    and ticker in momentum
    and ticker in value_scores
]

# Identify stocks excluded due to missing factor data
excluded_stocks = {}

for ticker in tickers:
    if ticker not in valid_tickers:
        missing = []

        if ticker not in betas:
            missing.append("Beta")
        if ticker not in market_caps:
            missing.append("Size")
        if ticker not in profitability:
            missing.append("Profitability")
        if ticker not in momentum:
            missing.append("Momentum")
        if ticker not in value_scores:
            missing.append("Value")

        excluded_stocks[ticker] = missing

# Rank each factor
beta_rank = sorted(valid_tickers, key=lambda t: betas[t])
size_rank = sorted(valid_tickers, key=lambda t: market_caps[t])
profitability_rank = sorted(valid_tickers, key=lambda t: profitability[t], reverse=True)
momentum_rank = sorted(valid_tickers, key=lambda t: momentum[t], reverse=True)
value_rank = sorted(valid_tickers, key=lambda t: value_scores[t])

# Create the final composite score
composite_scores = {}

for ticker in valid_tickers:
    beta_score = beta_rank.index(ticker) + 1
    size_score = size_rank.index(ticker) + 1
    profitability_score = profitability_rank.index(ticker) + 1
    momentum_score = momentum_rank.index(ticker) + 1
    value_score = value_rank.index(ticker) + 1

    composite_scores[ticker] = (
        beta_score * 0.20
        + size_score * 0.20
        + profitability_score * 0.20
        + momentum_score * 0.20
        + value_score * 0.20
    )

# Final ranking
ranking_composite = sorted(composite_scores.items(), key=lambda x: x[1])

print("\nFACTOR-BASED STOCK SCREENER")
print("=" * 40)
print(f"Stocks analyzed: {len(tickers)}")
print(f"Stocks ranked:   {len(valid_tickers)}")
print(f"Stocks excluded: {len(excluded_stocks)}")

print("\nFINAL COMPOSITE RANKING")
print("-" * 40)
print(f"{'Rank':<6}{'Ticker':<14}{'Score':>8}")
print("-" * 40)

for rank, (ticker, score) in enumerate(ranking_composite, start=1):
    print(f"{rank:<6}{ticker:<14}{score:>8.2f}")

print("\nEXCLUDED STOCKS")
print("-" * 40)

if excluded_stocks:
    for ticker, missing in excluded_stocks.items():
        print(f"{ticker:<12} Missing: {', '.join(missing)}")
else:
    print("None")
