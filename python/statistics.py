"""
Statistics and Aggregation Functions
Computes macro and sectoral statistics for the K+S model.
Based on fun_KS_stats.h
"""

from typing import Dict, List, Any
from .agents import BaseAgent
from .config import *
import math


def compute_sectoral_statistics(sector: BaseAgent, sector_name: str) -> Dict[str, float]:
    """
    Compute statistics for a sector.
    
    Args:
        sector: Sector agent (Capital or Consumption)
        sector_name: "Firm1" or "Firm2"
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    firms = sector.get_children(sector_name)
    n_firms = len(firms)
    
    if n_firms == 0:
        return stats
    
    # Market shares
    market_shares = [firm.V("_f1" if sector_name == "Firm1" else "_f2") 
                    for firm in firms]
    
    # Herfindahl-Hirschman Index (HHI)
    HH = sum(f * f for f in market_shares)
    stats[f'HH{sector_name[-1]}'] = HH
    
    # Average firm age
    ages = [firm.V("_life1cycle" if sector_name == "Firm1" else "_life2cycle") 
            for firm in firms]
    stats[f'age{sector_name[-1]}avg'] = sum(ages) / n_firms if n_firms > 0 else 0.0
    
    # Average net worth
    if sector_name == "Firm1":
        NW_avg = sum(firm.V("_NW1") for firm in firms) / n_firms
        stats['NW1avg'] = NW_avg
    else:
        NW_avg = sum(firm.V("_NW2") for firm in firms) / n_firms
        stats['NW2avg'] = NW_avg
    
    return stats


def compute_labor_statistics(labor_sector: BaseAgent) -> Dict[str, float]:
    """
    Compute labor market statistics.
    Based on fun_KS_labor.h and fun_KS_stats.h
    
    Args:
        labor_sector: Labor supply sector
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    workers = labor_sector.get_children("Worker")
    n_workers = len(workers)
    
    if n_workers == 0:
        return stats
    
    # Skills statistics
    skills = [worker.V("_s") for worker in workers]
    skills_V = [worker.V("_sV") for worker in workers]
    skills_T = [worker.V("_sT") for worker in workers]
    
    stats['sAvg'] = sum(skills) / n_workers
    stats['sVavg'] = sum(skills_V) / n_workers
    stats['sTavg'] = sum(skills_T) / n_workers
    
    # Skill standard deviations
    if n_workers > 1:
        s_mean = stats['sAvg']
        sV_mean = stats['sVavg']
        sT_mean = stats['sTavg']
        
        stats['sSD'] = math.sqrt(sum((s - s_mean)**2 for s in skills) / (n_workers - 1))
        stats['sVsd'] = math.sqrt(sum((s - sV_mean)**2 for s in skills_V) / (n_workers - 1))
        stats['sTsd'] = math.sqrt(sum((s - sT_mean)**2 for s in skills_T) / (n_workers - 1))
    
    # Min/max skills
    stats['sMax'] = max(skills) if skills else 0.0
    stats['sMin'] = min(skills) if skills else 0.0
    stats['sTmax'] = max(skills_T) if skills_T else 0.0
    stats['sTmin'] = min(skills_T) if skills_T else 0.0
    
    # Wage statistics (employed workers only)
    employed_workers = [w for w in workers if w.V("_employed") > 0]
    if employed_workers:
        wages = [w.V("_w") for w in employed_workers]
        stats['wAvg'] = sum(wages) / len(employed_workers)
        stats['wMax'] = max(wages)
        stats['wMin'] = min(wages)
        
        if len(employed_workers) > 1:
            w_mean = stats['wAvg']
            stats['wSD'] = math.sqrt(sum((w - w_mean)**2 for w in wages) / (len(employed_workers) - 1))
    
    # Employment tenure
    employed_tenures = [w.V("_Te") for w in employed_workers if hasattr(w, '_Te')]
    if employed_tenures:
        stats['TeAvg'] = sum(employed_tenures) / len(employed_tenures)
    
    return stats


def compute_financial_statistics(financial_sector: BaseAgent) -> Dict[str, float]:
    """
    Compute financial sector statistics.
    Based on fun_KS_financial.h and fun_KS_stats.h
    
    Args:
        financial_sector: Financial sector
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    banks = financial_sector.get_children("Bank")
    n_banks = len(banks)
    
    if n_banks == 0:
        return stats
    
    # Total loans
    total_loans = sum(bank.V("_Loans") for bank in banks)
    stats['Loans'] = total_loans
    
    # Total deposits
    total_depo = sum(bank.V("_Depo") for bank in banks)
    stats['Depo'] = total_depo
    
    # Total bank net worth
    total_NWb = sum(bank.V("_NWb") for bank in banks)
    stats['NWb'] = total_NWb
    
    # Bad debt
    total_bad_debt = sum(bank.V("_BadDeb1") + bank.V("_BadDeb2") 
                        for bank in banks)
    stats['BadDeb'] = total_bad_debt
    
    # Bank fragility
    if n_banks > 0:
        avg_fragility = sum(bank.V("_Bda") for bank in banks) / n_banks
        stats['Bda'] = avg_fragility
    
    # Number of bank failures
    bank_failures = sum(1 for bank in banks if bank.V("_NWb") <= 0)
    stats['Bfail'] = bank_failures
    
    # Herfindahl index for banking
    if total_depo > 0:
        bank_shares = [bank.V("_Depo") / total_depo for bank in banks]
        HHb = sum(f * f for f in bank_shares)
        stats['HHb'] = HHb
    
    return stats


def compute_credit_statistics(capital_sector: BaseAgent, 
                              consumption_sector: BaseAgent) -> Dict[str, float]:
    """
    Compute credit demand and supply statistics.
    Based on fun_KS_stats.h
    
    Args:
        capital_sector: Capital sector
        consumption_sector: Consumption sector
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    # Sector 1 credit
    firms1 = capital_sector.get_children("Firm1")
    if firms1:
        CD1 = sum(firm.V("_CD1") for firm in firms1)
        CD1c = sum(firm.V("_CD1c") for firm in firms1)
        CS1 = sum(firm.V("_CS1") for firm in firms1)
        Deb1max = sum(firm.V("_Deb1max") for firm in firms1)
        
        stats['CD1'] = CD1
        stats['CD1c'] = CD1c
        stats['CS1'] = CS1
        stats['Deb1max'] = Deb1max
    
    # Sector 2 credit
    firms2 = consumption_sector.get_children("Firm2")
    if firms2:
        CD2 = sum(firm.V("_CD2") for firm in firms2)
        CD2c = sum(firm.V("_CD2c") for firm in firms2)
        CS2 = sum(firm.V("_CS2") for firm in firms2)
        Deb2max = sum(firm.V("_Deb2max") for firm in firms2)
        
        stats['CD2'] = CD2
        stats['CD2c'] = CD2c
        stats['CS2'] = CS2
        stats['Deb2max'] = Deb2max
    
    # Total credit
    stats['CD'] = stats.get('CD1', 0) + stats.get('CD2', 0)
    stats['CDc'] = stats.get('CD1c', 0) + stats.get('CD2c', 0)
    stats['CS'] = stats.get('CS1', 0) + stats.get('CS2', 0)
    
    return stats


def compute_productivity_statistics(capital_sector: BaseAgent) -> Dict[str, float]:
    """
    Compute productivity statistics for capital sector.
    Based on fun_KS_stats.h
    
    Args:
        capital_sector: Capital sector
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    firms = capital_sector.get_children("Firm1")
    n_firms = len(firms)
    
    if n_firms == 0:
        return stats
    
    # Average productivity
    Atau_values = [firm.V("_Atau") for firm in firms]
    Btau_values = [firm.V("_Btau") for firm in firms]
    
    stats['AtauAvg'] = sum(Atau_values) / n_firms
    stats['BtauAvg'] = sum(Btau_values) / n_firms
    
    # Max productivity
    stats['AtauMax'] = max(Atau_values) if Atau_values else 0.0
    stats['BtauMax'] = max(Btau_values) if Btau_values else 0.0
    
    # Min productivity
    stats['AtauMin'] = min(Atau_values) if Atau_values else 0.0
    stats['BtauMin'] = min(Btau_values) if Btau_values else 0.0
    
    return stats


def compute_inflation(current_price_index: float, 
                     lagged_price_index: float) -> float:
    """
    Compute inflation rate.
    
    Args:
        current_price_index: Current period price index
        lagged_price_index: Previous period price index
        
    Returns:
        Inflation rate
    """
    if lagged_price_index > 0:
        return (current_price_index / lagged_price_index) - 1.0
    return 0.0


def compute_price_index(consumption_sector: BaseAgent) -> float:
    """
    Compute price index for consumption goods.
    Weighted average of prices by market share.
    
    Args:
        consumption_sector: Consumption sector
        
    Returns:
        Price index
    """
    firms = consumption_sector.get_children("Firm2")
    
    if not firms:
        return 1.0
    
    # Weight by market share
    price_index = sum(firm.V("_p2") * firm.V("_f2") for firm in firms)
    
    return price_index


def compute_growth_rate(current_value: float, lagged_value: float) -> float:
    """
    Compute growth rate between two periods.
    
    Args:
        current_value: Current period value
        lagged_value: Previous period value
        
    Returns:
        Growth rate
    """
    if lagged_value > 0:
        return (current_value / lagged_value) - 1.0
    return 0.0
