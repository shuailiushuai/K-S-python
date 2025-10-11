"""
K+S Model Python Implementation - Complete Replication Guide
=============================================================

This document provides the complete pseudocode and implementation plan for
replicating the K+S ABM model from C++/LSD to Python.

## Model Architecture Overview

### Agent Types (from fun_KS_class.h)

1. **Worker** (fun_KS_worker.h - 16 equations)
   - Employment status tracking
   - Skills accumulation (vintage & tenure)
   - Job search and application
   - Wage negotiation
   - Production contribution

2. **Firm1** - Capital-good firms (fun_KS_firm1.h - 25 equations)
   - R&D (innovation & imitation)
   - Machine production
   - Technology vintages
   - Pricing strategy
   - Customer relationships

3. **Firm2** - Consumption-good firms (fun_KS_firm2.h - 48 equations)
   - Demand expectations (5 modes)
   - Production planning
   - Machine purchase and scrapping
   - Vintage management
   - Labor hiring/firing
   - Price competition

4. **Bank** (fun_KS_bank.h - 15 equations)
   - Deposit collection
   - Credit allocation
   - Basel capital adequacy
   - Pecking order credit rationing
   - Interest rate setting

5. **Vintage** (fun_KS_vintage.h - 10 equations)
   - Machine productivity
   - Worker allocation
   - Skills accumulation
   - Scrapping decisions

### Sector Containers

1. **Capital Sector** (fun_KS_capital.h - 24 equations)
   - Firm1 population management
   - Entry/exit dynamics
   - Market shares
   - R&D aggregates
   - Technology frontier

2. **Consumption Sector** (fun_KS_consumption.h - 30 equations)
   - Firm2 population management
   - Entry/exit with institutional change support
   - Market competition
   - Capacity utilization
   - Quality differentiation

3. **Financial Sector** (fun_KS_financial.h - 28 equations)
   - Bank population management
   - Central bank policy (Taylor rule)
   - Interest rate structure
   - Reserves and bonds
   - Bank bail-outs

4. **Labor Market** (fun_KS_labor.h - 20 equations)
   - Worker population
   - Job search matching
   - Wage setting (centralized/decentralized)
   - Skills training
   - Unemployment benefits

5. **Government** (fun_KS_country.h - 35 equations)
   - Tax collection
   - Public expenditure
   - Fiscal rules (4 modes)
   - Debt management
   - Minimum wage policy

### Time Stepping (fun_KS.cpp - timeStep equation)

The model follows strict computational ordering:

```python
def time_step(t):
    # 1. Monetary policy
    update_prime_rate()  # Central bank Taylor rule
    update_interest_structure()  # Deposits, loans, reserves rates
    
    # 2. Expectations and planning
    firm1_rd_decisions()  # Innovation/imitation attempts
    firm2_demand_expectations()  # Adaptive/extrapolative expectations
    firm2_production_planning()  # Desired output
    
    # 3. Labor market
    firm1_labor_demand()  # R&D + production workers
    firm2_labor_demand()  # Production workers
    worker_job_search()  # Applications
    labor_market_matching()  # Hiring process
    update_wages()  # Wage indexation/adjustment
    
    # 4. Production (capital-good sector)
    firm1_production()  # Machine output
    firm1_pricing()  # Mark-up pricing
    
    # 5. Investment (consumption-good sector)
    firm2_machine_orders()  # Expansion + replacement
    capital_goods_market()  # Machine allocation
    firm2_investment()  # Machine installation
    
    # 6. Production (consumption-good sector)
    firm2_production()  # Consumer good output
    firm2_pricing()  # Variable mark-up
    
    # 7. Consumption market
    worker_consumption_demand()  # Based on income
    consumption_goods_market()  # Good allocation
    firm2_sales()  # Revenue and market shares
    
    # 8. Financial operations
    firm1_credit_demand()  # Finance production/investment
    firm2_credit_demand()  # Finance production/investment
    bank_credit_supply()  # Credit allocation
    bank_credit_rationing()  # Pecking order
    
    # 9. Accounting and taxes
    firm1_profits()  # Gross and net profits
    firm2_profits()  # Gross and net profits
    bank_profits()  # Interest margins
    collect_taxes()  # Government revenue
    pay_dividends()  # Firm/bank dividends
    pay_bonuses()  # Worker profit sharing
    
    # 10. Aggregates
    compute_gdp()  # Real and nominal
    compute_unemployment()  # Labor statistics
    compute_inflation()  # Price indices
    
    # 11. Entry and exit
    firm1_exit()  # Market share or bankruptcy
    firm2_exit()  # Market share or bankruptcy
    bank_exit()  # Negative net worth
    firm1_entry()  # Stochastic entry
    firm2_entry()  # Stochastic entry with regime change
    
    # 12. Government budget
    compute_deficit()  # Revenue - expenditure
    update_public_debt()  # Debt accumulation
    check_fiscal_rules()  # Adjust tax rate if needed
    
    # 13. End-of-period updates
    update_vintage_skills()  # Learning-by-doing
    worker_aging()  # Retirement
    bank_capital_adequacy()  # Basel rules
    update_statistics()  # Collect time series
```

## Key Equations and Logic

### 1. Firm1 R&D Process (fun_KS_firm1.h::_Atau)

```python
def firm1_innovation_imitation(firm1):
    \"\"\"
    Innovation and imitation process for capital-good firms.
    Updates machine productivity (Atau) and unit cost (Btau).
    \"\"\"
    # Normalized R&D expenditure
    nu = firm1.params['nu']  # R&D share of revenue
    RD = nu * firm1.S1_lag  # R&D budget
    
    xi = firm1.params['xi']  # Innovation share
    RD_inn = xi * RD  # Innovation budget
    RD_imi = (1 - xi) * RD  # Imitation budget
    
    # Innovation attempt
    alpha1, beta1 = firm1.params['alpha1'], firm1.params['beta1']
    zeta1 = firm1.params['zeta1']
    
    x_inn = beta_distribution(alpha1, beta1)  # Success draw
    prob_inn = 1 - exp(-zeta1 * RD_inn)  # Success probability
    
    if random() < prob_inn:
        # Innovation successful
        x1inf, x1sup = firm1.params['x1inf'], firm1.params['x1sup']
        x = uniform(x1inf, x1sup)
        A_inn = firm1.A_lag * (1 + x)  # New productivity
        B_inn = firm1.params['w2avg'] / A_inn  # New unit cost
    else:
        A_inn = B_inn = INF  # Failed
    
    # Imitation attempt  
    alpha2, beta2 = firm1.params['alpha2'], firm1.params['beta2']
    zeta2 = firm1.params['zeta2']
    
    x_imi = beta_distribution(alpha2, beta2)
    prob_imi = 1 - exp(-zeta2 * RD_imi)
    
    if random() < prob_imi:
        # Find best competitor to imitate
        competitors = [f for f in sector1.firms if f != firm1]
        distances = []
        for comp in competitors:
            # Euclidean distance in normalized space
            d = sqrt((comp.A_norm - firm1.A_norm)**2 + 
                    (comp.p_norm - firm1.p_norm)**2)
            distances.append((d, comp))
        
        target = min(distances, key=lambda x: x[0])[1]
        A_imi = target.A
        B_imi = firm1.params['w2avg'] / A_imi
    else:
        A_imi = B_imi = INF
    
    # Select best technology (innovation or imitation)
    candidates = [
        (firm1.A_lag, firm1.B_lag),  # Current
        (A_inn, B_inn),  # Innovation
        (A_imi, B_imi)  # Imitation
    ]
    
    # Payback period criterion
    b = firm2.params['b']  # Payback period
    costs = [(B * b + A * firm1.p1_lag) for A, B in candidates]
    best_idx = argmin(costs)
    
    firm1.Atau, firm1.Btau = candidates[best_idx]
    firm1.innovation_success = (best_idx == 1)
    firm1.imitation_success = (best_idx == 2)
```

### 2. Firm2 Expectations (fun_KS_firm2.h::_D2e)

```python
def firm2_demand_expectations(firm2):
    \"\"\"
    Compute expected demand using configured expectation mode.
    \"\"\"
    mode = firm2.params['flagExpect']
    
    if mode == 0:  # Myopic 1-period
        De = firm2.D2_lag[0]
    
    elif mode == 1:  # Myopic 4-period weighted
        e1, e2, e3, e4 = [firm2.params[f'e{i}'] for i in range(1, 5)]
        weights_sum = e1 + e2 + e3 + e4
        if weights_sum > 0:
            De = (e1*firm2.D2_lag[0] + e2*firm2.D2_lag[1] +
                  e3*firm2.D2_lag[2] + e4*firm2.D2_lag[3]) / weights_sum
        else:
            De = firm2.D2_lag[0]
    
    elif mode == 2:  # Accelerating GD
        e5 = firm2.params['e5']
        g = (firm2.D2_lag[0] / firm2.D2_lag[1] - 1) if firm2.D2_lag[1] > 0 else 0
        De = firm2.D2_lag[0] * (1 + e5 * g)
    
    elif mode == 3:  # First-order adaptive
        e6 = firm2.params['e6']
        De = firm2.D2_lag[0] + e6 * (firm2.D2_lag[0] - firm2.D2e_lag)
    
    elif mode == 4:  # Extrapolative-accelerating
        e7, e8 = firm2.params['e7'], firm2.params['e8']
        if firm2.D2_lag[1] > 0:
            g1 = firm2.D2_lag[0] / firm2.D2_lag[1] - 1
            g2 = firm2.D2_lag[1] / firm2.D2_lag[2] - 1 if firm2.D2_lag[2] > 0 else 0
            De = firm2.D2_lag[0] * (1 + e7*g1 + e8*(g1 - g2))
        else:
            De = firm2.D2_lag[0]
    
    # Add animal spirits component
    e0 = firm2.params['e0']
    c2 = sector2.aggregate_capacity()
    De_potential = firm2.market_share * c2
    
    firm2.D2e = (1 - e0) * De + e0 * De_potential
    return firm2.D2e
```

### 3. Labor Market Matching (fun_KS_labor.h + fun_KS_consumption.h::_L2)

```python
def labor_market_matching(labor_market, t):
    \"\"\"
    Match workers to firms through decentralized search.
    \"\"\"
    # Step 1: Workers submit applications
    for worker in labor_market.workers:
        num_apps = worker.compute_applications(labor_market, t)
        
        if num_apps > 0:
            # Select firms to apply to
            if worker.employed == 2:
                # Employed in sector 2 - apply to own + random others
                firms = [worker.employer] + random_sample(
                    sector2.firms, num_apps - 1
                )
            else:
                # Unemployed or sector 1 - apply to random firms
                firms = random_sample(
                    sector1.firms + sector2.firms, num_apps
                )
            
            # Submit applications
            for firm in firms:
                firm.application_queue.append({
                    'worker': worker,
                    'w_requested': worker.compute_requested_wage(t),
                    's': worker.state.s,
                    'Te': worker.state.Te
                })
    
    # Step 2: Determine hiring sequence
    hiring_seq = labor_market.params.get('flagHireSeq', 0)
    
    if hiring_seq == 0:
        hiring_order = shuffle(sector2.firms)
    elif hiring_seq == 1:
        # Firms offering higher wages hire first
        hiring_order = sorted(sector2.firms, 
                            key=lambda f: f.wage_offer, reverse=True)
    elif hiring_seq == 2:
        # Firms without workers hire first
        no_workers = [f for f in sector2.firms if f.L2 == 0]
        with_workers = [f for f in sector2.firms if f.L2 > 0]
        hiring_order = shuffle(no_workers) + shuffle(with_workers)
    elif hiring_seq == 3:
        # Firms without workers hire first, then by wage
        no_workers = sorted([f for f in sector2.firms if f.L2 == 0],
                          key=lambda f: f.wage_offer, reverse=True)
        with_workers = sorted([f for f in sector2.firms if f.L2 > 0],
                            key=lambda f: f.wage_offer, reverse=True)
        hiring_order = no_workers + with_workers
    
    # Step 3: Firms make offers sequentially
    for firm in hiring_order:
        vacancies = firm.L2d - firm.L2  # Desired - current
        
        if vacancies <= 0:
            continue
        
        # Process application queue
        applicants = firm.application_queue
        
        if not applicants:
            continue
        
        # Determine wage offer
        if labor_market.params.get('flagWageOffer', 0) == 0:
            # Wage premium mode
            base_wage = firm.compute_wage_premium()
            offers = [(app['worker'], base_wage) for app in applicants]
        else:
            # Lowest possible wage mode
            requested_wages = [app['w_requested'] for app in applicants]
            offers = [(app['worker'], app['w_requested']) 
                     for app in applicants]
        
        # Sort applicants by hiring order
        hiring_order = labor_market.params.get('flagHireOrder2', 0)
        if hiring_order == 1:  # Higher wage first
            offers.sort(key=lambda x: -x[1])
        elif hiring_order == 3:  # Higher skills first
            offers.sort(key=lambda x: -x[0].state.s)
        # ... other ordering modes
        
        # Make offers
        hired = 0
        for worker, wage in offers:
            if hired >= vacancies:
                break
            
            # Worker evaluates offer
            if worker.accept_job_offer(firm, wage, 2, t):
                firm.hire_worker(worker, wage)
                hired += 1
        
        firm.application_queue.clear()
```

### 4. Replicator Dynamics (fun_KS_firm2.h::_f2)

```python
def update_market_shares(sector2, t):
    \"\"\"
    Update market shares using replicator dynamics.
    \"\"\"
    chi = sector2.params['chi']  # Selectivity
    omega1, omega2, omega3 = [sector2.params[f'omega{i}'] for i in range(1, 4)]
    
    # Compute average market values
    total_sales = sum(f.S2 for f in sector2.firms)
    avg_price = sum(f.p2 * f.S2 for f in sector2.firms) / total_sales
    avg_unfilled = sum(f.D2 - f.Q2 for f in sector2.firms) / len(sector2.firms)
    avg_quality = sum(f.quality * f.S2 for f in sector2.firms) / total_sales
    
    # Compute competitiveness
    for firm in sector2.firms:
        E_price = omega1 * (avg_price / firm.p2)
        E_unfilled = omega2 * (avg_unfilled / max(firm.D2 - firm.Q2, 0.001))
        E_quality = omega3 * (firm.quality / avg_quality)
        
        firm.competitiveness = (E_price + E_unfilled + E_quality) / \
                             (omega1 + omega2 + omega3)
    
    # Average competitiveness
    avg_E = sum(f.competitiveness * f.f2 for f in sector2.firms)
    
    # Update market shares
    for firm in sector2.firms:
        firm.f2 = firm.f2 * (1 + chi * (firm.competitiveness - avg_E))
    
    # Normalize
    total = sum(f.f2 for f in sector2.firms)
    for firm in sector2.firms:
        firm.f2 = firm.f2 / total
```

### 5. Bank Credit Rationing (fun_KS_bank.h::_cScores)

```python
def bank_credit_allocation(bank, t):
    \"\"\"
    Allocate credit using pecking order based on firm financial health.
    \"\"\"
    # Step 1: Rank clients by net-worth-to-sales ratio
    firm1_clients = bank.cli1_list
    firm2_clients = bank.cli2_list
    
    rank1 = [(f.NW1_lag / max(f.S1_lag, 0.001), f) for f in firm1_clients]
    rank2 = [(f.NW2_lag / max(f.S2_lag, 0.001), f) for f in firm2_clients]
    
    rank1.sort(reverse=True)
    rank2.sort(reverse=True)
    
    # Step 2: Assign credit class (1=best, 4=worst)
    n1, n2 = len(rank1), len(rank2)
    
    for i, (ratio, firm) in enumerate(rank1):
        if i < n1 * 0.25:
            firm.qc1 = 1
        elif i < n1 * 0.5:
            firm.qc1 = 2
        elif i < n1 * 0.75:
            firm.qc1 = 3
        else:
            firm.qc1 = 4
    
    for i, (ratio, firm) in enumerate(rank2):
        if i < n2 * 0.25:
            firm.qc2 = 1
        elif i < n2 * 0.5:
            firm.qc2 = 2
        elif i < n2 * 0.75:
            firm.qc2 = 3
        else:
            firm.qc2 = 4
    
    # Step 3: Allocate credit by pecking order
    total_credit = bank.compute_total_credit_supply()
    
    # Priority order: class 1 sector 1, class 1 sector 2, class 2 sector 1, etc.
    for credit_class in range(1, 5):
        # Sector 1 first
        for firm in [f for f, _ in rank1 if f.qc1 == credit_class]:
            if total_credit <= 0:
                break
            
            credit_demand = firm.CD1c
            credit_granted = min(credit_demand, total_credit)
            firm.CS1 = credit_granted
            total_credit -= credit_granted
        
        # Then sector 2
        for firm in [f for f, _ in rank2 if f.qc2 == credit_class]:
            if total_credit <= 0:
                break
            
            credit_demand = firm.CD2c
            credit_granted = min(credit_demand, total_credit)
            firm.CS2 = credit_granted
            total_credit -= credit_granted
```

## Implementation Status

### Completed Components
- [x] Type definitions and enums
- [x] Random number generator (MT19937)
- [x] Support functions (mov_avg_bound, etc.)
- [x] Configuration loader (.lsd files)
- [x] Worker agent (complete)

### Remaining Components (Pseudocode Provided Above)
- [ ] Firm1 agent (capital-good firms)
- [ ] Firm2 agent (consumption-good firms)
- [ ] Bank agent
- [ ] Vintage object
- [ ] Capital sector container
- [ ] Consumption sector container
- [ ] Financial sector container
- [ ] Labor market container
- [ ] Country coordinator
- [ ] Government
- [ ] Central bank
- [ ] Scheduler (timeStep)
- [ ] Data collection
- [ ] Analysis scripts

### Testing Strategy
1. Unit tests for each agent type
2. Integration tests for sector interactions
3. Validation against C++ output for identical parameters
4. Sensitivity analysis to check parameter effects
5. Stock-flow consistency tests

### Performance Optimization
1. NumPy vectorization for aggregate computations
2. Numba JIT for tight loops
3. Efficient data structures (dict for ID lookup)
4. Lazy evaluation where possible
5. Progress bars for long simulations

## Next Steps

The implementation continues with creating the Firm1, Firm2, and Bank agents,
followed by sector containers and the main simulation scheduler.

Each component strictly follows the C++ equations with line-by-line correspondence
documented in docstrings.
\"\"\"
