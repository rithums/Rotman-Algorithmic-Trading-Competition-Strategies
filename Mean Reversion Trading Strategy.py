# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 09:35:00 2024

"""

import requests
from time import sleep
import numpy as np  # Import numpy for numerical operations

# Initialize the session with your API key
s = requests.Session()
s.headers.update({'X-API-key': 'NLJFH66O'})

# Global variables
MAX_LONG_EXPOSURE = 300000
MAX_SHORT_EXPOSURE = -100000
ORDER_LIMIT = 5000
PRICE_HISTORY_LENGTH = 20  # Number of ticks to average over for mean reversion

# Function to get the current tick and status
def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']

# Function to get the best bid and ask prices for a ticker
def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']
       
        best_bid_price = bid_side_book[0]["price"]
        best_ask_price = ask_side_book[0]["price"]
 
        return best_bid_price, best_ask_price

# Function to get the current position
def get_position():
    resp = s.get('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return sum(item['position'] for item in book)  # Sum positions across all securities

# Mean Reversion Strategy Implementation
def mean_reversion_strategy(ticker, price_history):
    if len(price_history) < PRICE_HISTORY_LENGTH:
        return None, None  # Not enough data to make a decision

    mean_price = np.mean(price_history)
    current_price = (get_bid_ask(ticker)[0] + get_bid_ask(ticker)[1]) / 2  # Average of best bid and ask prices

    # Define thresholds for trading
    buy_threshold = mean_price * 0.98  # 2% below mean
    sell_threshold = mean_price * 1.02  # 2% above mean

    # Decision making based on the current price
    if current_price < buy_threshold:
        return 'BUY', current_price
    elif current_price > sell_threshold:
        return 'SELL', current_price
    else:
        return None, None  # No action needed

def main():
    tick, status = get_tick()
    ticker_list = ['OWL','CROW','DOVE','DUCK']
    price_history = {ticker: [] for ticker in ticker_list}  # Store price history for each ticker

    while status == 'ACTIVE':
        for ticker_symbol in ticker_list:
            position = get_position()
            best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)

            # Update price history
            current_price = (best_bid_price + best_ask_price) / 2  # Average price
            price_history[ticker_symbol].append(current_price)

            # Limit price history to the defined length
            if len(price_history[ticker_symbol]) > PRICE_HISTORY_LENGTH:
                price_history[ticker_symbol].pop(0)  # Remove the oldest price

            # Implement the mean reversion strategy
            action, price = mean_reversion_strategy(ticker_symbol, price_history[ticker_symbol])
           
            if action == 'BUY' and position < MAX_LONG_EXPOSURE:
                resp = s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_bid_price, 'action': 'BUY'})
           
            elif action == 'SELL' and position > MAX_SHORT_EXPOSURE:
                resp = s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_ask_price, 'action': 'SELL'})

            sleep(0.75)
