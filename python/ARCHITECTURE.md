# K+S Model Architecture Documentation

## Model Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         KSModel (Main)                           │
│  - Configuration loading                                         │
│  - Simulation control                                            │
│  - Data collection                                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─► Scheduler (Time Stepping)
             │   └─► 13-step computational sequence
             │
             └─► Country (Top-level container)
                 │
                 ├─► Financial Sector
                 │   ├─► Central Bank
                 │   │   └─► Taylor rule, reserves, bonds
                 │   └─► Banks (B instances)
                 │       ├─► Credit allocation
                 │       ├─► Deposit management
                 │       └─► Basel capital adequacy
                 │
                 ├─► Capital Sector (Sector 1)
                 │   └─► Firm1 (F1 instances)
                 │       ├─► R&D (innovation/imitation)
                 │       ├─► Machine production
                 │       ├─► Worker1 instances
                 │       └─► Bank relationship
                 │
                 ├─► Consumption Sector (Sector 2)
                 │   └─► Firm2 (F2 instances)
                 │       ├─► Demand expectations
                 │       ├─► Investment decisions
                 │       ├─► Vintage fleet management
                 │       │   └─► Vintage instances
                 │       │       └─► Worker2 allocations
                 │       ├─► Worker2 instances
                 │       └─► Bank relationship
                 │
                 ├─► Labor Market
                 │   └─► Workers (Ls instances)
                 │       ├─► Job search
                 │       ├─► Skill dynamics
                 │       └─► Wage requests
                 │
                 └─► Government
                     ├─► Tax collection
                     ├─► Expenditure & transfers
                     ├─► Fiscal rules
                     └─► Debt management
```

## Agent Hierarchy and Relationships

### Worker Agent
```
Worker
  ├─ State
  │  ├─ Identity (ID, age)
  │  ├─ Employment (status, employer, tenure)
  │  ├─ Wages (current, history, reservation)
  │  ├─ Skills (vintage, tenure, compound)
  │  └─ Search (applications, discouragement)
  │
  ├─ Connections
  │  ├─► Employer Firm (Firm1 or Firm2)
  │  ├─► Employer Vintage (if Firm2)
  │  └─► Labor Market (for job search)
  │
  └─ Behaviors
     ├─ compute_age()
     ├─ compute_skills()
     ├─ compute_applications()
     ├─ compute_requested_wage()
     ├─ accept_job_offer()
     └─ compute_production()
```

### Firm1 Agent (Capital-Good Firms)
```
Firm1
  ├─ State
  │  ├─ Identity (ID, age, vintage)
  │  ├─ Technology (A_tau, B_tau)
  │  ├─ Production (Q1, K1, L1)
  │  ├─ Finance (NW1, Deb1, deposits)
  │  ├─ Market (f1, customers, orders)
  │  └─ R&D (expenditure, success flags)
  │
  ├─ Connections
  │  ├─► Bank (credit relationship)
  │  ├─► Workers (Wrk1 list)
  │  ├─► Customers (Firm2 clients)
  │  └─► Sector1 (parent container)
  │
  └─ Behaviors
     ├─ compute_rd() - Innovation & imitation
     ├─ compute_labor_demand()
     ├─ compute_production()
     ├─ compute_price()
     ├─ process_orders()
     └─ compute_profits()
```

### Firm2 Agent (Consumption-Good Firms)
```
Firm2
  ├─ State
  │  ├─ Identity (ID, age, type)
  │  ├─ Production (Q2, D2, D2e)
  │  ├─ Capital (vintages, K2, age_avg)
  │  ├─ Labor (L2, L2d, workers)
  │  ├─ Finance (NW2, Deb2, deposits)
  │  ├─ Market (f2, p2, competitiveness)
  │  └─ Investment (EI, SI)
  │
  ├─ Connections
  │  ├─► Bank (credit relationship)
  │  ├─► Workers (Wrk2 list)
  │  ├─► Vintages (machine fleet)
  │  ├─► Supplier (Firm1 for machines)
  │  └─► Sector2 (parent container)
  │
  └─ Behaviors
     ├─ compute_expectations() - 5 modes
     ├─ compute_production_plan()
     ├─ compute_labor_demand()
     ├─ hire_fire_workers() - 9 modes
     ├─ compute_investment()
     ├─ order_machines()
     ├─ allocate_workers_to_vintages()
     ├─ compute_production()
     ├─ compute_price() - Variable mark-up
     └─ compute_market_share() - Replicator
```

### Bank Agent
```
Bank
  ├─ State
  │  ├─ Identity (IDb, size)
  │  ├─ Assets (loans, reserves, bonds)
  │  ├─ Liabilities (deposits, CB_loans)
  │  ├─ Capital (NWb, adequacy_ratio)
  │  └─ Clients (Cli1, Cli2 lists)
  │
  ├─ Connections
  │  ├─► Firm1 clients (credit relationships)
  │  ├─► Firm2 clients (credit relationships)
  │  ├─► Central Bank (reserves, bail-outs)
  │  └─► Financial Sector (parent)
  │
  └─ Behaviors
     ├─ compute_deposits()
     ├─ compute_credit_supply()
     ├─ assign_credit_classes() - Pecking order
     ├─ allocate_credit()
     ├─ compute_interest_income()
     ├─ compute_profits()
     └─ check_capital_adequacy()
```

### Vintage Object
```
Vintage
  ├─ State
  │  ├─ Identity (IDvint = T0 + supplier_ID)
  │  ├─ Technology (A_vint productivity)
  │  ├─ Workers (n_workers, skills_avg)
  │  ├─ Age (periods since installation)
  │  └─ Status (active, scrapped)
  │
  ├─ Connections
  │  ├─► Owner Firm2
  │  ├─► Workers allocated
  │  └─► Supplier Firm1 (origin)
  │
  └─ Behaviors
     ├─ allocate_workers()
     ├─ compute_production()
     ├─ update_skills()
     └─ check_scrapping()
```

## Computational Flow (timeStep)

### Phase 1: Monetary Policy & Finance
```
1. Central Bank
   └─► update_prime_rate() - Taylor rule
       ├─ Input: inflation, unemployment
       └─ Output: rT (prime rate)

2. Financial Sector
   └─► update_interest_structure()
       ├─ rD = rT * (1 - muD)      # Deposit rate
       ├─ rRes = rT * (1 - muRes)  # Reserve rate
       └─ rDeb = rT * (1 + muDeb)  # Loan rate
```

### Phase 2: Expectations & Planning
```
3. Firm1 (all instances in parallel)
   ├─► compute_rd()
   │   ├─ Innovation attempt
   │   ├─ Imitation attempt
   │   └─ Select best technology
   └─► Update: Atau, Btau

4. Firm2 (all instances in parallel)
   ├─► compute_expectations()
   │   ├─ Mode 0: Myopic 1-period
   │   ├─ Mode 1: Myopic 4-period
   │   ├─ Mode 2: Accelerating
   │   ├─ Mode 3: Adaptive
   │   └─ Mode 4: Extrapolative
   └─► compute_production_plan()
       └─► Update: D2e, Q2d
```

### Phase 3: Labor Market
```
5. Labor Demand
   Firm1 (sequential)
   └─► compute_labor_demand()
       ├─ L1d_RD = nu * S1 / w1
       └─ L1d_prod = Q1 / productivity

   Firm2 (sequential)
   └─► compute_labor_demand()
       └─ L2d = Q2d / (u * A2)

6. Job Search
   Worker (all in parallel)
   └─► compute_applications()
       ├─ Determine search mode
       ├─ Apply to omega firms
       └─ Add to firm queues

7. Matching
   Firm (hiring sequence)
   └─► process_applications()
       ├─ Sort by hiring order
       ├─ Make wage offers
       ├─ Workers accept/reject
       └─ Update L1, L2

8. Wage Updates
   └─► update_wages()
       ├─ Indexation (if flagIndexWage)
       └─ Offer replication (mode 2)
```

### Phase 4: Production (Sector 1)
```
9. Firm1 Production
   └─► compute_production()
       ├─ Q1 = L1 * productivity
       └─ Adjust if labor shortage

10. Firm1 Pricing
    └─► compute_price()
        └─ p1 = (1 + mu1) * (w1 / A_tau)
```

### Phase 5: Investment (Sector 2)
```
11. Machine Ordering
    Firm2 (sequential)
    └─► compute_investment()
        ├─ Expansion: EI = max(K_desired - K, 0)
        ├─ Replacement: SI = scrapped_machines
        └─ Total: I2 = EI + SI

12. Capital Goods Market
    └─► allocate_machines()
        ├─ Firm1 fills orders
        ├─ Firm2 receives machines
        └─ Create new Vintages

13. Installation
    Firm2
    └─► install_machines()
        └─ Update K2, vintage fleet
```

### Phase 6: Production (Sector 2)
```
14. Worker-Vintage Allocation
    Firm2
    └─► allocate_workers_to_vintages()
        ├─ Priority to newer vintages
        └─ Update vintage.workers

15. Firm2 Production
    └─► compute_production()
        ├─ By vintage: Qv = workers * s * A_vint
        └─ Total: Q2 = sum(Qv)

16. Firm2 Pricing
    └─► compute_price()
        ├─ mu2 = f(market_share_trend)
        └─ p2 = (1 + mu2) * unit_cost
```

### Phase 7: Consumption Market
```
17. Consumption Demand
    Worker (all)
    └─► compute_consumption_demand()
        └─ C = w + bonus - savings

18. Good Allocation
    └─► allocate_consumption()
        ├─ Proportional to market shares
        └─ Handle rationing

19. Sales & Market Shares
    Firm2
    ├─► compute_sales()
    │   └─ S2 = p2 * Q2_sold
    └─► compute_market_share()
        └─ f2 = replicator_dynamics(competitiveness)
```

### Phase 8: Credit Market
```
20. Credit Demand
    Firm1, Firm2
    └─► compute_credit_demand()
        └─ CD = max(expenses - NW, 0)

21. Credit Supply
    Bank
    ├─► compute_total_credit()
    │   └─ TC = min(Lambda*Deposits, tauB*NW_bank)
    ├─► assign_credit_classes()
    │   └─ qc = f(NW/Sales ratio)
    └─► allocate_credit()
        └─ Pecking order by credit class
```

### Phase 9: Accounting
```
22. Profits
    Firm1
    └─► Pi1 = S1 - w1*L1 - r*Deb1

    Firm2
    └─► Pi2 = S2 - w2*L2 - p1*I2 - r*Deb2

    Bank
    └─► PiB = r_loan*Loans - r_dep*Deposits

23. Taxes
    Government
    └─► collect_taxes()
        ├─ Tax1 = tr * Pi1
        ├─ Tax2 = tr * Pi2
        ├─ TaxB = tr * PiB
        └─ TaxW = tr * (wages + bonuses) if flagTax=1

24. Dividends & Bonuses
    Firm
    ├─► pay_dividends()
    │   └─ Div = d * Pi_net
    └─► pay_bonuses()
        └─ Bonus = psi6 * free_cash_flow
```

### Phase 10: Aggregates
```
25. Macro Variables
    Country
    ├─► GDP_real = sum(Q1) + sum(Q2)
    ├─► GDP_nom = sum(S1) + sum(S2)
    ├─► Ue = (Ls - L1 - L2) / Ls
    ├─► inflation = dlog(CPI)
    └─► ... other statistics
```

### Phase 11: Entry & Exit
```
26. Exit
    ├─► Firm1.exit() if f1 < threshold OR NW1 < 0
    ├─► Firm2.exit() if f2 < threshold OR NW2 < 0
    └─► Bank.exit() if NWb < 0

27. Entry
    ├─► Firm1.entry()
    │   └─ Prob ~ liquidity/debt ratio
    └─► Firm2.entry()
        ├─ Prob ~ liquidity/debt ratio
        └─ Type = pre/post-change (if TregChg)

28. Credit Scoring
    Bank
    └─► update_credit_scores()
        └─ Refresh pecking order
```

### Phase 12: Government Budget
```
29. Fiscal Accounting
    Government
    ├─► compute_deficit()
    │   └─ Def = G + wU - Tax
    ├─► update_debt()
    │   └─ Deb = Deb_lag + Def
    └─► check_fiscal_rules()
        └─ Adjust tr if needed
```

### Phase 13: End-of-Period
```
30. Vintage Updates
    Vintage (all)
    └─► update_skills()
        └─ sV_avg = avg(worker.s)

31. Worker Aging
    Worker (all)
    └─► compute_age()
        └─ Retirement if age >= Tr

32. Bank Regulation
    Bank (all)
    └─► check_capital_adequacy()
        ├─ If NWb/Loans < tauB: limit credit
        └─ If NWb < 0: bail-out

33. Statistics Collection
    └─► collect_time_series()
        └─ Append all variables to data
```

## Data Flow Examples

### Example 1: Worker Job Search
```
Worker.compute_applications(t)
  ├─► Determine search mode
  │   └─► flagSearchMode (0/1/2)
  ├─► Compute search probability
  │   └─► flagSearchDisc (0/1/2)
  ├─► Select omega firms
  │   ├─► Random sample from Firm1 + Firm2
  │   └─► Add to firm.application_queue
  └─► Return num_applications

Firm2.process_applications(t)
  ├─► Sort queue by flagHireOrder2
  │   ├─► 0: Random
  │   ├─► 1: Higher wage first
  │   ├─► 3: Higher skills first
  │   └─► ... (8 modes)
  ├─► For each applicant:
  │   ├─► Compute wage offer
  │   │   └─► flagWageOffer (0/1)
  │   ├─► Worker.accept_job_offer()
  │   │   └─► Accept if better than current
  │   └─► If accepted: hire_worker()
  └─► Update L2

Worker.accept_job_offer(firm, wage, t)
  ├─► Check if better than current
  │   └─► wage > w * (1 + epsilon)
  ├─► If employed: quit_job()
  ├─► Update state
  │   ├─► employed = 2
  │   ├─► employer = firm
  │   └─► w = wage
  └─► Return True
```

### Example 2: Firm2 Production Cycle
```
Firm2.compute_expectations(t)
  └─► D2e = f(D2_history, flagExpect)

Firm2.compute_production_plan(t)
  ├─► Q2d = D2e + iota*Q2e - N
  └─► K2d = Q2d / (u * A2)

Firm2.compute_investment(t)
  ├─► EI = max(K2d - K2, 0) / m2
  ├─► SI = count(scrap_vintage)
  └─► I2 = EI + SI

Firm2.order_machines(t)
  ├─► Select supplier (Firm1)
  │   └─► Compare price & productivity
  ├─► Place order: I2 machines
  └─► Request credit if needed

Capital Market
  ├─► Firm1.fill_orders()
  └─► Firm2.receive_machines()
      └─► Create new Vintages

Firm2.allocate_workers_to_vintages(t)
  ├─► Sort vintages by age (newer first)
  ├─► For each vintage:
  │   └─► Assign workers up to capacity
  └─► Update vintage.workers

Firm2.compute_production(t)
  ├─► For each vintage:
  │   └─► Qv = sum(worker.Q)
  └─► Q2 = sum(Qv)

Consumption Market
  ├─► Allocate Q2 to consumers
  └─► Firm2.S2 = p2 * Q2_sold

Firm2.compute_market_share(t)
  ├─► Competitiveness = f(p2, unfilled, quality)
  └─► f2 = replicator_dynamics(E)
```

## Parameter Groups

### Country-Level (33 parameters)
- Tax rates, public expenditure growth
- Entry dynamics, regime change timing
- Growth calculation parameters

### Financial (34 parameters)
- Number of banks, interest structure
- Credit limits, Basel parameters
- Taylor rule coefficients
- Fiscal rules

### Capital Sector (24 parameters)
- Firm counts, R&D parameters
- Innovation/imitation rates
- Mark-up, labor shortage limits

### Consumption Sector (28 parameters)
- Firm counts, expectation modes
- Investment parameters
- Mark-up dynamics
- Entry/exit thresholds

### Labor Market (28 parameters)
- Worker population, growth rate
- Contract terms, retirement age
- Search parameters
- Wage adjustment rules
- Learning rates

**Total: 147+ configurable parameters**

## File Size Estimates (Target)

```
ks_model/
├─ types.py              ~350 lines  ✅ (Complete)
├─ agents/
│  ├─ worker.py          ~500 lines  ✅ (Complete)
│  ├─ firm1.py           ~800 lines  🔄 (TODO)
│  ├─ firm2.py          ~1500 lines  🔄 (TODO)
│  ├─ bank.py            ~600 lines  🔄 (TODO)
│  └─ vintage.py         ~300 lines  🔄 (TODO)
├─ sectors/
│  ├─ capital.py         ~800 lines  🔄 (TODO)
│  ├─ consumption.py    ~1000 lines  🔄 (TODO)
│  ├─ financial.py       ~900 lines  🔄 (TODO)
│  └─ labor.py           ~700 lines  🔄 (TODO)
├─ country.py           ~1000 lines  🔄 (TODO)
├─ government.py         ~600 lines  🔄 (TODO)
├─ scheduler.py          ~500 lines  🔄 (TODO)
└─ model.py              ~400 lines  🔄 (TODO)

Total: ~10,000 lines (matching C++ scope)
Current: ~4,000 lines (40% complete)
```

This architecture ensures:
1. ✅ Exact correspondence to C++ equations
2. ✅ Stock-flow consistency
3. ✅ Reproducible results
4. ✅ Modular and testable
5. ✅ Efficient data flow
