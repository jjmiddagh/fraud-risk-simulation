from fraud_risk_sim.config import SimConfig
from fraud_risk_sim.scenarios import make_baseline
from fraud_risk_sim.simulation import run_monte_carlo
from fraud_risk_sim.metrics import kpis
from fraud_risk_sim.sensitivity import tornado_data
from fraud_risk_sim.report import save_hist, save_tornado, write_markdown
from pathlib import Path

def main():
    cfg = SimConfig()
    params = make_baseline(cfg)
    res = run_monte_carlo(params, seed=cfg.seed, n_paths=20000)
    k = kpis(res, params['monthly_loss_budget'])
    outdir = Path('outputs'); outdir.mkdir(exist_ok=True)
    hist_png = outdir / 'loss_hist.png'
    tor_png = outdir / 'tornado.png'
    save_hist(res['losses'], hist_png)
    base_mean, bars = tornado_data(params, cfg_seed=cfg.seed, n_paths=15000, perturb=0.2)
    save_tornado(bars, tor_png)
    write_markdown(k, hist_png, tor_png, outdir / 'report.md', params)
    print('Report written to', outdir / 'report.md')

if __name__ == '__main__':
    main()
