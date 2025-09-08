import numpy as np

def kpis(sim_result: dict, monthly_loss_budget: float):
    losses = sim_result['losses']
    var95 = sim_result['var_95']
    cvar95 = sim_result['cvar_95']
    mean_loss = sim_result['mean_loss']

    breach_prob = float((losses > monthly_loss_budget).mean())
    return {
        'expected_loss': float(mean_loss),
        'var_95': float(var95),
        'cvar_95': float(cvar95),
        'breach_prob': float(breach_prob)
    }
