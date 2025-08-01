from dotenv import load_dotenv
import os
import yfinance as yf
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

def load_config():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    return db_url, api_key

class BaseSource(ABC):
    @abstractmethod
    def get_close_price(self, symbol: str, date: str) -> dict:
        pass

class YahooFinanceSource(BaseSource):
    def get_close_price(self, symbol: str, date: str) -> dict:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            end_dt = dt + timedelta(days=1)
            data = yf.download(symbol, start=date, end=end_dt.strftime("%Y-%m-%d"))
            print("DEBUG: DataFrame returned by yfinance:")
            print(data)
            if data.empty:
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "source": "YahooFinance",
                    "error": "No data returned. Check if the date is a valid trading day and the symbol is correct."
                }
            elif "Close" in data.columns:
                close_price = float(data["Close"][0])
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": close_price,
                    "source": "YahooFinance"
                }
            else:
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "source": "YahooFinance",
                    "error": "No closing price found in data."
                }
        except Exception as e:
            return {
                "symbol": symbol,
                "date": date,
                "close_price": None,
                "source": "YahooFinance",
                "error": str(e)
            }

def main():
    db_url, api_key = load_config()
    print(f"DATABASE_URL: {db_url}")
    if api_key:
        print(f"ALPHA_VANTAGE_API_KEY: {'*' * len(api_key)} (hidden)")
    else:
        print("ALPHA_VANTAGE_API_KEY: Not set")
    # Example invocation
    print("\n--- Example YahooFinanceSource fetch ---")
    source = YahooFinanceSource()
    # Use a recent valid trading date for demonstration
    result = source.get_close_price("MSFT", "2024-07-26")
    print(result)

if __name__ == "__main__":
    main()
