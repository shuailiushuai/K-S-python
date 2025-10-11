"""Utility functions for K+S model."""

from .random import (
    KSRandomGenerator,
    get_rng,
    set_rng_seed,
    uniform,
    uniform_int,
    normal,
    beta,
    pareto,
    choice,
    shuffle,
    bernoulli,
)

from .helpers import (
    mov_avg_bound,
    check_error,
    compute_market_share,
    compute_competitiveness,
    apply_replicator_dynamics,
    compute_herfindahl_index,
    select_supplier,
)

__all__ = [
    'KSRandomGenerator',
    'get_rng',
    'set_rng_seed',
    'uniform',
    'uniform_int',
    'normal',
    'beta',
    'pareto',
    'choice',
    'shuffle',
    'bernoulli',
    'mov_avg_bound',
    'check_error',
    'compute_market_share',
    'compute_competitiveness',
    'apply_replicator_dynamics',
    'compute_herfindahl_index',
    'select_supplier',
]
