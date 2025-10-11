"""
Stock-Flow Consistency Test for K+S Model

This module implements comprehensive stock-flow consistency tests
matching the C++ implementation in fun_KS_test.h

Based on Nikiforos & Zezza 2017 approach
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.country import Country
from config import get_default_config

# Threshold for SFC detection (same as C++)
SFCTHRD = 1e-4
TOL = 0.1


def test_sfc_balance_sheet(country: Country) -> dict:
    """
    Test balance sheet consistency
    
    All columns and rows should sum to zero (within threshold)
    
    Args:
        country: Country object after simulation step
        
    Returns:
        Dictionary with test results
    """
    results = {
        'passed': True,
        'errors': [],
        'warnings': []
    }
    
    cap_sector = country.capital_sector
    con_sector = country.consumption_sector
    fin_sector = country.financial_sector
    
    # Capital-good sector
    NW1 = cap_sector._NW1
    Deb1 = cap_sector._Deb1 if hasattr(cap_sector, '_Deb1') else 0
    Eq1 = cap_sector._Eq1 if hasattr(cap_sector, '_Eq1') else 0
    
    # Consumption-good sector
    NW2 = con_sector._NW2
    Deb2 = con_sector._Deb2 if hasattr(con_sector, '_Deb2') else 0
    Eq2 = con_sector._Eq2 if hasattr(con_sector, '_Eq2') else 0
    Knom = con_sector._Knom if hasattr(con_sector, '_Knom') else 0
    
    # Financial sector
    Loans = sum(bank._Loans for bank in fin_sector.banks)
    Depo = sum(bank._Depo for bank in fin_sector.banks)
    NWb = sum(bank._NWb for bank in fin_sector.banks)
    
    # Government
    Deb = country._Deb if hasattr(country, '_Deb') else 0
    
    # Test: Total assets = Total liabilities + Net worth
    # Firms: NW + Deposits = Loans + Equity + Capital
    firm_balance = (NW1 + NW2) - (Deb1 + Deb2 + Eq1 + Eq2 + Knom)
    
    # Banks: Loans + Reserves = Deposits + Net Worth
    bank_balance = Loans - (Depo + NWb)
    
    # Normalize by GDP
    GDPnom = country._GDPnom if hasattr(country, '_GDPnom') else 1.0
    if GDPnom > 0:
        firm_balance_norm = abs(firm_balance / GDPnom)
        bank_balance_norm = abs(bank_balance / GDPnom)
    else:
        firm_balance_norm = abs(firm_balance)
        bank_balance_norm = abs(bank_balance)
    
    # Check thresholds
    if firm_balance_norm > SFCTHRD:
        results['passed'] = False
        results['errors'].append(f"Firm balance sheet inconsistency: {firm_balance_norm:.6f}")
    
    if bank_balance_norm > SFCTHRD:
        results['passed'] = False
        results['errors'].append(f"Bank balance sheet inconsistency: {bank_balance_norm:.6f}")
    
    results['firm_balance'] = firm_balance_norm
    results['bank_balance'] = bank_balance_norm
    
    return results


def test_sfc_transaction_flow(country: Country) -> dict:
    """
    Test transaction flow consistency
    
    All income and expenditure flows should balance
    
    Args:
        country: Country object after simulation step
        
    Returns:
        Dictionary with test results
    """
    results = {
        'passed': True,
        'errors': [],
        'warnings': []
    }
    
    cap_sector = country.capital_sector
    con_sector = country.consumption_sector
    labor = country.labor_market
    
    # Income flows
    W1 = cap_sector._W1 if hasattr(cap_sector, '_W1') else 0
    W2 = con_sector._W2 if hasattr(con_sector, '_W2') else 0
    total_wages = W1 + W2
    
    Pi1 = cap_sector._Pi1
    Pi2 = con_sector._Pi2
    total_profits = Pi1 + Pi2
    
    # Expenditure flows
    S1 = cap_sector._S1 if hasattr(cap_sector, '_S1') else 0
    S2 = con_sector._S2
    total_sales = S1 + S2
    
    # GDP from income side
    GDP_income = total_wages + total_profits
    
    # GDP from expenditure side
    C = con_sector._S2  # Consumption
    I = con_sector._Inom if hasattr(con_sector, '_Inom') else 0  # Investment
    G = country._G if hasattr(country, '_G') else 0  # Government
    GDP_expenditure = C + I + G
    
    # Test: Income = Expenditure
    GDPnom = country._GDPnom if hasattr(country, '_GDPnom') else 1.0
    if GDPnom > 0:
        income_expenditure_gap = abs((GDP_income - GDP_expenditure) / GDPnom)
    else:
        income_expenditure_gap = abs(GDP_income - GDP_expenditure)
    
    if income_expenditure_gap > SFCTHRD:
        results['passed'] = False
        results['errors'].append(
            f"Income-Expenditure inconsistency: {income_expenditure_gap:.6f} "
            f"(Income: {GDP_income:.2f}, Expenditure: {GDP_expenditure:.2f})"
        )
    
    results['income_expenditure_gap'] = income_expenditure_gap
    results['gdp_income'] = GDP_income
    results['gdp_expenditure'] = GDP_expenditure
    
    return results


def test_sfc_net_lending(country: Country) -> dict:
    """
    Test net lending consistency
    
    Sum of all sectors' net lending should be zero
    
    Args:
        country: Country object after simulation step
        
    Returns:
        Dictionary with test results
    """
    results = {
        'passed': True,
        'errors': [],
        'warnings': []
    }
    
    cap_sector = country.capital_sector
    con_sector = country.consumption_sector
    fin_sector = country.financial_sector
    
    # Sector net lending = Income - Expenditure - Investment
    # Capital sector
    Pi1 = cap_sector._Pi1
    Tax1 = cap_sector._Tax1 if hasattr(cap_sector, '_Tax1') else 0
    W1 = cap_sector._W1 if hasattr(cap_sector, '_W1') else 0
    net_lending_1 = Pi1 - Tax1 - W1
    
    # Consumption sector
    Pi2 = con_sector._Pi2
    Tax2 = con_sector._Tax2 if hasattr(con_sector, '_Tax2') else 0
    W2 = con_sector._W2 if hasattr(con_sector, '_W2') else 0
    Inom = con_sector._Inom if hasattr(con_sector, '_Inom') else 0
    net_lending_2 = Pi2 - Tax2 - W2 - Inom
    
    # Workers (consumption)
    C = con_sector._S2
    net_lending_workers = (W1 + W2) - C
    
    # Government
    Tax = Tax1 + Tax2
    G = country._G if hasattr(country, '_G') else 0
    net_lending_gov = Tax - G
    
    # Sum should be zero
    total_net_lending = net_lending_1 + net_lending_2 + net_lending_workers + net_lending_gov
    
    GDPnom = country._GDPnom if hasattr(country, '_GDPnom') else 1.0
    if GDPnom > 0:
        net_lending_error = abs(total_net_lending / GDPnom)
    else:
        net_lending_error = abs(total_net_lending)
    
    if net_lending_error > SFCTHRD:
        results['passed'] = False
        results['errors'].append(
            f"Net lending inconsistency: {net_lending_error:.6f} "
            f"(Total: {total_net_lending:.2f})"
        )
    
    results['net_lending_error'] = net_lending_error
    results['sector_net_lending'] = {
        'capital': net_lending_1,
        'consumption': net_lending_2,
        'workers': net_lending_workers,
        'government': net_lending_gov,
        'total': total_net_lending
    }
    
    return results


def run_all_sfc_tests(country: Country, verbose: bool = True) -> dict:
    """
    Run all stock-flow consistency tests
    
    Args:
        country: Country object after simulation
        verbose: Print detailed results
        
    Returns:
        Dictionary with all test results
    """
    results = {
        'balance_sheet': test_sfc_balance_sheet(country),
        'transaction_flow': test_sfc_transaction_flow(country),
        'net_lending': test_sfc_net_lending(country)
    }
    
    # Overall pass/fail
    all_passed = all(r['passed'] for r in results.values())
    results['all_passed'] = all_passed
    
    if verbose:
        print("\n" + "="*70)
        print("STOCK-FLOW CONSISTENCY TEST RESULTS")
        print("="*70)
        
        for test_name, test_result in results.items():
            if test_name == 'all_passed':
                continue
            
            status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
            print(f"\n{test_name.replace('_', ' ').title()}: {status}")
            
            if test_result['errors']:
                print("  Errors:")
                for error in test_result['errors']:
                    print(f"    - {error}")
            
            if test_result.get('warnings'):
                print("  Warnings:")
                for warning in test_result['warnings']:
                    print(f"    - {warning}")
        
        print("\n" + "="*70)
        if all_passed:
            print("✅ ALL TESTS PASSED - Model is stock-flow consistent")
        else:
            print("❌ SOME TESTS FAILED - Check errors above")
        print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    """Run SFC tests on a simple simulation"""
    print("Running Stock-Flow Consistency Tests...")
    print("="*70)
    
    # Create and initialize country
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Run a few periods
    print("\nRunning 5-period simulation...")
    for t in range(1, 6):
        print(f"  Period {t}...")
        country.time_step()
    
    # Run SFC tests
    results = run_all_sfc_tests(country, verbose=True)
    
    # Exit with appropriate code
    sys.exit(0 if results['all_passed'] else 1)
