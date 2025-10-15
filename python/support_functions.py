"""
Support Functions for K+S Model
Helper functions for firm operations, worker management, and market interactions.
Based on fun_KS_support.h
"""

from typing import Optional, Dict, Any, List
from .agents import BaseAgent
from .config import *
from .random_generator import random_engine


def set_bank(firm: BaseAgent, banks: List[BaseAgent], bank_weights: List[float]) -> BaseAgent:
    """
    Assign a bank to a firm based on market share weights.
    
    Args:
        firm: Firm agent
        banks: List of bank agents
        bank_weights: Cumulative market share weights
        
    Returns:
        Selected bank
    """
    if not banks:
        return None
    
    # Random selection weighted by bank size
    r = random_engine.uniform(0, 1)
    
    for i, weight in enumerate(bank_weights):
        if r <= weight:
            return banks[i]
    
    # Fallback to last bank
    return banks[-1]


def update_debt(firm: BaseAgent, desired_debt: float, current_debt: float,
               max_debt: float) -> float:
    """
    Update firm debt considering constraints.
    
    Args:
        firm: Firm agent
        desired_debt: Desired debt level
        current_debt: Current debt
        max_debt: Maximum allowed debt
        
    Returns:
        New debt level
    """
    # Can't exceed maximum
    new_debt = min(desired_debt, max_debt)
    
    # Can't be negative
    new_debt = max(new_debt, 0.0)
    
    return new_debt


def cash_flow(firm: BaseAgent, profit: float, tax: float) -> float:
    """
    Manage firm cash flow and update net worth.
    
    Args:
        firm: Firm agent
        profit: Gross profit
        tax: Tax payment
        
    Returns:
        Net profit after tax
    """
    net_profit = profit - tax
    
    # Update net worth
    NW_old = firm.V("_NW1") if hasattr(firm, '_NW1') else firm.V("_NW2")
    NW_new = NW_old + net_profit
    
    if hasattr(firm, '_NW1'):
        firm.WRITE("_NW1", NW_new)
    else:
        firm.WRITE("_NW2", NW_new)
    
    return net_profit


def send_order(supplier: BaseAgent, client: BaseAgent, n_machines: float, t: int):
    """
    Client firm sends order to capital good supplier.
    
    Args:
        supplier: Supplier firm (Firm1)
        client: Client firm (Firm2)
        n_machines: Number of machines ordered
        t: Current time period
    """
    # Create order (simplified - would create Cli object)
    # Store order information
    if hasattr(supplier, '_orders'):
        supplier._orders.append({
            'client': client,
            'quantity': n_machines,
            'time': t
        })


def set_supplier(firm: BaseAgent, capital_sector: BaseAgent, 
                supplier_weights: List[float]) -> Optional[BaseAgent]:
    """
    Select a supplier for consumption good firm.
    Based on competitiveness weights.
    
    Args:
        firm: Consumption firm
        capital_sector: Capital sector containing suppliers
        supplier_weights: Cumulative competitiveness weights
        
    Returns:
        Selected supplier or None
    """
    suppliers = capital_sector.get_children("Firm1")
    
    if not suppliers:
        return None
    
    # Random selection weighted by competitiveness
    r = random_engine.uniform(0, 1)
    
    for i, weight in enumerate(supplier_weights):
        if r <= weight:
            return suppliers[i]
    
    # Fallback to last supplier
    return suppliers[-1]


def compute_supplier_competitiveness(supplier: BaseAgent, 
                                     client_needs: Dict[str, Any]) -> float:
    """
    Compute supplier competitiveness for client selection.
    Based on price and quality.
    
    Args:
        supplier: Supplier firm
        client_needs: Client requirements
        
    Returns:
        Competitiveness index
    """
    p1 = supplier.V("_p1")
    Atau = supplier.V("_Atau")
    
    if p1 <= 0:
        return 0.0
    
    # Competitiveness = productivity / price
    # Higher is better
    E = Atau / p1
    
    return E


def fire_workers(firm: BaseAgent, mode: int, excess_capacity: float,
                n_workers: int, workers: List[BaseAgent]) -> int:
    """
    Fire workers according to specified mode.
    
    Args:
        firm: Firm agent
        mode: Firing rule (0-6)
        excess_capacity: Excess production capacity
        n_workers: Current number of workers
        workers: List of workers
        
    Returns:
        Number of workers fired
    """
    if mode == 0:  # No firing
        return 0
    
    # Compute number to fire based on excess capacity
    if excess_capacity <= 0:
        return 0
    
    # Simple rule: fire proportionally to excess
    to_fire = int(excess_capacity * n_workers)
    to_fire = min(to_fire, n_workers)
    
    # Apply firing rule
    if mode == 1:  # Fire most recent hires (LIFO)
        fired = workers[-to_fire:] if to_fire > 0 else []
    elif mode == 2:  # Fire oldest workers (FIFO)
        fired = workers[:to_fire] if to_fire > 0 else []
    elif mode == 3:  # Fire randomly
        indices = random_engine.choice(len(workers), size=to_fire, replace=False)
        fired = [workers[i] for i in indices]
    else:  # Default LIFO
        fired = workers[-to_fire:] if to_fire > 0 else []
    
    # Mark workers as fired
    for worker in fired:
        worker.WRITE("_employed", 0)
        worker.WRITE("_Te", 0)  # Reset tenure
    
    return len(fired)


def hire_worker(worker: BaseAgent, sector: int, firm: BaseAgent, wage: float):
    """
    Hire a worker to a firm.
    
    Args:
        worker: Worker agent
        sector: Sector (1 or 2)
        firm: Hiring firm
        wage: Wage offered
    """
    worker.WRITE("_employed", sector)
    worker.WRITE("_w", wage)
    worker.WRITE("_Te", 0)  # Start tenure at 0
    worker.WRITE_HOOK(EMPLOYER, firm)


def entry_firm1(capital_sector: BaseAgent, n_entrants: int, 
               params: Dict[str, Any], t: int) -> List[BaseAgent]:
    """
    Create new firms in capital sector.
    
    Args:
        capital_sector: Capital sector
        n_entrants: Number of firms to create
        params: Model parameters
        t: Current time
        
    Returns:
        List of new firms
    """
    new_firms = []
    
    # Get existing firms for benchmarking
    existing = capital_sector.get_children("Firm1")
    n_existing = len(existing)
    
    for i in range(n_entrants):
        # Create new firm with ID
        firm_id = n_existing + i + 1
        # Would create full Firm1 object here
        # new_firm = Firm1(firm_id, capital_sector)
        # Initialize with market averages
        # new_firms.append(new_firm)
        pass
    
    return new_firms


def entry_firm2(consumption_sector: BaseAgent, n_entrants: int,
               params: Dict[str, Any], t: int) -> List[BaseAgent]:
    """
    Create new firms in consumption sector.
    
    Args:
        consumption_sector: Consumption sector
        n_entrants: Number of firms to create
        params: Model parameters
        t: Current time
        
    Returns:
        List of new firms
    """
    new_firms = []
    
    # Get existing firms for benchmarking
    existing = consumption_sector.get_children("Firm2")
    n_existing = len(existing)
    
    for i in range(n_entrants):
        # Create new firm with ID
        firm_id = n_existing + i + 1
        # Would create full Firm2 object here
        pass
    
    return new_firms


def exit_firm(firm: BaseAgent, sector: BaseAgent) -> float:
    """
    Exit firm from sector.
    
    Args:
        firm: Firm to exit
        sector: Sector agent
        
    Returns:
        Fired workers count
    """
    # Fire all workers
    workers_fired = 0
    
    # Get firm workers (would need worker list)
    # for worker in firm_workers:
    #     fire_worker(worker)
    #     workers_fired += 1
    
    # Remove firm from sector
    firm_type = "Firm1" if hasattr(firm, '_ID1') else "Firm2"
    sector.delete_child(firm_type, firm)
    
    return workers_fired


def compute_desired_labor(firm: BaseAgent, production_target: float,
                         productivity: float, params: Dict[str, Any]) -> float:
    """
    Compute desired labor for production target.
    
    Args:
        firm: Firm agent
        production_target: Target production
        productivity: Labor productivity
        params: Model parameters
        
    Returns:
        Desired number of workers
    """
    if productivity <= 0:
        return 0.0
    
    # Account for modularity (for capital firms)
    if hasattr(firm, '_ID1'):
        m = params.get('m1', 1.0)
    else:
        m = params.get('m2', 1.0)
    
    # Labor = production / (productivity * modularity)
    L_desired = production_target / (productivity * m)
    
    return max(L_desired, 0.0)


def compute_wage_offer(firm: BaseAgent, sector: int, 
                      params: Dict[str, Any]) -> float:
    """
    Compute wage offer by firm.
    
    Args:
        firm: Firm agent
        sector: Sector (1 or 2)
        params: Model parameters
        
    Returns:
        Wage offer
    """
    # Base on average wage in sector (simplified)
    if sector == 1:
        w_avg = firm.V("_w1") if hasattr(firm, '_w1') else INIWAGE
    else:
        w_avg = firm.V("_w2avg") if hasattr(firm, '_w2avg') else INIWAGE
    
    # Add some randomness
    wage_offer = w_avg * random_engine.uniform(0.95, 1.05)
    
    return wage_offer
