from datetime import date, datetime

batch_schema = {
    "symbol": str,
    "companyName": str,
    "open": float,
    "openTime": datetime,
    "close": float,
    "closeTime": datetime,
    "high": float,
    "highTime": datetime,
    "low": float,
    "lowTime": datetime,
    "latestPrice": float,
    "latestUpdate": datetime,
    "latestVolume": int,
    "volume": int,
}

last_quote_schema = {
    "symbol": str,
    "price": float,
    "time": datetime,
    "size": int,
}

tops_schema = {
    "symbol": str,
    "bidSize": int,
    "bidPrice": float,
    "askSize": int,
    "askPrice": float,
    "volume": int,
    "lastSalePrice": float,
    "lastSaleSize": int,
    "lastSaleTime": datetime,
    "lastUpdated": datetime,
    "sector": str,
    "securityType": str,
    "seq": int,
}

holdings_schema = {
    "symbol": str,
    "quantity": int,
    "price": float,
    "time": datetime,
}

charts_schema = {
    "date": date,
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": int,
    "symbol": str,
    "quantity": int,
}
