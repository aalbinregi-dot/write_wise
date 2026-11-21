"""
Evaluation Metrics — QWK, MAE, RMSE, Pearson, Spearman
"""
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score, mean_absolute_error, mean_squared_error


def quadratic_weighted_kappa(y_true, y_pred, min_score=1, max_score=6):
    """Compute Quadratic Weighted Kappa — primary metric for essay scoring."""
    y_true_r = np.clip(np.round(y_true).astype(int), min_score, max_score)
    y_pred_r = np.clip(np.round(y_pred).astype(int), min_score, max_score)
    return cohen_kappa_score(y_true_r, y_pred_r, weights='quadratic')


def compute_all_metrics(y_true, y_pred, min_score=1, max_score=6):
    """Compute all essay scoring evaluation metrics."""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    qwk   = quadratic_weighted_kappa(y_true, y_pred, min_score, max_score)
    mae   = mean_absolute_error(y_true, y_pred)
    rmse  = np.sqrt(mean_squared_error(y_true, y_pred))
    r_p, _ = pearsonr(y_true, y_pred)
    r_s, _ = spearmanr(y_true, y_pred)

    return {
        'qwk':     round(float(qwk),  4),
        'mae':     round(float(mae),  4),
        'rmse':    round(float(rmse), 4),
        'pearson': round(float(r_p),  4),
        'spearman':round(float(r_s),  4),
    }


def print_metrics_table(results: dict):
    """Print comparison table of all models."""
    print(f"\n{'Model':<35} {'QWK':>8} {'MAE':>8} {'RMSE':>8} {'Pearson':>10} {'Spearman':>10}")
    print('-' * 80)
    for model_name, metrics in results.items():
        print(f"{model_name:<35} {metrics['qwk']:>8.4f} {metrics['mae']:>8.4f} "
              f"{metrics['rmse']:>8.4f} {metrics['pearson']:>10.4f} {metrics['spearman']:>10.4f}")
