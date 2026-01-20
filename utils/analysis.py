"""
Analysis and evaluation utilities.

This module provides functions for printing model weights and repository rankings.
"""

import numpy as np
from typing import List, Tuple, Dict


def print_optimal_weights(model_names: List[str], optimal_weights: List[float]):
    """
    Print optimal weights in a visual format.
    
    Args:
        model_names: List of model names
        optimal_weights: Optimal weights for each model
    """
    print("\n✓ Optimal Weights Found:")
    for name, weight in zip(model_names, optimal_weights):
        bar_length = int(weight * 50)
        bar = '█' * bar_length
        print(f"  {name:20s}: {weight:.4f} {bar}")


def print_top_repositories(repo_scores: List[Tuple[str, float]], top_n: int = 15):
    """
    Print top N repositories with their scores.
    
    Args:
        repo_scores: List of (repo_url, score) tuples
        top_n: Number of top repositories to display
    """
    print(f"\n  Top {top_n} Repositories:")
    max_score = repo_scores[0][1] if repo_scores else 1.0
    
    for i, (repo, score) in enumerate(repo_scores[:top_n], 1):
        repo_name = repo.split('/')[-1]
        stars = '⭐' * min(5, int(score / max_score * 5) + 1)
        print(f"  {i:2d}. {repo_name:35s} (score: {score:7.4f}) {stars}")


def evaluate_performance(
    samples: List[Tuple],
    ai_comparisons: Dict[str, List[float]],
    optimal_weights: List[float],
    model_names: List[str]
) -> Dict:
    """
    Evaluate model performance on test set.
    
    Args:
        test_samples: Test set samples (idx_a, idx_b, human_log_mult)
        test_ai_comparisons: AI predictions on test set
        optimal_weights: Optimal weights from training
        model_names: List of model names
        
    Returns:
        Dict with evaluation metrics
    """
    # Compute weighted predictions
    weighted_predictions = []
    human_judgments = []
    
    for i, (idx_a, idx_b, human_log_mult) in enumerate(samples):
        if i >= len(ai_comparisons[model_names[0]]):
            break
            
        # Weighted combination of AI predictions
        weighted_pred = sum(
            w * ai_comparisons[model][i]
            for w, model in zip(optimal_weights, model_names)
        )
        weighted_predictions.append(weighted_pred)
        human_judgments.append(human_log_mult)
    
    weighted_predictions = np.array(weighted_predictions)
    human_judgments = np.array(human_judgments)
    
    # Compute metrics
    # 1. Mean squared error
    mse = np.mean((weighted_predictions - human_judgments) ** 2)
    
    # 2. Agreement rate (same sign)
    agreement_rate = np.mean(np.sign(weighted_predictions) == np.sign(human_judgments))
    
    # 3. Correlation
    correlation = np.corrcoef(weighted_predictions, human_judgments)[0, 1]
    
    # 4. Mean absolute error
    mae = np.mean(np.abs(weighted_predictions - human_judgments))
    
    return {
        'mse': mse,
        'rmse': np.sqrt(mse),
        'mae': mae,
        'agreement_rate': agreement_rate,
        'correlation': correlation,
        'num_samples': len(weighted_predictions)
    }


def print_evaluation(metrics: Dict):
    """
    Print test evaluation metrics in a nice format.
    
    Args:
        metrics: Dictionary of evaluation metrics
    """
    
    print(f"\n  Samples evaluated: {metrics['num_samples']}")
    print(f"\n  Agreement Metrics:")
    print(f"    • Agreement rate:  {metrics['agreement_rate']:.2%} (predictions match human direction)")
    print(f"    • Correlation:     {metrics['correlation']:.4f} (Pearson correlation)")
    
    print(f"\n  Error Metrics:")
    print(f"    • MSE:             {metrics['mse']:.4f}")
    print(f"    • RMSE:            {metrics['rmse']:.4f}")
    print(f"    • MAE:             {metrics['mae']:.4f}")


def evaluate_on_dataset(
    samples: List[Tuple],
    logits: List[np.ndarray],
    optimal_weights: List[float],
    model_names: List[str],
) -> Dict:
    """
    Evaluate model performance on a dataset by computing predictions from logits.
    
    Args:
        samples: Dataset samples (idx_a, idx_b, human_log_mult)
        logits: Logits for each model [num_models x num_repos]
        optimal_weights: Optimal weights from training
        model_names: List of model names
        dataset_name: Name of dataset for display (e.g., "Training Set", "Test Set")
        
    Returns:
        Dict with evaluation metrics
    """
    
    # Create predictions from weighted logits
    ai_comparisons = {}
    for i, model_name in enumerate(model_names):
        predictions = []
        for idx_a, idx_b, _ in samples:
            # Compute difference in logits for this comparison
            pred = logits[i][idx_b] - logits[i][idx_a]
            predictions.append(pred)
        ai_comparisons[model_name] = predictions
    
    # Evaluate performance
    metrics = evaluate_performance(
        samples,
        ai_comparisons,
        optimal_weights,
        model_names
    )
    
    # Print results
    print_evaluation(metrics)
    
    return metrics
