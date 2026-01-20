"""
Tree visualization utilities.

This module provides functions for creating radial tree visualizations
of repository dependency graphs.
"""

import math
from typing import Dict, List, Tuple


def plot_tree(tree: Dict, weights: List[float], root: str):
    """
    Plots a tree (given as a nested dictionary) in a radial layout.
    The root is placed at the center (level 0) and nodes at level i are
    placed on a circle of radius i*k (pixels). Leaf nodes are assigned angles
    in DFS order (evenly spaced between 0° and 360°), and each internal node's
    angle is computed as the median of the angles of its descendant leaves.
    
    Edge labels (weights) are assigned in DFS order (i.e. in the order the DFS
    traversal visits the edges) and are printed with up to 3 decimal places.
    
    Duplicate node names are handled by assigning each node a unique internal ID.
    
    Parameters:
      tree (dict): A nested dictionary representing the tree.
                   For example:
                     {"node_a": {"node_b": None, "node_c": None},
                      "node_d": {"node_e": None}}
      weights (list of float): Edge labels in DFS order.
                               For the above tree (with an extra root),
                               the order is:
                               [edge from root->first child, then recursively
                                the edges in that subtree, then remaining edges]
      root (str): The label for the top-level (root) node.
    """
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n   Warning: networkx and/or matplotlib not available for plotting")
        return
    
    # Create a directed graph.
    G = nx.DiGraph()

    # Dictionaries to store each node's display label, its level (distance from root),
    # and (later) its assigned angle (in degrees).
    node_labels = {}
    level = {}
    node_angles = {}
    # For each node, store the list of its children (by unique id) in the order encountered.
    children_mapping = {}

    # We'll assign a unique ID to each node by appending an incrementing counter.
    node_counter = 0
    weight_index = 0

    # Create the root node.
    root_uid = f"{root}_{node_counter}"
    node_counter += 1
    G.add_node(root_uid)
    node_labels[root_uid] = root
    level[root_uid] = 0

    # --- Build the graph (and assign weights) using DFS ---
    def build_graph_dfs(parent_uid, subtree):
        nonlocal node_counter, weight_index
        # If there is no subtree, nothing to do.
        if not subtree:
            return
        for child_name, child_subtree in subtree.items():
            # Create a unique id for the child node.
            child_uid = f"{child_name}_{node_counter}"
            node_counter += 1
            G.add_node(child_uid)
            node_labels[child_uid] = child_name
            # Set the child's level.
            level[child_uid] = level[parent_uid] + 1
            # Record the child in the parent's children list.
            children_mapping.setdefault(parent_uid, []).append(child_uid)
            # Add the edge from parent to child.
            G.add_edge(parent_uid, child_uid)
            # Assign the next weight (if available) to the edge in DFS order.
            if weight_index < len(weights):
                G[parent_uid][child_uid]['weight'] = weights[weight_index]
                weight_index += 1
            else:
                G[parent_uid][child_uid]['weight'] = None
            # Recurse into the child's subtree, if any.
            if child_subtree:
                build_graph_dfs(child_uid, child_subtree)

    # Build the graph starting from the root.
    build_graph_dfs(root_uid, tree)

    # --- Compute the radial positions ---
    # (a) Collect all leaf nodes in DFS order.
    def dfs_collect_leaves(node, leaves):
        if node not in children_mapping:
            leaves.append(node)
        else:
            for child in children_mapping[node]:
                dfs_collect_leaves(child, leaves)

    dfs_leaves = []
    dfs_collect_leaves(root_uid, dfs_leaves)
    n_leaves = len(dfs_leaves)
    
    # (b) Assign each leaf an angle evenly spaced between 0° and 360°.
    for i, leaf in enumerate(dfs_leaves):
        angle = (i * 360 / n_leaves) % 360
        node_angles[leaf] = angle

    # (c) For internal nodes, assign their angle as the median of the angles
    # of all descendant leaves. (Since DFS order was used to collect leaves,
    # we do not re-sort the angles.)
    def assign_internal_angles(node):
        if node not in children_mapping:
            return [node_angles[node]]
        else:
            descendant_angles = []
            for child in children_mapping[node]:
                descendant_angles.extend(assign_internal_angles(child))
            n = len(descendant_angles)
            if n % 2 == 1:
                median_angle = descendant_angles[n // 2]
            else:
                median_angle = (descendant_angles[n // 2 - 1] + descendant_angles[n // 2]) / 2
            node_angles[node] = median_angle
            return descendant_angles

    assign_internal_angles(root_uid)

    # (d) Compute (x, y) coordinates for each node:
    #     Nodes at level i are placed at radius r = i * k.
    k = 100  # radial spacing in pixels per level.
    pos = {}
    for node in G.nodes():
        r = level[node] * k
        theta_rad = math.radians(node_angles[node])
        pos[node] = (r * math.cos(theta_rad), r * math.sin(theta_rad))

    # --- Prepare edge labels with weights formatted to 3 decimal places ---
    edge_labels = {}
    for u, v in G.edges():
        weight = G[u][v]['weight']
        if weight is not None:
            edge_labels[(u, v)] = f"{weight:.3f}"
        else:
            edge_labels[(u, v)] = ""

    # --- Draw the graph ---
    plt.figure(figsize=(16, 16))
    nx.draw(G, pos, labels=node_labels, with_labels=True, node_size=1500,
            node_color='lightblue', arrows=True)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    from config import ETHEREUM_DEPENDENCY_TREE_GRAPH

    output_file = ETHEREUM_DEPENDENCY_TREE_GRAPH
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n   Graph saved to: {output_file}")
    plt.close()  # Close instead of show to avoid blocking


def build_repository_tree(repo_scores: List[Tuple[str, float]]) -> Tuple[Dict, List[float]]:
    """
    Build a hierarchical tree structure from repository scores.
    
    Repositories are grouped into categories based on their type,
    and weights are calculated in DFS order for visualization.
    
    Args:
        repo_scores: List of (repo_url, score) tuples, sorted by score
        
    Returns:
        Tuple of (tree_dict, weights_list)
    """
    # Categories for grouping repositories
    categories = {
        "Execution Clients": [],
        "Consensus Clients": [],
        "Smart Contract Languages": [],
        "Development Tools": [],
        "Libraries & SDKs": [],
        "Applications": []
    }
    
    # Repository name patterns for categorization
    execution_clients = ['go-ethereum', 'nethermind', 'erigon', 'besu', 'reth']
    consensus_clients = ['prysm', 'lighthouse', 'teku', 'nimbus', 'lodestar', 'grandine']
    languages = ['solidity', 'vyper', 'fe']
    dev_tools = ['foundry', 'hardhat', 'remix', 'truffle', 'scaffold-eth']
    libraries = ['ethers.js', 'web3.js', 'web3.py', 'viem', 'alloy', 'nethereum']
    
    # Categorize all repositories
    for repo_url, score in repo_scores:
        repo_name = repo_url.split('/')[-1].lower()
        
        if any(client in repo_name for client in execution_clients):
            categories["Execution Clients"].append((repo_url, score))
        elif any(client in repo_name for client in consensus_clients):
            categories["Consensus Clients"].append((repo_url, score))
        elif any(lang in repo_name for lang in languages):
            categories["Smart Contract Languages"].append((repo_url, score))
        elif any(tool in repo_name for tool in dev_tools):
            categories["Development Tools"].append((repo_url, score))
        elif any(lib in repo_name for lib in libraries):
            categories["Libraries & SDKs"].append((repo_url, score))
        else:
            categories["Applications"].append((repo_url, score))
    
    # Build tree structure in the format expected by plot_tree
    tree = {}
    weights = []
    
    # Calculate category weights as sum of their repository scores
    category_weights = {}
    for category, repos in categories.items():
        if repos:
            # Use all repos in the category for weight calculation
            category_weights[category] = sum(score for _, score in repos)
    
    # Normalize category weights
    if category_weights:
        total_weight = sum(category_weights.values())
        for category in category_weights:
            category_weights[category] /= total_weight
    
    # Build tree and collect weights in DFS order
    for category, repos in categories.items():
        if repos:  # Only include non-empty categories
            # Add category weight (edge from root to category)
            weights.append(category_weights.get(category, 0))
            
            # Add category to tree
            tree[category] = {}
            
            # Add all repos to this category
            repo_weights = []
            
            for repo_url, score in repos:
                repo_name = repo_url.split('/')[-1]
                tree[category][repo_name] = None
                repo_weights.append(score)
            
            # Normalize repo weights within this category so they sum to 1
            if repo_weights:
                repo_sum = sum(repo_weights)
                repo_weights = [w / repo_sum for w in repo_weights]
                weights.extend(repo_weights)
    
    return tree, weights


def create_and_save_visualization(repo_scores: List[Tuple[str, float]], filter_repos: set = None):
    """
    Create and save a tree visualization of repository dependencies.
    
    Args:
        repo_scores: List of (repo_url, score) tuples
        filter_repos: Optional set of repo URLs to include (if None, include all)
    """
    print("\n   Building repository dependency tree...")
    
    # Filter repositories if specified
    if filter_repos is not None:
        repo_scores = [(url, score) for url, score in repo_scores if url in filter_repos]
        print(f"   Filtered to {len(repo_scores)} repositories from test set")
    else:
        print("   Using all repositories with direct LLM scores")
    
    tree, weights = build_repository_tree(repo_scores)
    
    print(f"   Categories: {len(tree)}")
    print(f"   Total repositories shown: {sum(len(repos) for repos in tree.values())}")
    print(f"   Total weights: {len(weights)}")
    
    try:
        plot_tree(tree, weights, "Ethereum")
    except Exception as e:
        print(f"\n   Warning: Could not create visualization: {e}")
        print("   This might be due to missing matplotlib or networkx libraries.")
