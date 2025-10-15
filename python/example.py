"""
Example usage of the K+S ABM model.
Demonstrates model initialization, execution, and results analysis.
"""

from python.model import KSModel
from python.random_generator import random_engine
import matplotlib.pyplot as plt


def get_baseline_parameters():
    """
    Get baseline model parameters (based on Cent_wage-Baseline_v2.lsd).
    
    Returns:
        Dictionary with all model parameters
    """
    params = {
        # Country-level parameters
        'Crec': 0.5,           # Unfilled consumption recovery limit
        'TregChg': 0,          # Regime change period (0=no change)
        'gG': 0.01,            # Growth rate of fixed public expenditure
        'mLim': 0.1,           # Cap on moving-average growth
        'mPer': 4,             # Periods for moving-average growth
        'omicron': 0.5,        # Entry sensitivity to market conditions
        'stick': 0.1,          # Number of firms stickiness
        'tr': 0.20,            # Tax rate
        'x2inf': -0.5,         # Lower support for entry distribution
        'x2sup': 0.5,          # Upper support for entry distribution
        
        # Financial market parameters
        'B': 10,               # Number of banks
        'DebRule': 1.0,        # Max debt to GDP ratio
        'DefPrule': 0.05,      # Max deficit to GDP ratio
        'EqB0': 1.0,           # Initial bank equity multiple
        'Lambda': 3.0,         # Credit multiple
        'Lambda0': 10.0,       # Credit absolute floor
        'PhiB': 0.1,           # Bailout capital fraction
        'Trule': 50,           # Start time for fiscal rules
        'Ut': 0.05,            # Target unemployment (Taylor rule)
        'alphaB': 2.0,         # Bank size heterogeneity (Pareto)
        'betaB': 0.5,          # Bank fragility sensitivity
        'dB': 0.5,             # Bank dividend rate
        'deltaB': 0.1,         # Debt repayment share
        'deltaDeb': 0.1,       # Government debt repayment share
        'gammaPi': 1.5,        # Taylor rule inflation sensitivity
        'gammaU': 0.5,         # Taylor rule unemployment sensitivity
        'kConst': 0.02,        # Interest ramping by credit class
        'mPerB': 4,            # Bank moving-average periods
        'muBonds': 0.8,        # Bonds spread
        'muD': 0.5,            # Deposit spread (mark-down)
        'muDeb': 2.0,          # Debt spread (mark-up)
        'muRes': 0.8,          # Reserves spread
        'piT': 0.02,           # Target inflation
        'rAdj': 0.001,         # Minimum rate adjustment
        'rT': 0.02,            # Target prime rate
        'rhoBonds': 0.01,      # Bonds risk premium
        'tauB': 0.08,          # Capital adequacy ratio
        'thetaBonds': 20,      # Bonds average maturity
        
        # Capital sector parameters
        'Deb10ratio': 0.5,     # Initial debt-to-equity ratio
        'F10': 20,             # Initial number of capital firms
        'F1max': 50,           # Maximum capital firms
        'F1min': 5,            # Minimum capital firms
        'L1rdMax': 0.3,        # Maximum R&D labor share
        'L1shortMax': 0.2,     # Maximum labor shortage
        'NW10': 1.0,           # Initial net worth
        'Phi3': 0.5,           # Lower NW support for entrants
        'Phi4': 1.0,           # Upper NW support for entrants
        'alpha1': 2.0,         # Innovation Beta parameter
        'beta1': 2.0,          # Innovation Beta parameter
        'alpha2': 2.0,         # Imitation Beta parameter
        'beta2': 2.0,          # Imitation Beta parameter
        'd1': 0.5,             # Dividend rate sector 1
        'gamma': 0.2,          # New customer share
        'm1': 1.0,             # Worker output capital goods
        'mu1': 0.25,           # Mark-up sector 1
        'n1': 4,               # Market share evaluation periods
        'nu': 0.1,             # R&D revenue share
        'x1inf': -0.1,         # Lower innovation bound
        'x1sup': 0.1,          # Upper innovation bound
        'x5': 0.1,             # Entrant productivity advantage
        'xi': 0.5,             # R&D innovation share
        'zeta1': 1.0,          # Innovation elasticity
        'zeta2': 1.0,          # Imitation elasticity
        
        # Consumption sector parameters
        'Deb20ratio': 0.5,     # Initial debt-to-equity ratio
        'F20': 100,            # Initial number of consumption firms
        'F2max': 200,          # Maximum consumption firms
        'F2min': 20,           # Minimum consumption firms
        'NW20': 1.0,           # Initial net worth
        'Phi1': 0.5,           # Lower NW support for entrants
        'Phi2': 1.0,           # Upper NW support for entrants
        'b': 20,               # Machine payback period
        'chi': 2.0,            # Replicator dynamics selectivity
        'd2': 0.5,             # Dividend rate sector 2
        'e0': 0.5,             # Animal spirits weight
        'e1': 0.5,             # t-1 demand weight
        'e2': 0.3,             # t-2 demand weight
        'e3': 0.15,            # t-3 demand weight
        'e4': 0.05,            # t-4 demand weight
        'e5': 0.5,             # Acceleration rate
        'e6': 0.5,             # Adaptive expectation factor
        'e7': 0.3,             # First order extrapolative factor
        'e8': 0.2,             # Second order extrapolative factor
        'ent2HldPer': 50,      # Hold period for post-change firms
        'ent2HldShr': 0.5,     # Share of post-change entrants
        'eta': 20,             # Machine technical lifetime
        'f2min': 0.001,        # Minimum market share
        'f2minPosChg': 0.0,    # Min probability post-change
        'f2trdChg': 0.0,       # Min market share post-change
        'iota': 0.1,           # Inventory share
        'kappaMax': 0.2,       # Capital max growth threshold
        'kappaMin': -0.1,      # Capital min growth threshold
        'm2': 1.0,             # Machine output consumption goods
        'mu20': 0.25,          # Initial mark-up sector 2
        'n2': 4,               # Market share evaluation periods
        'omega1': 1.0,         # Price competitiveness weight
        'omega2': 1.0,         # Unfilled demand weight
        'omega3': 0.0,         # Quality weight
        'u': 0.8,              # Planned capacity utilization
        'upsilon': 0.05,       # Mark-up adjustment sensitivity
        
        # Labor supply parameters
        'Gamma': 0.5,          # Unemployed training coverage
        'GammaCost': 0.1,      # Training cost share
        'Ls0': 1000,           # Initial workers
        'Lscale': 1.0,         # Worker scale
        'Tc': 4,               # Contract term
        'Tp': 2,               # Protection period
        'Tr': 0,               # Retirement period (0=no retirement)
        'Ts': 4,               # Wage memory periods
        'delta': 0.01,         # Labor force growth
        'epsilon': 0.02,       # Min wage increment to switch
        'kappa': 1.0,          # Global discouragement intensity
        'lambda': 1.0,         # Individual discouragement intensity
        'omega': 5,            # Job applications per employed
        'omegaU': 10,          # Job applications per unemployed
        'phi': 0.5,            # Unemployment benefit rate
        'psi1': 0.5,           # Inflation pass-through to wages
        'psi2': 0.5,           # Productivity elasticity of wages
        'psi3': -0.3,          # Unemployment elasticity of wages
        'psi4': 0.5,           # Firm productivity wage elasticity
        'psi5': 0.2,           # Vacancy rate wage elasticity
        'psi6': 0.3,           # Profit sharing rate
        'rho': 0.5,            # Labor sharing parameter
        'sigma': 0.1,          # Learning-by-doing degree
        'tauG': 0.05,          # Government training factor
        'tauT': 0.02,          # Tenure learning factor
        'tauU': 0.01,          # Unemployed skill deterioration
        'theta': 0.1,          # Extra capacity when hiring
        'w0min': 0.5,          # Minimum subsistence wage
        'wCap': 2.0,           # Wage change cap multiple
        
        # Control flags
        'flagCons': 2,         # Consumption composition mode
        'flagGovExp': 2,       # Government expenditure mode
        'flagTax': 1,          # Taxation mode
        'flagCreditRule': 2,   # Credit supply rule
        'flagFiscalRule': 2,   # Fiscal rule type
        'flagAllFirmsChg': 0,  # Regime change mode
        'flagExpect': 1,       # Expectation formation
        'flagAddWorkers': 0,   # Additional workers on full employment
        'flagSearchMode': 1,   # Job search mode
        'flagSearchDisc': 1,   # Job search discouragement
        'flagHireSeq': 0,      # Hiring sequence
        'flagHireOrder1': 0,   # Hiring order sector 1
        'flagHireOrder2': 0,   # Hiring order sector 2
        'flagFireOrder1': 0,   # Firing order sector 1
        'flagFireOrder2': 0,   # Firing order sector 2
        'flagFireRule': 2,     # Firing rule
        'flagHeterWage': 1,    # Wage heterogeneity
        'flagWageOffer': 1,    # Wage offer mode
        'flagWagePremium': 1,  # Wage premium mode
        'flagIndexWage': 1,    # Wage indexation
        'flagIndexMinWage': 1, # Min wage indexation
        'flagLearn1': 2,       # Learning in capital sector
        'flagWorkerLBU': 3,    # Worker learning cumulativeness
        'flagWorkerSkProd': 3, # Worker skills effect on productivity
        
        # Simulation settings
        'T_max': 1000,         # Maximum simulation periods
    }
    
    return params


def main():
    """Run example simulation"""
    print("=" * 70)
    print("K+S ABM Model - Python Implementation")
    print("Labor- and finance-augmented K+S Model (version 5.1.3)")
    print("=" * 70)
    print()
    
    # Get parameters
    params = get_baseline_parameters()
    
    # Initialize model with fixed seed for reproducibility
    print("Initializing model...")
    model = KSModel(params, random_seed=42)
    print()
    
    # Run simulation
    results = model.run(T_max=500)
    
    # Plot results
    print("\nGenerating plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('K+S Model Simulation Results', fontsize=14, fontweight='bold')
    
    # GDP
    axes[0, 0].plot(results['time'], results['GDPreal'], 'b-', linewidth=1.5)
    axes[0, 0].set_title('Real GDP')
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('GDP')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Nominal GDP
    axes[0, 1].plot(results['time'], results['GDPnom'], 'r-', linewidth=1.5)
    axes[0, 1].set_title('Nominal GDP')
    axes[0, 1].set_xlabel('Time')
    axes[0, 1].set_ylabel('GDP')
    axes[0, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('python/ks_model_results.png', dpi=150, bbox_inches='tight')
    print("Results saved to python/ks_model_results.png")
    
    print("\nSimulation completed successfully!")


if __name__ == "__main__":
    main()
