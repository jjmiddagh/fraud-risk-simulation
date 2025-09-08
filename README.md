# Fraud Risk Simulation

Monte Carlo engine for model risk limits with fast scenario sampling and automated sensitivity reports.

**What it shows on your portfolio**
- Executive-quality case study (Quarto `.qmd` provided)
- Clean Python package with tests-ready structure
- Risk limits analysis: expected loss, VaR/CVaR, budget breach probability
- Scenario sampling (stratified/Latin Hybrid) and sensitivity (tornado chart)
- Reproducible report artifacts in `outputs/`

## Quickstart

```bash
# create env (example)
python -m venv .venv && . .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run a demo simulation & generate report
python run_simulation.py

# (optional) launch the Streamlit app
streamlit run app/app.py
```

## Project Layout
```
fraud-risk-simulation/
├─ fraud_risk_sim/
│  ├─ __init__.py
│  ├─ config.py            # Risk knobs and defaults
│  ├─ scenarios.py         # Scenario generation (baseline, stress, LHS sampler)
│  ├─ simulation.py        # Core Monte Carlo engine
│  ├─ metrics.py           # KPIs: VaR, CVaR, breach prob, etc.
│  ├─ sensitivity.py       # One-way and multi-way sensitivity
│  ├─ report.py            # Save plots & markdown report
├─ app/
│  └─ app.py               # Streamlit front end
├─ outputs/                # Auto-generated charts and report.md
├─ images/
│  └─ fraud-sim.png        # Promo image (generated)
├─ docs/
│  └─ fraud-risk-simulation.qmd  # Portfolio case study page
├─ run_simulation.py
├─ requirements.txt
├─ LICENSE
└─ README.md
```

## Notes
- All randomness uses a `seed` to remain reproducible.
- Replace simple placeholder fraud model with your production scoring logic or a calibrated probability function.
