#!/usr/bin/env python3
"""
WORKING TRADING SYSTEM - CLAWS OF DOOM v2
No dependencies on broken ML pipeline. Uses proven strategies only.
"""
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

CAPITAL_BASE = 10000

def fetch_yahoo(symbol, period='6mo'):
    """Fetch data from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval=1d"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps, unit='s'),
            'open': quotes['open'],
            'high': quotes['high'],
            'low': quotes['low'],
            'close': quotes['close'],
            'volume': quotes['volume']
        })
        return df.dropna()
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def fetch_fear_greed():
    """Fetch Crypto Fear & Greed Index"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return int(data['data'][0]['value'])
    except:
        return 50  # Neutral fallback

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_sma(prices, period):
    return prices.rolling(window=period).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

class ClawsSystem:
    def __init__(self):
        self.picks = []
        self.performance = {
            'systems': {
                'connors_rsi2': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
                'fib_pullback': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
                'vix_fear': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            }
        }
    
    def strategy_connors_rsi2(self, symbol):
        """Connors RSI-2 Mean Reversion"""
        df = fetch_yahoo(symbol)
        if df is None or len(df) < 50:
            return None
        
        close = df['close']
        rsi2 = calculate_rsi(close, 2)
        sma200 = calculate_sma(close, 200)
        
        current_price = close.iloc[-1]
        current_rsi2 = rsi2.iloc[-1]
        current_sma200 = sma200.iloc[-1]
        
        # Entry: RSI-2 < 5, price > 200 SMA
        if current_rsi2 < 5 and current_price > current_sma200:
            # Falling knife protection
            if current_price < current_sma200 * 0.8:
                return None
            
            atr = calculate_atr(df).iloc[-1]
            confidence = min(0.8, 0.73 + (5 - current_rsi2) * 0.02)
            
            return {
                'id': f"crsi2_{symbol}_{datetime.now().strftime('%Y%m%d')}",
                'symbol': symbol,
                'strategy': 'connors_rsi2',
                'direction': 'LONG',
                'confidence': confidence,
                'entry_price': current_price,
                'tp_price': current_price + atr * 1.5,
                'sl_price': current_price - atr * 2.0,
                'position_pct': 0.04,  # 4% of capital
                'reason': f'RSI-2 = {current_rsi2:.1f} (oversold), above 200 SMA',
                'timestamp': datetime.now().isoformat()
            }
        return None
    
    def strategy_fibonacci_pullback(self, symbol):
        """Fibonacci Trend Pullback"""
        df = fetch_yahoo(symbol)
        if df is None or len(df) < 50:
            return None
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        sma50 = calculate_sma(close, 50)
        sma200 = calculate_sma(close, 200)
        
        current_price = close.iloc[-1]
        current_sma50 = sma50.iloc[-1]
        current_sma200 = sma200.iloc[-1]
        
        # Bull trend
        if current_sma50 > current_sma200:
            swing_high = high.rolling(20).max().iloc[-1]
            swing_low = low.rolling(20).min().iloc[-1]
            fib_50 = swing_high - 0.5 * (swing_high - swing_low)
            fib_618 = swing_high - 0.618 * (swing_high - swing_low)
            
            # Price near Fib level
            near_fib = abs(current_price - fib_50) / current_price < 0.01 or \
                       abs(current_price - fib_618) / current_price < 0.01
            
            if near_fib:
                atr = calculate_atr(df).iloc[-1]
                return {
                    'id': f"fib_{symbol}_{datetime.now().strftime('%Y%m%d')}",
                    'symbol': symbol,
                    'strategy': 'fib_pullback',
                    'direction': 'LONG',
                    'confidence': 0.71,
                    'entry_price': current_price,
                    'tp_price': swing_high,
                    'sl_price': current_price - atr * 2.0,
                    'position_pct': 0.035,  # 3.5% of capital
                    'reason': f'Fib pullback in bull trend (50>200 SMA)',
                    'timestamp': datetime.now().isoformat()
                }
        return None
    
    def strategy_vix_fear(self, symbol):
        """VIX/Fear Reversal - uses Fear & Greed Index"""
        if symbol not in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            return None  # Only for crypto
        
        fg_index = fetch_fear_greed()
        
        # Extreme fear = buy signal
        if fg_index <= 15:
            df = fetch_yahoo(symbol.replace('-USD', '-USD'))
            if df is None:
                return None
            
            current_price = df['close'].iloc[-1]
            atr = calculate_atr(df).iloc[-1]
            
            confidence = min(0.8, 0.71 + (15 - fg_index) * 0.01)
            
            return {
                'id': f"fear_{symbol}_{datetime.now().strftime('%Y%m%d')}",
                'symbol': symbol,
                'strategy': 'vix_fear',
                'direction': 'LONG',
                'confidence': confidence,
                'entry_price': current_price,
                'tp_price': current_price * 1.08,  # 8% target
                'sl_price': current_price - atr * 2.0,
                'position_pct': 0.04,
                'reason': f'Fear & Greed = {fg_index} (extreme fear)',
                'timestamp': datetime.now().isoformat()
            }
        return None
    
    def run_all(self):
        """Run all strategies"""
        symbols = ['SPY', 'QQQ', 'IWM', 'BTC-USD', 'ETH-USD']
        
        for symbol in symbols:
            # Connors RSI-2
            pick = self.strategy_connors_rsi2(symbol)
            if pick:
                self.picks.append(pick)
            
            # Fibonacci Pullback
            pick = self.strategy_fibonacci_pullback(symbol)
            if pick:
                self.picks.append(pick)
            
            # VIX Fear (crypto only)
            if symbol in ['BTC-USD', 'ETH-USD']:
                pick = self.strategy_vix_fear(symbol)
                if pick:
                    self.picks.append(pick)
        
        # Sort by confidence
        self.picks.sort(key=lambda x: x['confidence'], reverse=True)
        return self.picks[:5]  # Top 5 picks
    
    def save(self):
        """Save to JSON"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'capital_base': CAPITAL_BASE,
            'picks': self.picks,
            'performance': self.performance
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/picks.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return output

if __name__ == '__main__':
    print("☠️ CLAWS OF DOOM v2 - Executing...")
    system = ClawsSystem()
    picks = system.run_all()
    system.save()
    print(f"Generated {len(picks)} picks:")
    for p in picks:
        print(f"  {p['symbol']}: {p['strategy']} @ ${p['entry_price']:.2f} (conf: {p['confidence']:.2f})")
