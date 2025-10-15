"""
Model Configuration and Constants
Contains all initial notional definitions and hook-related constants
"""

# Initial notional definitions (from fun_KS_class.h)
INIPROD = 1      # initial notional machine productivity
INIWAGE = 1      # initial notional wage
INISKILL = 1     # initial notional worker skills

# Hook-related definitions - number of dynamic hooks per object type
FIRM1HK = 2      # Firm1 hooks
FIRM2HK = 4      # Firm2 hooks
WORKERHK = 2     # Worker hooks

# Dynamic hook name to number
BANK = 0         # from Firm1/Firm2 to Bank
BCLIENT = 1      # from Firm1/Firm2 to Cli1/Cli2 (in Bank)
SUPPL = 2        # from Firm2 to Broch (in Firm2)
TOPVINT = 3      # from Firm2 to Vint (in Firm2)
FWRK = 0         # from Worker to Wkr1/Wrkr2 (in Capital/Firm2)
VWRK = 1         # from Worker to WrkV (in Vint in Firm2)

# Vintage (machine technological generation) data packing/unpacking
def VNT(T0, IDsuppl):
    """Pack vintage data"""
    return 10000 * int(T0) + int(IDsuppl)

def T0(IDvint):
    """Unpack time from vintage ID"""
    return int(IDvint // 10000)

def SUP(IDvint):
    """Unpack supplier ID from vintage ID"""
    return int(IDvint - 10000 * T0(IDvint))

# Utility function for rounding values too close to a reference
def ROUND(V, Ref, Tol):
    """Round values too close to a reference"""
    return V if abs(V - Ref) > Tol else Ref
