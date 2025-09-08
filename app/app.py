
# allow imports from the project root (so fraud_risk_sim works on Cloud)
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
from pathlib import Path

st.set_page_config(page_title='Fraud Risk Simulation', layout='wide')
st.title('Fraud Risk Simulation')

cfg = SimConfig()

cols = st.columns(3)
with cols[0]:
    n_transactions = st.number_input('Monthly transactions', value=cfg.n_transactions, step=10000)
    avg_ticket = st.number_input('Average ticket', value=cfg.avg_ticket, step=1.0)
    base_fraud_rate = st.number_input('Base fraud rate', value=cfg.base_fraud_rate, step=0.0001, format='%.4f')
with cols[1]:
    detection_rate = st.slider('Detection rate', 0.0, 1.0, cfg.detection_rate, 0.01)
    sev_mu = st.number_input('Severity mu (log space)', value=cfg.sev_mu, step=0.1)
    sev_sigma = st.number_input('Severity sigma', value=cfg.sev_sigma, step=0.05)
with cols[2]:
    monthly_loss_budget = st.number_input('Monthly loss budget', value=cfg.monthly_loss_budget, step=10000.0)
    n_paths = st.slider('Simulation paths', 5_000, 100_000, 20_000, step=5_000)
    seed = st.number_input('Random seed', value=cfg.seed, step=1)

params = dict(
    n_transactions=int(n_transactions),
    avg_ticket=float(avg_ticket),
    base_fraud_rate=float(base_fraud_rate),
    detection_rate=float(detection_rate),
    false_positive_rate=cfg.false_positive_rate,
    sev_mu=float(sev_mu),
    sev_sigma=float(sev_sigma),
    monthly_loss_budget=float(monthly_loss_budget)
)

if st.button('Run Simulation'):
    res = run_monte_carlo(params, seed=int(seed), n_paths=int(n_paths))
    k = kpis(res, monthly_loss_budget)
    colA, colB, colC, colD = st.columns(4)
    colA.metric('Expected Loss', f"${k['expected_loss']:,.0f}")
    colB.metric('VaR(95%)', f"${k['var_95']:,.0f}")
    colC.metric('CVaR(95%)', f"${k['cvar_95']:,.0f}")
    colD.metric('Budget Breach Prob', f"{100*k['breach_prob']:.1f}%")

    # charts to temp files in outputs/
    outdir = Path('outputs'); outdir.mkdir(exist_ok=True)
    hist_png = outdir / 'loss_hist.png'
    tor_png = outdir / 'tornado.png'
    save_hist(res['losses'], hist_png)
    base_mean, bars = tornado_data(params, cfg_seed=int(seed), n_paths=min(50000, int(n_paths)), perturb=0.2)
    save_tornado(bars, tor_png)

    st.subheader('Loss Distribution')
    st.image(str(hist_png))

    st.subheader('Sensitivity (Tornado)')
    st.image(str(tor_png))

st.caption('© ' + str(__import__('datetime').datetime.now().year) + ' Joshua J. Middagh')
