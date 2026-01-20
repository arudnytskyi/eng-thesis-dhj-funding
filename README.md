# Distilled Human Judgment(DHJ) for Public Goods Funding

Implementation of Vitalik Buterin's [Distilled Human Judgment](https://vitalik.eth.limo/general/2025/02/28/aihumans.html) mechanism - a governance framework that uses sparse human judgments to align multiple AI systems for large-scale decision-making.

## Overview

This system applies DHJ to **funding allocation** for Ethereum ecosystem repositories. It combines judgments from 37 human jurors with predictions from 14 AI models to produce aligned repository rankings that guide funding decisions.

This work corresponds to the **Deep Funding real-world task** ([CryptoPond ModelFactory, Project 2564617](https://cryptopond.xyz/modelfactory/detail/2564617?tab=0)), which aims to rank Ethereum repositories by their contribution to the ecosystem.

**Dataset**: 311 training comparisons, 96 test comparisons  
**Models**: Claude Opus 4.1, GPT-5.1, Llama-3.1-405B, Gemini 2.5 Pro, and 10 others

### Key Features

- **Open Competitive Market**: Model-agnostic ensemble where any AI system can participate
- **Convex Optimization**: Minimizes squared disagreement in log-space for global optimum
- **Future-Proof**: Mechanism remains stable as AI models evolve
- **Transparent Rules**: Optimization is fully open-source, even if participating models are proprietary

## Results

| Metric | Training | Test | Interpretation |
|--------|----------|------|----------------|
| **Agreement Rate** | 71.06% | 72.92% | Directional accuracy (picks same winner) |
| **Correlation** | 0.492 | 0.548 | Magnitude alignment with human judgments |
| **RMSE** | 2.48 | 2.38 | ~12× average multiplicative error |

**Optimal Weights** (Top 3 models):
- Claude Opus 4.1: 38.9%
- GPT-4.1: 32.8%
- Llama-3.1-405B: 28.3%

## Installation

```bash
pip install -r requirements.txt
python main.py
```

**Project Structure**:
- `main.py` - Main workflow execution
- `config.py` - Model selection and API configuration  
- `utils/` - Scoring, optimization, and visualization modules
- `dataset/` - Training/test data and cached scores
- `analyze_decision_time.py` - Analyze decision time distributions
- `analyze_multipliers.py` - Analyze multiplier distributions

## Configuration

Edit `config.py` to customize models and API settings:

```python
API_KEY = None  # Set to None to use cached scores only
API_URL = None  # Your API endpoint

MODELS_TO_TEST = {
    'claude-opus-4.1': 'Claude Opus 4.1',
    'gpt-5.1': 'GPT-5.1',
    # ... add more models
}
```

## Data Format

Human jurors provide pairwise comparisons in CSV format:

```csv
timestamp,juror,repo_a,repo_b,parent,choice,multiplier,reasoning
2024-12-24,L1Juror1,github.com/org/A,github.com/org/B,ethereum,2,10.0,"B is 10× more impactful..."
```

- **choice**: 1 (A preferred) or 2 (B preferred)
- **multiplier**: How many times more valuable (e.g., 10.0 = 10×)
- Dataset contains extreme multipliers: 50×, 100×, up to 1320×

## System Strengths

### Model-Agnostic and Diversity-Preserving
DHJ creates an open competitive marketplace for any AI system:
- Closed/open-source models
- Specialized code models
- Ensemble agents
- Human+AI hybrids
- Even heuristic algorithms

### Transparent Mechanism
The optimization rule is fully open-source, even if participants are proprietary—mirroring governance structures like markets where rules are public but participants can be private.

### Minimal Designer Bias
The convex quadratic objective with simple constraints means structure comes from human judgment data, not mechanism designer preferences.

### Future-Proof
As AI architectures evolve every 3-6 months, only participants change—the decision rule remains constant, providing long-term institutional stability.
