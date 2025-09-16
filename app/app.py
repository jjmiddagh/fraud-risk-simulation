# app/app.py
# Streamlit Fraud Risk Simulation UI (complete)
# - Plain-English collapsible "How it works"
# - Stats table ABOVE the chart
# - Altair histogram with rounded x-axis values (configurable decimals)
# - Bin count + Y-scale controls
# - CSV downloads
#
# Requires: streamlit, numpy, pandas, (altair recommended)

import time
import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Simulation binding ----------------
# If you have your own engine at src/simulation.py with:
#   def run_simulation(n_sims, fraud_rate, severity_mu, severity_sigma, seed=None) -> np.ndarray
# this will use it. Otherwise, we fall back to a simple Bernoulli*Lognormal toy model.
SIM_IMPL = None
try:
    from src.simulation import run_simulation as _run_simulation  # type: ignore
    SIM_IMPL = "external"
except Exception:
    SIM_IMPL = "internal"

def run_simulation(n_sims: int, fraud_rate: float, severity_mu: float, severity_sigma: float, seed: int | None) -> np.ndarray:
    if SIM_IMPL == "external":
        return _run_simulation(
            n_sims=n_sims,
            fraud_rate=fraud_rate,
            severity_mu=severity_mu,
            severity_sigma=severity_sigma,
            seed=seed,
        )
    # Fallback toy engine
    rng = np.random.default_rng(seed)
    fraud_flags = rng.binomial(n=1, p=fraud_rate, size=n_sims)
    severities = rng.lognormal(mean=severity_mu, sigma=severity_sigma, size=n_sims)
    losses = fraud_flags * severities
    return losses

def summarize_losses(losses: np.ndarray, var_levels=(0.95, 0.99)) -> pd.DataFrame:
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
        "nonzero_rate": float((s > 0).mean()),
        "total_loss": s.sum(),
    }
    for q in var_levels:
        var_q = s.quantile(q)
        tail = s[s >= var_q]
        cvar_q = tail.mean() if not tail.empty else var_q
        out[f"VaR@{int(q*100)}"] = var_q
        out[f"CVaR@{int(q*100)}"] = cvar_q
    return pd.DataFrame([out])

# ---------------- UI ----------------
st.set_page_config(page_title="Fraud Risk Simulation", page_icon="🎲", layout="wide")
st.title("🎲 Fraud Risk Simulation")

with st.expander("How it works (for everyone)", expanded=False):
    st.markdown(
        """
**Goal**  
Get a quick picture of how much money fraud could cost under different assumptions.

**What you do**  
- Adjust the sliders for how often fraud might happen and how big a fraud loss might be.  
- Click **Run**.

**What happens behind the scenes**  
- Imagine flipping a coin thousands of times. Each flip decides whether a case is fraud (based on the Fraud rate you set).  
- When fraud occurs, we roll the dice to see *how large the loss is*.  
- Doing this many times builds up a picture of both *typical outcomes* and *rare but costly ones*.

**How to read the results**  
- **Average (Mean)** → what you normally expect to lose.  
- **Percentiles (95th / 99th)** → in 95% or 99% of cases, losses are lower than this.  
- **Worst-case thresholds (VaR)** → the cut-off for the worst few percent of scenarios.  
- **Severe tail losses (CVaR)** → if you land in those worst cases, this is the *average hit* you take.
        """
    )

# Sidebar controls
st.sidebar.header("Parameters")
n_sims = st.sidebar.number_input("Number of simulations", min_value=1_000, max_value=5_000_000, value=100_000, step=10_000)
fraud_rate = st.sidebar.slider("Fraud rate (probability)", min_value=0.0, max_value=0.2, value=0.03, step=0.001)
severity_mu = st.sidebar.slider("Severity log-μ", min_value=-2.0, max_value=5.0, value=1.2, step=0.1, help="Higher → larger typical loss when fraud occurs.")
severity_sigma = st.sidebar.slider("Severity log-σ", min_value=0.1, max_value=2.0, value=0.8, step=0.1, help="Higher → more variable/tail-heavy losses.")
seed = st.sidebar.number_input("Random seed (optional)", min_value=0, max_value=10_000_000, value=42, step=1)

st.subheader("Run Simulation")
left, right = st.columns([1, 1])
with left:
    run_clicked = st.button("Run", type="primary")

# Session state for results
if "losses" not in st.session_state:
    st.session_state.losses = None
if "stats" not in st.session_state:
    st.session_state.stats = None

# Run
if run_clicked:
    t0 = time.time()
    losses = run_simulation(
        n_sims=int(n_sims),
        fraud_rate=float(fraud_rate),
        severity_mu=float(severity_mu),
        severity_sigma=float(severity_sigma),
        seed=int(seed),
    )
    dt = time.time() - t0
    stats = summarize_losses(losses)
    stats.insert(0, "runtime_sec", round(dt, 3))
    stats.insert(0, "engine", SIM_IMPL)
    st.session_state.losses = losses
    st.session_state.stats = stats

# ---------------- Output: table FIRST, then chart ----------------
if st.session_state.stats is not None:
    # Stats table
    st.markdown("### Output Statistics")
    st.dataframe(st.session_state.stats, use_container_width=True)

    # Chart controls
    st.markdown("##### Distribution (non-zero losses)")
    nz = st.session_state.losses[st.session_state.losses > 0]

    if nz.size == 0:
        st.info("All simulated losses are zero under current parameters.")
    else:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            bins = st.slider("Bin count", 10, 100, 40, 5)
        with c2:
            y_scale = st.selectbox("Y scale", ["Linear", "Log"], index=0)
        with c3:
            dec = st.slider("Axis decimals", 0, 8, 6)  # controls rounding on x-axis

        # Preferred: Altair chart with rounded labels
        try:
            import altair as alt

            df = pd.DataFrame({"loss": nz})
            fmt = f".{dec}f"  # e.g., ".6f" -> 0.675787

            y_scale_cfg = alt.Scale(type="log") if y_scale == "Log" else alt.Scale(type="linear")

            chart = (
                alt.Chart(df)
                .transform_bin("loss_bin", "loss", maxbins=bins)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "loss_bin:Q",
                        axis=alt.Axis(
                            title="Loss",
                            format=fmt,       # rounded axis labels
                            labelAngle=45,    # rotate to avoid crowding (set 90 for vertical)
                            labelOverlap=False,
                        ),
                    ),
                    y=alt.Y("count()", title="Count", scale=y_scale_cfg),
                    tooltip=[
                        alt.Tooltip("loss_bin:Q", title="Bin start", format=fmt),
                        alt.Tooltip("count()", title="Count"),
                    ],
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            # Fallback if Altair isn't available: rounded labels too
            counts, edges = np.histogram(nz, bins=bins)
            mids = (edges[:-1] + edges[1:]) / 2
            labels = np.round(mids, dec).astype(str)
            hist_df = pd.DataFrame({"loss_bin": labels, "count": counts}).set_index("loss_bin")
            st.bar_chart(hist_df["count"])

    # Downloads
    stats_csv = st.session_state.stats.to_csv(index=False).encode("utf-8")
    st.download_button("Download stats (CSV)", data=stats_csv, file_name="simulation_stats.csv", mime="text/csv")

    if st.checkbox("Include raw losses CSV (may be large)"):
        losses_df = pd.DataFrame({"loss": st.session_state.losses})
        losses_csv = losses_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download raw losses (CSV)", data=losses_csv, file_name="losses.csv", mime="text/csv")
else:
    st.info("Set the sliders on the left, then click **Run** to generate results.")
