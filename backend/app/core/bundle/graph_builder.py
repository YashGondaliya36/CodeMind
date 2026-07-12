import json
import yaml
from pathlib import Path
from app.config import settings

def build_graph(repo_name: str) -> None:
    """
    Scans all OKF markdown files for a repository, extracts their tags,
    and builds a graph.json mapping nodes and edges based on shared tags.
    """
    bundle_dir = settings.bundles_path / repo_name
    modules_dir = bundle_dir / "modules"
    
    if not modules_dir.exists():
        return
        
    nodes = []
    edges = []
    file_tags = {}
    
    # 1. Parse all modules to create nodes and collect tags
    for md_file in modules_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        
        title = md_file.stem
        tags = []
        
        # Extract YAML frontmatter
        if content.startswith("---"):
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter:
                        title = frontmatter.get("title", title)
                        tags = frontmatter.get("tags", [])
            except Exception:
                pass
                
        node_id = f"modules/{md_file.name}"
        nodes.append({
            "id": node_id,
            "label": title,
            "type": "file",
            "tags": list(tags)
        })
        file_tags[node_id] = tags
        
    # Common tags that shouldn't create edges because they connect everything
    ignore_tags = {"python", "script", "module", "utility", "automation"}

    # 2. Build edges based on shared tags
    node_ids = list(file_tags.keys())
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            id1 = node_ids[i]
            id2 = node_ids[j]
            
            # Filter out ignored tags before checking intersection
            tags1 = set(file_tags[id1]) - ignore_tags
            tags2 = set(file_tags[id2]) - ignore_tags
            
            shared = tags1.intersection(tags2)
            
            # Require at least 2 highly-specific shared tags to create a connection
            if len(shared) >= 2:  
                edges.append({
                    "source": id1,
                    "target": id2,
                    "label": list(shared)[0] 
                })
                
    # 3. Save graph.json
    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    graph_path = bundle_dir / "graph.json"
    graph_path.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")
