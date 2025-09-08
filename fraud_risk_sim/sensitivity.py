import numpy as np
from .simulation import run_monte_carlo

def tornado_data(params: dict, cfg_seed=42, n_paths=10000, perturb=0.2):
    """Return low/high KPI deltas for key drivers using a +/- perturbation.
    """
    keys = ['base_fraud_rate', 'detection_rate', 'sev_sigma']
    base = run_monte_carlo(params, seed=cfg_seed, n_paths=n_paths)
    base_mean = base['mean_loss']
    bars = []
    for k in keys:
        p_lo = params.copy()
        p_hi = params.copy()
        if k == 'detection_rate':
            p_lo[k] = max(0.0, params[k]*(1-perturb))
            p_hi[k] = min(1.0, params[k]*(1+perturb))
        else:
            p_lo[k] = params[k]*(1-perturb)
            p_hi[k] = params[k]*(1+perturb)
        lo = run_monte_carlo(p_lo, seed=cfg_seed, n_paths=n_paths)['mean_loss']
        hi = run_monte_carlo(p_hi, seed=cfg_seed, n_paths=n_paths)['mean_loss']
        bars.append((k, float(lo - base_mean), float(hi - base_mean)))
    # sort by absolute impact (max of |lo|, |hi|)
    bars.sort(key=lambda x: max(abs(x[1]), abs(x[2])), reverse=True)
    return base_mean, bars
