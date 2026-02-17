#!/usr/bin/env python3
"""
Generate collaboration network from real GitHub data.
Edges represent PR review interactions between agents.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

ORG = "ai-village-agents"

# Map GitHub usernames to display names
DISPLAY_NAMES = {
    "claude-3-7-sonnet": "Claude 3.7 Sonnet",
    "deepseek-v32": "DeepSeek-V3.2",
    "gemini-3-pro-ai-village": "Gemini 3 Pro",
    "claudehaiku45": "Claude Haiku 4.5",
    "claude-opus-4-6": "Claude Opus 4.6",
    "gpt-5-1": "GPT-5.1",
    "claude-sonnet-45": "Claude Sonnet 4.5",
    "gemini-25-pro-collab": "Gemini 2.5 Pro",
    "claude-opus-4-5": "Claude Opus 4.5",
    "gpt-5-ai-village": "GPT-5",
    "viral-crypto": "Viral Crypto",
    "Dnonmi": "Dnonmi",
    "actions-user": "Actions User"
}

# AI agent usernames (exclude humans/bots)
AI_AGENTS = {
    "claude-3-7-sonnet", "deepseek-v32", "gemini-3-pro-ai-village",
    "claudehaiku45", "claude-opus-4-6", "gpt-5-1", "claude-sonnet-45",
    "gemini-25-pro-collab", "claude-opus-4-5", "gpt-5-ai-village"
}

def run_gh_api(endpoint):
    """Run a gh api command and return parsed JSON."""
    cmd = ["gh", "api", endpoint, "--paginate"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching {endpoint}: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        items = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    if isinstance(data, list):
                        items.extend(data)
                    else:
                        items.append(data)
                except:
                    pass
        return items

def get_repos():
    """Get all repos in the organization."""
    repos = run_gh_api(f"/orgs/{ORG}/repos?per_page=100")
    return [r["name"] for r in repos if not r.get("archived")]

def get_prs_for_repo(repo):
    """Get PRs for a repo (last 100)."""
    prs = run_gh_api(f"/repos/{ORG}/{repo}/pulls?state=all&per_page=100")
    return prs

def get_reviews_for_pr(repo, pr_number):
    """Get reviews for a specific PR."""
    reviews = run_gh_api(f"/repos/{ORG}/{repo}/pulls/{pr_number}/reviews")
    return reviews

def main():
    print("Generating collaboration network from GitHub data...")
    
    repos = get_repos()
    print(f"Found {len(repos)} repos")
    
    # Edge weights: interaction count between agents
    edge_weights = defaultdict(int)
    agent_participation = set()
    
    # Process each repo
    for repo_idx, repo in enumerate(repos):
        print(f"  Processing {repo} ({repo_idx+1}/{len(repos)})")
        prs = get_prs_for_repo(repo)
        
        for pr in prs:
            if not isinstance(pr, dict):
                continue
            
            # Get PR author
            author = pr.get("user", {}).get("login")
            if not author:
                continue
            
            # Only consider AI agents
            if author not in AI_AGENTS:
                continue
            
            agent_participation.add(author)
            
            # Get reviews for this PR
            pr_number = pr.get("number")
            if not pr_number:
                continue
            
            reviews = get_reviews_for_pr(repo, pr_number)
            for review in reviews:
                if not isinstance(review, dict):
                    continue
                
                reviewer = review.get("user", {}).get("login")
                if not reviewer or reviewer == author:
                    continue
                
                if reviewer not in AI_AGENTS:
                    continue
                
                # Add edge (undirected)
                edge_key = tuple(sorted([author, reviewer]))
                edge_weights[edge_key] += 1
                agent_participation.add(reviewer)
    
    # Build nodes list
    nodes = []
    for agent in sorted(agent_participation):
        display_name = DISPLAY_NAMES.get(agent, agent)
        nodes.append({"id": display_name})
    
    # Build edges list
    edges = []
    for (agent1, agent2), weight in sorted(edge_weights.items(), key=lambda x: -x[1]):
        display1 = DISPLAY_NAMES.get(agent1, agent1)
        display2 = DISPLAY_NAMES.get(agent2, agent2)
        edges.append({
            "source": display1,
            "target": display2,
            "weight": weight
        })
    
    # Create network object
    network = {
        "nodes": nodes,
        "edges": edges
    }
    
    # Save to file
    output_path = "data/collaboration_network_real.json"
    with open(output_path, "w") as f:
        json.dump(network, f, indent=2)
    
    print(f"\nSaved collaboration network to {output_path}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print("\nTop collaborations:")
    for edge in edges[:10]:
        print(f"  {edge['source']} ↔ {edge['target']}: {edge['weight']} interactions")

if __name__ == "__main__":
    main()
