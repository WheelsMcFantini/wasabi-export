import json
import csv
import requests
from datetime import datetime

# Function to get data from the API
def fetch_trade_history(trader_address, next_page_token="0"):
    url = f"https://gateway.wasabi.xyz/tradeHistory?env=prod&nextPageToken={next_page_token}&traderAddress={trader_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}")

# Function to parse trade data and extract relevant fields
def parse_trades(data):
    trades = []
    for item in data["items"]:
        # Convert timestamp to human-readable date
        date = datetime.fromtimestamp(item["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract core transaction data
        trade = {
            "date": date,
            "action": item["action"],
            "transaction_hash": item["transactionHash"],
            "token_symbol": item["token"]["symbol"],
            "token_name": item["token"]["name"],
            "price": float(item["price"]),
            "amount": float(item["amount"]) / (10 ** item["token"]["decimals"]), # Convert from wei
            "fees": float(item["fees"]) / (10 ** 18),  # Assuming fees are in wei
            "pnl": float(item["pnl"]) / (10 ** 18) if item["pnl"] != "0" else 0,  # Convert PnL from wei
            "roi": item["roi"],
            "position_id": item["position"]["id"],
            "side": item["position"]["side"],
            "leverage": item["position"]["leverage"],
            "entry_price": item["position"]["entryPrice"],
            "down_payment": item["position"]["downPayment"],
            "principal": item["position"]["principal"],
            "market_name": item["market"]["name"],
            "chain": item["market"]["chain"]
        }
        
        # Add order type specific data
        trade["order_type"] = item["orderType"]
        
        # Add specific data for open/close/liquidate
        if "data" in item:
            if "interestPaid" in item["data"]:
                trade["interest_paid"] = float(item["data"]["interestPaid"]) / (10 ** 18)
            if "principalRepaid" in item["data"]:
                trade["principal_repaid"] = float(item["data"]["principalRepaid"]) / (10 ** 18)
            if "collateralAmount" in item["data"]:
                trade["collateral_amount"] = item["data"]["collateralAmount"]
            
        trades.append(trade)
    
    return trades

# Function to save trades to CSV
def save_to_csv(trades, filename='trades.csv'):
    if not trades:
        print("No trades to save")
        return
        
    # Get all unique keys from all trades
    fieldnames = set()
    for trade in trades:
        fieldnames.update(trade.keys())
    
    # Sort fieldnames for consistent output
    fieldnames = sorted(fieldnames)
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(trade)
    
    print(f"Saved {len(trades)} trades to {filename}")

# Function to process all pages of trade history
def process_all_trade_history(trader_address):
    all_trades = []
    next_page_token = "0"
    
    while True:
        print(f"Fetching page with token: {next_page_token}")
        data = fetch_trade_history(trader_address, next_page_token)
        trades = parse_trades(data)
        all_trades.extend(trades)
        
        if data["hasNextPage"]:
            next_page_token = data["nextPageToken"]
        else:
            break
    
    return all_trades

# Main execution
def main():
    # Replace with your trader address
    trader_address = "Ethereum Address Here"
    
    try:
        # Option 1: Process from local file
        # with open('paste.txt', 'r') as f:
        #     data = json.load(f)
        #     trades = parse_trades(data)
        
        # Option 2: Fetch directly from API (all pages)
        trades = process_all_trade_history(trader_address)
        
        # Save to CSV
        save_to_csv(trades, f"wasabi_trades-{trader_address}.csv")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()