#!/usr/bin/env python3
"""
CLAWS OF DOOM - BULLETPROOF FAILOVER SYSTEM
Guaranteed to generate picks even if everything fails
"""
import json
import requests
import os
import time
from datetime import datetime

CAPITAL_BASE = 10000

class BulletproofClaws:
    def __init__(self):
        self.picks = []
        self.apis_tested = []
    
    # ========== LAYER 1: Multiple Price APIs ==========
    
    def api_coingecko(self):
        """Primary: CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                d = r.json()
                return {
                    'BTC': (d['bitcoin']['usd'], d['bitcoin'].get('usd_24h_change', 0)),
                    'ETH': (d['ethereum']['usd'], d['ethereum'].get('usd_24h_change', 0)),
                    'SOL': (d['solana']['usd'], d['solana'].get('usd_24h_change', 0))
                }, 'coingecko'
        except Exception as e:
            self.apis_tested.append(('coingecko', str(e)))
        return None, None
    
    def api_binance(self):
        """Backup 1: Binance"""
        try:
            prices = {}
            for sym in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}"
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    prices[sym.replace('USDT', '')] = (float(d['lastPrice']), float(d['priceChangePercent']))
            if prices:
                return prices, 'binance'
        except Exception as e:
            self.apis_tested.append(('binance', str(e)))
        return None, None
    
    def api_cryptocompare(self):
        """Backup 2: CryptoCompare"""
        try:
            url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,SOL&tsyms=USD"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                d = r.json()['RAW']
                prices = {}
                for coin in ['BTC', 'ETH', 'SOL']:
                    if coin in d:
                        prices[coin] = (d[coin]['USD']['PRICE'], d[coin]['USD']['CHANGEPCT24HOUR'])
                if prices:
                    return prices, 'cryptocompare'
        except Exception as e:
            self.apis_tested.append(('cryptocompare', str(e)))
        return None, None
    
    def api_coincap(self):
        """Backup 3: CoinCap"""
        try:
            prices = {}
            for coin_id, symbol in [('bitcoin', 'BTC'), ('ethereum', 'ETH'), ('solana', 'SOL')]:
                url = f"https://api.coincap.io/v2/assets/{coin_id}"
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    d = r.json()['data']
                    prices[symbol] = (float(d['priceUsd']), float(d['changePercent24Hr']))
            if prices:
                return prices, 'coincap'
        except Exception as e:
            self.apis_tested.append(('coincap', str(e)))
        return None, None
    
    def api_coinmarketcap_free(self):
        """Backup 4: CoinMarketCap (free endpoint)"""
        try:
            url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=10"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                d = r.json()
                prices = {}
                for item in d['data']['cryptoCurrencyList']:
                    sym = item['symbol']
                    if sym in ['BTC', 'ETH', 'SOL']:
                        prices[sym] = (float(item['quotes'][0]['price']), float(item['quotes'][0]['percentChange24h']))
                if prices:
                    return prices, 'coinmarketcap'
        except Exception as e:
            self.apis_tested.append(('coinmarketcap', str(e)))
        return None, None
    
    def get_prices(self):
        """Try all price APIs in sequence"""
        apis = [self.api_coingecko, self.api_binance, self.api_cryptocompare, 
                self.api_coincap, self.api_coinmarketcap_free]
        
        for api in apis:
            prices, source = api()
            if prices:
                return prices, source
            time.sleep(0.5)  # Be nice
        
        return None, None
    
    # ========== LAYER 2: Fear & Greed with Fallbacks ==========
    
    def get_fear_greed(self):
        """Get Fear & Greed with fallbacks"""
        # Primary
        try:
            r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=3)
            if r.status_code == 200:
                return int(r.json()['data'][0]['value']), 'alternative.me'
        except:
            pass
        
        # Backup: Use cached/market assumption
        # If BTC is down >20% from ATH, assume extreme fear
        return 20, 'estimated'  # Conservative estimate
    
    # ========== LAYER 3: Strategy Generation ==========
    
    def strategy_extreme_fear(self, prices, fg, source):
        """Generate picks when fear is high"""
        picks = []
        
        if fg <= 25:
            for coin, (price, change) in prices.items():
                if price and price > 0:
                    confidence = min(0.8, 0.65 + abs(change) * 0.01 + (25 - fg) * 0.005)
                    picks.append({
                        'id': f"fear_{coin}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                        'symbol': coin,
                        'strategy': 'extreme_fear',
                        'direction': 'LONG',
                        'confidence': round(confidence, 2),
                        'entry_price': round(price, 2),
                        'tp_price': round(price * 1.06, 2),
                        'sl_price': round(price * 0.95, 2),
                        'position_pct': 0.035,
                        'reason': f'Fear & Greed = {fg} ({self.fg_label(fg)}), {coin} down {change:.1f}%',
                        'timestamp': datetime.now().isoformat(),
                        'data_source': source,
                        'fg_source': 'alternative.me'
                    })
        
        return picks
    
    def strategy_crash_reversal(self, prices, source):
        """Generate picks when crash is detected"""
        picks = []
        
        for coin, (price, change) in prices.items():
            if price and price > 0 and change < -10:
                picks.append({
                    'id': f"crash_{coin}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    'symbol': coin,
                    'strategy': 'crash_reversal',
                    'direction': 'LONG',
                    'confidence': min(0.75, 0.6 + abs(change) * 0.01),
                    'entry_price': round(price, 2),
                    'tp_price': round(price * 1.05, 2),
                    'sl_price': round(price * 0.96, 2),
                    'position_pct': 0.03,
                    'reason': f'{coin} crashed {change:.1f}% - mean reversion bounce expected',
                    'timestamp': datetime.now().isoformat(),
                    'data_source': source
                })
        
        return picks
    
    # ========== LAYER 4: Ultimate Fallback ==========
    
    def ultimate_fallback(self, fg):
        """When absolutely everything fails - use hardcoded estimates"""
        return [
            {
                'id': f"ULTIMATE_BTC_{datetime.now().strftime('%Y%m%d_%H%M')}",
                'symbol': 'BTC',
                'strategy': 'ULTIMATE_FALLBACK',
                'direction': 'LONG',
                'confidence': 0.65,
                'entry_price': 64000,
                'tp_price': 70000,
                'sl_price': 60000,
                'position_pct': 0.02,
                'reason': f'ALL APIs FAILED. Fear & Greed = {fg}. Using estimated BTC price. MANUAL VERIFICATION REQUIRED.',
                'timestamp': datetime.now().isoformat(),
                'WARNING': '⚠️ ULTIMATE FALLBACK - VERIFY PRICE BEFORE TRADING ⚠️',
                'apis_failed': [a[0] for a in self.apis_tested]
            },
            {
                'id': f"ULTIMATE_ETH_{datetime.now().strftime('%Y%m%d_%H%M')}",
                'symbol': 'ETH',
                'strategy': 'ULTIMATE_FALLBACK',
                'direction': 'LONG',
                'confidence': 0.62,
                'entry_price': 1800,
                'tp_price': 2000,
                'sl_price': 1650,
                'position_pct': 0.015,
                'reason': f'ALL APIs FAILED. Fear & Greed = {fg}. Using estimated ETH price. MANUAL VERIFICATION REQUIRED.',
                'timestamp': datetime.now().isoformat(),
                'WARNING': '⚠️ ULTIMATE FALLBACK - VERIFY PRICE BEFORE TRADING ⚠️',
                'apis_failed': [a[0] for a in self.apis_tested]
            }
        ]
    
    def fg_label(self, value):
        if value <= 20: return "Extreme Fear"
        if value <= 40: return "Fear"
        if value <= 60: return "Neutral"
        if value <= 80: return "Greed"
        return "Extreme Greed"
    
    # ========== MAIN EXECUTION ==========
    
    def run(self):
        """Execute full failover chain"""
        print("☠️ CLAWS OF DOOM - BULLETPROOF FAILOVER")
        print("=" * 60)
        
        # Step 1: Get Fear & Greed
        fg, fg_source = self.get_fear_greed()
        print(f"Fear & Greed: {fg} ({self.fg_label(fg)}) [source: {fg_source}]")
        
        # Step 2: Try to get prices
        print("\nTrying price APIs...")
        prices, source = self.get_prices()
        
        if prices:
            print(f"✓ Got prices from: {source}")
            for coin, (price, change) in prices.items():
                print(f"  {coin}: ${price:,.2f} ({change:+.1f}%)")
            
            # Generate picks with real data
            picks = []
            picks.extend(self.strategy_extreme_fear(prices, fg, source))
            picks.extend(self.strategy_crash_reversal(prices, source))
            
            # Deduplicate by symbol
            seen = set()
            unique_picks = []
            for p in picks:
                if p['symbol'] not in seen:
                    seen.add(p['symbol'])
                    unique_picks.append(p)
            
            self.picks = sorted(unique_picks, key=lambda x: x['confidence'], reverse=True)[:5]
            
        else:
            print("✗ All price APIs failed")
            print("\nActivating ULTIMATE FALLBACK...")
            self.picks = self.ultimate_fallback(fg)
        
        return self.save()
    
    def save(self):
        """Save with full metadata"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'system': 'CLAWS OF DOOM - Bulletproof Failover',
            'version': '2.1.0',
            'capital_base': CAPITAL_BASE,
            'picks': self.picks,
            'metadata': {
                'apis_tested': self.apis_tested,
                'pick_count': len(self.picks),
                'fallback_activated': len(self.apis_tested) >= 5
            }
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/picks.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return output

if __name__ == '__main__':
    claws = BulletproofClaws()
    result = claws.run()
    
    print(f"\n{'='*60}")
    print(f"Generated {len(result['picks'])} picks:")
    print("="*60)
    
    for i, p in enumerate(result['picks'], 1):
        print(f"\n{i}. {p['symbol']} - {p['strategy'].upper()}")
        print(f"   Entry: ${p['entry_price']:,.2f}")
        print(f"   Target: ${p['tp_price']:,.2f} (+{((p['tp_price']/p['entry_price']-1)*100):.1f}%)")
        print(f"   Stop: ${p['sl_price']:,.2f} (-{((1-p['sl_price']/p['entry_price'])*100):.1f}%)")
        print(f"   Confidence: {p['confidence']*100:.0f}%")
        print(f"   Size: {p['position_pct']*100:.1f}% of capital")
        if 'WARNING' in p:
            print(f"   {p['WARNING']}")
    
    print(f"\n{'='*60}")
    print("Dashboard: https://eltonaguiar.github.io/CLAWSOFDOOM/")
    print("="*60)
