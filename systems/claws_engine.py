#!/usr/bin/env python3
"""
CLAWS OF DOOM v2 - Alternative API Version
Uses multiple free APIs to avoid rate limits
"""
import json
import requests
from datetime import datetime
import os
import time

CAPITAL_BASE = 10000

class ClawsSystem:
    def __init__(self):
        self.picks = []
    
    def fetch_crypto_prices(self):
        """Try multiple free APIs"""
        prices = {}
        
        # API 1: CoinGecko (primary)
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                prices['BTC'] = (data['bitcoin']['usd'], data['bitcoin'].get('usd_24h_change', 0))
                prices['ETH'] = (data['ethereum']['usd'], data['ethereum'].get('usd_24h_change', 0))
                prices['SOL'] = (data['solana']['usd'], data['solana'].get('usd_24h_change', 0))
                return prices, 'coingecko'
        except:
            pass
        
        time.sleep(1)  # Be nice to APIs
        
        # API 2: Binance (backup)
        try:
            for symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    coin = symbol.replace('USDT', '')
                    prices[coin] = (float(data['lastPrice']), float(data['priceChangePercent']))
            if prices:
                return prices, 'binance'
        except:
            pass
        
        time.sleep(1)
        
        # API 3: CryptoCompare (backup)
        try:
            url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,SOL&tsyms=USD"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()['RAW']
                for coin in ['BTC', 'ETH', 'SOL']:
                    if coin in data:
                        prices[coin] = (data[coin]['USD']['PRICE'], data[coin]['USD']['CHANGEPCT24HOUR'])
                if prices:
                    return prices, 'cryptocompare'
        except:
            pass
        
        return None, None
    
    def fetch_fear_greed(self):
        """Fetch Fear & Greed"""
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return int(resp.json()['data'][0]['value'])
        except:
            pass
        return 50
    
    def run_all(self):
        """Generate picks based on market data"""
        prices, source = self.fetch_crypto_prices()
        fg = self.fetch_fear_greed()
        
        picks = []
        
        if prices:
            # Strategy: Extreme Fear + Large Drop
            if fg <= 25:
                for coin, (price, change) in prices.items():
                    if change < -5:  # Down more than 5%
                        confidence = min(0.8, 0.65 + abs(change) * 0.01 + (25 - fg) * 0.005)
                        picks.append({
                            'id': f"fear_{coin}_{datetime.now().strftime('%Y%m%d')}",
                            'symbol': coin,
                            'strategy': 'extreme_fear',
                            'direction': 'LONG',
                            'confidence': confidence,
                            'entry_price': price,
                            'tp_price': price * 1.06,
                            'sl_price': price * 0.95,
                            'position_pct': 0.035,
                            'reason': f'Fear & Greed = {fg}, {coin} down {change:.1f}% (source: {source})',
                            'timestamp': datetime.now().isoformat(),
                            'data_source': source
                        })
            
            # Strategy: Momentum Reversal (large drops)
            for coin, (price, change) in prices.items():
                if change < -10:  # Down more than 10%
                    picks.append({
                        'id': f"rev_{coin}_{datetime.now().strftime('%Y%m%d')}",
                        'symbol': coin,
                        'strategy': 'momentum_reversal',
                        'direction': 'LONG',
                        'confidence': min(0.72, 0.6 + abs(change) * 0.01),
                        'entry_price': price,
                        'tp_price': price * 1.05,
                        'sl_price': price * 0.96,
                        'position_pct': 0.03,
                        'reason': f'{coin} down {change:.1f}% in 24h - mean reversion (source: {source})',
                        'timestamp': datetime.now().isoformat(),
                        'data_source': source
                    })
        
        # Fallback if no API worked
        if not picks and fg <= 20:
            picks = self.fallback_picks(fg)
        
        picks.sort(key=lambda x: x['confidence'], reverse=True)
        self.picks = picks[:5]
        return self.picks
    
    def fallback_picks(self, fg):
        """Fallback when APIs fail"""
        return [
            {
                'id': f"fb_btc_{datetime.now().strftime('%Y%m%d')}",
                'symbol': 'BTC',
                'strategy': 'fallback_extreme_fear',
                'direction': 'LONG',
                'confidence': 0.7,
                'entry_price': 64000,
                'tp_price': 69120,
                'sl_price': 60800,
                'position_pct': 0.03,
                'reason': f'Fear & Greed = {fg} (extreme fear). APIs unavailable - verify price before trading.',
                'timestamp': datetime.now().isoformat(),
                'warning': 'FALLBACK MODE - Verify current price'
            },
            {
                'id': f"fb_eth_{datetime.now().strftime('%Y%m%d')}",
                'symbol': 'ETH',
                'strategy': 'fallback_extreme_fear',
                'direction': 'LONG',
                'confidence': 0.68,
                'entry_price': 1800,
                'tp_price': 1944,
                'sl_price': 1710,
                'position_pct': 0.025,
                'reason': f'Fear & Greed = {fg} (extreme fear). APIs unavailable - verify price before trading.',
                'timestamp': datetime.now().isoformat(),
                'warning': 'FALLBACK MODE - Verify current price'
            }
        ]
    
    def save(self):
        """Save to JSON"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'capital_base': CAPITAL_BASE,
            'picks': self.picks,
            'market_data': {
                'fear_greed': self.fetch_fear_greed(),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/picks.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return output

if __name__ == '__main__':
    print("☠️ CLAWS OF DOOM v2 - Multi-API Version")
    print("=" * 50)
    
    system = ClawsSystem()
    picks = system.run_all()
    system.save()
    
    print(f"\nGenerated {len(picks)} picks:\n")
    for p in picks:
        source = p.get('data_source', 'FALLBACK')
        print(f"  {p['symbol']} ({source}):")
        print(f"    Strategy: {p['strategy']}")
        print(f"    Entry: ${p['entry_price']:,.2f}")
        print(f"    Target: ${p['tp_price']:,.2f} (+{((p['tp_price']/p['entry_price']-1)*100):.1f}%)")
        print(f"    Stop: ${p['sl_price']:,.2f} (-{((1-p['sl_price']/p['entry_price'])*100):.1f}%)")
        print(f"    Confidence: {p['confidence']*100:.0f}%")
        if 'warning' in p:
            print(f"    ⚠️  {p['warning']}")
        print()
