"""
Capital Market Module  
Implements machine ordering, supplier selection, and vintage management
"""

from typing import List, Dict, Any, Optional
from utils.core_utils import get_random_engine
import math


class CapitalMarket:
    """
    Capital goods market for the K+S model
    Manages machine orders from consumption firms to capital firms
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def process_machine_orders(self, firms1: List, firms2: List, country_ext) -> float:
        """
        Process machine orders from sector 2 to sector 1
        Implements supplier selection and order fulfillment
        
        From fun_KS_capital.h: orders1 and related equations
        
        Returns:
            Total orders placed (D1)
        """
        n1 = self.config.get('Capital.n1', 4)
        
        # Initialize orders for all capital firms
        for firm in firms1:
            firm._D1 = 0  # Demand received
            if not hasattr(firm, 'orders'):
                firm.orders = []
            firm.orders.clear()
        
        total_orders = 0
        
        # Each consumption firm selects suppliers and places orders
        for firm2 in firms2:
            if not hasattr(firm2, '_ID2') or not hasattr(firm2, '_EI') or not hasattr(firm2, '_SI'):
                continue
            
            # Total machines to order (expansion + substitution)
            machines_needed = firm2._EI + firm2._SI if hasattr(firm2, '_EI') else 0
            
            if machines_needed <= 0:
                continue
            
            # Select supplier(s)
            selected_suppliers = self._select_suppliers(firm2, firms1, n1, country_ext)
            
            if not selected_suppliers:
                continue
            
            # Distribute orders (simplified: equal distribution)
            orders_per_supplier = machines_needed / len(selected_suppliers)
            
            for supplier in selected_suppliers:
                supplier._D1 += orders_per_supplier
                if not hasattr(supplier, 'orders'):
                    supplier.orders = []
                supplier.orders.append({
                    'client': firm2,
                    'quantity': orders_per_supplier,
                    'price': supplier._p1
                })
                total_orders += orders_per_supplier
                
                # Track client relationship
                if not hasattr(supplier, '_BC'):
                    supplier._BC = 0
                supplier._BC += 1  # Client count
        
        return total_orders
    
    def _select_suppliers(self, firm2, firms1: List, n1: int, country_ext) -> List:
        """
        Select suppliers for a consumption firm
        Based on competitiveness (productivity and price)
        """
        if len(firms1) == 0:
            return []
        
        # Sample n1 suppliers randomly
        sample_size = min(n1, len(firms1))
        indices = get_random_engine().rng.choice(len(firms1), size=sample_size, replace=False)
        sampled = [firms1[i] for i in indices]
        
        # Compute competitiveness: higher productivity / lower price is better
        competitiveness = []
        for supplier in sampled:
            prod = supplier._Atau if hasattr(supplier, '_Atau') else 1.0
            price = supplier._p1 if hasattr(supplier, '_p1') else 1.0
            comp = prod / price if price > 0 else 0
            competitiveness.append((comp, supplier))
        
        # Select best supplier(s) - in simple version, just the best one
        competitiveness.sort(reverse=True)
        
        # Store selected supplier
        if competitiveness:
            firm2.supplier = competitiveness[0][1]
            return [competitiveness[0][1]]
        
        return []
    
    def deliver_machines(self, firms1: List):
        """
        Produce and deliver machines ordered
        Updates Q1 (production) and deliveries to clients
        """
        for firm in firms1:
            # Production is already computed in firm.produce()
            # Here we just handle delivery logistics
            
            if not hasattr(firm, 'orders') or not firm.orders:
                continue
            
            available = firm._Q1 if hasattr(firm, '_Q1') else 0
            
            # Distribute available production to orders
            total_ordered = sum(order['quantity'] for order in firm.orders)
            
            if total_ordered <= 0:
                continue
            
            for order in firm.orders:
                if available <= 0:
                    break
                
                # Proportional allocation
                delivery = min(order['quantity'], 
                             available * order['quantity'] / total_ordered)
                
                # Add machine to client firm as new vintage
                client = order['client']
                self._add_vintage_to_firm(client, delivery, firm, order['price'])
                
                available -= delivery
            
            firm.orders.clear()
    
    def _add_vintage_to_firm(self, firm2, quantity: float, supplier, price: float):
        """
        Add delivered machines as a new vintage to consumption firm
        Creates vintage with supplier's technology
        """
        if not hasattr(firm2, 'vintages'):
            firm2.vintages = {}
        
        # Get technology from supplier
        productivity = supplier._Atau if hasattr(supplier, '_Atau') else 1.0
        
        # Create vintage ID
        vintage_id = f"t{len(firm2.vintages)}_s{supplier.id}"
        
        # Add to firm's capital stock
        firm2.vintages[vintage_id] = {
            'productivity': productivity,
            'quantity': quantity,
            'age': 0,
            'price': price,
            'supplier_id': supplier.id
        }
        
        # Update capital stock
        if not hasattr(firm2, '_K'):
            firm2._K = 0
        firm2._K += quantity
    
    def age_vintages(self, firms2: List):
        """
        Age all vintages and scrap old ones
        """
        b = self.config.get('Consumption.b', 3.0)
        
        for firm in firms2:
            if not hasattr(firm, 'vintages') or not firm.vintages:
                continue
            
            # Handle both dict and list structures
            if isinstance(firm.vintages, dict):
                vintages_to_remove = []
                
                for vintage_id, vintage in firm.vintages.items():
                    vintage['age'] += 1
                    
                    # Scrap if too old
                    if vintage['age'] > b:
                        vintages_to_remove.append(vintage_id)
                        if hasattr(firm, '_K'):
                            firm._K -= vintage['quantity']
                
                # Remove scrapped vintages
                for vid in vintages_to_remove:
                    del firm.vintages[vid]
            elif isinstance(firm.vintages, list):
                # Handle list structure
                firm.vintages = [v for v in firm.vintages 
                               if hasattr(v, 'age') and v.age <= b]
