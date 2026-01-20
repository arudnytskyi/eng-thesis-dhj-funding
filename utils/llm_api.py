"""
LLM API client for querying AI models.

This module handles communication with LLM APIs for repository comparison tasks.
"""

import os
import json
import requests
import re
from typing import List, Dict, Optional


def query_llm_api(
    model: str,
    messages: List[Dict[str, str]],
    api_url: str,
    api_key: Optional[str] = None,
    project: Optional[str] = None,
    stream: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 12288
) -> str:
    """
    Query the LLM API with a chat completion request.
    
    Args:
        model: Model ID (e.g., 'gpt-4.1-mini', 'claude-sonnet-4')
        messages: List of message dicts with 'role' and 'content'
        api_url: Full API endpoint URL
        api_key: API key for authentication
        project: Optional project identifier
        stream: Enable streaming mode
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        
    Returns:
        The model's response text, or None if the request fails
    """
    headers = {
        'Content-Type': 'application/json'
    }
    
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    if project:
        headers['project'] = project
    
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': stream
    }
    
    print(f"\n[API Request]")
    print(f"  Model: {model}")
    print(f"  Messages: {len(messages)} message(s)")
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=480  # Increased timeout for verbose models like DeepSeek-R1
        )
        
        print(f"  Status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        
        # Try different response formats
        content = None
        finish_reason = None
        
        # Format 1: Standard OpenAI format
        if 'choices' in result and len(result['choices']) > 0:
            choice = result['choices'][0]
            finish_reason = choice.get('finish_reason')
            
            if 'message' in choice:
                msg = choice['message']
                # Try to get content, handle both dict and potential None values
                if isinstance(msg, dict):
                    content = msg.get('content') or msg.get('text')
                elif isinstance(msg, str):
                    content = msg
            elif 'text' in choice:
                content = choice['text']
        
        # Format 2: Direct content field
        elif 'content' in result:
            content = result['content']
        
        # Format 3: Response field
        elif 'response' in result:
            content = result['response']
        
        # Format 4: Text field
        elif 'text' in result:
            content = result['text']
        
        # Check if content is valid (not None, not empty, not just whitespace)
        if content and isinstance(content, str) and content.strip():
            print(f"  Response length: {len(content)} chars")
            if finish_reason == 'length':
                print(f"  ⚠️  Warning: Response truncated (finish_reason='length')")
                print(f"  ⚠️  Consider increasing max_tokens parameter")
            return content
        else:
            print(f"  ⚠️  Warning: Could not extract content from response")
            if finish_reason == 'length':
                print(f"  ⚠️  finish_reason='length' but content is empty - model may have content filter or other issue")
            print(f"  Response keys: {list(result.keys())}")
            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                print(f"  Choice keys: {list(choice.keys())}")
                if 'message' in choice:
                    msg = choice['message']
                    print(f"  Message: {msg}")
                    # Check for annotations or content filters
                    if 'annotations' in msg and msg['annotations']:
                        print(f"  ⚠️  Annotations present: {msg['annotations']}")
                if 'provider_specific_fields' in choice:
                    psf = choice['provider_specific_fields']
                    print(f"  Provider specific fields: {psf}")
            print(f"  Response sample: {str(result)[:300]}...")
            return None
            
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ HTTP Error: {e}")
        try:
            error_detail = response.json()
            print(f"  Error details: {error_detail}")
        except:
            print(f"  Response text: {response.text[:200] if response else 'No response'}...")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON Decode Error: {e}")
        print(f"  Response text: {response.text[:200] if response else 'No response'}...")
        return None
    except KeyError as e:
        print(f"  ❌ KeyError: {e}")
        print(f"  Response structure: {str(result)[:300]}...")
        return None
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_scoring_prompt(repos: List[str], parent: str = "Ethereum") -> str:
    """
    Generate prompt asking AI to score all repositories.
    
    Args:
        repos: List of repository URLs
        parent: Parent context (default: "Ethereum")
        
    Returns:
        Prompt string asking for scores
    """
    repo_names = [repo.split('/')[-1] for repo in repos]
    
    prompt = f"""You are evaluating open-source projects that contributed to {parent}'s success.

Rate each project on a 0-100 scale based on:
- Historical impact on {parent}'s development and adoption
- Current importance to the ecosystem
- Security, reliability, and decentralization contributions
- Developer adoption and community usage
- Technical innovation and influence on other projects

Projects to rate:
"""
    
    for i, (repo_url, repo_name) in enumerate(zip(repos, repo_names), 1):
        prompt += f"{i}. {repo_name} ({repo_url})\n"
    
    prompt += f"""
Provide your answer ONLY as a Python list of {len(repos)} numbers (0-100).
The numbers should reflect relative importance and roughly sum to {len(repos) * 50}.

Format: [score1, score2, score3, ...]
No explanation. Just the list.
"""
    
    return prompt


def parse_score_list(response_text: str) -> List[float]:
    """
    Parse AI response to extract list of scores.
    
    Handles:
    - DeepSeek-R1 format with <think>...</think> tags
    - Truncated responses (partial lists)
    - Various list formats
    
    Args:
        response_text: Raw response from AI
        
    Returns:
        List of scores
    """
    # For DeepSeek-R1: Extract content after </think> if present
    if '<think>' in response_text:
        # Find content after the last </think> tag
        parts = response_text.split('</think>')
        if len(parts) > 1:
            response_text = parts[-1]
    
    # Try to find a list pattern [...]
    # Look for complete list first
    match = re.search(r'\[([^\]]+)\]', response_text)
    
    # If no complete list found, look for partial list (truncated)
    if not match:
        match = re.search(r'\[([^]]*)', response_text)
        if match:
            print("    (Warning: Found partial/truncated list)")
    
    if not match:
        raise ValueError(f"Could not find list in response: {response_text[:200]}")
    
    # Extract numbers from the list
    list_content = match.group(1)
    numbers = re.findall(r'-?\d+\.?\d*', list_content)
    scores = [float(n) for n in numbers]
    
    return scores


def query_model_for_scores(
    model_id: str,
    repos: List[str],
    api_url: Optional[str],
    api_key: Optional[str] = None,
    cache: Optional[Dict] = None,
    parent: str = "Ethereum"
) -> List[float]:
    """
    Query a single AI model for scores of all repositories.
    
    Args:
        model_id: Model identifier
        repos: List of repository URLs
        api_url: API endpoint (None to use cache only)
        api_key: Optional API key
        cache: Optional cache dictionary
        parent: Parent context
        
    Returns:
        List of scores (one per repository)
    """
    # Create cache key
    cache_key = f"{model_id}:scores:{len(repos)}"
    
    # Check cache
    if cache is not None and cache_key in cache:
        print(f"  {model_id:25s}: Loaded from cache")
        return cache[cache_key]
    
    # If no API URL provided, can only use cache
    if api_url is None:
        raise ValueError(
            f"Model '{model_id}' not found in cache and no API URL provided. "
            f"Cannot fetch scores without API access. "
            f"Please provide API_URL in config.py or ensure this model has cached scores."
        )
    
    # Generate prompt
    prompt = generate_scoring_prompt(repos, parent)
    
    # Query API
    print(f"  {model_id:25s}: Querying API...")
    
    messages = [{"role": "user", "content": prompt}]
    
    # DeepSeek-R1 models need much more tokens (they include reasoning)
    max_tokens = 16384
    
    response = query_llm_api(
        model=model_id,
        messages=messages,
        api_url=api_url,
        api_key=api_key,
        temperature=0.3,
        max_tokens=max_tokens
    )
    
    if response is None:
        print(f"  {model_id:25s}: FAILED - using default scores")
        # Return uniform scores as fallback
        return [50.0] * len(repos)
    
    # Parse scores
    try:
        scores = parse_score_list(response)
        
        if len(scores) != len(repos):
            print(f"  {model_id:25s}: WARNING - got {len(scores)} scores, expected {len(repos)}")
            
            # If we got a truncated response, fill in remaining with average
            if len(scores) < len(repos):
                avg_score = sum(scores) / len(scores) if scores else 50.0
                missing_count = len(repos) - len(scores)
                print(f"  {model_id:25s}: Padding {missing_count} missing scores with avg={avg_score:.1f}")
                scores.extend([avg_score] * missing_count)
            else:
                # More scores than repos - truncate
                scores = scores[:len(repos)]
        
        print(f"  {model_id:25s}: ✓ Got {len(scores)} scores (sum={sum(scores):.1f}, avg={sum(scores)/len(scores):.1f})")
        
        # Cache the result
        if cache is not None:
            cache[cache_key] = scores
        
        return scores
        
    except Exception as e:
        print(f"  {model_id:25s}: ERROR parsing response - {e}")
        print(f"  {model_id:25s}: Using default uniform scores (50.0)")
        return [50.0] * len(repos)


def query_all_models_for_scores(
    model_ids: List[str],
    repos: List[str],
    api_url: Optional[str],
    api_key: Optional[str] = None,
    cache_file: Optional[str] = None,
    parent: str = "Ethereum"
) -> Dict[str, List[float]]:
    """
    Query all AI models for scores.
    
    Args:
        model_ids: List of model identifiers
        repos: List of repository URLs
        api_url: API endpoint (None to use cache only)
        api_key: Optional API key
        cache_file: Path to cache file
        parent: Parent context
        
    Returns:
        Dict mapping model_id to list of scores
    """
    # Load cache
    cache = {}
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            print(f"Loaded cache from {cache_file}")
        except Exception as e:
            print(f"Failed to load cache: {e}")
    
    # Show mode
    if api_url is None:
        print("\n⚠️  Running in CACHE-ONLY mode (no API calls will be made)")
        print("   Models not in cache will use default scores")
    
    # Query each model
    distributions = {}
    for model_id in model_ids:
        scores = query_model_for_scores(
            model_id, repos, api_url, api_key, cache, parent
        )
        distributions[model_id] = scores
    
    # Save cache
    if cache_file:
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            print(f"\nSaved cache to {cache_file}")
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    return distributions
