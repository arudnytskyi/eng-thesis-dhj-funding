"""
Optimized AI Model Alignment Workflow using Repository Scoring.

This workflow:
1. Asks AI models for COMPLETE scores for all repositories
2. Converts scores to logits
3. Uses train.csv samples to find optimal model weights
4. Evaluates on test.csv for generalization metrics


Usage:
    python main.py
"""

import json
from typing import List, Dict, Optional

import config
from utils.data_loader import load_and_prepare_data
from utils.analysis import (
    print_optimal_weights,
    print_top_repositories,
    evaluate_on_dataset
)
from utils.tree_visualization import create_and_save_visualization
from utils.scoring import (
    find_optimal_weights,
    scores_to_logits,
    compute_weighted_scores
)
from utils.llm_api import query_all_models_for_scores


def run_scoring_workflow(
    train_csv_path: str,
    test_csv_path: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_ids: Optional[List[str]] = None,
    visualize: bool = True,
    parent: str = "Ethereum"
) -> Dict:
    """
    Execute the complete scoring workflow.
    
    Workflow steps:
    1. Query AI models for complete scores
    2. Convert to logits
    3. Find optimal weights using train samples
    4. Evaluate on test samples
    5. Compute final rankings
    
    Args:
        train_csv_path: Path to training CSV
        test_csv_path: Path to test CSV
        api_url: API endpoint URL (None to use cached scores only)
        api_key: Optional API key
        model_ids: List of model IDs to evaluate
        visualize: Whether to create visualizations
        parent: Parent context (default: "Ethereum")
        
    Returns:
        Dict with results including optimal_weights, repo_scores, test_metrics
    """
    # Handle model_ids as dict or list
    if isinstance(model_ids, dict):
        model_ids = list(model_ids.keys())
    
    print("=" * 80)
    print(" " * 15 + "Distilled Human Judgement")
    print("=" * 80)
    print("\nWorkflow Overview:")
    print("  1. AI models provide COMPLETE scores for all repositories")
    print("  2. Scores converted to logits (no inference needed!)")
    print("  3. Train set: Find optimal model combination weights")
    print("  4. Test set: Evaluate generalization performance")
    
    # ========================================================================
    # Step 1: Load train and test data
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 1: Loading Human Juror Comparison Data")
    print("=" * 80)
    
    print("\n📂 Loading TRAINING comparisons from train.csv...")
    train_samples, train_repo_to_idx, train_idx_to_repo, train_df = load_and_prepare_data(train_csv_path)
    print(f"  ✓ {len(train_samples)} training comparisons")
    print(f"  ✓ {len(train_repo_to_idx)} unique repositories in training set")
    
    print("\n📂 Loading TEST comparisons from test.csv...")
    test_samples, test_repo_to_idx, test_idx_to_repo, test_df = load_and_prepare_data(test_csv_path)
    print(f"  ✓ {len(test_samples)} test comparisons")
    print(f"  ✓ {len(test_repo_to_idx)} unique repositories in test set")
    
    # Create unified repository index
    all_repos_set = set(train_repo_to_idx.keys()) | set(test_repo_to_idx.keys())
    all_repos = sorted(all_repos_set)
    repo_to_idx = {repo: idx for idx, repo in enumerate(all_repos)}
    idx_to_repo = {idx: repo for repo, idx in repo_to_idx.items()}
    num_repos = len(all_repos)
    
    print(f"\n  Combined repository space: {num_repos} unique repositories")
    print(f"  Models to evaluate: {', '.join(model_ids)}")
    
    # Remap train and test samples to unified index
    train_samples = [
        (repo_to_idx[train_idx_to_repo[a]], 
         repo_to_idx[train_idx_to_repo[b]], 
         log_mult)
        for a, b, log_mult in train_samples
    ]
    test_samples = [
        (repo_to_idx[test_idx_to_repo[a]], 
         repo_to_idx[test_idx_to_repo[b]], 
         log_mult)
        for a, b, log_mult in test_samples
    ]
    
    # ========================================================================
    # Step 2: Query AI models for COMPLETE scores
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 2: Querying AI Models for Repository Scores")
    print("=" * 80)
    print(f"\n✓ Each model will score ALL {num_repos} repositories")
    
    distributions = query_all_models_for_scores(
        model_ids, all_repos, api_url, api_key, 
        cache_file=config.SCORES_CACHE_FILE, parent=parent
    )
    
    # Show sample scores
    print("\n  Sample scores from first model:")
    first_model = model_ids[0]
    for i in range(min(5, num_repos)):
        repo_name = all_repos[i].split('/')[-1]
        score = distributions[first_model][i]
        print(f"    {repo_name:30s}: {score:.1f}")
    
    # ========================================================================
    # Step 3: Convert to logits
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 3: Converting Scores to Logits")
    print("=" * 80)
    print("\n✓ Converting distributions to log-space")
    
    logits = scores_to_logits(distributions)
    model_names = list(distributions.keys())
    
    print(f"  ✓ Created logits for {len(logits)} models")
    print(f"  ✓ Each model has {len(logits[0])} logit values (one per repo)")
    
    # ========================================================================
    # Step 4: Find optimal weights using TRAIN set
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 4: Finding Optimal Model Combination (using Train Set)")
    print("=" * 80)
    print(f"\n✓ Using {len(train_samples)} training comparisons to optimize weights")
    print("  Minimizing disagreement with human juror judgments...")
    
    optimal_weights = find_optimal_weights(logits, train_samples)
    print_optimal_weights(model_names, optimal_weights)
    
    # ========================================================================
    # Step 5a: Evaluate on TRAIN set
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 5a: Evaluating Performance on Training Set")
    print("=" * 80)
    
    train_metrics = evaluate_on_dataset(
        train_samples,
        logits,
        optimal_weights,
        model_names,
    )
    
    # ========================================================================
    # Step 5b: Evaluate on TEST set
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 5b: Evaluating Generalization (on Test Set)")
    print("=" * 80)
    
    test_metrics = evaluate_on_dataset(
        test_samples,
        logits,
        optimal_weights,
        model_names,
    )
    
    # ========================================================================
    # Step 6: Compute final repository scores
    # ========================================================================
    print("\n" + "=" * 80)
    print("Step 6: Computing Final Repository Rankings")
    print("=" * 80)
    print("\n✓ Using weighted combination of all model logits")
    
    repo_scores = compute_weighted_scores(logits, optimal_weights, idx_to_repo)
    
    print(f"\n  ✓ Scored all {len(repo_scores)} repositories")
    print_top_repositories(repo_scores, top_n=20)
    
    # ========================================================================
    # Step 7: Visualize results (test repos only)
    # ========================================================================
    if visualize:
        print("\n" + "=" * 80)
        print("Step 7: Creating Visualization (Test Set Repositories)")
        print("=" * 80)
        
        test_repos = set(test_repo_to_idx.keys())
        create_and_save_visualization(repo_scores, filter_repos=test_repos)
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print(" " * 25 + "Workflow Complete!")
    print("=" * 80)
    
    print("\nPerformance Summary:")
    print(f"  • Training samples: {len(train_samples)}")
    print(f"  • Test samples: {len(test_samples)}")
    print(f"  • Repositories ranked: {len(repo_scores)}")
    
    print("\n  Training Set Performance:")
    print(f"    - Agreement rate: {train_metrics['agreement_rate']:.2%}")
    print(f"    - Correlation:    {train_metrics['correlation']:.4f}")
    print(f"    - RMSE:           {train_metrics['rmse']:.4f}")
    
    print("\n  Test Set Performance:")
    print(f"    - Agreement rate: {test_metrics['agreement_rate']:.2%}")
    print(f"    - Correlation:    {test_metrics['correlation']:.4f}")
    print(f"    - RMSE:           {test_metrics['rmse']:.4f}")
    
    print("\nOptimal Model Weights:")
    for name, weight in zip(model_names, optimal_weights):
        print(f"  • {name:25s}: {weight:.4f}")
    
    return {
        'optimal_weights': optimal_weights,
        'model_names': model_names,
        'repo_to_idx': repo_to_idx,
        'idx_to_repo': idx_to_repo,
        'repo_scores': repo_scores,
        'distributions': distributions,
        'logits': logits,
        'train_samples': train_samples,
        'test_samples': test_samples,
        'train_metrics': train_metrics,
        'test_metrics': test_metrics,
        'test_repos': set(test_repo_to_idx.keys())
    }


if __name__ == '__main__':
    try:
        results = run_scoring_workflow(
            train_csv_path=config.TRAIN_CSV,
            test_csv_path=config.TEST_CSV,
            api_url=config.API_URL,
            api_key=config.API_KEY,
            model_ids=config.MODELS_TO_TEST,
            visualize=config.VISUALIZE
        )
        
        print("\n✅ Success! Results available in 'results' dictionary:")
        print(f"   • optimal_weights: Model combination weights")
        print(f"   • repo_scores: Complete rankings for {len(results['repo_scores'])} repositories")
        print(f"   • train_metrics: Performance on training data")
        print(f"   • test_metrics: Generalization performance on unseen data")
        print(f"   • distributions: Raw AI scores for each model")
        print(f"   • logits: Log-space representations")
        
        # Save results (convert numpy arrays to Python types)
        output_file = config.SCORING_RESULTS_FILE
        
        # Helper to convert numpy types to Python types
        def convert_to_serializable(obj):
            if hasattr(obj, 'tolist'):
                return obj.tolist()
            elif hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        with open(output_file, 'w') as f:
            json.dump({
                'model_names': results['model_names'],
                'optimal_weights': convert_to_serializable(results['optimal_weights']),
                'train_metrics': convert_to_serializable(results['train_metrics']),
                'test_metrics': convert_to_serializable(results['test_metrics']),
                'repo_scores': [(repo, float(score)) for repo, score in results['repo_scores'][:50]]
            }, f, indent=2)
        print(f"\n📊 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
