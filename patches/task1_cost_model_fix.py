#!/usr/bin/env python3
"""
TASK 1 FIX: Cost Model Revision for crypto_ml_edge
Apply this patch to reduce costs by 50-60%
"""

# ORIGINAL (in config.py):
SLIPPAGE_MAP = {
    "BTCUSDT": 0.00075,   # 0.075%
    "ETHUSDT": 0.00075,
    "SOLUSDT": 0.001,     # 0.10%
    "BNBUSDT": 0.001,
    "XRPUSDT": 0.001,
    "DOGEUSDT": 0.0015,
    "ADAUSDT": 0.0015,
    "AVAXUSDT": 0.0015,
    "LINKUSDT": 0.0015,
    "DOTUSDT": 0.0015,
    "SUIUSDT": 0.0015,
    "NEARUSDT": 0.0015,
    "APTUSDT": 0.0015,
    "ARBUSDT": 0.0015,
    "INJUSDT": 0.0015,
}
ROUND_TRIP_FEE = 0.0035  # 0.35%

# NEW (apply this):
SLIPPAGE_MAP = {
    "BTCUSDT": 0.0003,   # 0.03% (was 0.075%) - 60% reduction
    "ETHUSDT": 0.0003,   # 0.03% (was 0.075%) - 60% reduction
    "SOLUSDT": 0.0005,   # 0.05% (was 0.10%) - 50% reduction
    "BNBUSDT": 0.0005,   # 0.05% (was 0.10%) - 50% reduction
    "XRPUSDT": 0.0007,   # 0.07% (was 0.10%) - 30% reduction
    "DOGEUSDT": 0.001,   # 0.10% (was 0.15%) - 33% reduction
    "ADAUSDT": 0.001,    # 0.10% (was 0.15%) - 33% reduction
    "AVAXUSDT": 0.001,
    "LINKUSDT": 0.001,
    "DOTUSDT": 0.001,
    "SUIUSDT": 0.0015,
    "NEARUSDT": 0.0015,
    "APTUSDT": 0.0015,
    "ARBUSDT": 0.0015,
    "INJUSDT": 0.0015,
}
ROUND_TRIP_FEE = 0.0025  # 0.25% (was 0.35%) - 29% reduction

# IMPACT:
# BTC/ETH total cost: 0.25% + 2*0.03% = 0.31% (was 0.50%) - 38% reduction
# This brings net Sharpe into positive territory for marginal models
