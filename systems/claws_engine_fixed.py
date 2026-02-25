#!/usr/bin/env python3
"""
CLAWS OF DOOM v2 - FIXED VERSION
Uses CoinGecko for crypto (reliable) and handles Yahoo Finance blocks
"""
import json
import requests
from datetime import datetime
import os

CAPITAL_BASE = 10000

# CoinGecko API (reliable, no auth needed)
COINGECKO_URL = "https://api.coingecko.com/api/v3"

def fetch_crypto_price(coin_id):
    """Fetch crypto price from CoinGecko"""
    try:
        url = f"{COINGECKO_URL}/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get(coin_id, {}).get('usd'), data.get(coin_id, {}).get('usd_24h_change', 0)
    except Exception as e:
        print(f"Error fetching {coin_id}: {e}")
        return None, 0

def fetch_fear_greed():
    """Fetch Crypto Fear & Greed Index"""
    try:
        url = "https://api.alternative.me/fng/?limit=2"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return int(data['data'][0]['value'])
    except:
        return 50

def fetch_market_data():
    """Fetch market data for analysis"""
    try:
        # Get BTC dominance and market data
        url = f"{COINGECKO_URL}/global"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get('data', {})
    except:
        return {}

class ClawsSystem:
    def __init__(self):
        self.picks = []
        self.coin_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana'
        }
    
    def strategy_extreme_fear(self):
        """Buy when Fear & Greed shows extreme fear (< 20)"""
        fg = fetch_fear_greed()
        
        if fg <= 20:
            btc_price, btc_change = fetch_crypto_price('bitcoin')
            eth_price, eth_change = fetch_crypto_price('ethereum')
            
            picks = []
            
            if btc_price and btc_change < -5:  # BTC down > 5%
                picks.append({
                    'id': f"fear_btc_{datetime.now().strftime('%Y%m%d')}",
                    'symbol': 'BTC',
                    'strategy': 'extreme_fear',
                    'direction': 'LONG',
                    'confidence': min(0.8, 0.71 + (20 - fg) * 0.01),
                    'entry_price': btc_price,
                    'tp_price': btc_price * 1.06,  # 6% target
                    'sl_price': btc_price * 0.95,  # 5% stop
                    'position_pct': 0.04,
                    'reason': f'Fear & Greed = {fg} (extreme fear), BTC down {btc_change:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            if eth_price and eth_change < -5:
                picks.append({
                    'id': f"fear_eth_{datetime.now().strftime('%Y%m%d')}",
                    'symbol': 'ETH',
                    'strategy': 'extreme_fear',
                    'direction': 'LONG',
                    'confidence': min(0.75, 0.68 + (20 - fg) * 0.01),
                    'entry_price': eth_price,
                    'tp_price': eth_price * 1.06,
                    'sl_price': eth_price * 0.95,
                    'position_pct': 0.035,
                    'reason': f'Fear & Greed = {fg} (extreme fear), ETH down {eth_change:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            return picks
        return []
    
    def strategy_btc_dominance(self):
        """Trade based on BTC dominance shifts"""
        market_data = fetch_market_data()
        btc_dominance = market_data.get('market_cap_percentage', {}).get('btc', 50)
        
        # When BTC dominance spikes, altcoins often follow
        if btc_dominance > 55:  # High BTC dominance
            eth_price, _ = fetch_crypto_price('ethereum')
            if eth_price:
                return [{
                    'id': f"dom_eth_{datetime.now().strftime('%Y%m%d')}",
                    'symbol': 'ETH',
                    'strategy': 'btc_dominance',
                    'direction': 'LONG',
                    'confidence': 0.65,
                    'entry_price': eth_price,
                    'tp_price': eth_price * 1.05,
                    'sl_price': eth_price * 0.97,
                    'position_pct': 0.03,
                    'reason': f'BTC dominance high ({btc_dominance:.1f}%), ETH lagging',
                    'timestamp': datetime.now().isoformat()
                }]
        return []
    
    def strategy_momentum_reversal(self):
        """Mean reversion after large daily moves"""
        coins = ['bitcoin', 'ethereum', 'solana']
        picks = []
        
        for coin in coins:
            price, change = fetch_crypto_price(coin)
            if price and change < -8:  # Down > 8% in 24h
                symbol = coin.upper()[:3]
                picks.append({
                    'id': f"rev_{symbol}_{datetime.now().strftime('%Y%m%d')}",
                    'symbol': symbol,
                    'strategy': 'momentum_reversal',
                    'direction': 'LONG',
                    'confidence': min(0.72, 0.65 + abs(change) * 0.01),
                    'entry_price': price,
                    'tp_price': price * 1.04,
                    'sl_price': price * 0.96,
                    'position_pct': 0.03,
                    'reason': f'{symbol} down {change:.1f}% in 24h (mean reversion)',
                    'timestamp': datetime.now().isoformat()
                })
        
        return picks
    
    def run_all(self):
        """Run all strategies"""
        all_picks = []
        
        # Strategy 1: Extreme Fear
        all_picks.extend(self.strategy_extreme_fear())
        
        # Strategy 2: BTC Dominance
        all_picks.extend(self.strategy_btc_dominance())
        
        # Strategy 3: Momentum Reversal
        all_picks.extend(self.strategy_momentum_reversal())
        
        # Sort by confidence
        all_picks.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.picks = all_picks[:5]  # Top 5
        return self.picks
    
    def save(self):
        """Save to JSON"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'capital_base': CAPITAL_BASE,
            'picks': self.picks,
            'market_data': {
                'fear_greed': fetch_fear_greed(),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/picks.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return output

if __name__ == '__main__':
    print("☠️ CLAWS OF DOOM v2 - FIXED - Executing...")
    system = ClawsSystem()
    picks = system.run_all()
    system.save()
    print(f"Generated {len(picks)} picks:")
    for p in picks:
        print(f"  {p['symbol']}: {p['strategy']} @ ${p['entry_price']:.2f} (conf: {p['confidence']:.2f})")
