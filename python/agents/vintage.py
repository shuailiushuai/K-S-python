"""
Vintage (Machine) Class

Vintages represent different generations of machines
with different productivities and skills requirements.
"""


class Vintage:
    """
    Vintage (machine generation) class
    
    Each vintage represents a cohort of machines bought at the same time
    from the same supplier with the same technology.
    """
    
    def __init__(self, vintage_id: int, birth_time: int, supplier_id: int,
                 productivity: float, machines: int, price: float):
        """
        Initialize a vintage
        
        Args:
            vintage_id: Unique identifier (encoded as T0*10000 + supplier_id)
            birth_time: Time when vintage was purchased
            supplier_id: ID of Firm1 supplier
            productivity: Machine productivity (A_tau)
            machines: Number of machines in vintage
            price: Price per machine
        """
        self.vintage_id = vintage_id
        self.birth_time = birth_time
        self.supplier_id = supplier_id
        self.productivity = productivity
        self.machines = machines
        self.price = price
        
        # Worker skills associated with vintage
        self.public_skills = 1.0  # Public (shared) vintage skills
        self.avg_skills = 1.0  # Average worker skills on vintage
        self.workers = 0  # Number of workers using this vintage
    
    def add_machines(self, n_machines: int):
        """Add machines to this vintage"""
        self.machines += n_machines
    
    def remove_machines(self, n_machines: int):
        """Remove machines from this vintage (scrapping)"""
        self.machines -= n_machines
        self.machines = max(0, self.machines)
    
    def update_skills(self, new_avg_skills: float):
        """Update average worker skills for this vintage"""
        self.avg_skills = new_avg_skills
    
    def __repr__(self):
        return (f"Vintage(id={self.vintage_id}, t={self.birth_time}, "
                f"A={self.productivity:.3f}, K={self.machines})")
