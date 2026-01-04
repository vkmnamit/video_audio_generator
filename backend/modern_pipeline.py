
import os
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    try:
        from app_secrets import API_KEY as SECRET_API_KEY
        API_KEY = SECRET_API_KEY
    except ImportError:
        pass

async def get_ai_completion(messages: List[Dict[str, str]], json_mode: bool = False) -> str:
    """Helper to get completion from OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "mistralai/devstral-2512:free",
        "messages": messages,
        "max_tokens": 4000,
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"AI API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        return content.strip()

async def stage1_scholar_extraction(topic: str) -> str:
    """Stage 1: Deep Ground-Truth Fact Extraction with Logic Mandate."""
    prompt = f"""
    You are 'The Scholar', a leading software architect.
    Conduct a deep logic-first analysis for: {topic}
    
    EXTRACT:
    - Line-by-line logic flow (Pseudocode or Real Code).
    - Every data structure involved (Arrays, Pointers, Windows).
    - Big O analysis (Time and Space).
    - Precise mathematical invariants.
    
    Goal: Provide an exhaustive 'Ground Truth' foundation. NO HIGH-LEVEL SUMMARIES. We need the raw logic.
    """
    
    messages = [
        {"role": "system", "content": "You are a PhD-level software engineer. Extract raw logic, indices, and code. No conversational fluff."},
        {"role": "user", "content": prompt}
    ]
    
    return await get_ai_completion(messages)

async def stage2_narrative_architect(topic: str, facts: str) -> List[Dict[str, Any]]:
    """Stage 2: Plan the narrative with a 'Mechanism-First' policy for any domain."""
    prompt = f"""
    You are 'The Architect'. Plan a high-density technical masterclass for '{topic}'.
    FACTS & DATA: {facts}
    
    PLANNING RULES:
    - IDENTIFY the "Ground Truth" mechanism (e.g., a process, a set of data, a formula).
    - FORBIDDEN: Do NOT use 'definition' if you can show a list, a table, or a process.
    - PREFER: 'process' (for steps), 'table' (for data), 'formula' (for math/science), 'array' (for lists), 'code' (for logic).
    - Each scene must focus on A SINGLE data state or process step.
    
    FOR EACH SCENE:
    1. 'headline': The specific mechanism being shown.
    2. 'narration': Expert analysis (15-30 words).
    3. 'scene_type': (code, array, process, formula, table, diagram, title).

    Return ONLY a JSON list:
    [
        {{"headline": "...", "narration": "...", "scene_type": "..."}},
        ...
    ]
    """
    
    messages = [
        {"role": "system", "content": "You are a master technical architect. You break down complex topics into raw data and step-by-step mechanisms. No fluff. Return ONLY JSON list."},
        {"role": "user", "content": prompt}
    ]
    
    content = await get_ai_completion(messages, json_mode=True)
    if '```json' in content: content = content.split('```json')[1].split('```')[0].strip()
    return json.loads(content)

async def stage3_frame_specialist(scene: Dict[str, Any], topic: str, context: str, prev_scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Stage 3: Provide the RAW DATA manifest for the frame (Domain Agnostic)."""
    prev_info = f"PREVIOUS STATE: {prev_scene.get('visual_manifest', {}).get('primary_object', '')}" if prev_scene else "START"
    
    prompt = f"""
    You are 'The Specialist Designer'. Provide the RAW DATA for this frame.
    TOPIC: {topic} | SCENE: {scene['headline']}
    {prev_info}
    GLOBAL CONTEXT: {context[:1200]}
    
    DATA RULES:
    - 'primary_object': The core data. (If table: [[row1], [row2]], If formula: LaTeX, If array/list: [item1, item2], If code: raw string).
    - 'secondary_objects': Pointers, labels, or accents that clarify the data.
    - 'narration': {scene['narration']}
    
    Return ONLY JSON:
    {{
        "headline": "...",
        "narration": "...",
        "captions": "...",
        "scene_type": "{scene['scene_type']}",
        "visual_manifest": {{
            "colors": ["#000000", "#FFFFFF"],
            "primary_object": "THE RAW DATA Structure",
            "secondary_objects": ["Label for...", "Arrow to..."],
            "animations": ["entrance_pop"],
            "target_duration_seconds": 6.5
        }}
    }}
    """
    
    messages = [
        {"role": "system", "content": "You are a specialized technical designer. You provide raw, production-ready data structures. Return ONLY JSON."},
        {"role": "user", "content": prompt}
    ]
    
    content = await get_ai_completion(messages, json_mode=True)
    if '```json' in content: content = content.split('```json')[1].split('```')[0].strip()
    return json.loads(content)

async def generate_modern_premium_script(topic: str) -> Dict[str, Any]:
    """Orchestrate the Deep 'Logic-First' Analysis (Iterative Design)."""
    print(f"🚀 Starting Real-Logic Breakdown for: {topic}")
    
    print("✨ Stage 1: Logic & Fact Extraction...")
    facts = await stage1_scholar_extraction(topic)
    
    print("🎬 Stage 2: Code-First Architecture...")
    scene_plan = await stage2_narrative_architect(topic, facts)
    
    print(f"🎨 Stage 3: Designing {len(scene_plan)} logic frames sequentially...")
    final_scenes = []
    last_designed_scene = None
    
    # Process frames SEQUENTIALLY to ensure conceptual and visual continuity
    for scene in scene_plan:
        designed_scene = await stage3_frame_specialist(scene, topic, facts, last_designed_scene)
        # Ensure duration is at least matching narration weight
        words = len(designed_scene.get('narration', '').split())
        base_dur = max(6.0, (words / 2.0) + 2.0) # Buffer for complex tech
        designed_scene['duration'] = max(base_dur, designed_scene.get('visual_manifest', {}).get('target_duration_seconds', 0))
        
        final_scenes.append(designed_scene)
        last_designed_scene = designed_scene
    
    return {
        "title": topic,
        "total_duration": sum(s['duration'] for s in final_scenes),
        "scenes": final_scenes,
        "bg_color": final_scenes[0]['visual_manifest']['colors'][0] if final_scenes else "#000000",
        "research_foundation": facts
    }

if __name__ == "__main__":
    # Test run
    import asyncio
    async def test():
        topic = "Quantum Entanglement"
        result = await generate_modern_premium_script(topic)
        print(json.dumps(result, indent=2))
        
    asyncio.run(test())
