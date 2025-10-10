"""
Capital Market

Implements machine tool trading between capital-good and consumption-good firms.
- Network-based relationships (suppliers and clients)
- Machine ordering and delivery
- Technology diffusion through client relationships
"""

import numpy as np
from typing import List
from agents.vintage import Vintage


class CapitalMarket:
    """
    Capital goods (machine tools) market
    """
    
    def __init__(self, params, firms1: List, firms2: List):
        """
        Initialize capital market
        
        Args:
            params: Parameters object
            firms1: List of Firm1 objects (suppliers)
            firms2: List of Firm2 objects (buyers)
        """
        self.params = params
        self.firms1 = firms1
        self.firms2 = firms2
        
        # Market statistics
        self.total_orders = 0.0
        self.total_deliveries = 0.0
    
    def establish_initial_relationships(self):
        """
        Establish initial supplier-customer relationships
        """
        gamma = self.params.get('gamma', 0.5)  # Share of firms as initial clients
        
        for firm1 in self.firms1:
            # Each Firm1 gets a random set of initial clients
            n_clients = max(1, int(gamma * len(self.firms2)))
            clients = np.random.choice(self.firms2, size=n_clients, replace=False)
            
            for client in clients:
                firm1.clients.append(client)
                if client.main_supplier is None:
                    client.main_supplier = firm1
                client.suppliers.append(firm1)
    
    def process_orders(self, t: int):
        """
        Process machine orders from Firm2 to Firm1
        """
        self.total_orders = 0.0
        
        # Reset orders for all Firm1
        for firm1 in self.firms1:
            firm1.orders = 0.0
        
        # Each Firm2 places orders
        for firm2 in self.firms2:
            if firm2.investment_desired > 0:
                # Select supplier
                supplier = self._select_supplier(firm2, t)
                
                if supplier is not None:
                    # Place order
                    supplier.orders += firm2.investment_desired
                    self.total_orders += firm2.investment_desired
                    
                    # Store order for delivery
                    if not hasattr(firm2, 'pending_orders'):
                        firm2.pending_orders = []
                    
                    firm2.pending_orders.append({
                        'supplier': supplier,
                        'machines': firm2.investment_desired,
                        'time': t
                    })
    
    def _select_supplier(self, firm2, t: int):
        """
        Firm2 selects supplier based on price and quality
        
        Firms consider their existing suppliers plus some new options.
        """
        gamma = self.params.get('gamma', 0.5)  # New supplier search rate
        
        # Candidates: existing suppliers + random new ones
        candidates = firm2.suppliers.copy()
        
        # Add potential new suppliers
        n_new = max(1, int(gamma * len(self.firms1)))
        potential_new = [f for f in self.firms1 if f not in candidates]
        
        if potential_new:
            new_suppliers = np.random.choice(
                potential_new,
                size=min(n_new, len(potential_new)),
                replace=False
            )
            candidates.extend(new_suppliers)
        
        if not candidates:
            return None
        
        # Select best based on price and productivity
        best_supplier = None
        best_score = -np.inf
        
        for supplier in candidates:
            # Score based on machine productivity and price
            # Lower price and higher productivity is better
            if supplier.price > 0:
                score = supplier.machine_productivity / supplier.price
            else:
                score = supplier.machine_productivity
            
            if score > best_score:
                best_score = score
                best_supplier = supplier
        
        # Update relationships
        if best_supplier not in firm2.suppliers:
            firm2.suppliers.append(best_supplier)
        
        if firm2 not in best_supplier.clients:
            best_supplier.clients.append(firm2)
        
        firm2.main_supplier = best_supplier
        
        return best_supplier
    
    def deliver_machines(self, t: int):
        """
        Deliver ordered machines and update capital stock
        
        Machines are delivered immediately after production, even if supplier
        couldn't produce the full order due to labor constraints.
        """
        self.total_deliveries = 0.0
        m2 = self.params.get('m2', 1.0)
        
        for firm2 in self.firms2:
            if not hasattr(firm2, 'pending_orders') or not firm2.pending_orders:
                continue
            
            # Deliver pending orders
            orders_to_remove = []
            
            for i, order in enumerate(firm2.pending_orders):
                supplier = order['supplier']
                machines_ordered = order['machines']
                
                # Deliver what the supplier has produced (may be partial)
                # In the C++ model, machines are delivered after production
                if supplier.output > 0:
                    # Deliver the minimum of what was ordered and what was produced
                    machines_delivered = min(machines_ordered, supplier.output)
                    
                    # Create new vintage with delivered machines
                    vintage_id = t * 10000 + supplier.firm_id
                    
                    vintage = Vintage(
                        vintage_id=vintage_id,
                        birth_time=t,
                        supplier_id=supplier.firm_id,
                        productivity=supplier.machine_productivity,
                        machines=int(machines_delivered),
                        price=supplier.price
                    )
                    
                    firm2.vintages.append(vintage)
                    firm2.capital_stock += machines_delivered
                    
                    # Update supplier
                    supplier.output -= machines_delivered
                    supplier.sales += machines_delivered
                    
                    self.total_deliveries += machines_delivered
                    
                    # Mark for removal (even if partial delivery)
                    orders_to_remove.append(i)
            
            # Remove delivered orders
            for i in reversed(orders_to_remove):
                firm2.pending_orders.pop(i)
            
            # Scrap old vintages
            self._scrap_vintages(firm2, t)
    
    def _scrap_vintages(self, firm2, t: int):
        """
        Remove old or unproductive vintages
        """
        b = self.params.get('b', 20)  # Payback period
        eta = self.params.get('eta', 20)  # Technical lifetime
        
        # Remove vintages that are too old
        vintages_to_keep = []
        
        for vintage in firm2.vintages:
            age = t - vintage.birth_time
            
            # Keep if not too old and still productive
            if age < eta and vintage.machines > 0:
                vintages_to_keep.append(vintage)
            else:
                # Scrap vintage
                firm2.capital_stock -= vintage.machines
        
        firm2.vintages = vintages_to_keep
