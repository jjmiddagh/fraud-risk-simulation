import os
import numpy as np
import matplotlib.pyplot as plt

def save_hist(losses, out_png):
    plt.figure()
    plt.hist(losses, bins=60)
    plt.xlabel('Monthly fraud loss')
    plt.ylabel('Frequency')
    plt.title('Loss distribution')
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()

def save_tornado(bars, out_png):
    labels = [k for k, lo, hi in bars]
    lows = [min(lo, hi) for k, lo, hi in bars]
    highs = [max(lo, hi) for k, lo, hi in bars]
    y = range(len(labels))
    plt.figure()
    for i in y:
        plt.plot([lows[i], highs[i]], [i, i])
    plt.yticks(list(y), labels)
    plt.xlabel('Δ mean loss vs baseline')
    plt.title('Sensitivity (tornado)')
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()

def write_markdown(kpi_dict, hist_png, tor_png, out_md, params):
    lines = []
    lines.append('# Fraud Risk Simulation Report\n')
    lines.append('## Key Performance Indicators\n')
    for k, v in kpi_dict.items():
        lines.append(f'- **{k.replace("_"," ").title()}**: {v:,.2f}\n')
    lines.append('\n## Distribution\n')
    lines.append(f'![]({os.path.basename(hist_png)})\n')
    lines.append('\n## Sensitivity\n')
    lines.append(f'![]({os.path.basename(tor_png)})\n')
    lines.append('\n## Inputs\n')
    for k, v in params.items():
        lines.append(f'- {k}: {v}\n')
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
