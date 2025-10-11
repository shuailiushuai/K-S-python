"""
Unit tests for Worker agent.

Tests the worker agent implementation against expected behaviors
from the C++ model (fun_KS_worker.h).
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ks_model.agents import Worker
from ks_model.types import INISKILL, INIWAGE
from utils import set_rng_seed


@pytest.fixture
def worker_params():
    """Standard worker parameters for testing."""
    return {
        'Tc': 12,
        'Tr': 40,
        'w0min': 1.0,
        'Ts': 4,
        'epsilon': 0.05,
        'omega': 5,
        'omegaU': 10,
        'flagSearchMode': 0,
        'flagWorkerLBU': 3,
        'tauT': 0.01,
        'tauU': 0.02,
    }


@pytest.fixture
def worker(worker_params):
    """Create a standard worker for testing."""
    set_rng_seed(12345)
    return Worker(worker_id=1, initial_params=worker_params)


class TestWorkerInitialization:
    """Test worker initialization."""
    
    def test_worker_creation(self, worker):
        """Test that worker is created with correct initial values."""
        assert worker.state.ID == 1
        assert worker.state.employed == 0
        assert worker.state.age == 1
        assert worker.state.Te == 0
        assert worker.state.w == INIWAGE
        assert worker.state.s == INISKILL
        assert worker.state.sV == INISKILL
        assert worker.state.sT == INISKILL
    
    def test_worker_parameters(self, worker):
        """Test that parameters are correctly set."""
        assert worker.state.Tc == 12
        assert worker.state.retirement_age == 40
        assert worker.state.wRes == 1.0


class TestWorkerAging:
    """Test worker aging and retirement."""
    
    def test_age_increment(self, worker):
        """Test that worker age increases correctly."""
        initial_age = worker.state.age
        new_age = worker.compute_age(t=1)
        assert new_age == initial_age + 1
        assert worker.state.age == new_age
    
    def test_retirement(self, worker_params):
        """Test that worker retires and is reborn."""
        # Create worker at retirement age
        worker = Worker(worker_id=1, initial_params=worker_params)
        worker.state.age = 40  # At retirement age
        worker.state.employed = 2
        worker.state.Te = 20
        
        new_age = worker.compute_age(t=1)
        
        # Should be reborn at age 1
        assert new_age == 1
        assert worker.state.age == 1
        assert worker.state.employed == 0
        assert worker.state.Te == 0


class TestWorkerSkills:
    """Test worker skill dynamics."""
    
    def test_skills_deteriorate_unemployed(self, worker):
        """Test that skills deteriorate when unemployed."""
        worker.state.employed = 0
        worker.state.sT = 1.0
        
        initial_skills = worker.state.sT
        worker.compute_skills(t=1)
        
        # Skills should decrease by tauU (0.02)
        expected = initial_skills * (1 - 0.02)
        assert abs(worker.state.sT - expected) < 0.001
    
    def test_skills_improve_employed(self, worker):
        """Test that skills improve when employed."""
        worker.state.employed = 2
        worker.state.sT = 1.0
        
        initial_skills = worker.state.sT
        worker.compute_skills(t=1)
        
        # Skills should increase by tauT (0.01)
        expected = initial_skills * (1 + 0.01)
        assert abs(worker.state.sT - expected) < 0.001
    
    def test_compound_skills(self, worker):
        """Test compound skills calculation."""
        worker.state.sV = 1.2
        worker.state.sT = 0.8
        worker.state.employed = 0  # Unemployed so sT will deteriorate
        
        # Mode 3: average of vintage and tenure
        skills = worker.compute_skills(t=1)
        
        # sT deteriorates by tauU (0.02), sV stays same
        expected_sT = 0.8 * (1 - 0.02)
        expected = (1.2 + expected_sT) / 2
        assert abs(skills - expected) < 0.001


class TestWorkerWages:
    """Test worker wage dynamics."""
    
    def test_requested_wage_no_memory(self, worker_params):
        """Test requested wage with no memory."""
        worker_params['Ts'] = 0
        worker = Worker(worker_id=1, initial_params=worker_params)
        
        requested = worker.compute_requested_wage(t=1)
        assert requested == worker.state.wRes
    
    def test_requested_wage_with_memory(self, worker):
        """Test requested wage with memory."""
        # Set wage history
        worker.state.w_history = [1.5, 1.4, 1.3, 1.2]
        
        requested = worker.compute_requested_wage(t=1)
        
        # Should be average of last 4 wages plus epsilon
        avg = (1.5 + 1.4 + 1.3 + 1.2) / 4
        expected = avg * (1 + 0.05)
        assert abs(requested - expected) < 0.001
    
    def test_update_wage(self, worker):
        """Test wage update and history tracking."""
        worker.update_wage(1.5, t=1)
        
        assert worker.state.w == 1.5
        assert worker.state.w_history[0] == 1.5
        assert len(worker.state.w_history) <= 8


class TestWorkerJobAcceptance:
    """Test worker job offer acceptance."""
    
    def test_accept_job_when_unemployed(self, worker):
        """Test that unemployed worker accepts any reasonable offer."""
        worker.state.employed = 0
        worker.state.w = 1.0
        
        # Mock firm object
        class MockFirm:
            pass
        
        firm = MockFirm()
        accepted = worker.accept_job_offer(firm, 1.1, 2, t=1)
        
        assert accepted
        assert worker.state.employed == 2
        assert worker.state.employer == firm
        assert worker.state.w == 1.1
    
    def test_reject_lower_wage_when_employed(self, worker):
        """Test that employed worker rejects lower wage offers."""
        worker.state.employed = 2
        worker.state.w = 1.5
        
        class MockFirm:
            pass
        
        firm = MockFirm()
        accepted = worker.accept_job_offer(firm, 1.4, 2, t=1)
        
        assert not accepted
        assert worker.state.w == 1.5  # Wage unchanged


class TestWorkerProduction:
    """Test worker production output."""
    
    def test_production_with_vintage(self, worker):
        """Test production when worker is allocated to a vintage."""
        class MockVintage:
            A = 2.0  # Productivity
        
        worker.state.employer_vintage = MockVintage()
        worker.state.s = 1.5
        
        production = worker.compute_production()
        
        # Q = s * A_vintage
        expected = 1.5 * 2.0
        assert abs(production - expected) < 0.001
    
    def test_production_without_vintage(self, worker):
        """Test production when worker has no vintage."""
        worker.state.employer_vintage = None
        
        production = worker.compute_production()
        
        assert production == 0.0


class TestWorkerDataExport:
    """Test worker data export."""
    
    def test_to_dict(self, worker):
        """Test worker state export to dictionary."""
        data = worker.to_dict()
        
        assert isinstance(data, dict)
        assert 'ID' in data
        assert 'employed' in data
        assert 'age' in data
        assert 'w' in data
        assert 's' in data
        assert data['ID'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
