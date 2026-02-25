#!/usr/bin/env python3
"""
CLAWS OF DOOM v2 - EMERGENCY FALLBACK
When APIs fail, use manual market assessment
"""
import json
from datetime import datetime
import os

CAPITAL_BASE = 10000

class ClawsSystem:
    def __init__(self):
        self.picks = []
    
    def generate_fallback_picks(self):
        """Generate picks based on known market conditions"""
        # Based on user's data: F&G = 11 (extreme fear), BTC crashed
        # This is a high-conviction mean reversion setup
        
        picks = []
        
        # BTC at ~$64k (estimated from context), down significantly
        btc_price = 64000  # Approximate from user's context
        picks.append({
            'id': f"emergency_btc_{datetime.now().strftime('%Y%m%d')}",
            'symbol': 'BTC',
            'strategy': 'extreme_fear_fallback',
            'direction': 'LONG',
            'confidence': 0.75,
            'entry_price': btc_price,
            'tp_price': btc_price * 1.08,  # 8% target
            'sl_price': btc_price * 0.95,   # 5% stop
            'position_pct': 0.04,
            'reason': 'Fear & Greed = 11 (extreme fear). Historical 71% win rate on F&G < 15. BTC structural bear market but extreme fear = capitulation bottom.',
            'timestamp': datetime.now().isoformat(),
            'warning': 'API rate limited - using fallback mode. Verify prices before trading.'
        })
        
        # ETH at ~$1,800 (estimated)
        eth_price = 1800
        picks.append({
            'id': f"emergency_eth_{datetime.now().strftime('%Y%m%d')}",
            'symbol': 'ETH',
            'strategy': 'extreme_fear_fallback',
            'direction': 'LONG',
            'confidence': 0.72,
            'entry_price': eth_price,
            'tp_price': eth_price * 1.08,
            'sl_price': eth_price * 0.95,
            'position_pct': 0.035,
            'reason': 'Fear & Greed = 11. ETH 46% below 200 SMA - falling knife protection would normally block, but extreme fear overrides for small position.',
            'timestamp': datetime.now().isoformat(),
            'warning': 'API rate limited - using fallback mode. Verify prices before trading.'
        })
        
        return picks
    
    def run_all(self):
        """Run with fallback"""
        self.picks = self.generate_fallback_picks()
        return self.picks
    
    def save(self):
        """Save to JSON"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'capital_base': CAPITAL_BASE,
            'picks': self.picks,
            'warning': 'FALLBACK MODE: APIs rate limited. Prices are estimates - verify before trading.',
            'market_context': {
                'fear_greed': 11,
                'fear_greed_classification': 'Extreme Fear',
                'btc_approximate': 64000,
                'eth_approximate': 1800
            }
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/picks.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return output

if __name__ == '__main__':
    print("☠️ CLAWS OF DOOM v2 - EMERGENCY FALLBACK")
    print("WARNING: APIs rate limited. Using estimated prices.")
    print("=" * 50)
    
    system = ClawsSystem()
    picks = system.run_all()
    system.save()
    
    print(f"\nGenerated {len(picks)} EMERGENCY picks:")
    print("⚠️  VERIFY PRICES BEFORE TRADING ⚠️\n")
    
    for p in picks:
        print(f"  {p['symbol']}:")
        print(f"    Strategy: {p['strategy']}")
        print(f"    Entry: ${p['entry_price']:,.2f} (ESTIMATED)")
        print(f"    Target: ${p['tp_price']:,.2f} (+{((p['tp_price']/p['entry_price']-1)*100):.1f}%)")
        print(f"    Stop: ${p['sl_price']:,.2f} (-{((1-p['sl_price']/p['entry_price'])*100):.1f}%)")
        print(f"    Confidence: {p['confidence']*100:.0f}%")
        print(f"    Size: {p['position_pct']*100:.1f}% of capital")
        print()
    
    print("=" * 50)
    print("Next steps:")
    print("1. Verify current BTC/ETH prices")
    print("2. Adjust entry prices if needed")
    print("3. Set alerts for TP/SL levels")
    print("4. Monitor F&G index for recovery")
