import numpy as np

def run_monte_carlo(params: dict, seed: int = 42, n_paths: int = 10_000):
    rng = np.random.default_rng(seed)

    n_tx = params['n_transactions']
    avg_ticket = params['avg_ticket']
    p_fraud = params['base_fraud_rate']
    p_detect = params['detection_rate']
    sev_mu = params['sev_mu']
    sev_sigma = params['sev_sigma']

    # Approximate number of fraudulent transactions per path ~ Binomial
    # But to be fast, use Poisson approximation with lambda = n_tx * p_fraud
    lam = n_tx * p_fraud
    n_fraud = rng.poisson(lam, size=n_paths).astype(np.int64)

    # Loss severity for *undetected* fraud only
    # fraction not detected:
    frac_undetected = np.clip(1.0 - p_detect, 0.0, 1.0)

    # For efficiency, draw a big pool of severities then segment per path
    total_draws = int(n_fraud.sum() * frac_undetected + 1)
    if total_draws <= 0:
        # No fraud draws; return zeros
        losses = np.zeros(n_paths)
        return {
            'losses': losses,
            'mean_loss': losses.mean(),
            'var_95': np.quantile(losses, 0.95),
            'cvar_95': 0.0,
            'n_fraud_mean': n_fraud.mean(),
        }

    severities = np.exp(rng.normal(sev_mu, sev_sigma, size=total_draws))

    # Aggregate by path
    losses = np.zeros(n_paths)
    cursor = 0
    for i, nf in enumerate(n_fraud):
        undet = int(nf * frac_undetected)
        if undet > 0:
            sl = severities[cursor: cursor + undet].sum()
            cursor += undet
        else:
            sl = 0.0
        losses[i] = sl

    # Metrics
    var_95 = np.quantile(losses, 0.95)
    tail = losses[losses >= var_95]
    cvar_95 = tail.mean() if tail.size else 0.0

    return {
        'losses': losses,
        'mean_loss': float(losses.mean()),
        'var_95': float(var_95),
        'cvar_95': float(cvar_95),
        'n_fraud_mean': float(n_fraud.mean()),
    }
