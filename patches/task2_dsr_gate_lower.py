#!/usr/bin/env python3
"""
TASK 2 FIX: DSR Gate Lowering for Experimental Phase
Apply this to config.py
"""

# ORIGINAL:
MIN_DSR_PROBABILITY = 0.95  # Strict gate - 0 models pass

# NEW - Two-tier system:
MIN_DSR_PROBABILITY = 0.75  # Experimental phase - let marginal models trade
MIN_DSR_PRODUCTION = 0.95   # Keep strict for final deployment

# In validation.py, modify the gate logic:
"""
if dsr_probability >= MIN_DSR_PROBABILITY:
    verdict = "PASS"
    if dsr_probability >= MIN_DSR_PRODUCTION:
        tier = "PRODUCTION"
    else:
        tier = "EXPERIMENTAL"  # Trade with reduced size
else:
    verdict = "FAIL"
"""

# Position sizing based on tier:
# PRODUCTION: Full size (5% per trade)
# EXPERIMENTAL: Half size (2.5% per trade)
