"""
GDP Diagnostic Tool

Comprehensive analysis of GDP calculation to identify discrepancies
between real and nominal GDP.
"""

from ks_model import KSModel


def analyze_gdp_period(model, t):
    """
    Detailed breakdown of GDP components for a specific period
    """
    pC0 = model.params.get('pC0', 1.0)
    pK0 = model.params.get('pK0', 1.0)
    m2 = model.params.get('m2', 1.0)
    
    print(f"\n{'='*70}")
    print(f"GDP ANALYSIS FOR PERIOD {t}")
    print(f"{'='*70}")
    
    # CONSUMPTION COMPONENT
    print(f"\n1. CONSUMPTION COMPONENT:")
    Q2e = sum(f.output for f in model.firms2)
    sales_units = sum(f.sales for f in model.firms2)
    inventories = sum(f.inventories for f in model.firms2)
    
    # Real consumption: Q2e * pC0
    real_C = Q2e * pC0
    
    # Nominal consumption: sum(sales * price)
    nom_C = sum(f.sales * f.price for f in model.firms2)
    
    # Aggregate price level
    avg_price = sum(f.price * f.market_share for f in model.firms2) if model.firms2 else 1.0
    
    print(f"   Output (Q2e): {Q2e:.2f} units")
    print(f"   Sales: {sales_units:.2f} units")
    print(f"   Inventories: {inventories:.2f} units")
    print(f"   Avg Price: {avg_price:.2f} (pC0={pC0:.2f})")
    print(f"   Real C = Q2e * pC0 = {Q2e:.2f} * {pC0:.2f} = {real_C:.2f}")
    print(f"   Nom C = sum(sales * price) = {nom_C:.2f}")
    print(f"   Ratio C_real/C_nom = {real_C/nom_C if nom_C > 0 else 0:.2f}")
    
    # INVESTMENT COMPONENT
    print(f"\n2. INVESTMENT COMPONENT:")
    
    # Count machines delivered this period by price range
    total_machines = 0
    low_price_machines = 0  # price < 5
    mid_price_machines = 0  # 5 <= price < 15
    high_price_machines = 0  # price >= 15
    total_inv_value = 0
    
    for firm in model.firms2:
        for vintage in firm.vintages:
            if vintage.birth_time == t:
                total_machines += vintage.machines
                total_inv_value += vintage.machines * vintage.price
                
                if vintage.price < 5:
                    low_price_machines += vintage.machines
                elif vintage.price < 15:
                    mid_price_machines += vintage.machines
                else:
                    high_price_machines += vintage.machines
    
    # Real investment
    real_I = total_machines * pK0
    
    # Nominal investment
    nom_I = total_inv_value
    
    print(f"   Total machines delivered: {total_machines:.0f}")
    print(f"     Low price (<5): {low_price_machines:.0f} machines")
    print(f"     Mid price (5-15): {mid_price_machines:.0f} machines")
    print(f"     High price (>=15): {high_price_machines:.0f} machines")
    print(f"   Real I = machines * pK0 = {total_machines:.0f} * {pK0:.2f} = {real_I:.2f}")
    print(f"   Nom I = sum(machines * current_price) = {nom_I:.2f}")
    if total_machines > 0:
        avg_machine_price = nom_I / total_machines
        print(f"   Avg machine price = {avg_machine_price:.2f} (should be ~{pK0:.2f})")
    print(f"   Ratio I_real/I_nom = {real_I/nom_I if nom_I > 0 else 0:.2f}")
    
    # Check Firm1 prices
    print(f"\n3. FIRM1 (CAPITAL GOODS) PRICES:")
    if model.firms1:
        firm1_prices = [f.price for f in model.firms1]
        print(f"   Number of Firm1: {len(model.firms1)}")
        print(f"   Price range: {min(firm1_prices):.2f} to {max(firm1_prices):.2f}")
        print(f"   Average price: {sum(firm1_prices)/len(firm1_prices):.2f}")
    
    # INVENTORY CHANGE
    print(f"\n4. INVENTORY CHANGE:")
    if hasattr(model, 'prev_inventory_value'):
        current_inv_value = sum(f.inventories * f.price for f in model.firms2)
        d_inv_nom = current_inv_value - model.prev_inventory_value
        print(f"   Previous inventory value: {model.prev_inventory_value:.2f}")
        print(f"   Current inventory value: {current_inv_value:.2f}")
        print(f"   Change in nominal inventories: {d_inv_nom:.2f}")
    else:
        d_inv_nom = 0
        print(f"   No previous inventory data (first period)")
    
    # TOTAL GDP
    print(f"\n5. TOTAL GDP:")
    gdp_real_calc = real_C + real_I
    gdp_nom_calc = nom_C + nom_I + d_inv_nom
    
    print(f"   Real GDP = C + I = {real_C:.2f} + {real_I:.2f} = {gdp_real_calc:.2f}")
    print(f"   Nom GDP = C + I + dN = {nom_C:.2f} + {nom_I:.2f} + {d_inv_nom:.2f} = {gdp_nom_calc:.2f}")
    print(f"   Ratio GDP_real/GDP_nom = {gdp_real_calc/gdp_nom_calc if gdp_nom_calc > 0 else 0:.2f}")
    
    # From stats
    if model.stats.data['GDP_real']:
        gdp_real_stats = model.stats.data['GDP_real'][-1]
        gdp_nom_stats = model.stats.data['GDP_nominal'][-1]
        print(f"\n   From statistics module:")
        print(f"   Real GDP: {gdp_real_stats:.2f}")
        print(f"   Nom GDP: {gdp_nom_stats:.2f}")
    
    # DIAGNOSIS
    print(f"\n6. DIAGNOSIS:")
    if total_machines > 0:
        avg_machine_price = nom_I / total_machines
        if avg_machine_price < pK0 * 0.5:
            print(f"   ⚠️  WARNING: Avg machine price ({avg_machine_price:.2f}) is much lower than pK0 ({pK0:.2f})")
            print(f"   This explains why Nom GDP < Real GDP for investment")
        elif avg_machine_price > pK0 * 1.5:
            print(f"   ⚠️  WARNING: Avg machine price ({avg_machine_price:.2f}) is much higher than pK0 ({pK0:.2f})")
    
    if real_C / nom_C if nom_C > 0 else 0 > 1.5:
        print(f"   ⚠️  WARNING: Real consumption much higher than nominal")
        print(f"   Possible issue: Sales tracking or price deflation")
    
    return {
        'real_C': real_C,
        'nom_C': nom_C,
        'real_I': real_I,
        'nom_I': nom_I,
        'total_machines': total_machines,
        'avg_machine_price': nom_I / total_machines if total_machines > 0 else 0,
    }


def main():
    """Run diagnostic analysis"""
    print("K+S Model GDP Diagnostic Tool")
    print("="*70)
    
    model = KSModel(seed=42)
    
    # Run simulation for several periods
    periods_to_analyze = [1, 5, 10, 20, 30]
    
    for t in range(1, max(periods_to_analyze) + 1):
        model.t = t
        model.step()
        model.stats.collect(model, t)
        
        if t in periods_to_analyze:
            analyze_gdp_period(model, t)
    
    print(f"\n{'='*70}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
