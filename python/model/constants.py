"""
Constants and Initial Notional Definitions
Defines constants used throughout the K+S model
"""

# Initial notional definitions
INIPROD = 1.0   # Initial notional machine productivity
INIWAGE = 1.0   # Initial notional wage
INISKILL = 1.0  # Initial notional worker skills

# Hook-related definitions (for object references)
# Number of dynamic hooks per object type
FIRM1HK = 2     # Firm1 hooks
FIRM2HK = 4     # Firm2 hooks
WORKERHK = 2    # Worker hooks

# Dynamic hook names to indices
BANK = 0        # From Firm1/Firm2 to Bank
BCLIENT = 1     # From Firm1/Firm2 to Cli1/Cli2 (in Bank)
SUPPL = 2       # From Firm2 to Broch (in Firm2)
TOPVINT = 3     # From Firm2 to Vint (in Firm2)
FWRK = 0        # From Worker to Wkr1/Wrkr2 (in Capital/Firm2)
VWRK = 1        # From Worker to WrkV (in Vint in Firm2)

# Numerical tolerances
TOL = 1e-6      # General tolerance for comparisons
TOL_ZERO = 1e-10  # Tolerance for zero checks

# Fast mode settings
FASTMODE = 0    # 0=observe, 1=fast, 2=fast_full
