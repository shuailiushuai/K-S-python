"""
Test cash_flow() implementation
Tests the complete financial management cycle including deposit/debt dynamics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from model.agent import Agent
from model.firm1 import Firm1
from model.firm2 import Firm2
from model.bank import Bank
from model.support import cash_flow, update_debt, update_depo


def create_test_firm(firm_type="Firm1"):
    """Create a test firm with minimal setup"""
    # Create hierarchy: Country -> Sector -> Firm
    country = Agent("Country", None)
    
    # Financial sector
    financial = Agent("Financial", country)
    country.add_child(financial)
    financial.write("deltaB", 0.1, 0)  # 10% debt repayment rate
    
    # Sector
    if firm_type == "Firm1":
        sector = Agent("Capital", country)
        country.add_child(sector)
        firm = Firm1(1, sector)
    else:
        sector = Agent("Consumption", country)
        country.add_child(sector)
        firm = Firm2(1, sector)
    
    sector.add_child(firm)
    
    # Bank
    bank = Bank(1, financial)
    financial.add_child(bank)
    bank.write("_TC1free", 100.0, 0)  # Available credit for sector 1
    bank.write("_TC2free", 100.0, 0)  # Available credit for sector 2
    
    # Link firm to bank
    firm.set_hook(0, bank)  # BANK hook
    
    return firm, bank, country


def test_update_depo():
    """Test update_depo function"""
    print("\n=== Testing update_depo ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Test increment
    firm.write("_NW1", 100.0, 0)
    result = update_depo(firm, 50.0, True)
    assert result == 150.0, f"Expected 150.0, got {result}"
    assert firm.read("_NW1", 0) == 150.0
    print("✓ Increment deposit: 100 + 50 = 150")
    
    # Test decrement
    result = update_depo(firm, -30.0, True)
    assert result == 120.0, f"Expected 120.0, got {result}"
    assert firm.read("_NW1", 0) == 120.0
    print("✓ Decrement deposit: 150 - 30 = 120")
    
    # Test set (not increment)
    result = update_depo(firm, 200.0, False)
    assert result == 200.0, f"Expected 200.0, got {result}"
    assert firm.read("_NW1", 0) == 200.0
    print("✓ Set deposit: 200")
    
    print("✓ update_depo tests passed")


def test_update_debt():
    """Test update_debt function"""
    print("\n=== Testing update_debt ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Initialize
    firm.write("_Deb1", 0.0, 0)
    firm.write("_CD1", 0.0, 0)
    firm.write("_CD1c", 0.0, 0)
    firm.write("_CS1", 0.0, 0)
    
    # Test taking a new loan
    result = update_debt(firm, 100.0, 80.0)  # Desired 100, got 80
    assert result == 80.0, f"Expected 80.0, got {result}"
    assert firm.read("_Deb1", 0) == 80.0
    assert firm.read("_CD1", 0) == 100.0  # Desired credit
    assert firm.read("_CD1c", 0) == 20.0  # Credit constraint (desired - got)
    assert firm.read("_CS1", 0) == 80.0   # Supplied credit
    print("✓ New loan: desired=100, supplied=80, debt=80")
    
    # Test repaying debt
    result = update_debt(firm, 0.0, -30.0)  # Repay 30
    assert result == 50.0, f"Expected 50.0, got {result}"
    assert firm.read("_Deb1", 0) == 50.0
    print("✓ Repay debt: 80 - 30 = 50")
    
    # Test write-off small debt
    firm.write("_Deb1", 0.0005, 0)
    result = update_debt(firm, 0.0, -0.0005)
    assert result == 0.0, f"Expected 0.0, got {result}"
    assert firm.read("_Deb1", 0) == 0.0
    print("✓ Write-off small debt: 0.0005 -> 0")
    
    print("✓ update_debt tests passed")


def test_cash_flow_with_profits():
    """Test cash_flow when firm has profits"""
    print("\n=== Testing cash_flow with profits ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Setup
    firm.write("_NW1", 100.0, 0)      # Current deposits
    firm.write("_Deb1", 50.0, 0)      # Current debt
    firm.write("_Div1", 10.0, 1)      # Previous period dividends
    firm.write("_NW1p", 0.0, 0)       # Production cost provision
    
    # Test: Profit=100, Tax=25, Bonus=0, Div_lag=10
    # Free cash = 100 - 25 - 0 - 10 = 65
    # Debt repayment desired = 50 * 0.1 = 5
    # After repayment: 65 - 5 = 60 added to deposits
    # Final deposits: 100 + 60 = 160
    # Final debt: 50 - 5 = 45
    
    result = cash_flow(firm, 100.0, 25.0)
    assert result == 65.0, f"Expected free cash flow 65.0, got {result}"
    
    final_nw = firm.read("_NW1", 0)
    final_debt = firm.read("_Deb1", 0)
    
    print(f"  Initial: NW=100, Debt=50")
    print(f"  Profit=100, Tax=25, Dividends_lag=10")
    print(f"  Free cash flow: {result}")
    print(f"  Final: NW={final_nw:.2f}, Debt={final_debt:.2f}")
    
    # Check that debt was repaid and rest went to deposits
    assert final_debt == 45.0, f"Expected debt 45.0, got {final_debt}"
    assert final_nw == 160.0, f"Expected NW 160.0, got {final_nw}"
    
    print("✓ cash_flow with profits test passed")


def test_cash_flow_with_losses_covered_by_deposits():
    """Test cash_flow when firm has losses covered by deposits"""
    print("\n=== Testing cash_flow with losses (covered by deposits) ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Setup
    firm.write("_NW1", 100.0, 0)      # Sufficient deposits
    firm.write("_Deb1", 0.0, 0)       # No debt
    firm.write("_Div1", 5.0, 1)       # Previous dividends
    firm.write("_NW1p", 0.0, 0)
    
    # Test: Loss=-50, Tax=0, Div_lag=5
    # Free cash = -50 - 0 - 0 - 5 = -55
    # Deposits cover: 100 > 55
    # Final deposits: 100 - 55 = 45
    
    result = cash_flow(firm, -50.0, 0.0)
    assert result == -55.0, f"Expected free cash flow -55.0, got {result}"
    
    final_nw = firm.read("_NW1", 0)
    final_debt = firm.read("_Deb1", 0)
    
    print(f"  Initial: NW=100, Debt=0")
    print(f"  Loss=-50, Tax=0, Dividends_lag=5")
    print(f"  Free cash flow: {result}")
    print(f"  Final: NW={final_nw:.2f}, Debt={final_debt:.2f}")
    
    assert final_nw == 45.0, f"Expected NW 45.0, got {final_nw}"
    assert final_debt == 0.0, f"Expected debt 0.0, got {final_debt}"
    
    print("✓ cash_flow with losses (covered) test passed")


def test_cash_flow_with_losses_need_credit():
    """Test cash_flow when firm has losses and needs credit"""
    print("\n=== Testing cash_flow with losses (needs credit) ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Setup
    firm.write("_NW1", 20.0, 0)       # Insufficient deposits
    firm.write("_Deb1", 0.0, 0)
    firm.write("_Div1", 5.0, 1)
    firm.write("_NW1p", 0.0, 0)
    firm.write("_CS1a", 100.0, 0)     # Available credit
    firm.write("_CD1", 0.0, 0)
    firm.write("_CD1c", 0.0, 0)
    firm.write("_CS1", 0.0, 0)
    
    # Test: Loss=-50, Tax=0, Div_lag=5
    # Free cash = -50 - 0 - 0 - 5 = -55
    # Deposits only cover: 20
    # Need credit: 55 - 20 = 35
    # Credit available, so deposits -> 0
    
    result = cash_flow(firm, -50.0, 0.0)
    assert result == -55.0, f"Expected free cash flow -55.0, got {result}"
    
    final_nw = firm.read("_NW1", 0)
    final_debt = firm.read("_Deb1", 0)
    
    print(f"  Initial: NW=20, Debt=0")
    print(f"  Loss=-50, Tax=0, Dividends_lag=5")
    print(f"  Free cash flow: {result}")
    print(f"  Need credit: 35")
    print(f"  Final: NW={final_nw:.2f}, Debt={final_debt:.2f}")
    
    assert final_nw == 0.0, f"Expected NW 0.0, got {final_nw}"
    assert final_debt == 35.0, f"Expected debt 35.0, got {final_debt}"
    
    print("✓ cash_flow with losses (needs credit) test passed")


def test_cash_flow_bankruptcy_signal():
    """Test cash_flow when firm cannot get enough credit (bankruptcy)"""
    print("\n=== Testing cash_flow with bankruptcy signal ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Setup
    firm.write("_NW1", 10.0, 0)       # Very low deposits
    firm.write("_Deb1", 0.0, 0)
    firm.write("_Div1", 2.0, 1)
    firm.write("_NW1p", 0.0, 0)
    firm.write("_CS1a", 20.0, 0)      # Limited available credit
    firm.write("_CD1", 0.0, 0)
    firm.write("_CD1c", 0.0, 0)
    firm.write("_CS1", 0.0, 0)
    
    # Test: Loss=-60, Tax=0, Div_lag=2
    # Free cash = -60 - 0 - 0 - 2 = -62
    # Deposits: 10
    # Need credit: 52
    # Available credit: 20 < 52 (insufficient!)
    # Should set NW to -1e-6 (bankruptcy signal)
    
    result = cash_flow(firm, -60.0, 0.0)
    assert result == -62.0, f"Expected free cash flow -62.0, got {result}"
    
    final_nw = firm.read("_NW1", 0)
    final_debt = firm.read("_Deb1", 0)
    
    print(f"  Initial: NW=10, Debt=0")
    print(f"  Loss=-60, Tax=0, Dividends_lag=2")
    print(f"  Free cash flow: {result}")
    print(f"  Need credit: 52, Available: 20 (INSUFFICIENT)")
    print(f"  Final: NW={final_nw:.6f}, Debt={final_debt:.2f}")
    
    assert final_nw == -1e-6, f"Expected NW -1e-6 (bankruptcy), got {final_nw}"
    assert final_debt == 52.0, f"Expected debt 52.0, got {final_debt}"
    
    print("✓ cash_flow bankruptcy signal test passed")


def test_firm_methods():
    """Test firm-level tax and dividend methods"""
    print("\n=== Testing firm methods ===")
    
    firm, bank, country = create_test_firm("Firm1")
    
    # Setup
    firm.write("_Pi1", 100.0, 0)
    firm.write("_NW1", 50.0, 0)
    firm.write("_Deb1", 20.0, 0)
    firm.write("_Div1", 5.0, 1)
    firm.write("_NW1p", 0.0, 0)
    
    # Test compute_tax_and_cash_flow
    tax = firm.compute_tax_and_cash_flow(0.25)  # 25% tax rate
    assert tax == 25.0, f"Expected tax 25.0, got {tax}"
    assert firm.read("_Tax1", 0) == 25.0
    print(f"✓ Tax computed: {tax}")
    
    # Test compute_dividends
    div = firm.compute_dividends(0.5)  # 50% payout
    expected_div = 0.5 * (100.0 - 25.0)  # 50% of (profit - tax)
    assert div == expected_div, f"Expected div {expected_div}, got {div}"
    assert firm.read("_Div1", 0) == expected_div
    print(f"✓ Dividends computed: {div}")
    
    print("✓ Firm methods test passed")


def run_all_tests():
    """Run all cash_flow tests"""
    print("\n" + "="*60)
    print("CASH_FLOW IMPLEMENTATION TESTS")
    print("="*60)
    
    try:
        test_update_depo()
        test_update_debt()
        test_cash_flow_with_profits()
        test_cash_flow_with_losses_covered_by_deposits()
        test_cash_flow_with_losses_need_credit()
        test_cash_flow_bankruptcy_signal()
        test_firm_methods()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return True
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
