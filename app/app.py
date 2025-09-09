# allow imports from the project root (so fraud_risk_sim works locally and on Cloud)
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from fraud_risk_sim.config import SimConfig
from fraud_risk_sim.scenarios import make_baseline
from fraud_risk_sim.simulation import run_monte_carlo
from fraud_risk_sim.metrics import kpis
from fraud_risk_sim.sensitivity import tornado_data
from fraud_risk_sim.report import save_hist, save_tornado

st.set_page_config(page_title="Fraud Risk Simulator", page_icon="🛡️", layout="wide")
st.title("Fraud Risk Simulator")

# ===== Instructions (right-side content) =====
INSTRUCTIONS = """
**What it simulates**  
- A Monte Carlo portfolio of transactions over a chosen time horizon.  
- A base **fraud rate** determines how many are truly fraudulent.  
- A **model score** is generated for each txn; higher for fraud, lower for non-fraud, with overlap governed by **model quality / detection rate**.  
- A **decision policy** flags txns; we compute **TP/FP/FN/TN** and monetize outcomes.

**Quick start**  
1. Set **Monthly transactions** and **Average ticket**.  
2. Choose **Base fraud rate** (fraction like 0.003 = 0.3%).  
3. Set **Detection rate** and loss **severity** (μ, σ for lognormal).  
4. Choose **Simulation paths** (more = tighter confidence) and **Random seed**.  
5. Click **Run Simulation**.

**Key inputs**  
- **Base fraud rate** – prevalence of fraud.  
- **Detection rate** – probability your controls flag fraud (at the chosen policy).  
- **Loss severity (μ, σ)** – lognormal parameters governing fraud loss sizes.  
- **Monthly loss budget ($)** – threshold to compute breach probability.  

**Outputs**  
- **KPIs**: Expected net impact, Fraud blocked / Missed, FP cost, Budget breach probability.  
- **Loss distribution** (histogram) and **Sensitivity (tornado)**.
"""

# ====== TOP: two vertical blocks next to each other ======
left, right = st.columns([7,5], gap="large")

with left:
    st.subheader("Controls")

    # Use a baseline config for defaults
    try:
        cfg = make_baseline()
    except Exception:
        # Fallback defaults if make_baseline isn't available at runtime
        class _Cfg: pass
        cfg = _Cfg()
        cfg.n_transactions = 500_000
        cfg.avg_ticket = 50.0
        cfg.base_fraud_rate = 0.003
        cfg.detection_rate = 0.72
        cfg.sev_mu = 3.2
        cfg.sev_sigma = 1.1
        cfg.monthly_loss_budget = 250_000.0
        cfg.seed = 42

    with st.form("sim_inputs"):
        c1, c2, c3 = st.columns(3)

        with c1:
            n_transactions = st.number_input(
                "Monthly transactions",
                value=int(getattr(cfg, "n_transactions", 500_000)),
                step=10_000,
                help="Average monthly transaction count; totals scale with this."
            )
            avg_ticket = st.number_input(
                "Average ticket ($)",
                value=float(getattr(cfg, "avg_ticket", 50.0)),
                step=1.0,
                help="Average transaction amount used to translate rates into dollars."
            )
            base_fraud_rate = st.number_input(
                "Base fraud rate",
                value=float(getattr(cfg, "base_fraud_rate", 0.003)),
                step=0.0001, format="%.4f",
                help="Fraction of transactions that are truly fraudulent (e.g., 0.003 = 0.3%)."
            )

        with c2:
            detection_rate = st.slider(
                "Detection rate",
                min_value=0.0, max_value=1.0,
                value=float(getattr(cfg, "detection_rate", 0.72)), step=0.01,
                help="Probability your controls flag a fraudulent txn at the chosen policy."
            )
            sev_mu = st.number_input(
                "Severity μ (log space)",
                value=float(getattr(cfg, "sev_mu", 3.2)), step=0.1,
                help="Mean of lognormal fraud severity (log space). Higher ⇒ larger typical losses."
            )
            sev_sigma = st.number_input(
                "Severity σ",
                value=float(getattr(cfg, "sev_sigma", 1.1)), step=0.05,
                help="Std dev of lognormal severity; higher ⇒ heavier tails (more extreme losses)."
            )

        with c3:
            monthly_loss_budget = st.number_input(
                "Monthly loss budget ($)",
                value=float(getattr(cfg, "monthly_loss_budget", 250_000.0)),
                step=10_000.0,
                help="Budget threshold used to compute breach probability."
            )
            n_paths = st.slider(
                "Simulation paths",
                min_value=5_000, max_value=100_000,
                value=20_000, step=5_000,
                help="Monte Carlo trials; more = tighter confidence on KPIs (slower)."
            )
            seed = st.number_input(
                "Random seed",
                value=int(getattr(cfg, "seed", 42)), step=1,
                help="Set for reproducible results."
            )

        submitted = st.form_submit_button("Run Simulation")

with right:
    st.subheader("How it works")
    st.markdown(INSTRUCTIONS)

# ====== BOTTOM: horizontal block with outputs ======
st.divider()
results_area = st.container()

if submitted:
    params = dict(
        n_transactions=int(n_transactions),
        avg_ticket=float(avg_ticket),
        base_fraud_rate=float(base_fraud_rate),
        detection_rate=float(detection_rate),
        # retaining placeholder for compatibility if your engine expects it:
        false_positive_rate=getattr(cfg, "false_positive_rate", 0.0),
        sev_mu=float(sev_mu),
        sev_sigma=float(sev_sigma),
        monthly_loss_budget=float(monthly_loss_budget),
    )

    with results_area:
        try:
            res = run_monte_carlo(params, cfg_seed=int(seed), n_paths=int(n_paths))
        except TypeError:
            # Fallback signature without cfg_seed if your function differs
            res = run_monte_carlo(params, int(seed), int(n_paths))

        # KPIs table/metrics
        try:
            summary = kpis(params, res)
        except Exception as e:
            summary = None

        # Show KPIs cleanly
        if summary:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Expected Net Impact ($)", f"{summary.get('net_impact_mean', 0):,.0f}")
            m2.metric("Fraud Blocked ($)", f"{summary.get('blocked_mean', 0):,.0f}")
            m3.metric("Missed Fraud ($)", f"{summary.get('missed_mean', 0):,.0f}")
            m4.metric("Budget Breach P(%)", f"{100*summary.get('budget_breach_prob', 0):.1f}%")

        # Charts: histogram and tornado; saved to outputs/ then displayed
        outdir = Path('outputs'); outdir.mkdir(exist_ok=True)
        hist_png = outdir / 'loss_hist.png'
        tor_png = outdir / 'tornado.png'

        try:
            save_hist(res['losses'], hist_png)
            base_mean, bars = tornado_data(params, cfg_seed=int(seed), n_paths=min(50000, int(n_paths)), perturb=0.2)
            save_tornado(bars, tor_png)

            st.subheader("Loss Distribution")
            st.image(str(hist_png))

            st.subheader("Sensitivity (Tornado)")
            st.image(str(tor_png))
        except Exception as e:
            st.error(f"Could not render charts: {e}")

st.caption('© ' + str(__import__('datetime').datetime.now().year) + ' Joshua J. Middagh')
