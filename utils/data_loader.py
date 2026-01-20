"""
Data loading and preparation utilities.

This module handles loading human comparison data from CSV files and
preparing it for model training and evaluation.
"""

import pandas as pd
import math


def load_and_prepare_data(csv_path: str):
    """
    Load training data from CSV and prepare for optimization.
    
    Args:
        csv_path: Path to CSV file with comparison data
        
    Returns:
        samples: List of (idx_a, idx_b, log_multiplier) tuples
        repo_to_idx: Dict mapping repo URL to index
        idx_to_repo: Dict mapping index to repo URL
        df: Original dataframe for reference
    """
    df = pd.read_csv(csv_path)
    
    # Create repository index
    all_repos = set(df['repo_a'].unique()) | set(df['repo_b'].unique())
    repo_to_idx = {repo: idx for idx, repo in enumerate(sorted(all_repos))}
    idx_to_repo = {idx: repo for repo, idx in repo_to_idx.items()}
    
    # Convert to indexed samples
    samples = []
    for _, row in df.iterrows():
        idx_a = repo_to_idx[row['repo_a']]
        idx_b = repo_to_idx[row['repo_b']]
        
        # Convert multiplier to log space
        # choice=1 means repo_a is better (negative log)
        # choice=2 means repo_b is better (positive log)
        log_mult = math.log(row['multiplier'])
        if row['choice'] == 1:
            log_mult = -log_mult
        
        samples.append((idx_a, idx_b, log_mult))
    
    return samples, repo_to_idx, idx_to_repo, df
