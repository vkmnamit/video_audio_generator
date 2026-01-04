
from scene_policy import decide_scene_type

def test_tree_detection():
    print("🌲 Testing Tree Scene Detection...")
    
    topic = "Classification of Living Things"
    
    scenes = [
        {
            "headline": "THE TREE OF LIFE",
            "narration": "Living things are classified into several kingdoms like Animals, Plants, and Fungi."
        },
        {
            "headline": "TYPES OF VERTEBRATES",
            "narration": "Vertebrates are divided into five main groups: mammals, birds, reptiles, amphibians, and fish."
        }
    ]
    
    for i, scene in enumerate(scenes):
        scene_type = decide_scene_type(scene, topic=topic)
        print(f"Scene {i+1} [{scene['headline']}]:")
        print(f"  Detected Type: {scene_type}")
        print(f"  Expected Type: tree")
        
        if scene_type == "tree":
            print("  ✅ SUCCESS: Correctly identified as TREE")
        else:
            print(f"  ❌ FAILURE: Identified as {scene_type}")

if __name__ == "__main__":
    test_tree_detection()
