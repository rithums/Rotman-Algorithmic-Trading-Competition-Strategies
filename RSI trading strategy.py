# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 09:35:00 2024

@author: Oriana.Rahman
"""

import requests
from time import sleep
import numpy as np

# Initialize the requests session with API key
s = requests.Session()
s.headers.update({'X-API-key': 'GEDY404J'})  # Make sure you use YOUR API Key

# Global variables
MAX_LONG_EXPOSURE = 300000
MAX_SHORT_EXPOSURE = -100000
ORDER_LIMIT = 5000
RSI_PERIOD = 14  # Period for RSI calculation
RSI_OVERBOUGHT = 70  # Overbought threshold
RSI_OVERSOLD = 30  # Oversold threshold

def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']


def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']

        best_bid_price = bid_side_book[0]['price']
        best_ask_price = ask_side_book[0]['price']

        return best_bid_price, best_ask_price

def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/securities/tas', params=payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return (book[0]['position']) + (book[1]['position']) + (book[2]['position'])

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/orders', params=payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get('http://localhost:9999/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def calculate_rsi(price_history, period=RSI_PERIOD):
    if len(price_history) < period:
        return None  # Not enough data
    delta = np.diff(price_history[-period:])
    gain = np.mean(delta[delta > 0]) if np.any(delta > 0) else 0
    loss = -np.mean(delta[delta < 0]) if np.any(delta < 0) else 0

    rs = gain / loss if loss > 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    tick, status = get_tick()
    ticker_list = ['OWL', 'CROW', 'DOVE', 'DUCK']

    # Store price history for RSI calculation
    price_history = {ticker: [] for ticker in ticker_list}

    while status == 'ACTIVE':
        for ticker_symbol in ticker_list:
            position = get_position()
            best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)

            # Simulating the collection of the last price for RSI calculation
            # Assuming the last price is the best ask price for this example
            price_history[ticker_symbol].append(best_ask_price)

            current_rsi = calculate_rsi(price_history[ticker_symbol])
            print(f"Current RSI for {ticker_symbol}: {current_rsi}")

            # Buy logic based on RSI
            if current_rsi is not None and current_rsi < RSI_OVERSOLD and position < MAX_LONG_EXPOSURE:
                print(f"Buying {ORDER_LIMIT} shares of {ticker_symbol} at {best_bid_price}")
                s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_bid_price, 'action': 'BUY'})

            # Sell logic based on RSI
            if current_rsi is not None and current_rsi > RSI_OVERBOUGHT and position > MAX_SHORT_EXPOSURE:
                print(f"Selling {ORDER_LIMIT} shares of {ticker_symbol} at {best_ask_price}")
                s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_ask_price, 'action': 'SELL'})

            sleep(0.75)

            # Cancel open orders after each cycle
            s.post('http://localhost:9999/v1/commands/cancel', params={'ticker': ticker_symbol})

        tick, status = get_tick()

if __name__ == '__main__':
    main()
