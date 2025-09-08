import numpy as np
from .config import SimConfig

def make_baseline(cfg: SimConfig):
    return dict(
        n_transactions=cfg.n_transactions,
        avg_ticket=cfg.avg_ticket,
        base_fraud_rate=cfg.base_fraud_rate,
        detection_rate=cfg.detection_rate,
        false_positive_rate=cfg.false_positive_rate,
        sev_mu=cfg.sev_mu,
        sev_sigma=cfg.sev_sigma,
        monthly_loss_budget=cfg.monthly_loss_budget,
    )

def make_stress(cfg: SimConfig, fraud_uplift=1.5, detection_drop=0.9, sigma_uplift=1.1):
    """Stress scenario that increases fraud rate and severity and reduces detection.
    """
    s = make_baseline(cfg)
    s['base_fraud_rate'] *= fraud_uplift
    s['detection_rate'] *= detection_drop
    s['sev_sigma'] *= sigma_uplift
    return s

def lhs_samples(low_high_pairs, n, seed=42):
    """Simple Latin-hypercube-like sampler on independent ranges.
    low_high_pairs: dict[name] = (low, high)
    """
    rng = np.random.default_rng(seed)
    out = []
    for k, (lo, hi) in low_high_pairs.items():
        # stratified bins
        bins = np.linspace(0, 1, n+1)
        u = (bins[:-1] + bins[1:]) / 2.0
        rng.shuffle(u)
        vals = lo + u * (hi - lo)
        out.append(vals)
    # stack into records
    samples = [ {k: out[i][j] for i, k in enumerate(low_high_pairs.keys())} for j in range(n) ]
    return samples
