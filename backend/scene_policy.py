# scene_policy.py
"""
Domain-agnostic scene policy engine for deciding scene_type based on intent, content, and voiceover.
"""

# FIX 3: FORCE OVERRIDE FOR ALGORITHMS
ALGO_SCENE_OVERRIDE = {
  "merge sort": {
     3: "divide_merge_scene",
     4: "merge_process_scene"
  },
  "quick sort": {
     3: "divide_merge_scene",
     4: "merge_process_scene"
  },
  "sorting": {
     1: "title",
     2: "array"
  }
}

def infer_scene_type(scene_content: str, topic: str, scene_id: int = None):
    """
    FIX 2: Add a Scene Intent Analyzer (MANDATORY)
    Decide scene type AFTER script analysis.
    """
    text = scene_content.lower()
    topic_lower = topic.lower()
    
    print(f"🔍 DEBUG POLICY: Topic='{topic_lower}', Content Snippet='{text[:60]}...'")

    # Determine if we are in an algorithm context
    is_merge_sort = "merge sort" in topic_lower
    is_quick_sort = "quick sort" in topic_lower
    is_algo = is_merge_sort or is_quick_sort

    # FIX 5: Add a Safety Rule
    if is_merge_sort:
        if "array" in text or "list" in text:
             # If we are in merge sort and see array, it's likely a divide or merge step
             if "split" in text or "divide" in text or "recursion" in text:
                 res = "divide_merge_scene"
                 print(f"🎯 DEBUG POLICY RESULT: {res} (Merge Sort Split)")
                 return res
             if "merge" in text and "sorted" in text:
                 res = "merge_process_scene"
                 print(f"🎯 DEBUG POLICY RESULT: {res} (Merge Sort Merge)")
                 return res
    
    # Check overrides based on substrings in topic
    for algo_key, overrides in ALGO_SCENE_OVERRIDE.items():
        if algo_key in topic_lower:
            if scene_id is not None and scene_id in overrides:
                res = overrides[scene_id]
                print(f"🎯 DEBUG POLICY RESULT: {res} (Manual Override)")
                return res

    if any(w in text for w in ["formula", "equation", "calculate", "calculation", "math", "expression", "equals", "="]):
        res = "formula"
        print(f"🎯 DEBUG POLICY RESULT: {res} (Math Detect)")
        return res

    if any(w in text for w in ["difference", "vs", "versus", "compared to"]):
        return "comparison"

    if "input" in text and "output" in text:
        return "flowchart"

    if any(w in text for w in [
        "types of", "forms of", "kinds of", "categories of", "classified into", "divided into", "structure of", "varieties of", "branches of", "groups of", "classes of",
        "category", "categories", "types", "classification", "taxonomy"
    ]):
        return "tree"

    if any(w in text for w in ["split", "recursion", "recursive", "break", "halves", "subarray", "base case"]) or (is_algo and "divide" in text):
        return "divide_merge_scene"

    if any(w in text for w in ["merge", "combine", "joining", "sorted array", "sorted list"]) or (is_algo and "result" in text and scene_id and scene_id > 4):
        return "merge_process_scene"

    if any(w in text for w in ["linked list", "nodes", "pointer"]):
        return "linked_list"

    if any(w in text for w in ["code", "python", "javascript", "cpp", "function", "variable"]):
        return "code"

    if any(w in text for w in ["table", "rows", "columns", "data set"]):
        return "table"

    # If it's an algorithm, we generally want specialized scenes, not generic 'array'
    if "array" in text and not is_algo:
        res = "array"
        print(f"🎯 DEBUG POLICY RESULT: {res} (Array Keyword Detect)")
        return res

    # Fallback to existing logic or concept flow
    if any(w in text for w in ["first", "then", "next", "step", "how it works", "process", "workflow", "procedure"]):
        return "process"

    if any(w in text for w in ["for example", "for instance", "imagine"]):
        return "example"
    if any(w in text for w in ["means", "refers to", "is defined as", "what is", "is a "]):
        return "definition"
    if any(w in text for w in ["understanding", "intro", "introduction", "welcome"]):
        return "title"
    if any(w in text for w in ["in summary", "finally", "to conclude", "takeaway", "takeaways", "remember", "wrap up"]):
        return "summary"
    
    res = "concept_flow_scene"
    print(f"🎯 DEBUG POLICY RESULT: {res} (Fallback)")
    return res

def decide_scene_type(scene, topic=None, scene_id=None):
    """Legacy wrapper for backward compatibility"""
    content_text = " ".join([
        str(scene.get("intent", "")),
        str(scene.get("headline", "")),
        str(scene.get("content", "")),
        str(scene.get("voiceover", "")),
        str(scene.get("narration", ""))
    ])
    return infer_scene_type(content_text, topic or "general", scene_id)
