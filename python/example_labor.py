"""
Example: Labor Market Matching
Demonstrates worker-firm matching in labor market
"""

from model.labor import LaborMarket, create_application
from model.worker import Worker
from model.firm1 import Firm1
from model.firm2 import Firm2
from model.agent import Agent
from model.random_engine import random_engine
from model.data_structures import Application

# Initialize random engine for reproducibility
random_engine.seed(789)

# Create mock Country
country = Agent("Country", None)
country.set_param("flagWorkerLBU", 3)
country.set_param("flagWorkerSkProd", 3)
country.set_param("flagLearn1", 2)
country.set_param("flagSearchMode", 0)
country.set_param("flagSearchDisc", 0)

# Create labor market
labor = LaborMarket(parent=country)
labor.set_param("Tr", 40)
labor.set_param("Gamma", 0.5)
labor.set_param("tauG", 0.05)
labor.set_param("tauU", 0.01)
labor.set_param("tauT", 0.02)
labor.set_param("sigma", 0.5)
labor.write("sTavg", 1.0, 1)
labor.write("sTmin", 0.8, 1)
labor._w0min = 0.8
labor._wCent = 1.0

print("=" * 70)
print("K+S Model - Labor Market Matching Example")
print("=" * 70)

# Create workers
print("\n### Creating Workers ###")
workers = []
for i in range(1, 11):
    worker = Worker(worker_id=i, parent=labor)
    
    # Mix of employed and unemployed
    if i <= 6:
        employed = 2  # Sector 2
        age = 25 + i
        skills = 0.8 + i * 0.05
    else:
        employed = 0  # Unemployed
        age = 28 + i
        skills = 0.7 + i * 0.03
    
    worker.initialize(age=age, tc=12, w_res=0.9, sv0=skills)
    worker._employed = employed
    worker._s = skills
    worker._sT = skills
    worker._sV = skills * 0.9
    worker._wR = 0.95 + i * 0.02  # Wage request
    worker._Te = i if employed > 0 else 0
    worker._Tu = 0 if employed > 0 else i - 6
    
    worker.write("_employed", employed)
    worker.write("_s", skills)
    worker.write("_sT", skills)
    worker.write("_wR", worker._wR)
    worker.write("_Te", worker._Te, 1)
    worker.write("_Tu", worker._Tu)
    
    workers.append(worker)
    
    status = f"Sector {employed}" if employed > 0 else "Unemployed"
    print(f"Worker {i}: {status:12s} Skills={skills:.3f} WageReq=${worker._wR:.3f}")

# Create firms in sector 1
print("\n" + "=" * 70)
print("### Creating Firms - Sector 1 (Capital Goods) ###")

capital = Agent("Capital", country)
capital.set_param("L1rdMax", 0.3)
capital.write("w1avg", 1.0, 1)

firms1 = []
for i in range(1, 3):
    firm = Firm1(firm_id=i, parent=capital)
    firm.write("_L1", 5, 1)      # Current workers
    firm.write("_L1d", 7, 0)     # Desired workers (need to hire 2)
    firm.write("_p1", 1.5, 1)
    firms1.append(firm)
    
    print(f"Firm1-{i}: Current={firm.read('_L1', 1)} workers, "
          f"Desired={firm.read('_L1d', 0)} workers, "
          f"Vacancies={firm.read('_L1d', 0) - firm.read('_L1', 1)}")

# Create firms in sector 2
print("\n" + "=" * 70)
print("### Creating Firms - Sector 2 (Consumption Goods) ###")

consumption = Agent("Consumption", country)
consumption.set_param("f2min", 0.001)

firms2 = []
for i in range(1, 4):
    firm = Firm2(firm_id=i, parent=consumption)
    firm.write("_L2", 8, 1)      # Current workers
    firm.write("_L2d", 10 + i, 0)  # Desired workers
    firm.write("_w2o", 1.0 + i * 0.05, 0)  # Wage offer
    firm.write("_S2", 100.0, 1)
    firms2.append(firm)
    
    print(f"Firm2-{i}: Current={firm.read('_L2', 1)} workers, "
          f"Desired={firm.read('_L2d', 0)} workers, "
          f"Vacancies={firm.read('_L2d', 0) - firm.read('_L2', 1)}, "
          f"WageOffer=${firm.read('_w2o', 0):.3f}")

# Collect applications from unemployed workers
print("\n" + "=" * 70)
print("### Job Applications ###")

applications_s1 = []
applications_s2 = {firm: [] for firm in firms2}

for worker in workers:
    if worker._employed == 0:  # Unemployed workers apply
        # Create application
        app = create_application(worker)
        
        # Apply to sector 1
        applications_s1.append(app)
        
        # Apply to 2-3 firms in sector 2
        num_firms = min(2, len(firms2))
        for firm in random_engine.choice(firms2, num_firms, replace=False):
            app_copy = Application()
            app_copy.wrk = worker
            app_copy.w = app.w
            app_copy.s = app.s
            app_copy.ws = app.ws
            app_copy.Te = app.Te
            applications_s2[firm].append(app_copy)
        
        print(f"Worker {worker._id}: Applied to Sector 1 and {num_firms} Firm2s "
              f"(Skills={app.s:.3f}, WageReq=${app.w:.3f})")

print(f"\nTotal Applications to Sector 1: {len(applications_s1)}")
for firm in firms2:
    print(f"Applications to Firm2-{firm._ID2}: {len(applications_s2[firm])}")

# Match workers to Sector 1
print("\n" + "=" * 70)
print("### Matching - Sector 1 ###")

# Try different hiring modes
hiring_modes = [
    (0, "Lowest wage request"),
    (1, "Highest skills"),
    (2, "Longest tenure"),
    (3, "Best wage-skill ratio")
]

for mode, description in hiring_modes:
    matches = labor.match_sector1(firms1, applications_s1.copy(), hiring_mode=mode)
    print(f"\nHiring Mode {mode} ({description}):")
    print(f"  Matches: {len(matches)}")
    if matches:
        for firm, worker, wage in matches[:3]:  # Show first 3
            print(f"    Firm1-{firm._ID} ← Worker {worker._id} @ ${wage:.3f}")

# Match workers to Sector 2
print("\n" + "=" * 70)
print("### Matching - Sector 2 ###")

# Use skills-based hiring
matches_s2 = labor.match_sector2(firms2, applications_s2, hiring_mode=1)
print(f"Total Matches: {len(matches_s2)}")

for firm, worker, wage, action in matches_s2:
    print(f"  Firm2-{firm._ID2} ← Worker {worker._id} @ ${wage:.3f}")

# Compute labor market statistics
print("\n" + "=" * 70)
print("### Labor Market Statistics ###")

# Unemployment rates
Ue, U, Us = labor.compute_unemployment_rate(workers)
print(f"Effective Unemployment Rate: {Ue:.1%}")
print(f"Total Unemployment Rate: {U:.1%}")
print(f"Short-term Unemployment: {Us:.1%}")

# Average wage
wAvg = labor.compute_average_wage(workers)
print(f"\nAverage Wage: ${wAvg:.3f}")

# Average skills
sAvg, sTavg, sVavg = labor.compute_average_skills(workers)
print(f"\nAverage Skills:")
print(f"  Total: {sAvg:.3f}")
print(f"  Tenure: {sTavg:.3f}")
print(f"  Vintage: {sVavg:.3f}")

# Job openings
print("\n" + "=" * 70)
print("### Job Openings ###")

openings_s1 = labor.compute_job_openings_sector1(firms1)
openings_s2 = labor.compute_job_openings_sector2(firms2)

print(f"Sector 1 Openings: {openings_s1}")
print(f"Sector 2 Openings: {openings_s2}")
print(f"Total Openings: {openings_s1 + openings_s2}")

# Training
print("\n" + "=" * 70)
print("### Unemployment Training ###")

training_params = {
    'Gamma': 0.5,    # Train 50% of unemployed
    'tauG': 0.05,    # Learning rate
    'sigma': 0.5     # Target skill level
}

trained = labor.train_unemployed(workers, training_params)
print(f"Workers Trained: {trained}")
print(f"Training Coverage: {trained / max(1, sum(1 for w in workers if w._employed == 0)):.1%}")

# Show updated skills for trained workers
print("\nSkills After Training:")
for worker in workers[:3]:
    if worker._employed == 0:
        print(f"  Worker {worker._id}: Tenure Skills = {worker.read('_sT', 0):.3f}")

print("\n" + "=" * 70)
print("Labor market simulation completed successfully!")
print("=" * 70)

print("\n### Key Observations ###")
print("- Workers apply for jobs based on employment status")
print("- Firms can use different hiring criteria:")
print("  * Lowest wage (cost minimization)")
print("  * Highest skills (productivity maximization)")
print("  * Longest tenure (experience preference)")
print("  * Best wage-skill ratio (efficiency)")
print("- Search and match creates unemployment even with vacancies")
print("- Multiple unemployment measures capture different aspects")
print("- Government training helps unemployed workers maintain skills")
print("- Decentralized matching creates job search frictions")
