"""
Example: Basic Worker Agent Usage
Demonstrates the worker agent implementation
"""

from model.worker import Worker
from model.agent import Agent
from model.random_engine import random_engine
from model.constants import INISKILL

# Initialize random engine for reproducibility
random_engine.seed(12345)

# Create a mock Labor parent agent
labor = Agent("Labor", None)
labor.set_param("Tr", 40)  # Retirement age
labor.set_param("Gamma", 0.5)  # Training coverage
labor.set_param("tauG", 0.05)  # Training learning factor
labor.set_param("tauU", 0.01)  # Unemployment deterioration
labor.set_param("tauT", 0.02)  # Tenure learning factor
labor.set_param("sigma", 0.5)  # Public skill level
labor.write("sTavg", 1.0, 1)  # Average tenure skills
labor.write("sTmin", 0.8, 1)  # Minimum tenure skills

# Create a mock Country grandparent
country = Agent("Country", None)
country.add_child(labor)
country.set_param("flagWorkerLBU", 3)  # Both learning modes
country.set_param("flagWorkerSkProd", 3)  # Both skills affect productivity
country.set_param("flagLearn1", 2)  # Increase skills in sector 1
country.set_param("flagSearchMode", 0)  # Always search
country.set_param("flagSearchDisc", 0)  # No discouragement

# Create worker
worker = Worker(worker_id=1, parent=labor)
worker.initialize(age=25, tc=12, w_res=1.0, sv0=0.9)

print("=" * 60)
print("K+S Model - Worker Agent Example")
print("=" * 60)

# Simulate 10 periods
for t in range(1, 11):
    print(f"\n--- Period {t} ---")
    
    # Update age
    age = worker.compute_age(tr=40)
    print(f"Age: {age}")
    
    # Update skills
    skills = worker.compute_skills(
        flag_worker_lbu=3,
        flag_worker_sk_prod=3,
        flag_learn1=2,
        gamma=0.5,
        tau_g=0.05,
        tau_u=0.01,
        tau_t=0.02,
        sigma=0.5
    )
    print(f"Skills: {skills:.4f} (Tenure: {worker._sT:.4f}, Vintage: {worker._sV:.4f})")
    
    # Compute search probability
    search_prob = worker.compute_search_probability(
        flag_search_disc=0,
        search_prob=1.0,
        lambda_val=0.1
    )
    print(f"Search Probability: {search_prob:.4f}")
    
    # Apply for jobs
    num_applications = worker.apply_for_jobs(
        omega=3.0,  # Employed apply to 3 firms
        omega_u=5.0,  # Unemployed apply to 5 firms
        flag_search_mode=0
    )
    print(f"Applications: {num_applications}, Discouraged: {worker._discouraged}")
    
    # Update employment status (simulate employment in period 5)
    if t == 5:
        worker._employed = 2  # Hired in sector 2
        worker._Te = 0
        worker._Tu = 0
        worker.write("_employed", 2)
        print(">>> Worker hired in sector 2!")
    
    # Update lags for next period
    worker.update_lags()

print("\n" + "=" * 60)
print("Simulation completed successfully!")
print("=" * 60)

print("\n### Final Worker State ###")
print(f"Age: {worker._age_val}")
print(f"Employment Status: {worker._employed} (0=unemployed, 1=sector1, 2=sector2)")
print(f"Skills: {worker._s:.4f}")
print(f"Tenure Skills: {worker._sT:.4f}")
print(f"Vintage Skills: {worker._sV:.4f}")
print(f"Employment Tenure: {worker._Te}")
print(f"Unemployment Duration: {worker._Tu}")
