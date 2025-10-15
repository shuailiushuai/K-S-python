"""
Support Functions for K+S Model
Helper functions for firm operations, worker management, and market interactions.
Based on fun_KS_support.h
"""

from typing import Optional, Dict, Any, List, Tuple
from .agents import BaseAgent, Application, WageOffer
from .config import *
from .random_generator import random_engine
import random


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


def exit_firm(firm: BaseAgent, sector: BaseAgent, country_ext) -> float:
    """
    Exit firm from sector.
    Based on exit_firm() in fun_KS_support.h
    
    Args:
        firm: Firm to exit
        sector: Sector agent
        country_ext: Country extension
        
    Returns:
        Liquidation equity (or 0 if bad debt)
    """
    # Determine sector
    is_firm1 = hasattr(firm, '_ID1')
    sec = 0 if is_firm1 else 1
    
    # Get financial variables
    if is_firm1:
        NW = firm.V("_NW1")
        Deb = firm.V("_Deb1")
        Eq = firm.V("_Eq1")
    else:
        NW = firm.V("_NW2")
        Deb = firm.V("_Deb2")
        Eq = firm.V("_Eq2")
    
    # Remove equity from sector total
    if is_firm1:
        sector.INCR("Eq1", -Eq)
    else:
        sector.INCR("Eq2", -Eq)
    
    # Account liquidation equity or bad debt
    liq_val = NW - Deb
    
    if liq_val < 0:
        # Bank takes the loss (bad debt)
        liq_eq = 0.0
        
        # Get firm's bank
        bank = firm.get_hook("BANK")
        if bank:
            # Add bad debt to bank
            if is_firm1:
                bank.INCR("_BadDeb1", -liq_val)
            else:
                bank.INCR("_BadDeb2", -liq_val)
    else:
        # Liquidation equity returned
        liq_eq = max(liq_val, 0.0)
        if is_firm1:
            sector.INCR("cExit1", liq_eq)
        else:
            sector.INCR("cExit2", liq_eq)
    
    # Remove from bank's client list
    bank_client = firm.get_hook("BCLIENT")
    if bank_client:
        # Would delete BCLIENT bridge object
        pass
    
    # For Firm2, fire all workers and clean up
    if not is_firm1:
        firm.WRITE("_life2cycle", 4)  # Mark as exiting
        
        # Fire all workers
        workers_fired = fire_workers_all(firm, country_ext)
        
        # Remove from firm2 map
        firm_id = firm.V("_ID2")
        if firm_id in country_ext.firm2map:
            del country_ext.firm2map[firm_id]
        
        # Remove from firm2ptr list
        if firm in country_ext.firm2ptr:
            country_ext.firm2ptr.remove(firm)
    
    # Remove firm from sector
    firm_type = "Firm1" if is_firm1 else "Firm2"
    sector.delete_child(firm_type, firm)
    
    return liq_eq


def fire_workers_all(firm: BaseAgent, country_ext) -> float:
    """
    Fire all workers from a firm.
    
    Args:
        firm: Firm agent
        country_ext: Country extension
        
    Returns:
        Number of workers fired (scaled)
    """
    # Get all workers from this firm
    workers_fired = 0
    Lscale = country_ext.labSup.V("Lscale") if country_ext.labSup else 1.0
    
    # Search through all workers
    for worker in country_ext.labSup.get_children("Worker"):
        if worker.V("_employed") == 2:  # Employed in sector 2
            employer = worker.get_hook("FWRK")
            if employer == firm:
                fire_worker_full(worker)
                workers_fired += 1
    
    return workers_fired * Lscale


def entry_firm1(capital_sector: BaseAgent, n_entrants: int, 
               params: Dict[str, Any], country_ext, t: int) -> float:
    """
    Create new firms in capital sector.
    Based on entry_firm1() in fun_KS_support.h
    
    Args:
        capital_sector: Capital sector
        n_entrants: Number of firms to create
        params: Model parameters
        country_ext: Country extension
        t: Current time
        
    Returns:
        Total entry cost (new equity)
    """
    from .firm1 import Firm1
    
    entry_cost = 0.0
    
    # Get initialization parameters
    NW10 = params.get('NW10', 100.0)
    PPI = capital_sector.VL("PPI", 1) if hasattr(capital_sector, 'PPI') else 1.0
    pK0 = params.get('pK0', 1.0)
    NW10u = NW10 * PPI / pK0  # Minimum wealth
    
    # Get existing firms for averaging
    existing = capital_sector.get_children("Firm1")
    n_existing = len(existing)
    
    # Create entrants
    for i in range(n_entrants):
        # Create new firm
        firm_id = n_existing + i + 1
        new_firm = Firm1(firm_id, capital_sector)
        
        # Initialize with market averages
        if existing:
            # Average technology from existing firms
            avg_Atau = sum(f.V("_Atau") for f in existing) / len(existing)
            avg_Btau = sum(f.V("_Btau") for f in existing) / len(existing)
            new_firm.WRITE("_Atau", avg_Atau)
            new_firm.WRITE("_Btau", avg_Btau)
        else:
            # Use initial values
            new_firm.WRITE("_Atau", INIPROD)
            new_firm.WRITE("_Btau", INIPROD)
        
        # Set initial equity
        new_firm.WRITE("_NW1", NW10u)
        new_firm.WRITE("_Eq1", NW10u)
        new_firm.WRITE("_Deb1", 0.0)
        new_firm.WRITE("_t1ent", t)
        
        # Add to sector
        capital_sector.add_child("Firm1", new_firm)
        
        entry_cost += NW10u
    
    # Update sector entry cost
    capital_sector.INCR("cEntry1", entry_cost)
    
    return entry_cost


def entry_firm2(consumption_sector: BaseAgent, n_entrants: int,
               params: Dict[str, Any], country_ext, t: int) -> float:
    """
    Create new firms in consumption sector.
    Based on entry_firm2() in fun_KS_support.h
    
    Args:
        consumption_sector: Consumption sector
        n_entrants: Number of firms to create
        params: Model parameters
        country_ext: Country extension
        t: Current time
        
    Returns:
        Total entry cost (new equity)
    """
    from .firm2 import Firm2
    
    entry_cost = 0.0
    
    # Get initialization parameters
    NW20 = params.get('NW20', 100.0)
    PPI = country_ext.capSec.VL("PPI", 1) if hasattr(country_ext.capSec, 'PPI') else 1.0
    pK0 = params.get('pK0', 1.0)
    NW20u = NW20 * PPI / pK0  # Minimum wealth
    
    # Get existing firms for averaging
    existing = consumption_sector.get_children("Firm2")
    n_existing = len(existing)
    
    # Create entrants
    for i in range(n_entrants):
        # Create new firm
        firm_id = n_existing + i + 1
        new_firm = Firm2(firm_id, consumption_sector)
        
        # Initialize with market averages
        if existing:
            # Average markup from existing firms
            avg_mu2 = sum(f.V("_mu2") for f in existing) / len(existing)
            new_firm.WRITE("_mu2", avg_mu2)
        else:
            # Use initial markup
            mu20 = params.get('mu20', 0.25)
            new_firm.WRITE("_mu2", mu20)
        
        # Set initial equity
        new_firm.WRITE("_NW2", NW20u)
        new_firm.WRITE("_Eq2", NW20u)
        new_firm.WRITE("_Deb2", 0.0)
        new_firm.WRITE("_life2cycle", 0)
        
        # Add to sector
        consumption_sector.add_child("Firm2", new_firm)
        
        # Add to firm2 map
        country_ext.firm2ptr.append(new_firm)
        country_ext.firm2map[firm_id] = new_firm
        
        entry_cost += NW20u
    
    # Update sector entry cost
    consumption_sector.INCR("cEntry2", entry_cost)
    
    return entry_cost


def order_applications(order_mode: int, applications: List[Application]):
    """
    Sort worker applications according to specified order.
    Based on order_applications() in fun_KS_support.h
    
    Args:
        order_mode: Ordering strategy
            0 = random order
            1 = higher wage workers first
            2 = lower wage workers first
            3 = higher skills workers first
            4 = lower skills workers first
            5 = higher payback period workers first (w/s high)
            6 = lower payback period workers first (w/s low)
            7 = old hired workers first
            8 = recent hired workers first
        applications: List of applications to sort (modified in place)
    """
    if not applications:
        return
    
    if order_mode == 0:
        # Random order - shuffle
        random.shuffle(applications)
    elif order_mode == 1:
        # Higher wage first
        applications.sort(key=lambda a: a.w, reverse=True)
    elif order_mode == 2:
        # Lower wage first
        applications.sort(key=lambda a: a.w)
    elif order_mode == 3:
        # Higher skills first
        applications.sort(key=lambda a: a.s, reverse=True)
    elif order_mode == 4:
        # Lower skills first
        applications.sort(key=lambda a: a.s)
    elif order_mode == 5:
        # Higher payback (w/s ratio) first
        applications.sort(key=lambda a: a.ws, reverse=True)
    elif order_mode == 6:
        # Lower payback (w/s ratio) first
        applications.sort(key=lambda a: a.ws)
    elif order_mode == 7:
        # Old hired workers first (higher Te)
        applications.sort(key=lambda a: a.Te, reverse=True)
    elif order_mode == 8:
        # Recent hired workers first (lower Te)
        applications.sort(key=lambda a: a.Te)


def shuffle_offers(offers: List[WageOffer]):
    """Shuffle wage offers to break ties randomly"""
    random.shuffle(offers)


def order_offers(order_mode: int, offers: List[WageOffer]):
    """
    Sort wage offers according to specified order.
    Based on order_offers() in fun_KS_support.h
    
    Args:
        order_mode: Ordering strategy
            0 = random order
            1 = higher offers first
            2 = firms without workers hire first, then random
            3 = firms without workers hire first, then higher offers
        offers: List of offers to sort (modified in place)
    """
    if not offers:
        return
    
    # Always shuffle first to break ties randomly
    shuffle_offers(offers)
    
    if order_mode == 0:
        # Random order (already shuffled)
        pass
    elif order_mode == 1:
        # Higher offers first
        offers.sort(key=lambda o: o.offer, reverse=True)
    elif order_mode == 2 or order_mode == 3:
        # First sort all by number of workers (ascending)
        offers.sort(key=lambda o: o.workers)
        
        # For mode 3, additionally sort firms with workers by offer
        if order_mode == 3:
            # Find first firm with workers
            first_with_workers = 0
            for i, offer in enumerate(offers):
                if offer.workers > 0:
                    first_with_workers = i
                    break
            
            # Sort firms with workers by offer (descending)
            if first_with_workers < len(offers):
                offers[first_with_workers:] = sorted(
                    offers[first_with_workers:],
                    key=lambda o: o.offer,
                    reverse=True
                )


def hire_worker_full(worker: BaseAgent, sector: int, firm: BaseAgent, 
                     wage: float, country_ext) -> bool:
    """
    Hire a worker for a firm with full bookkeeping.
    Based on hire_worker() in fun_KS_support.h
    
    Args:
        worker: Worker agent
        sector: 1 or 2
        firm: Employing firm
        wage: Wage to pay
        country_ext: Country extension with sector references
        
    Returns:
        True if hired successfully
    """
    _employed = worker.V("_employed")
    
    # If already employed, must quit first
    if _employed > 0:
        Lscale = worker.parent.V("Lscale")
        
        if _employed == 1:
            # Was in sector 1
            country_ext.capSec.INCR("quits1", Lscale)
        else:
            # Was in sector 2
            old_firm = worker.get_hook("FWRK")
            if old_firm:
                old_firm.INCR("_quits2", Lscale)
        
        # Fire from old job
        fire_worker_full(worker)
    
    # Set new employment
    worker.WRITE("_employed", sector)
    worker.WRITE("_Te", 0)  # Reset tenure
    worker.WRITE("_CQ", 0)  # Reset cumulated production
    worker.WRITE("_w", wage)  # Set wage
    
    # Create worker-firm bridge
    worker.set_hook("FWRK", firm)
    
    # Handle skills for learning modes
    flagWorkerLBU = worker.grandparent.V("flagWorkerLBU")
    if flagWorkerLBU != 0 and flagWorkerLBU != 2:
        # Learning by vintage mode - set public skills
        sigma = worker.parent.V("sigma")
        worker.WRITE("_sV", sigma)
    
    return True


def fire_worker_full(worker: BaseAgent):
    """
    Fire a worker with full bookkeeping.
    Based on fire_worker() in fun_KS_support.h
    
    Args:
        worker: Worker to fire
    """
    worker.WRITE("_employed", 0)
    worker.WRITE("_Te", 0)
    
    # Remove firm bridge
    worker.set_hook("FWRK", None)
    worker.set_hook("VWRK", None)  # Remove vintage bridge too
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
