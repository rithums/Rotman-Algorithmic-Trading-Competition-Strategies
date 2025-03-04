# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 09:35:00 2024

@author: Rhythm Satav
"""

import requests
from time import sleep
import numpy as np

s = requests.Session()
s.headers.update({'X-API-key': 'NLJFH66O'})  # Make sure you use YOUR API Key

# Global variables
MAX_LONG_EXPOSURE = 300000
MAX_SHORT_EXPOSURE = -100000
ORDER_LIMIT = 5000
PRICE_HISTORY_LENGTH = 20  # Length for price history
BB_PERIOD = 20  # Period for Bollinger Bands
BB_STD_MULTIPLIER = 2  # Standard deviation multiplier for Bollinger Bands

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
       
        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]
       
        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]
 
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
    resp = s.get('http://localhost:9999/v1/orders/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def calculate_bollinger_bands(price_history, period=BB_PERIOD, std_multiplier=BB_STD_MULTIPLIER):
    if len(price_history) < period:
        return None, None, None  # Not enough data

    sma = np.mean(price_history[-period:])  # Simple Moving Average
    std_dev = np.std(price_history[-period:])  # Standard Deviation
    upper_band = sma + (std_dev * std_multiplier)  # Upper Bollinger Band
    lower_band = sma - (std_dev * std_multiplier)  # Lower Bollinger Band

    return upper_band, sma, lower_band

def main():
    tick, status = get_tick()
    ticker_list = ['OWL', 'CROW', 'DOVE', 'DUCK']

    # Store price history for each ticker
    price_history = {ticker: [] for ticker in ticker_list}

    while status == 'ACTIVE':        

        for i in range(4):
            ticker_symbol = ticker_list[i]
            position = get_position()
            best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)

            current_price = (best_bid_price + best_ask_price) / 2  # Average price
            price_history[ticker_symbol].append(current_price)

            # Limit price history size
            if len(price_history[ticker_symbol]) > PRICE_HISTORY_LENGTH:
                price_history[ticker_symbol].pop(0)  # Remove the oldest price

            # Calculate Bollinger Bands
            upper_band, sma, lower_band = calculate_bollinger_bands(price_history[ticker_symbol])

            # Trading logic based on Bollinger Bands
            if upper_band and lower_band:  # Check if we have enough data for Bollinger Bands
                if current_price < lower_band and position < MAX_LONG_EXPOSURE:
                    resp = s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_bid_price, 'action': 'BUY'})

                elif current_price > upper_band and position > MAX_SHORT_EXPOSURE:
                    resp = s.post('http://localhost:9999/v1/orders', params={'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_ask_price, 'action': 'SELL'})

            sleep(0.75)
