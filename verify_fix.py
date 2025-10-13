#!/usr/bin/env python3
"""
验证修复的演示脚本
Demonstration script to verify the fix

运行此脚本以验证模型现在产生动态结果
Run this script to verify the model now produces dynamic results
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from model.country import Country
from config import get_default_config
from model.random_engine import random_engine

def main():
    print("=" * 80)
    print("K+S 模型修复验证 / K+S Model Fix Verification")
    print("=" * 80)
    print()
    
    # Initialize model
    config = get_default_config()
    random_engine.seed(42)
    country = Country(config)
    country.initialize()
    
    print("运行20个周期的模拟... / Running 20-period simulation...")
    print()
    
    # Track key metrics
    gdp_values = []
    unemployment_values = []
    sales_values = []
    
    # Run simulation
    for t in range(1, 21):
        country.time_step()
        gdp_values.append(country._GDPreal)
        unemployment_values.append(country.labor_market._Ue * 100)
        sales_values.append(country.consumption_sector._S2)
    
    # Display results
    print("结果 / Results:")
    print("-" * 80)
    print(f"{'周期/Period':<12} {'实际GDP/Real GDP':<15} {'失业率%/Unemp%':<15} {'销售/Sales':<15}")
    print("-" * 80)
    
    for i in [0, 4, 9, 14, 19]:  # Show periods 1, 5, 10, 15, 20
        print(f"{i+1:<12} {gdp_values[i]:<15.2f} {unemployment_values[i]:<15.2f} {sales_values[i]:<15.2f}")
    
    print("-" * 80)
    print()
    
    # Verify dynamic behavior
    print("验证动态行为 / Verifying Dynamic Behavior:")
    print()
    
    # Check GDP growth
    gdp_grew = gdp_values[-1] > gdp_values[0]
    print(f"✅ GDP增长 / GDP Growth: {gdp_values[0]:.2f} → {gdp_values[-1]:.2f}")
    print(f"   状态 / Status: {'通过 PASS' if gdp_grew else '失败 FAIL'} ✓" if gdp_grew else "   Status: FAIL ✗")
    print()
    
    # Check unemployment decrease
    unemp_decreased = unemployment_values[-1] < unemployment_values[0]
    print(f"✅ 失业率变化 / Unemployment Change: {unemployment_values[0]:.1f}% → {unemployment_values[-1]:.1f}%")
    print(f"   状态 / Status: {'通过 PASS' if unemp_decreased else '失败 FAIL'} ✓" if unemp_decreased else "   Status: FAIL ✗")
    print()
    
    # Check sales activity
    sales_active = sales_values[-1] > 0
    print(f"✅ 销售活动 / Sales Activity: ${sales_values[-1]:.2f}")
    print(f"   状态 / Status: {'通过 PASS' if sales_active else '失败 FAIL'} ✓" if sales_active else "   Status: FAIL ✗")
    print()
    
    # Overall result
    all_pass = gdp_grew and unemp_decreased and sales_active
    
    print("=" * 80)
    if all_pass:
        print("✅ 所有检查通过 - 模型产生动态结果!")
        print("✅ ALL CHECKS PASSED - Model produces dynamic results!")
    else:
        print("✗ 某些检查失败 - 模型可能仍有问题")
        print("✗ SOME CHECKS FAILED - Model may still have issues")
    print("=" * 80)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
