# semantic_scene_map.py
# Central mapping for intent-based scene overrides for specific topics and scene indices

SEMANTIC_SCENE_MAP = {
    "merge sort": {
        3: "divide_and_merge_scene",
        4: "merge_scene"
    },
    "linked list": {
        3: "node_pointer_scene"
    },
    "stack": {
        3: "push_pop_scene"
    }
}

def get_semantic_scene_type(topic: str, scene_index: int):
    topic = topic.lower().strip()
    if topic in SEMANTIC_SCENE_MAP and scene_index in SEMANTIC_SCENE_MAP[topic]:
        return SEMANTIC_SCENE_MAP[topic][scene_index]
    return None
