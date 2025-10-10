"""
Statistics Collection and Analysis

Collects and stores time series data from the simulation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional


class Statistics:
    """
    Statistics collector for the K+S model
    
    Collects aggregate and microeconomic data during simulation.
    """
    
    def __init__(self):
        """
        Initialize statistics collector
        """
        self.data = {
            # Time
            'time': [],
            
            # Aggregate output and demand
            'GDP_real': [],
            'GDP_nominal': [],
            'consumption': [],
            'investment': [],
            'government_expenditure': [],
            
            # Prices and inflation
            'price_level': [],
            'inflation': [],
            'wage_avg': [],
            
            # Labor market
            'employment': [],
            'unemployment_rate': [],
            'vacancies': [],
            'labor_demand': [],
            'labor_supply': [],
            
            # Firms
            'num_firms1': [],
            'num_firms2': [],
            'entry_firms1': [],
            'exit_firms1': [],
            'entry_firms2': [],
            'exit_firms2': [],
            'avg_productivity1': [],
            'avg_productivity2': [],
            
            # Financial
            'total_debt': [],
            'total_credit': [],
            'interest_rate': [],
            'bank_equity': [],
            
            # Fiscal
            'tax_revenue': [],
            'public_debt': [],
            'deficit': [],
            
            # Distributions (selected time steps)
            'firm_sizes': {},
            'wage_distribution': {},
            'productivity_distribution': {},
        }
    
    def collect(self, model, t: int):
        """
        Collect statistics from model at time t
        
        Args:
            model: KSModel instance
            t: Current time step
        """
        self.data['time'].append(t)
        
        # Aggregate output
        gdp_real = self._calculate_gdp_real(model)
        gdp_nominal = self._calculate_gdp_nominal(model)
        self.data['GDP_real'].append(gdp_real)
        self.data['GDP_nominal'].append(gdp_nominal)
        
        # Consumption and investment
        total_consumption = sum(w.consumption_actual for w in model.workers)
        total_investment = sum(f.investment_desired for f in model.firms2)
        self.data['consumption'].append(total_consumption)
        self.data['investment'].append(total_investment)
        self.data['government_expenditure'].append(model.government.expenditure)
        
        # Prices
        price_level = self._calculate_price_level(model)
        self.data['price_level'].append(price_level)
        
        # Inflation
        if len(self.data['price_level']) > 1:
            inflation = (price_level / self.data['price_level'][-2]) - 1
        else:
            inflation = 0.0
        self.data['inflation'].append(inflation)
        
        # Average wage
        employed_workers = [w for w in model.workers if w.employed]
        if employed_workers:
            wage_avg = np.mean([w.wage for w in employed_workers])
        else:
            wage_avg = model.params.get('w0min', 1.0)
        self.data['wage_avg'].append(wage_avg)
        
        # Labor market
        employment = len(employed_workers)
        labor_supply = len(model.workers)
        unemployment_rate = 1 - (employment / labor_supply) if labor_supply > 0 else 0
        
        self.data['employment'].append(employment)
        self.data['unemployment_rate'].append(unemployment_rate)
        self.data['labor_supply'].append(labor_supply)
        
        # Vacancies and labor demand
        vacancies = (model.labor_market.vacancies_firm1 + 
                    model.labor_market.vacancies_firm2)
        labor_demand = sum(f.labor_demand for f in model.firms1 + model.firms2)
        self.data['vacancies'].append(vacancies)
        self.data['labor_demand'].append(labor_demand)
        
        # Firms
        self.data['num_firms1'].append(len(model.firms1))
        self.data['num_firms2'].append(len(model.firms2))
        
        # Entry/exit (now properly tracked)
        self.data['entry_firms1'].append(model.entry_firms1)
        self.data['exit_firms1'].append(model.exit_firms1)
        self.data['entry_firms2'].append(model.entry_firms2)
        self.data['exit_firms2'].append(model.exit_firms2)
        
        # Productivity
        if model.firms1:
            avg_prod1 = np.mean([f.machine_productivity for f in model.firms1])
        else:
            avg_prod1 = 1.0
        
        if model.firms2:
            avg_prod2 = np.mean([f._calculate_productivity() for f in model.firms2])
        else:
            avg_prod2 = 1.0
        
        self.data['avg_productivity1'].append(avg_prod1)
        self.data['avg_productivity2'].append(avg_prod2)
        
        # Financial
        total_debt = sum(f.debt for f in model.firms1 + model.firms2)
        total_credit = sum(b.loans for b in model.banks)
        bank_equity = sum(b.equity for b in model.banks)
        
        self.data['total_debt'].append(total_debt)
        self.data['total_credit'].append(total_credit)
        self.data['interest_rate'].append(model.central_bank.prime_rate)
        self.data['bank_equity'].append(bank_equity)
        
        # Fiscal
        self.data['tax_revenue'].append(model.government.tax_revenue)
        self.data['public_debt'].append(model.government.public_debt)
        self.data['deficit'].append(model.government.deficit)
        
        # Update model params with current values (for use by agents)
        model.params.set('inflation', inflation)
        model.params.set('unemployment_rate', unemployment_rate)
        model.params.set('wAvg', wage_avg)
        model.params.set('GDPnom', gdp_nominal)
        
        # Collect distributions at selected time steps
        if t % 50 == 0:
            self._collect_distributions(model, t)
    
    def _calculate_gdp_real(self, model) -> float:
        """Calculate real GDP (constant prices)"""
        # Production in real terms
        q1 = sum(f.output for f in model.firms1)
        q2 = sum(f.output for f in model.firms2)
        
        # Real GDP = real consumption + real investment
        # Simplified: use output values
        return q1 + q2
    
    def _calculate_gdp_nominal(self, model) -> float:
        """Calculate nominal GDP"""
        # Revenue from all sectors
        revenue1 = sum(f.revenue for f in model.firms1)
        revenue2 = sum(f.revenue for f in model.firms2)
        
        return revenue1 + revenue2
    
    def _calculate_price_level(self, model) -> float:
        """Calculate aggregate price level"""
        if model.firms2:
            # Weighted average of prices by market share
            price_level = sum(f.price * f.market_share for f in model.firms2)
        else:
            price_level = 1.0
        
        return price_level
    
    def _collect_distributions(self, model, t: int):
        """Collect microeconomic distributions"""
        # Firm sizes
        firm_sizes = [len(f.workers) for f in model.firms1 + model.firms2]
        self.data['firm_sizes'][t] = firm_sizes
        
        # Wage distribution
        wages = [w.wage for w in model.workers if w.employed]
        self.data['wage_distribution'][t] = wages
        
        # Productivity distribution
        prod1 = [f.machine_productivity for f in model.firms1]
        prod2 = [f._calculate_productivity() for f in model.firms2]
        self.data['productivity_distribution'][t] = prod1 + prod2
    
    def get_data(self) -> Dict[str, List]:
        """
        Get collected data
        
        Returns:
            Dictionary of time series data
        """
        return self.data
    
    def get_last(self, variable: str, default: float = 0.0) -> float:
        """
        Get last value of a variable
        
        Args:
            variable: Variable name
            default: Default value if no data
            
        Returns:
            Last value of variable
        """
        if variable in self.data and len(self.data[variable]) > 0:
            return self.data[variable][-1]
        return default
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert time series data to pandas DataFrame
        
        Returns:
            DataFrame with time series data
        """
        # Include only time series (not distributions)
        ts_data = {k: v for k, v in self.data.items() 
                   if isinstance(v, list) and k != 'time'}
        
        df = pd.DataFrame(ts_data)
        df.insert(0, 'time', self.data['time'])
        
        return df
    
    def save(self, filename: str):
        """
        Save statistics to file
        
        Args:
            filename: Output filename (CSV or JSON)
        """
        df = self.to_dataframe()
        
        if filename.endswith('.csv'):
            df.to_csv(filename, index=False)
        elif filename.endswith('.json'):
            df.to_json(filename, orient='records', indent=2)
        else:
            # Default to CSV
            df.to_csv(filename + '.csv', index=False)
        
        print(f"Statistics saved to {filename}")
    
    def summary(self) -> str:
        """
        Get summary statistics
        
        Returns:
            Summary string
        """
        df = self.to_dataframe()
        
        summary = "Simulation Summary Statistics\n"
        summary += "=" * 50 + "\n"
        summary += df.describe().to_string()
        
        return summary
