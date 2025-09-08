from dataclasses import dataclass

@dataclass
class SimConfig:
    # Portfolio/traffic
    n_transactions: int = 1_000_000
    avg_ticket: float = 85.0  # USD
    # Fraud model
    base_fraud_rate: float = 0.004  # 0.4%
    detection_rate: float = 0.72    # share of fraud detected/blocked
    false_positive_rate: float = 0.01
    # Loss severity (lognormal params)
    sev_mu: float = 4.2   # mean of log
    sev_sigma: float = 0.9  # std of log
    # Controls/budget
    monthly_loss_budget: float = 350_000.0
    # Random seed
    seed: int = 42
