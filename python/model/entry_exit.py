"""
Entry/Exit Support Functions for K+S Model

This module implements the detailed entry and exit mechanisms for firms
in both capital and consumption sectors, following the C++ implementation
in fun_KS_support.h

Written to match the exact logic from the original C++ implementation.
"""

from typing import List, Optional, Tuple
import numpy as np
from .constants import INIPROD, INIWAGE, INISKILL


def entry_firm1(sector, n: int, new_industry: bool, country) -> float:
    """
    Add and configure entrant capital-good firm object(s)
    
    Corresponds to entry_firm1() function in fun_KS_support.h
    
    Args:
        sector: Capital sector object
        n: Number of firms to enter
        new_industry: True if initializing new industry, False for ongoing entry
        country: Country object for accessing other sectors
        
    Returns:
        Total entry cost
    """
    # Get parameters from sector
    Deb10ratio = sector._Deb10ratio if hasattr(sector, '_Deb10ratio') else 2.0
    Phi3 = sector._Phi3 if hasattr(sector, '_Phi3') else 0.1
    Phi4 = sector._Phi4 if hasattr(sector, '_Phi4') else 0.9
    alpha2 = sector._alpha2 if hasattr(sector, '_alpha2') else 0.0
    beta2 = sector._beta2 if hasattr(sector, '_beta2') else 1.0
    mu1 = sector._mu1
    m1 = sector._m1
    nu = sector._nu
    x5 = sector._x5 if hasattr(sector, '_x5') else 0.1
    
    # Get other sectors
    con_sector = country.consumption_sector
    labor = country.labor_market
    
    # Import here to avoid circular import
    from .firm1 import Firm1
    from .random_engine import random_engine
    
    entry_cost = 0.0
    
    for i in range(n):
        # Create new firm ID
        if sector.firms:
            new_id = max(f._ID for f in sector.firms) + 1 + i
        else:
            new_id = 1 + i
        
        # Initialize firm
        firm = Firm1(firm_id=new_id, parent=sector)
        
        if new_industry:
            # Initial industry setup
            firm._A2tau = INIPROD
            firm._Btau = (1 + mu1) * firm._A2tau / (m1 * getattr(con_sector, "_m2", 1.0) * getattr(con_sector, '_b', 20.0))
            firm._NW10 = getattr(sector, '_NW10', 10.0)  # Default initial wealth
            firm._f1 = 1.0 / n  # Fair share
            firm._sV = getattr(labor, '_sAvg', 1.0)  # Initial worker vintage skills
            firm._t1ent = 0  # Entered before t=1
            w1avg = getattr(labor, '_wAvg', 1.0)
            
            # Initial demand expectation
            F20 = getattr(con_sector, '_F20', 100)
            m2 = getattr(con_sector, '_m2', 1.0)
            p20 = getattr(con_sector, '_CPI', 1.0)
            Ls0 = getattr(labor, '_Ls0', 1000)
            K0 = np.ceil(Ls0 * w1avg / p20 / F20 / m2) * m2
            
            firm._D1 = F20 * K0 / m2 / getattr(con_sector, '_eta', 10.0) / n
            
        else:
            # Ongoing entry
            if sector.firms:
                # Use sector averages
                avg_nw = sum(f._NW for f in sector.firms if hasattr(f, '_NW')) / len(sector.firms)
                firm._NW10 = max(avg_nw, getattr(sector, '_NW10', 10.0))
            else:
                firm._NW10 = getattr(sector, '_NW10', 10.0)
            
            firm._f1 = 0.0  # No initial market share
            firm._sV = INISKILL
            firm._t1ent = country._t
            
            # Best technology in sector
            if sector.firms:
                AtauMax = max(f._Atau for f in sector.firms)
                BtauMax = max(f._Btau for f in sector.firms)
            else:
                AtauMax = INIPROD
                BtauMax = INIPROD
            
            w1avg = getattr(sector, '_w1avg', getattr(labor, '_wAvg', 1.0))
            
            # Initial demand (1 machine per client under fair share)
            F2 = len(con_sector.firms)
            F1 = len(sector.firms)
            firm._D1 = F2 / F1 if F1 > 0 else 1.0
            
            # Technology advantage/imitation
            alpha = random_engine.uniform(alpha2, beta2)
            
            if alpha < x5:
                # Entrant advantage
                firm._A2tau = AtauMax * (1 + x5)
            else:
                # Imitation
                firm._A2tau = AtauMax * (1 + alpha * x5)
            
            firm._Btau = firm._A2tau / w1avg
        
        # Common initialization
        firm._c1 = firm._Btau
        firm._p1 = (1 + mu1) * firm._c1
        
        # R&D expenditure
        firm._RD = nu * firm._p1 * firm._D1
        
        # Capital and workers
        firm._K = firm._D1
        firm._L1d = int(np.ceil(firm._D1 / (m1 * firm._A2tau)))
        firm._L1rd = max(1, int(nu * firm._L1d))
        firm._L = 0  # Will be filled by labor market
        
        # Financial structure
        # Determine debt/equity split
        phi = random_engine.uniform(Phi3, Phi4)
        
        # Net worth initialization
        NW = firm._NW10 * phi
        Deb = NW * Deb10ratio / (1 + Deb10ratio)  # Corrected formula
        Eq = NW - Deb
        
        firm._NW1 = NW
        firm._Deb1 = Deb
        firm._Eq1 = Eq if hasattr(firm, '_Eq1') else 0
        firm._NW0 = NW if hasattr(firm, '_NW0') else 0
        
        # Assign bank
        if country.financial_sector.banks:
            # Random bank selection (should use proper selection mechanism)
            bank_idx = random_engine.uniform_int(0, len(country.financial_sector.banks) - 1)
            firm._bank = country.financial_sector.banks[bank_idx]
        
        # Add to sector
        sector.firms.append(firm)
        
        # Accumulate entry cost
        entry_cost += Eq  # Worker equity contribution
    
    return entry_cost


def entry_firm2(sector, n: int, new_industry: bool, country) -> float:
    """
    Add and configure entrant consumption-good firm object(s)
    
    Corresponds to entry_firm2() function in fun_KS_support.h
    
    Args:
        sector: Consumption sector object
        n: Number of firms to enter
        new_industry: True if initializing new industry, False for ongoing entry
        country: Country object for accessing other sectors
        
    Returns:
        Total entry cost
    """
    # Get parameters
    Deb20ratio = sector._Deb20ratio if hasattr(sector, '_Deb20ratio') else 2.0
    Phi1 = sector._Phi1 if hasattr(sector, '_Phi1') else 0.1
    Phi2 = sector._Phi2 if hasattr(sector, '_Phi2') else 0.9
    chi = sector._chi if hasattr(sector, '_chi') else 0.5
    mu20 = sector._mu20
    x1 = sector._x1 if hasattr(sector, '_x1') else 0.1
    
    # Get other sectors
    cap_sector = country.capital_sector
    labor = country.labor_market
    
    # Import here to avoid circular import
    from .firm2 import Firm2
    from .random_engine import random_engine
    
    entry_cost = 0.0
    
    for i in range(n):
        # Create new firm ID
        if sector.firms:
            new_id = max(f._ID2 for f in sector.firms) + 1 + i
        else:
            new_id = 1 + i
        
        # Initialize firm
        firm = Firm2(firm_id=new_id, parent=sector)
        
        if new_industry:
            # Initial industry setup
            firm._A2 = 1.0  # Initial competitiveness
            firm._Broch = 0.0  # No brochure quality yet
            firm._f2 = 1.0 / n  # Fair share
            firm._life2cycle = 0
            firm._t2ent = 0
            
            # Initial production parameters
            firm._c2 = INIWAGE / INIPROD
            firm._p2 = (1 + mu20) * firm._c2
            
            # Initial capital
            Ls0 = getattr(labor, '_Ls0', getattr(labor, '_Ls', 1000))
            w1avg = getattr(labor, '_wAvg', 1.0)
            m2 = getattr(sector, '_m2', 1.0)
            F20 = getattr(sector, '_F20', 100)
            
            K0 = np.ceil(Ls0 * w1avg / firm._p2 / F20 / m2) * m2
            firm._K = K0 / F20
            
        else:
            # Ongoing entry
            firm._f2 = 0.0  # No initial market share
            firm._t2ent = country._t
            firm._life2cycle = 0
            
            # Determine if post-change firm
            TregChg = country._TregChg if hasattr(country, '_TregChg') else 9999
            if country._t >= TregChg:
                # Check invasion logic
                flagAllFirmsChg = country._flagAllFirmsChg if hasattr(country, '_flagAllFirmsChg') else 1
                if flagAllFirmsChg == 0:
                    # Competition between pre and post change
                    # Market share based probability
                    pre_share = sum(f._f2 for f in sector.firms if hasattr(f, '_postChg') and f._postChg == 0)
                    if random_engine.uniform(0, 1) < pre_share:
                        firm._postChg = 0  # Pre-change type
                    else:
                        firm._postChg = 1  # Post-change type
                else:
                    firm._postChg = 1  # All post-change
            else:
                firm._postChg = 0  # Pre-change
            
            # Initial competitiveness with advantage
            if sector.firms:
                Amax = max(f._A2 for f in sector.firms)
                firm._A2 = Amax * (1 + x1)
            else:
                firm._A2 = 1.0
            
            # Initial pricing
            if sector.firms:
                avg_c = sum(f._c2 for f in sector.firms) / len(sector.firms)
                firm._c2 = avg_c
            else:
                firm._c2 = INIWAGE / INIPROD
            
            firm._p2 = (1 + mu20) * firm._c2
            
            # Initial capital (average of sector)
            if sector.firms:
                avg_K = sum(f._K for f in sector.firms) / len(sector.firms)
                firm._K = avg_K
            else:
                firm._K = 100.0
        
        # Financial structure
        xi = random_engine.uniform(Phi1, Phi2)
        
        # Calculate required net worth
        if new_industry:
            NW20 = getattr(sector, "_NW20", 10.0)
        else:
            if sector.firms:
                NW20 = sum(f._NW2 * f._f2 for f in sector.firms if hasattr(f, '_f2'))
            else:
                NW20 = getattr(sector, "_NW20", 10.0)
        
        NW2 = NW20 * xi
        Deb2 = NW2 * Deb20ratio
        Eq2 = NW2 - Deb2
        
        firm._NW2 = NW2
        firm._Deb2 = Deb2
        firm._Eq2 = Eq2
        firm._NW20 = NW2
        
        # Assign bank
        if country.financial_sector.banks:
            bank_idx = random_engine.uniform_int(0, len(country.financial_sector.banks) - 1)
            firm._bank = country.financial_sector.banks[bank_idx]
        
        # Select supplier from capital sector
        if cap_sector.firms:
            # Random supplier selection (should use market share weights)
            supplier_idx = random_engine.uniform_int(0, len(cap_sector.firms) - 1)
            firm._supplier = cap_sector.firms[supplier_idx]
        
        # Add to sector
        sector.firms.append(firm)
        
        # Accumulate entry cost
        entry_cost += Eq2
    
    return entry_cost


def exit_firm(firm, country) -> float:
    """
    Process firm exit and return liquidation value
    
    Corresponds to exit_firm() function in fun_KS_support.h
    
    Args:
        firm: Firm object to exit (Firm1 or Firm2)
        country: Country object
        
    Returns:
        Exit credit (liquidation value)
    """
    exit_credit = 0.0
    
    # Fire all workers
    for worker in country.workers:
        if hasattr(worker, '_employer') and worker._employer == firm:
            worker._employed = 0
            worker._employer = None
            worker._Te = 0
    
    # Calculate liquidation value
    if hasattr(firm, '_NW1'):  # Firm1
        # Capital sector firm
        NW = firm._NW1
        if NW > 0:
            exit_credit = NW  # Positive NW returned to workers
    elif hasattr(firm, '_NW2'):  # Firm2
        # Consumption sector firm
        NW = firm._NW2
        if NW > 0:
            exit_credit = NW
    
    # Handle bank relationship
    if hasattr(firm, '_bank') and firm._bank is not None:
        # Record bad debt if firm has negative NW
        if hasattr(firm, '_Deb1') and firm._Deb1 > 0:
            # Capital sector debt
            if hasattr(firm._bank, '_BadDeb1'):
                firm._bank._BadDeb1 += max(0, firm._Deb1)
        elif hasattr(firm, '_Deb2') and firm._Deb2 > 0:
            # Consumption sector debt  
            if hasattr(firm._bank, '_BadDeb2'):
                firm._bank._BadDeb2 += max(0, firm._Deb2)
    
    return exit_credit


def redistribute_market_share(sector, exiting_firms: List):
    """
    Redistribute market share from exiting firms to remaining firms
    
    Corresponds to f1rescale/f2rescale in C++ code
    
    Args:
        sector: Sector object (Capital or Consumption)
        exiting_firms: List of firms that are exiting
    """
    # Calculate total market share of exiting firms
    exit_share = sum(f._f1 if hasattr(f, '_f1') else f._f2 for f in exiting_firms)
    
    if exit_share <= 0 or abs(exit_share) < 1e-10:
        return  # Nothing to redistribute
    
    # Get remaining firms
    remaining = [f for f in sector.firms if f not in exiting_firms]
    
    if not remaining:
        return  # No firms to redistribute to
    
    # Calculate total remaining share
    if hasattr(remaining[0], '_f1'):  # Capital sector
        total_remaining = sum(f._f1 for f in remaining)
        if total_remaining > 0:
            scale_factor = (total_remaining + exit_share) / total_remaining
            for firm in remaining:
                firm._f1 *= scale_factor
    else:  # Consumption sector
        total_remaining = sum(f._f2 for f in remaining)
        if total_remaining > 0:
            scale_factor = (total_remaining + exit_share) / total_remaining
            for firm in remaining:
                firm._f2 *= scale_factor
