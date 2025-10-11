"""
K+S Model - Scenario Comparison Example
Demonstrates running multiple scenarios and comparing results
"""

from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.country import Country
from model.random_engine import random_engine
import sys


def run_scenario(name: str, config: dict, periods: int = 30) -> dict:
    """Run a simulation scenario"""
    print(f"\n{'='*70}")
    print(f"Running Scenario: {name}")
    print(f"{'='*70}")
    
    country = Country(config)
    random_engine.seed(42)  # Same seed for fair comparison
    country.initialize()
    
    results = country.simulate(periods)
    
    # Calculate summary statistics
    final_idx = len(results['t']) - 1
    avg_gdp = sum(results['GDPreal']) / len(results['GDPreal'])
    avg_unemp = sum(results['Unemployment']) / len(results['Unemployment']) * 100
    final_wage = country.labor_market._wAvg
    final_skills = sum(w._sT for w in country.workers if w._employed > 0) / max(1, sum(1 for w in country.workers if w._employed > 0))
    
    summary = {
        'name': name,
        'avg_gdp': avg_gdp,
        'final_gdp': results['GDPreal'][final_idx],
        'avg_unemployment': avg_unemp,
        'final_wage': final_wage,
        'final_skills': final_skills,
        'final_debt_gdp': results['Debt'][final_idx] / results['GDPnom'][final_idx] * 100,
    }
    
    print(f"\nSummary:")
    print(f"  Average GDP: ${summary['avg_gdp']:.2f}")
    print(f"  Final GDP: ${summary['final_gdp']:.2f}")
    print(f"  Average Unemployment: {summary['avg_unemployment']:.2f}%")
    print(f"  Final Wage: ${summary['final_wage']:.2f}")
    print(f"  Final Skills: {summary['final_skills']:.3f}")
    print(f"  Final Debt/GDP: {summary['final_debt_gdp']:.1f}%")
    
    return summary


def main():
    print("="*70)
    print("K+S Model - Scenario Comparison Example")
    print("="*70)
    
    periods = 30
    
    # Scenario 1: Baseline (20% tax, 1% growth)
    baseline_config = {
        'country': {
            'flagCons': 2,
            'flagGovExp': 2,
            'flagTax': 1,
            'tr': 0.20,
            'gG': 0.01,
        },
        'capital': {
            'F10': 15,
            'mu1': 0.10,
        },
        'consumption': {
            'F20': 30,
            'mu20': 0.20,
        },
        'financial': {
            'B': 3,
        }
    }
    
    # Scenario 2: High Tax (30% tax)
    high_tax_config = baseline_config.copy()
    high_tax_config['country'] = baseline_config['country'].copy()
    high_tax_config['country']['tr'] = 0.30
    
    # Scenario 3: Low Competition (fewer firms, higher markups)
    low_comp_config = baseline_config.copy()
    low_comp_config['capital'] = {'F10': 8, 'mu1': 0.15}
    low_comp_config['consumption'] = {'F20': 15, 'mu20': 0.30}
    low_comp_config['financial'] = {'B': 3}
    
    # Run scenarios
    results = []
    results.append(run_scenario("Baseline (20% tax)", baseline_config, periods))
    results.append(run_scenario("High Tax (30% tax)", high_tax_config, periods))
    results.append(run_scenario("Low Competition", low_comp_config, periods))
    
    # Comparison table
    print("\n" + "="*70)
    print("SCENARIO COMPARISON")
    print("="*70)
    print(f"\n{'Metric':<25} {'Baseline':<15} {'High Tax':<15} {'Low Comp':<15}")
    print("-"*70)
    
    metrics = [
        ('Average GDP', 'avg_gdp', '${:.2f}'),
        ('Final GDP', 'final_gdp', '${:.2f}'),
        ('Avg Unemployment', 'avg_unemployment', '{:.2f}%'),
        ('Final Wage', 'final_wage', '${:.2f}'),
        ('Final Skills', 'final_skills', '{:.3f}'),
        ('Debt/GDP Ratio', 'final_debt_gdp', '{:.1f}%'),
    ]
    
    for metric_name, metric_key, fmt in metrics:
        row = f"{metric_name:<25}"
        for result in results:
            value = result[metric_key]
            row += f" {fmt.format(value):<15}"
        print(row)
    
    print("\n" + "="*70)
    print("INSIGHTS")
    print("="*70)
    
    # Calculate differences
    baseline = results[0]
    high_tax = results[1]
    low_comp = results[2]
    
    print("\nHigh Tax vs Baseline:")
    tax_gdp_change = (high_tax['final_gdp'] - baseline['final_gdp']) / baseline['final_gdp'] * 100
    tax_wage_change = (high_tax['final_wage'] - baseline['final_wage']) / baseline['final_wage'] * 100
    print(f"  GDP Change: {tax_gdp_change:+.1f}%")
    print(f"  Wage Change: {tax_wage_change:+.1f}%")
    print(f"  Debt/GDP Change: {high_tax['final_debt_gdp'] - baseline['final_debt_gdp']:+.1f} percentage points")
    
    print("\nLow Competition vs Baseline:")
    comp_gdp_change = (low_comp['final_gdp'] - baseline['final_gdp']) / baseline['final_gdp'] * 100
    comp_wage_change = (low_comp['final_wage'] - baseline['final_wage']) / baseline['final_wage'] * 100
    print(f"  GDP Change: {comp_gdp_change:+.1f}%")
    print(f"  Wage Change: {comp_wage_change:+.1f}%")
    print(f"  Impact: Fewer firms → Less competition")
    
    print("\n" + "="*70)
    print("Scenario comparison completed successfully!")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
