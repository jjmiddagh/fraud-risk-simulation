# app/app.py
import time
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

# ---- Try to use your existing simulation engine if present ----
# Expecting a function like: run_simulation(n_sims, fraud_rate, severity_mu, severity_sigma, seed) -> np.ndarray
SIM_IMPL = None
try:
    # If your project uses src/simulation.py with run_simulation
    from src.simulation import run_simulation as _run_simulation  # type: ignore
    SIM_IMPL = "external"
except Exception:
    SIM_IMPL = "internal"

def run_simulation(n_sims: int, fraud_rate: float, severity_mu: float, severity_sigma: float, seed: int | None) -> np.ndarray:
    """Fallback simulator if src.simulation isn't available."""
    if SIM_IMPL == "external":
        return _run_simulation(n_sims=n_sims, fraud_rate=fraud_rate, severity_mu=severity_mu, severity_sigma=severity_sigma, seed=seed)
    rng = np.random.default_rng(seed)
    # Bernoulli for fraud occurrence; Lognormal for severity (example)
    fraud_flags = rng.binomial(n=1, p=fraud_rate, size=n_sims)
    severities = rng.lognormal(mean=severity_mu, sigma=severity_sigma, size=n_sims)
    losses = fraud_flags * severities
    return losses

def summarize_losses(losses: np.ndarray, var_levels=(0.95, 0.99)) -> pd.DataFrame:
    """Return a 1-row DataFrame of summary statistics."""
    if losses.size == 0:
        return pd.DataFrame()
    s = pd.Series(losses)
    out = {
        "samples": int(s.size),
        "mean": s.mean(),
        "std": s.std(ddof=1),
        "min": s.min(),
        "p50": s.quantile(0.50),
        "p90": s.quantile(0.90),
        "p95": s.quantile(0.95),
        "p99": s.quantile(0.99),
        "max": s.max(),
        "nonzero_rate": (s > 0).mean(),
        "total_loss": s.sum(),
    }
    # VaR / CVaR
    for q in var_levels:
        var = s.quantile(q)
        tail = s[s >= var]
        cvar = tail.mean() if not tail.empty else var
        out[f"VaR@{int(q*100)}"] = var
        out[f"CVaR@{int(q*100)}"] = cvar
    return pd.DataFrame([out])

# ----------------- UI -----------------
st.set_page_config(page_title="Fraud Risk Simulation", page_icon="🎲", layout="wide")
st.title("🎲 Fraud Risk Simulation")

# === Collapsible "How It Works" ===
with st.expander("How It Works", expanded=False):
    st.markdown("""
    This app simulates fraud losses using Monte Carlo techniques:
    1) We sample whether a transaction is fraudulent (Bernoulli with `fraud_rate`).
    2) If fraudulent, we draw a **severity** (lognormal with `severity_mu` and `severity_sigma`).
    3) Aggregate the resulting loss distribution and compute portfolio risk metrics (**VaR**, **CVaR**, percentiles, etc.).
    
    **Notes**
    - Parameters are illustrative; plug in your model’s true distributions/priors as needed.
    - If `src/simulation.run_simulation(...)` exists in your repo, the app will use it automatically.
    """)

# === Sidebar parameters ===
st.sidebar.header("Parameters")
n_sims = st.sidebar.number_input("Number of simulations", min_value=1000, max_value=5_000_000, value=100_000, step=10_000, help="Total Monte Carlo draws.")
fraud_rate = st.sidebar.slider("Fraud rate (probability)", min_value=0.0, max_value=0.2, value=0.03, step=0.001)
severity_mu = st.sidebar.slider("Severity log-μ", min_value=-2.0, max_value=5.0, value=1.2, step=0.1, help="Mean of lognormal (log-space).")
severity_sigma = st.sidebar.slider("Severity log-σ", min_value=0.1, max_value=2.0, value=0.8, step=0.1, help="Std dev of lognormal (log-space).")
seed = st.sidebar.number_input("Random seed (optional)", min_value=0, max_value=10_000_000, value=42, step=1)

# === Main run section ===
st.subheader("Run Simulation")
run_col, dl_col = st.columns([1,1])

with run_col:
    run_clicked = st.button("Run", type="primary")

# State for results
if "losses" not in st.session_state:
    st.session_state.losses = None
if "stats" not in st.session_state:
    st.session_state.stats = None

if run_clicked:
    start = time.time()
    losses = run_simulation(
        n_sims=int(n_sims),
        fraud_rate=float(fraud_rate),
        severity_mu=float(severity_mu),
        severity_sigma=float(severity_sigma),
        seed=int(seed) if seed is not None else None,
    )
    dur = time.time() - start
    stats = summarize_losses(losses)
    stats.insert(0, "runtime_sec", round(dur, 3))
    stats.insert(0, "engine", SIM_IMPL)

    st.session_state.losses = losses
    st.session_state.stats = stats

# === Output: chart + DATA TABLE OF STATS ===
if st.session_state.stats is not None:
    st.markdown("##### Distribution (non-zero losses)")
    nz = st.session_state.losses[st.session_state.losses > 0]
    if nz.size > 0:
        hist_df = pd.DataFrame({"loss": nz})
        st.bar_chart(hist_df.value_counts(bins=50, sort=False).rename("count"))  # quick density proxy
    else:
        st.info("All simulated losses are zero under current parameters.")

    st.markdown("### Output Statistics")
    st.dataframe(st.session_state.stats, use_container_width=True)

    # Download buttons
    with dl_col:
        stats_csv = st.session_state.stats.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download stats (CSV)",
            data=stats_csv,
            file_name="simulation_stats.csv",
            mime="text/csv",
        )
        # Raw losses can be large; gate behind a checkbox
        if st.checkbox("Include raw losses CSV (may be large)"):
            losses_df = pd.DataFrame({"loss": st.session_state.losses})
            losses_csv = losses_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download raw losses (CSV)",
                data=losses_csv,
                file_name="losses.csv",
                mime="text/csv",
            )
else:
    st.info("Configure parameters in the sidebar and click **Run** to generate results.")
