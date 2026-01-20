from pathlib import Path

# ---- API ----
# Set these to None to use cached scores only (no API calls)
API_KEY = None
API_URL = None

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent

PLOTS_DIR = BASE_DIR / "plots"
ETHEREUM_DEPENDENCY_TREE_GRAPH = PLOTS_DIR / "ethereum_dependency_tree.svg"
DECISION_TIMES_PLOT = PLOTS_DIR / "decision_times.svg"

DATASET_DIR = BASE_DIR / "dataset"
TRAIN_CSV = DATASET_DIR / "train.csv"
TEST_CSV = DATASET_DIR / "test.csv"

SCORES_CACHE_FILE = DATASET_DIR / "scores_cache.json"
SCORING_RESULTS_FILE = DATASET_DIR / "scoring_results.json"

# ---- Constants ----
VISUALIZE = True

MODELS_TO_TEST = {
    # Grok
    'grok-3': 'Grok 3',
    # Claude
    'claude-3-7-sonnet': 'Claude 3.7 Sonnet',
    'claude-sonnet-4': 'Claude Sonnet 4',
    'claude-sonnet-4.5': 'Claude Sonnet 4.5',
    'claude-opus-4.1': 'Claude Opus 4.1',
    # Gemini
    'gemini-2.5-pro': 'Gemini 2.5 Pro',
    'gemini-2.5-flash': 'Gemini 2.5 Flash',
    # OpenAI
    'o3-mini': 'O3 mini',
    'o4-mini': 'O4 mini',
    'gpt-oss-120b': 'GPT-OSS 120B',
    'gpt-5.1': 'GPT-5.1',
    'gpt-5-nano': 'GPT-5 Nano',
    'gpt-4.1': 'GPT-4.1',
    # Meta
    'Meta-Llama-3-1-405B-Instruct': 'Meta Llama 3.1 405B',
}
