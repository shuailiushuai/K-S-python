"""
K+S Model - Simulation Runner
Comprehensive simulation runner with configuration support
"""

from model.country import Country
from model.random_engine import random_engine
from config import load_config, get_default_config
import sys
import argparse
from pathlib import Path


class SimulationRunner:
    """
    Simulation runner for K+S model
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize simulation runner
        
        Args:
            config_path: Path to configuration file (optional)
        """
        if config_path:
            self.config = load_config(config_path)
        else:
            self.config = get_default_config()
        
        self.country = None
        self.results = None
    
    def setup(self):
        """Set up the simulation"""
        # Get simulation settings
        sim_config = self.config.get('simulation', {})
        seed = sim_config.get('seed', 42)
        
        # Initialize random engine
        random_engine.seed(seed)
        
        # Create country with configuration
        self.country = Country(self.config)
        self.country.initialize()
        
        print("Simulation setup complete:")
        print(f"  Random seed: {seed}")
        print(f"  Capital firms: {len(self.country.capital_sector.firms)}")
        print(f"  Consumption firms: {len(self.country.consumption_sector.firms)}")
        print(f"  Banks: {len(self.country.financial_sector.banks)}")
        print(f"  Workers: {len(self.country.workers)}")
        print()
    
    def run(self, periods: int = None):
        """
        Run the simulation
        
        Args:
            periods: Number of periods to run (overrides config)
        """
        if self.country is None:
            self.setup()
        
        # Get simulation settings
        sim_config = self.config.get('simulation', {})
        if periods is None:
            periods = sim_config.get('periods', 100)
        
        print(f"Running simulation for {periods} periods...")
        print()
        
        # Run simulation
        self.results = self.country.simulate(periods)
        
        print("Simulation complete!")
        print()
    
    def report(self):
        """Generate summary report"""
        if self.results is None:
            print("No results to report. Run simulation first.")
            return
        
        print("=" * 70)
        print("SIMULATION SUMMARY REPORT")
        print("=" * 70)
        print()
        
        # Time series overview
        print("Time Series Overview:")
        print(f"{'Period':<8} {'GDP(real)':<12} {'GDP(nom)':<12} {'Unemp%':<10} {'Debt/GDP%':<12}")
        print("-" * 70)
        
        # Show first 5, middle 5, and last 5 periods
        n = len(self.results['t'])
        indices = list(range(min(5, n))) + list(range(max(0, n//2-2), min(n, n//2+3))) + list(range(max(0, n-5), n))
        indices = sorted(set(indices))
        
        prev_idx = -1
        for idx in indices:
            if idx > prev_idx + 1:
                print("...")
            
            t = self.results['t'][idx]
            gdp_real = self.results['GDPreal'][idx]
            gdp_nom = self.results['GDPnom'][idx]
            unemp = self.results['Unemployment'][idx] * 100
            debt_gdp = (self.results['Debt'][idx] / gdp_nom * 100) if gdp_nom > 1 else 0
            
            print(f"{t:<8} {gdp_real:<12.2f} {gdp_nom:<12.2f} {unemp:<10.2f} {debt_gdp:<12.2f}")
            prev_idx = idx
        
        print()
        
        # Summary statistics
        print("=" * 70)
        print("SUMMARY STATISTICS")
        print("=" * 70)
        print()
        
        # Calculate averages (excluding first warmup periods)
        warmup = self.config.get('simulation', {}).get('warmup', 20)
        start_idx = min(warmup, len(self.results['t']))
        
        if len(self.results['t']) > start_idx:
            avg_gdp_real = sum(self.results['GDPreal'][start_idx:]) / (len(self.results['GDPreal']) - start_idx)
            avg_gdp_nom = sum(self.results['GDPnom'][start_idx:]) / (len(self.results['GDPnom']) - start_idx)
            avg_unemployment = sum(self.results['Unemployment'][start_idx:]) / (len(self.results['Unemployment']) - start_idx) * 100
            avg_debt = sum(self.results['Debt'][start_idx:]) / (len(self.results['Debt']) - start_idx)
            
            # Calculate growth rates
            growth_rates = [self.results['GDPreal'][i] / self.results['GDPreal'][i-1] - 1 
                           for i in range(max(start_idx, 1), len(self.results['GDPreal']))
                           if self.results['GDPreal'][i-1] > 0]
            avg_growth = sum(growth_rates) / len(growth_rates) * 100 if growth_rates else 0
            
            print("Macroeconomic Indicators (post-warmup):")
            print(f"  Average Real GDP: ${avg_gdp_real:.2f}")
            print(f"  Average Nominal GDP: ${avg_gdp_nom:.2f}")
            print(f"  Average GDP Growth: {avg_growth:.2f}%")
            print(f"  Average Unemployment: {avg_unemployment:.2f}%")
            print(f"  Average Public Debt: ${avg_debt:.2f}")
            print()
        
        # Final period statistics
        labor = self.country.labor_market
        print("Labor Market (final period):")
        print(f"  Total Labor Force: {labor._Ls}")
        print(f"  Employed Workers: {labor._L}")
        print(f"  Unemployment Rate: {labor._Ue * 100:.2f}%")
        print(f"  Average Wage: ${labor._wAvg:.2f}")
        print()
        
        # Sector statistics
        cap_sector = self.country.capital_sector
        con_sector = self.country.consumption_sector
        
        print("Sector Statistics (final period):")
        print(f"  Capital Goods Sector:")
        print(f"    Active Firms: {len(cap_sector.firms)}")
        print(f"    Production: {cap_sector._Q1e:.2f} machines")
        print(f"    Average Price: ${cap_sector._p1avg:.2f}")
        print(f"    Sector Profits: ${cap_sector._Pi1:.2f}")
        print()
        print(f"  Consumption Goods Sector:")
        print(f"    Active Firms: {len(con_sector.firms)}")
        print(f"    Production: {con_sector._Q2e:.2f} units")
        print(f"    Sales: ${con_sector._S2:.2f}")
        print(f"    Inventories: {con_sector._N:.2f} units")
        print(f"    Average Price: ${con_sector._p2avg:.2f}")
        print(f"    Sector Profits: ${con_sector._Pi2:.2f}")
        print()
        
        # Government statistics
        print("Government (final period):")
        print(f"  Expenditure: ${self.country._G:.2f}")
        print(f"  Tax Revenue: ${self.country._Tax:.2f}")
        print(f"  Primary Deficit: ${self.country._DefP:.2f}")
        print(f"  Total Deficit: ${self.country._Def:.2f}")
        print(f"  Public Debt: ${self.country._Deb:.2f}")
        print(f"  Debt-to-GDP Ratio: {self.country._DebGDP * 100:.2f}%")
        print()
        
        print("=" * 70)
    
    def save_results(self, output_path: str):
        """
        Save results to CSV file
        
        Args:
            output_path: Path to output file
        """
        if self.results is None:
            print("No results to save. Run simulation first.")
            return
        
        try:
            import csv
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                header = ['Period', 'GDPreal', 'GDPnom', 'Unemployment', 'Inflation', 'Debt', 'Deficit']
                writer.writerow(header)
                
                # Write data
                for i in range(len(self.results['t'])):
                    row = [
                        self.results['t'][i],
                        self.results['GDPreal'][i],
                        self.results['GDPnom'][i],
                        self.results['Unemployment'][i],
                        self.results['Inflation'][i],
                        self.results['Debt'][i],
                        self.results['Deficit'][i]
                    ]
                    writer.writerow(row)
            
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='K+S Model Simulation Runner')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (YAML)')
    parser.add_argument('--periods', '-p', type=int, 
                       help='Number of periods to simulate (overrides config)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output file path for results (CSV)')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip summary report')
    
    args = parser.parse_args()
    
    try:
        # Create and run simulation
        print("=" * 70)
        print("K+S MODEL SIMULATION RUNNER")
        print("=" * 70)
        print()
        
        if args.config:
            print(f"Loading configuration from: {args.config}")
        else:
            print("Using default configuration")
        print()
        
        runner = SimulationRunner(args.config)
        runner.setup()
        runner.run(args.periods)
        
        # Generate report
        if not args.no_report:
            runner.report()
        
        # Save results
        if args.output:
            runner.save_results(args.output)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
