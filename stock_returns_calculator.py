#!/usr/bin/env python3
"""
Stock Returns Calculator
Calculates returns for international stocks using Yahoo Finance data
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# Stock information with Yahoo Finance ticker symbols
STOCKS = {
    "Bizlink Holding": "3665.TW",
    "HD Korea Shipbui": "009540.KS",
    "Hanwha Corp": "000880.KS",
    "GE Vernova T&D I": "GVT&D.NS",
    "Ta Ya Elec": "1609.TW",
    "Acbel Polytech": "6282.TW",
    "Eva Airways": "2618.TW",
    "Wan Hai Lines": "2615.TW",
    "Time Technoplast": "TIMETECHNO.NS",
    "Yang Ming Marine": "2609.TW",
}

# Date range for returns calculation
START_DATE = "2025-03-31"
END_DATE = "2025-09-30"


def get_yahoo_finance_data(ticker: str, start_date: str, end_date: str) -> dict:
    """
    Fetch historical stock data from Yahoo Finance using their chart API.

    Args:
        ticker: Yahoo Finance ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Dictionary with dates and closing prices
    """
    # Convert dates to Unix timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86400  # Add 1 day to include end date

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "period1": start_ts,
        "period2": end_ts,
        "interval": "1d",
        "includePrePost": "false",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
            return {"error": f"No data returned for {ticker}"}

        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        quotes = result.get("indicators", {}).get("quote", [{}])[0]
        closes = quotes.get("close", [])

        if not timestamps or not closes:
            return {"error": f"No price data for {ticker}"}

        # Convert to dates and prices
        dates = [datetime.fromtimestamp(ts).strftime("%Y-%m-%d") for ts in timestamps]
        prices = {d: p for d, p in zip(dates, closes) if p is not None}

        return {"prices": prices, "currency": result.get("meta", {}).get("currency", "N/A")}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except (KeyError, IndexError, ValueError) as e:
        return {"error": f"Data parsing error: {str(e)}"}


def find_closest_price(prices: dict, target_date: str, direction: str = "forward") -> tuple:
    """
    Find the closest available price to a target date.

    Args:
        prices: Dictionary of date -> price
        target_date: Target date in YYYY-MM-DD format
        direction: 'forward' to look ahead, 'backward' to look behind

    Returns:
        Tuple of (actual_date, price) or (None, None) if not found
    """
    target = datetime.strptime(target_date, "%Y-%m-%d")

    if target_date in prices:
        return target_date, prices[target_date]

    # Look for closest date within 7 days
    for i in range(1, 8):
        if direction == "forward":
            check_date = (target + timedelta(days=i)).strftime("%Y-%m-%d")
        else:
            check_date = (target - timedelta(days=i)).strftime("%Y-%m-%d")

        if check_date in prices:
            return check_date, prices[check_date]

    # If not found in preferred direction, try the other direction
    for i in range(1, 8):
        if direction == "forward":
            check_date = (target - timedelta(days=i)).strftime("%Y-%m-%d")
        else:
            check_date = (target + timedelta(days=i)).strftime("%Y-%m-%d")

        if check_date in prices:
            return check_date, prices[check_date]

    return None, None


def calculate_return(start_price: float, end_price: float) -> float:
    """Calculate percentage return."""
    if start_price and start_price != 0:
        return ((end_price - start_price) / start_price) * 100
    return None


def main():
    """Main function to calculate and display stock returns."""
    print("=" * 80)
    print("STOCK RETURNS CALCULATOR")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("=" * 80)
    print()

    results = []

    for company_name, ticker in STOCKS.items():
        print(f"Fetching data for {company_name} ({ticker})...", end=" ")

        data = get_yahoo_finance_data(ticker, START_DATE, END_DATE)

        if "error" in data:
            print(f"ERROR: {data['error']}")
            results.append({
                "Company": company_name,
                "Ticker": ticker,
                "Start Date": "N/A",
                "Start Price": "N/A",
                "End Date": "N/A",
                "End Price": "N/A",
                "Return (%)": "N/A",
                "Currency": "N/A",
                "Status": f"Error: {data['error']}"
            })
            time.sleep(0.5)  # Rate limiting
            continue

        prices = data["prices"]
        currency = data.get("currency", "N/A")

        # Find prices closest to our target dates
        start_date_actual, start_price = find_closest_price(prices, START_DATE, "forward")
        end_date_actual, end_price = find_closest_price(prices, END_DATE, "backward")

        if start_price and end_price:
            ret = calculate_return(start_price, end_price)
            print(f"OK ({currency})")
            results.append({
                "Company": company_name,
                "Ticker": ticker,
                "Start Date": start_date_actual,
                "Start Price": f"{start_price:.2f}",
                "End Date": end_date_actual,
                "End Price": f"{end_price:.2f}",
                "Return (%)": f"{ret:.2f}%",
                "Currency": currency,
                "Status": "Success"
            })
        else:
            print("INCOMPLETE DATA")
            results.append({
                "Company": company_name,
                "Ticker": ticker,
                "Start Date": start_date_actual or "N/A",
                "Start Price": f"{start_price:.2f}" if start_price else "N/A",
                "End Date": end_date_actual or "N/A",
                "End Price": f"{end_price:.2f}" if end_price else "N/A",
                "Return (%)": "N/A",
                "Currency": currency,
                "Status": "Incomplete data"
            })

        time.sleep(0.5)  # Rate limiting between requests

    # Display results table
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    # Create DataFrame for nice display
    df = pd.DataFrame(results)

    # Print detailed results
    print(f"{'Company':<20} {'Ticker':<15} {'Start':<12} {'End':<12} {'Return':<12} {'Currency':<8}")
    print("-" * 80)

    successful_returns = []
    for r in results:
        print(f"{r['Company']:<20} {r['Ticker']:<15} {r['Start Price']:<12} {r['End Price']:<12} {r['Return (%)']:<12} {r['Currency']:<8}")
        if r['Return (%)'] != 'N/A':
            successful_returns.append(float(r['Return (%)'].replace('%', '')))

    print("-" * 80)

    if successful_returns:
        avg_return = sum(successful_returns) / len(successful_returns)
        print(f"\nAverage Return: {avg_return:.2f}%")
        print(f"Best Performer: {max(successful_returns):.2f}%")
        print(f"Worst Performer: {min(successful_returns):.2f}%")

    print()
    print("Note: Prices are adjusted closing prices in local currency.")
    print("Dates may vary slightly due to market holidays/weekends.")

    return results


if __name__ == "__main__":
    main()
