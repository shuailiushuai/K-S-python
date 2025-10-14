"""
Agent Initialization Functions
Replicates the initialization logic from fun_KS_support.h entry_firm1/entry_firm2
"""

from typing import List, Dict, Any
import math
from .core_utils import get_random_engine, INIPROD, INIWAGE, INISKILL


def compute_initial_conditions(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute initial equilibrium conditions for the economy
    Based on fun_KS_country.h initCountry function
    
    Returns dictionary with initial values for prices, demands, wages, etc.
    """
    # Extract parameters
    m1 = config.get('Capital.m1', 0.1)
    m2 = config.get('Consumption.m2', 1.0)
    mu1 = config.get('Capital.mu1', 0.08)
    mu20 = config.get('Consumption.mu20', 0.25)
    nu = config.get('Capital.nu', 0.04)
    phi = config.get('Labor.phi', 0.4)
    eta = config.get('Consumption.eta', 20.0)
    b = config.get('Consumption.b', 3.0)
    
    Ls0 = config.get('Labor.Ls0', 1000)
    F10 = config.get('Capital.F10', 50)
    F20 = config.get('Consumption.F20', 200)
    
    rT = config.get('Financial.rT', 0.01)
    muD = config.get('Financial.muD', 0.0)
    muDeb = config.get('Financial.muDeb', 0.1)
    muRes = config.get('Financial.muRes', 0.0)
    muBonds = config.get('Financial.muBonds', 0.25)
    
    flag_tax = config.get('flagTax', 1)
    tr = config.get('tr', 0.2) if flag_tax > 0 else 0.0
    gG = config.get('gG', 0.0)
    
    flag_worker_lbu = config.get('flagWorkerLBU', 1)
    sigma = config.get('Labor.sigma', 1.0)
    
    # Calculate initial productivities
    Btau0 = (1 + mu1) * INIPROD / (m1 * m2 * b)
    
    # Calculate initial costs and prices
    c10 = INIWAGE / (Btau0 * m1)
    c20 = INIWAGE / INIPROD
    p10 = (1 + mu1) * c10
    p20 = (1 + mu20) * c20
    
    # Calculate initial capital and demands
    K0 = Ls0 * INIWAGE / p20  # Full employment capital required
    D10 = K0 / (m2 * eta)  # Initial demand for sector 1
    RD0 = nu * D10 * p10  # Initial R&D expense
    
    # Initial demand for sector 2 (from worker wages and firm revenues)
    D20 = ((D10 * c10 + RD0) * (1 - phi - tr) + Ls0 * INIWAGE * phi) / (mu20 + phi + tr) * c20
    
    # Initial labor demands
    Ld10 = RD0 / INIWAGE + D10 / (Btau0 * m1)
    Ld20 = D20 / INIPROD
    
    # Initial productivity
    A0 = (D10 * p10 + D20 * p20) / (Ld10 + Ld20)
    
    # Initial competitiveness (average of omega1, omega2, omega3)
    omega1 = config.get('Consumption.omega1', 1.0)
    omega2 = config.get('Consumption.omega2', 1.0)
    omega3 = config.get('Consumption.omega3', 1.0)
    Eavg0 = (omega1 + omega2 + omega3) / 3
    
    # Initial interest rates
    rBonds = rT * (1 - muBonds)
    rD = rT * (1 - muD)
    rDeb = rT * (1 + muDeb)
    rRes = rT * (1 - muRes)
    
    # Initial government spending
    G0 = gG * Ls0
    
    # Initial vintage skills
    if flag_worker_lbu == 0 or flag_worker_lbu == 2:
        sV0 = INISKILL
    else:
        sV0 = sigma
    
    # Initial reservation wage
    wRes = phi * INIWAGE
    
    return {
        'Btau0': Btau0,
        'c10': c10,
        'c20': c20,
        'p10': p10,
        'p20': p20,
        'K0': K0,
        'D10': D10,
        'D20': D20,
        'RD0': RD0,
        'Ld10': Ld10,
        'Ld20': Ld20,
        'A0': A0,
        'Eavg0': Eavg0,
        'rBonds': rBonds,
        'rD': rD,
        'rDeb': rDeb,
        'rRes': rRes,
        'G0': G0,
        'sV0': sV0,
        'wRes': wRes,
        'w_avg': INIWAGE
    }


def initialize_firm1(firm, firm_num: int, total_firms: int, config: Dict[str, Any], 
                     init_cond: Dict[str, float], new_industry: bool = True):
    """
    Initialize a Firm1 (capital-good firm) agent
    Based on entry_firm1 function in fun_KS_support.h
    
    Args:
        firm: Firm1 agent object to initialize
        firm_num: Firm number (1-indexed)
        total_firms: Total number of firms
        config: Configuration dictionary
        init_cond: Initial conditions from compute_initial_conditions
        new_industry: True for initial setup, False for entrants
    """
    rng = get_random_engine()
    
    # Parameters
    Deb10ratio = config.get('Capital.Deb10ratio', 2.0)
    NW10 = config.get('Capital.NW10', 1.0)
    Phi3 = config.get('Capital.Phi3', 0.5)
    Phi4 = config.get('Capital.Phi4', 1.5)
    mu1 = config.get('Capital.mu1', 0.08)
    m1 = config.get('Capital.m1', 0.1)
    m2 = config.get('Consumption.m2', 1.0)
    nu = config.get('Capital.nu', 0.04)
    eta = config.get('Consumption.eta', 20.0)
    F20 = config.get('Consumption.F20', 200)
    Ls0 = config.get('Labor.Ls0', 1000)
    
    if new_industry:
        # Initial productivities
        firm._Atau = INIPROD
        firm._Btau = init_cond['Btau0']
        
        # Fair market share
        firm._f1 = 1.0 / total_firms
        
        # Initial vintage skills
        firm._sV = init_cond['sV0']
        
        # Entry time (before t=1)
        firm._t1ent = 0
        
        # Initial average wage
        w1avg = INIWAGE
        
        # Initial demand expectation (fair share of sector 2 demand)
        # Each Firm2 needs K0 capital, with 1/eta replacement factor per period
        p20 = init_cond['p20']
        K0_per_firm2 = math.ceil(Ls0 * w1avg / p20 / F20 / m2) * m2
        firm._D1 = F20 * K0_per_firm2 / m2 / eta / total_firms
        
    else:
        # Not implemented for entrants yet - would need firm stats
        raise NotImplementedError("Firm1 entry not yet implemented")
    
    # Initial cost, price and R&D
    mult = 1.0 if new_industry else rng.uniform(Phi3, Phi4)
    firm._c1 = w1avg / (firm._Btau * m1)
    firm._p1 = (1 + mu1) * firm._c1
    firm._RD = max(nu * firm._D1 * firm._p1, w1avg)
    firm._L1rd = math.floor(firm._RD / w1avg)
    
    # Initial net worth and financing
    firm._NW1 = mult * NW10
    firm._Deb1 = firm._NW1 * Deb10ratio
    firm._Eq1 = firm._NW1 * (1 - Deb10ratio)
    
    # Initial quality class (for statistics)
    firm._qc1 = 4
    
    # Set initial sales to match demand (firms start with backlog)
    firm._S1 = firm._D1
    firm._N1 = 0.0  # No initial inventory
    
    # Initial production equals sales
    firm._Q1 = firm._S1
    firm._Q1e = firm._S1
    
    # Compute initial labor demand
    firm._L1d = math.ceil(firm._RD / w1avg) + math.ceil(firm._D1 / (firm._Btau * m1))
    firm._L1 = firm._L1d  # Initially fully staffed
    
    # Initialize history
    if hasattr(firm, 'history'):
        firm.history['f1'].append(firm._f1)
        firm.history['Atau'].append(firm._Atau)
        firm.history['p1'].append(firm._p1)
        firm.history['Pi1'].append(0.0)


def initialize_firm2(firm, firm_num: int, total_firms: int, config: Dict[str, Any],
                     init_cond: Dict[str, float], new_industry: bool = True):
    """
    Initialize a Firm2 (consumption-good firm) agent
    Based on entry_firm2 function in fun_KS_support.h
    
    Args:
        firm: Firm2 agent object to initialize
        firm_num: Firm number (1-indexed)
        total_firms: Total number of firms
        config: Configuration dictionary
        init_cond: Initial conditions from compute_initial_conditions
        new_industry: True for initial setup, False for entrants
    """
    rng = get_random_engine()
    
    # Parameters
    Deb20ratio = config.get('Consumption.Deb20ratio', 2.0)
    NW20 = config.get('Consumption.NW20', 1.0)
    Phi1 = config.get('Consumption.Phi1', 0.1)
    Phi2 = config.get('Consumption.Phi2', 0.9)
    iota = config.get('Consumption.iota', 0.1)
    mu20 = config.get('Consumption.mu20', 0.25)
    m2 = config.get('Consumption.m2', 1.0)
    u = config.get('Consumption.u', 0.75)
    Ls0 = config.get('Labor.Ls0', 1000)
    
    if new_industry:
        # Initial demand (fair share)
        firm._D2 = init_cond['D20'] / total_firms
        firm._D2d = firm._D2
        firm._D2e = firm._D2
        
        # Initial competitiveness
        firm._E = init_cond['Eavg0']
        
        # Initial capital (full employment capital per firm)
        p20 = init_cond['p20']
        firm._K = math.ceil(Ls0 * INIWAGE / p20 / total_firms / m2) * m2
        
        # Initial inventories
        firm._N = iota * firm._D2
        
        # Initial net worth
        firm._NW2 = NW20
        
        # Initial capacity utilization
        firm._Q2u = 1.0
        
        # Fair market share
        firm._f2 = 1.0 / total_firms
        
        # Life cycle stage (3 = incumbent)
        firm._life2cycle = 3
        
        # Initial quality
        firm._q2 = 1.0
        
        # Entry time
        firm._t2ent = 0
        
        # Post-change flag (all pre-change initially)
        firm._postChg = False
        
        # Initial wages
        w2avg = INIWAGE
        firm._w2avg = w2avg
        firm._w2o = w2avg
        
    else:
        # Not implemented for entrants yet
        raise NotImplementedError("Firm2 entry not yet implemented")
    
    # Initial productivity (from supplier technology)
    if hasattr(firm, 'supplier') and firm.supplier is not None:
        firm._A2 = firm.supplier._Atau
    else:
        firm._A2 = INIPROD
    
    # Initial unit costs and price
    firm._c2 = w2avg / firm._A2
    firm._p2 = (1 + mu20) * firm._c2
    
    # Initial free cash (for 1 period production + inventories)
    firm._NW2f = max((1 + iota) * firm._D2 * firm._c2, NW20)
    
    # Add capital cost for initial capital stock
    if hasattr(firm, 'supplier') and firm.supplier is not None:
        p1 = firm.supplier._p1
    else:
        p1 = init_cond['p10']
    
    firm._NW2 = p1 * firm._K / m2 + firm._NW2f if not new_industry else firm._NW2f
    
    # Initial debt and equity
    firm._Deb2 = firm._NW2 * Deb20ratio
    firm._Eq2 = firm._NW2 * (1 - Deb20ratio)
    
    # Initial markup
    firm._mu2 = mu20
    
    # Initial compound skills
    firm._s2avg = init_cond['sV0']
    firm._sT2min = INISKILL
    
    # Quality class
    firm._qc2 = 4
    
    # Set initial sales to match demand
    firm._S2 = firm._D2
    
    # Initial production
    firm._Q2 = firm._D2 + firm._N  # Production includes inventory buildup
    firm._Q2e = firm._Q2
    
    # Compute initial labor demand (production / labor productivity)
    firm._L2d = math.ceil(firm._Q2 / firm._A2)
    firm._L2 = firm._L2d  # Initially fully staffed
    
    # Initialize history
    if hasattr(firm, 'history'):
        firm.history['f2'].append(firm._f2)
        firm.history['A2'].append(firm._A2)
        firm.history['p2'].append(firm._p2)
        firm.history['Pi2'].append(0.0)


def initialize_worker(worker, worker_num: int, config: Dict[str, Any],
                      init_cond: Dict[str, float]):
    """
    Initialize a Worker agent
    Based on worker initialization in fun_KS_country.h initCountry
    
    Args:
        worker: Worker agent object to initialize
        worker_num: Worker number (1-indexed)
        config: Configuration dictionary
        init_cond: Initial conditions
    """
    rng = get_random_engine()
    
    # Parameters
    Tc = config.get('Labor.Tc', 1)
    Tr = config.get('Labor.Tr', 0)
    
    # Draw worker age uniformly in [1, Tr]
    worker._age = rng.uniform_int(1, max(Tr, 1))
    
    # Contract term
    worker._Tc = Tc
    
    # Initial reservation wage
    worker._wRes = init_cond['wRes']
    
    # Initially unemployed
    worker._employed = 0
    
    # Initial skills
    worker._sT = INISKILL  # Tenure skills (learning-by-doing)
    worker._sV = init_cond['sV0']  # Vintage skills (learning-by-using)
    worker._s = worker._sT * worker._sV  # Compound skills
    
    # Initialize wage to reservation wage
    worker._w = init_cond['wRes']


def initialize_bank(bank, bank_num: int, total_banks: int, config: Dict[str, Any],
                    init_cond: Dict[str, float]):
    """
    Initialize a Bank agent
    Based on bank initialization in fun_KS_country.h initCountry
    
    Args:
        bank: Bank agent object to initialize
        bank_num: Bank number (1-indexed)
        total_banks: Total number of banks
        config: Configuration dictionary
        init_cond: Initial conditions
    """
    rng = get_random_engine()
    
    # Bank ID
    bank._IDb = bank_num
    
    # Initial desired market share (will be set based on client distribution)
    # For now, equal shares
    bank._fD = 1.0 / total_banks
    
    # Initial equity (will be set based on required capital adequacy)
    EqB0 = config.get('Financial.EqB0', 10.0)
    bank._EqB = EqB0
    
    # Initial deposits, loans, reserves (will be computed from firms)
    bank._DepB = 0.0
    bank._LoanB = 0.0
    bank._ResB = 0.0
    
    # Bad debt
    bank._BadDebB = 0.0
    
    # Profits
    bank._PiB = 0.0
