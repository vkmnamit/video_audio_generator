import json
import uuid
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from moviepy import (
    TextClip, 
    ColorClip, 
    AudioFileClip, 
    CompositeVideoClip, 
    concatenate_videoclips,
    ImageClip
)
from gtts import gTTS
import edge_tts
import asyncio
import requests
import random
import numpy as np
from fastapi.staticfiles import StaticFiles
from app_secrets import API_KEY
from PIL import Image
from io import BytesIO

# Create directories if they don't exist
os.makedirs("backend/output", exist_ok=True)
os.makedirs("backend/temp/audio", exist_ok=True)
os.makedirs("backend/temp/images", exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# 🖼️ IMAGE FETCHING - Get relevant images for topics
# ══════════════════════════════════════════════════════════════════════════════

def fetch_image_for_topic(query: str, width: int = 600, height: int = 400) -> str:
    """Fetch a relevant image from Unsplash for the given topic"""
    try:
        # Use Unsplash Source (free, no API key needed)
        # Clean query for URL
        clean_query = query.replace(" ", ",").lower()[:50]
        image_url = f"https://source.unsplash.com/{width}x{height}/?{clean_query}"
        
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            # Save image temporarily
            img_path = f"backend/temp/images/{uuid.uuid4()}.jpg"
            with open(img_path, 'wb') as f:
                f.write(response.content)
            return img_path
    except Exception as e:
        print(f"   ⚠️ Could not fetch image: {e}")
    
    return None

def create_image_clip(image_path: str, target_width: int, target_height: int, duration: float):
    """Create an ImageClip with proper sizing"""
    try:
        if image_path and os.path.exists(image_path):
            img_clip = ImageClip(image_path).with_duration(duration)
            # Resize to fit
            img_clip = img_clip.resized(width=target_width)
            return img_clip
    except Exception as e:
        print(f"   ⚠️ Error creating image clip: {e}")
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 MINIMALIST YOUTUBE SHORTS STYLE - Dark, Bold, Geometric
# ══════════════════════════════════════════════════════════════════════════════
# Style: Dark background, bold white text, geometric shapes, high contrast accents

# Scene Type → Frame Style mapping (UNIVERSAL - works for any topic)
FRAME_STYLES = {
    # Basic frames
    "title": "title_frame",         # 🎬 Big bold title
    "intro": "title_frame",         # 🎬 Same as title
    "outro": "title_frame",         # 🎬 End frame
    "summary": "summary_frame",     # ✅ Checkmarks, key points
    
    # Content frames
    "definition": "definition_frame",  # 📖 Define a term
    "explanation": "explanation_frame", # 💡 Explain a concept
    "example": "example_frame",        # 📌 Show an example
    "fact": "fact_frame",              # � Big number/statistic
    
    # Structured content
    "list": "list_frame",           # 📋 Bullet points
    "process": "process_frame",     # ⚙️ Steps with arrows
    "comparison": "comparison_frame", # ⚖️ Side-by-side comparison
    "timeline": "timeline_frame",   # � Timeline events
    "formula": "formula_frame",     # � Math formula
    "diagram": "diagram_frame",     # 📊 Simple diagram
    "flowchart": "flowchart_frame", # 🔀 Flowchart with nodes
    "array": "array_frame",         # 📊 Array visualization
    "table": "table_frame",         # 📋 Data table
    
    # Legacy/fallback
    "inputs": "list_frame",
    "output": "fact_frame",
    "step": "process_frame",
    "result": "fact_frame",
}

# Accent colors for variety (high contrast on dark bg)
ACCENT_COLORS = [
    (0, 255, 136),    # Neon Green
    (255, 107, 107),  # Coral Red
    (78, 205, 196),   # Teal
    (255, 230, 109),  # Yellow
    (199, 125, 255),  # Purple
    (255, 159, 67),   # Orange
]

# Dark background color
DARK_BG = (18, 18, 24)  # Near black with slight blue

# Helper functions for text handling
def wrap_text(text, max_chars=25):
    """Wrap text to fit within boxes - prevents overflow"""
    if not text:
        return ""
    words = str(text).split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line = (current_line + " " + word).strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = word[:max_chars]
    if current_line:
        lines.append(current_line)
    return "\n".join(lines[:3])  # Max 3 lines

def truncate_text(text, max_chars=40):
    """Truncate text with ellipsis - prevents overflow"""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."

FRAME_DESCRIPTIONS = {
    "title_frame": "🎬 TITLE - Bold centered text, accent underline",
    "summary_frame": "✅ SUMMARY - Checkmarks, key takeaways",
    "definition_frame": "📖 DEFINITION - Term + meaning",
    "explanation_frame": "💡 EXPLANATION - Concept with visual",
    "example_frame": "📌 EXAMPLE - Concrete example",
    "fact_frame": "🔢 FACT - Big number/statistic",
    "list_frame": "📋 LIST - Bullet points",
    "process_frame": "⚙️ PROCESS - Steps with arrows",
    "flowchart_frame": "🔀 FLOWCHART - Nodes with connections",
    "array_frame": "📊 ARRAY - Algorithm visualization",
    "table_frame": "📋 TABLE - Data in rows/columns",
    "comparison_frame": "⚖️ COMPARISON - Side by side",
    "timeline_frame": "📅 TIMELINE - Events in order",
    "formula_frame": "🧮 FORMULA - Math equation with parts",
    "diagram_frame": "📊 DIAGRAM - Shapes and connections",
}

def log_separator(char="═", length=80):
    print(f"\n{char * length}")

def log_header(title):
    log_separator()
    print(f"  {title}")
    log_separator()

app = FastAPI(title="Aetheris API")

# Mount output directory to serve video files
app.mount("/output", StaticFiles(directory="backend/output"), name="output")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    target_audience: Optional[str] = " students"
    video_type: Optional[str] = "short" # "short" (40-50s) or "long" (2-3m)

class VideoResponse(BaseModel):
    video_url: str
    title: str
    duration: float

@app.get("/")
async def root():
    return {"message": "Welcome to Aetheris - AI Video System"}

@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(request: PromptRequest):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    duration_constraint = "40-50 seconds" if request.video_type == "short" else "2-3 minutes"
    num_scenes = "6-8" if request.video_type == "short" else "10-15"
    
    # ══════════════════════════════════════════════════════════════════════════
    # 🎯 GEN-Z STYLE VIDEO: Engaging, Funny, Dramatic, Visual
    # ══════════════════════════════════════════════════════════════════════════
    system_prompt = f"""You are the BEST teacher in the world. You make ANY topic easy to understand. Create a {duration_constraint} explainer video.

🎓 YOUR TEACHING STYLE:
- Explain like you're talking to a curious 10-year-old
- Use REAL LIFE examples they can relate to  
- Break complex things into TINY simple pieces
- Use analogies: "It's like when you..."
- Show, don't just tell - USE VISUALS that make sense
- Make them go "Ohhhh, NOW I get it!"

🧠 THINK LIKE A TEACHER - CHOOSE THE RIGHT VISUAL:
Before each scene, ask: "What's the BEST way to show this?"

Available visual types - USE WHAT MAKES SENSE:
- ARRAY → When showing numbers being moved, sorted, or compared (like sorting algorithms)
- FLOWCHART → When showing step-by-step process with connections
- FORMULA → When there's a math equation to explain
- COMPARISON → When comparing two things side by side
- DIAGRAM → When showing parts of something or cycles
- TABLE → When showing data in rows and columns
- LIST/PROCESS → When listing steps or items

🎯 VIDEO STRUCTURE (Follow this flow):

1️⃣ HOOK (scene_type: "title")
   - Start with a question that makes them curious
   - "Ever wondered why...?" or "What if I told you...?"

2️⃣ WHAT IS IT? (scene_type: "definition") 
   - Define it in ONE simple sentence
   - Use an analogy: "It's basically like..."

3️⃣ WHY IT MATTERS (scene_type: "explanation")
   - Connect to their real life
   - "You use this every time you..."

4️⃣ HOW IT WORKS (USE THE RIGHT VISUAL!)
   - Think: "What would I DRAW on a whiteboard?"
   - Numbers/sorting? → Use "array" with array_data
   - Steps with flow? → Use "flowchart" with flow_nodes
   - Math equation? → Use "formula" with formula_parts
   - Process steps? → Use "process" with bullet_points
   - Comparing? → Use "comparison"

5️⃣ REAL EXAMPLE (scene_type: "example")
   - Something from their daily life
   - "Like when you..."

6️⃣ KEY TAKEAWAY (scene_type: "summary")
   - 2-3 simple points to remember
   - End with something memorable

═══════════════════════════════════════════════════════════════════════

📝 NARRATION STYLE - Talk like a friendly teacher:
- Simple words, short sentences
- "So basically...", "Think of it like...", "Here's the cool part..."
- Explain like you're helping a friend understand
- NO jargon - if you must use a term, explain it immediately

═══════════════════════════════════════════════════════════════════════

🎨 VISUAL ELEMENTS (Important!):

For FLOWCHART scenes, provide:
  "flow_nodes": [
    {{"id": 1, "text": "Input Name", "type": "input"}},
    {{"id": 2, "text": "Process Step", "type": "process"}},
    {{"id": 3, "text": "Output Result", "type": "output"}}
  ]
  "flow_connections": [[1,2], [2,3]]

For FORMULA scenes, provide:
  "formula_text": "E = mc²"
  "formula_parts": [
    {{"symbol": "E", "meaning": "Energy"}},
    {{"symbol": "m", "meaning": "Mass"}},
    {{"symbol": "c²", "meaning": "Speed of light squared"}}
  ]

For DIAGRAM scenes, provide:
  "diagram_type": "cycle" | "hierarchy" | "comparison" | "parts"
  "diagram_elements": ["Element 1", "Element 2", "Element 3"]
  "diagram_center": "Main concept in center"

For COMPARISON scenes, provide:
  "compare_left": {{"title": "Thing A", "points": ["Point 1", "Point 2"]}}
  "compare_right": {{"title": "Thing B", "points": ["Point 1", "Point 2"]}}

For ARRAY scenes (REQUIRED for sorting algorithms like Bubble Sort, Selection Sort, Merge Sort, Quick Sort, etc.):
  "array_data": [5, 3, 8, 1, 2],  // The numbers to visualize
  "highlight_indices": [0, 1],     // Indices being examined (yellow)
  "compare_indices": [0, 1],       // Indices being compared (blue)
  "swap_indices": [0, 1],          // Indices being swapped (red)
  "sorted_indices": [3, 4]         // Already sorted indices (green)

For TABLE scenes, provide:
  "table_headers": ["Column 1", "Column 2", "Column 3"]
  "table_rows": [["Row1 Col1", "Row1 Col2", "Row1 Col3"], ["Row2 Col1", "Row2 Col2", "Row2 Col3"]]

═══════════════════════════════════════════════════════════════════════

💡 TEACHING TIP:
Think about what a GREAT teacher would draw on a whiteboard!
- Teaching sorting? Draw the array with numbers moving!
- Teaching a formula? Show what each symbol means!
- Teaching a process? Draw the flow with arrows!
- Comparing things? Show them side by side!

The VISUAL should make the concept CLICK instantly. 
Choose whatever visualization BEST explains the concept.

═══════════════════════════════════════════════════════════════════════

📋 OUTPUT FORMAT:
{{
  "title": "Catchy Title (5 words max)",
  "vibe": "funny" | "dramatic" | "mind-blowing" | "chill",
  "scenes": [
    {{
      "scene_type": "title|definition|explanation|process|flowchart|fact|example|diagram|formula|comparison|array|table|summary",
      "headline": "2-4 WORDS MAX",
      "narration": "Spoken text - casual, engaging, human",
      "icon": "relevant emoji",
      "accent_color": "green|red|teal|yellow|purple|orange",
      // + scene-specific fields from above
    }}
  ]
}}

═══════════════════════════════════════════════════════════════════════

🔥 EXAMPLE for "How WiFi Works":

{{
  "title": "WiFi is Magic? Nope.",
  "vibe": "mind-blowing",
  "scenes": [
    {{
      "scene_type": "title",
      "headline": "INVISIBLE INTERNET?",
      "narration": "You're literally downloading TikToks through WALLS right now. How is that even possible?",
      "icon": "📶",
      "accent_color": "purple"
    }},
    {{
      "scene_type": "definition",
      "headline": "WIFI = RADIO",
      "narration": "WiFi is just fancy radio waves. Yep, same thing that plays music in your car. But for data.",
      "icon": "📻",
      "accent_color": "teal"
    }},
    {{
      "scene_type": "flowchart",
      "headline": "THE JOURNEY",
      "narration": "Here's how your meme gets from the internet to your phone.",
      "flow_nodes": [
        {{"id": 1, "text": "Internet", "type": "input"}},
        {{"id": 2, "text": "Router", "type": "process"}},
        {{"id": 3, "text": "Radio Waves", "type": "process"}},
        {{"id": 4, "text": "Your Phone", "type": "output"}}
      ],
      "flow_connections": [[1,2], [2,3], [3,4]],
      "accent_color": "green"
    }},
    {{
      "scene_type": "fact",
      "headline": "SPEED CHECK",
      "narration": "WiFi 6 can transfer data at 9.6 GIGABITS per second. That's downloading a whole movie in like... 3 seconds.",
      "fact_number": "9.6 Gbps",
      "fact_comparison": "= 1 movie in 3 sec",
      "icon": "⚡",
      "accent_color": "yellow"
    }},
    {{
      "scene_type": "summary",
      "headline": "NOW YOU KNOW",
      "narration": "WiFi equals radio waves equals internet through walls. You're basically a wizard now. You're welcome.",
      "key_points": ["WiFi = Radio waves", "Router = Translator", "Walls can't stop it"],
      "icon": "🧙",
      "accent_color": "purple"
    }}
  ]
}}

═══════════════════════════════════════════════════════════════════════

CRITICAL RULES:
1. Headlines: MAX 4 words, ALL CAPS
2. Narration: MAX 25 words per scene, conversational
3. Keep it SIMPLE - no jargon
4. Be FUNNY but still educational  
5. Generate {num_scenes} scenes
6. Match the vibe to the topic (science=mind-blowing, history=dramatic, etc.)
7. Target audience: {request.target_audience}
"""
    
    user_message = f"Topic: {request.prompt}. Audience: {request.target_audience}."

    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "response_format": {"type": "json_object"}
    }

    # ══════════════════════════════════════════════════════════════════════════
    # 📤 LOG: AI PROMPT BEING SENT
    # ══════════════════════════════════════════════════════════════════════════
    log_header("🚀 AETHERIS VIDEO GENERATION STARTED")
    print(f"📝 User Prompt: {request.prompt}")
    print(f"👥 Target Audience: {request.target_audience}")
    print(f"🎬 Video Type: {request.video_type} ({duration_constraint})")
    log_separator("─")
    print("📤 SYSTEM PROMPT TO AI:")
    print(f"   {system_prompt[:200]}...")
    log_separator("─")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            script_data = json.loads(result['choices'][0]['message']['content'])
            if isinstance(script_data, list) and len(script_data) > 0:
                script_data = script_data[0]
            
            # ══════════════════════════════════════════════════════════════════
            # 📥 LOG: AI RESPONSE RECEIVED
            # ══════════════════════════════════════════════════════════════════
            log_header("📥 AI SCRIPT GENERATED")
            print(f"🎬 Video Title: {script_data.get('title', 'Untitled')}")
            print(f"🎞️  Total Scenes: {len(script_data.get('scenes', []))}")
            log_separator("─")
            
            # Preview scene breakdown
            print("📋 SCENE BREAKDOWN (Scene Type → Frame Style):")
            for idx, s in enumerate(script_data.get('scenes', [])):
                stype = s.get('scene_type', 'explanation').lower()
                frame_style = FRAME_STYLES.get(stype, 'concept_frame')
                print(f"   Scene {idx+1}: [{stype.upper()}] → {FRAME_DESCRIPTIONS.get(frame_style, frame_style)}")
            log_separator("─")
            
            video_id = str(uuid.uuid4())
            clips = []
            total_duration = 0
            
            # Voice options for more human-like sound
            # Male: en-US-GuyNeural, en-US-ChristopherNeural
            # Female: en-US-JennyNeural, en-US-AriaNeural
            voice = "en-US-ChristopherNeural"  # Natural male voice
            
            for i, scene in enumerate(script_data['scenes']):
                # 1. Generate Audio with Edge TTS (more human-like)
                audio_path = f"backend/temp/audio/{video_id}_{i}.mp3"
                narration_text = scene.get('narration', '')
                
                try:
                    # Use edge_tts for natural voice
                    communicate = edge_tts.Communicate(narration_text, voice)
                    await communicate.save(audio_path)
                except Exception as e:
                    print(f"   ⚠️ Edge TTS failed, falling back to gTTS: {e}")
                    # Fallback to gTTS if edge_tts fails
                    tts = gTTS(text=narration_text, lang='en')
                    tts.save(audio_path)
                
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                
                # Canvas size (9:16 for shorts, 16:9 for long)
                width, height = (1080, 1920) if request.video_type == "short" else (1920, 1080)
                
                # Determine Frame Style based on Scene Type
                scene_type = scene.get('scene_type', 'explanation').lower()
                frame_style = FRAME_STYLES.get(scene_type, 'concept_frame')
                
                # Get accent color from scene or pick random
                accent_name = scene.get('accent_color', 'green').lower()
                accent_map = {'green': 0, 'red': 1, 'teal': 2, 'yellow': 3, 'purple': 4, 'orange': 5}
                accent_color = ACCENT_COLORS[accent_map.get(accent_name, random.randint(0, 5))]
                
                # Get headline (fallback to narration excerpt)
                headline = scene.get('headline', scene.get('narration', 'TOPIC')[:30].upper())
                visual_elements = scene.get('visual_elements', [])
                
                # ══════════════════════════════════════════════════════════════
                # 🎬 LOG: RENDERING SCENE
                # ══════════════════════════════════════════════════════════════
                print(f"\n🎬 RENDERING SCENE {i+1}/{len(script_data['scenes'])}")
                print(f"   📌 Scene Type: {scene_type.upper()}")
                print(f"   🎨 Frame Style: {FRAME_DESCRIPTIONS.get(frame_style, frame_style)}")
                print(f"   � Headline: {headline}")
                print(f"   🎨 Accent Color: {accent_name}")
                print(f"   ⏱️  Duration: {duration:.1f}s")
                print(f"   �️  Narration: \"{scene.get('narration', '')[:60]}...\"")
                print(f"   🔷 Visual Elements: {visual_elements}")

                layers = []
                
                # ═══════════════════════════════════════════════════════════════
                # 🎨 MINIMALIST YOUTUBE SHORTS STYLE RENDERING
                # ═══════════════════════════════════════════════════════════════
                
                # DARK BACKGROUND (base for all frames)
                bg_clip = ColorClip(size=(width, height), color=DARK_BG, duration=duration)
                
                # Get font (use system font)
                font_path = "/System/Library/Fonts/Helvetica.ttc"
                if not os.path.exists(font_path):
                    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

                # Get optional scene data
                list_items = scene.get('list_items', [])
                steps = scene.get('steps', [])
                compare_items = scene.get('compare_items', {})
                formula_text = scene.get('formula_text', '')
                timeline_items = scene.get('timeline_items', [])
                fact_number = scene.get('fact_number', '')
                icon = scene.get('icon', '')
                narration = scene.get('narration', '')

                # === TITLE FRAME ===
                if frame_style == "title_frame":
                    print(f"   → Rendering TITLE FRAME")
                    
                    # Icon if provided
                    if icon:
                        icon_clip = TextClip(text=icon, font_size=100, color='white', font=font_path).with_duration(duration)
                        icon_clip = icon_clip.with_position(('center', int(height * 0.3)))
                        layers.append(icon_clip)
                    
                    # Main headline
                    title_clip = TextClip(text=headline, font_size=85, color='white', font=font_path).with_duration(duration)
                    title_clip = title_clip.with_position(('center', int(height * 0.42)))
                    
                    # Accent underline
                    underline_w = min(len(headline) * 45, width - 200)
                    underline = ColorClip(size=(underline_w, 6), color=accent_color, duration=duration)
                    underline = underline.with_position(('center', int(height * 0.50)))
                    
                    layers.extend([title_clip, underline])

                # === DEFINITION FRAME ===
                elif frame_style == "definition_frame":
                    print(f"   → Rendering DEFINITION FRAME")
                    
                    # Headline (the term)
                    term_clip = TextClip(text=headline, font_size=70, color=accent_color, font=font_path).with_duration(duration)
                    term_clip = term_clip.with_position(('center', int(height * 0.08)))
                    layers.append(term_clip)
                    
                    # Fetch image for the term
                    print(f"   🖼️ Fetching definition image for: {headline}...")
                    img_path = fetch_image_for_topic(headline, width=int(width * 0.8), height=int(height * 0.30))
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.8), int(height * 0.30), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.18)))
                            layers.append(img_clip)
                    
                    # Definition text
                    def_clip = TextClip(
                        text=narration[:150], font_size=40, color='white', font=font_path,
                        method='caption', size=(width - 150, None)
                    ).with_duration(duration)
                    def_clip = def_clip.with_position(('center', int(height * 0.55)))
                    layers.append(def_clip)

                # === EXPLANATION FRAME ===
                elif frame_style == "explanation_frame":
                    print(f"   → Rendering EXPLANATION FRAME")
                    
                    # Headline at top
                    head_clip = TextClip(text=headline, font_size=65, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.08)))
                    layers.append(head_clip)
                    
                    # Fetch relevant image for the topic
                    image_query = f"{headline} {narration[:30]}"
                    print(f"   🖼️ Fetching image for: {image_query[:40]}...")
                    img_path = fetch_image_for_topic(image_query, width=int(width * 0.85), height=int(height * 0.35))
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.85), int(height * 0.35), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.18)))
                            layers.append(img_clip)
                    else:
                        # Fallback to accent box if no image
                        box = ColorClip(size=(int(width * 0.7), 180), color=accent_color, duration=duration)
                        box = box.with_position(('center', int(height * 0.35)))
                        layers.append(box)
                    
                    # Narration text at bottom
                    text_clip = TextClip(
                        text=narration[:120], font_size=38, color='#DDDDDD', font=font_path,
                        method='caption', size=(width - 120, None)
                    ).with_duration(duration)
                    text_clip = text_clip.with_position(('center', int(height * 0.62)))
                    layers.append(text_clip)

                # === LIST FRAME ===
                elif frame_style == "list_frame":
                    print(f"   → Rendering LIST FRAME")
                    
                    # Headline
                    head_clip = TextClip(text=headline, font_size=60, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.12)))
                    layers.append(head_clip)
                    
                    # List items with bullets
                    items = list_items if list_items else [narration[:50]]
                    y_start = int(height * 0.25)
                    for idx, item in enumerate(items[:5]):
                        bullet = TextClip(text="●", font_size=40, color=accent_color, font=font_path).with_duration(duration)
                        bullet = bullet.with_position((int(width * 0.15), y_start + idx * 80))
                        
                        item_text = TextClip(
                            text=str(item)[:40], font_size=38, color='white', font=font_path
                        ).with_duration(duration)
                        item_text = item_text.with_position((int(width * 0.22), y_start + idx * 80))
                        
                        layers.extend([bullet, item_text])

                # === PROCESS FRAME ===
                elif frame_style == "process_frame":
                    print(f"   → Rendering PROCESS FRAME")
                    
                    # Headline
                    head_clip = TextClip(text=headline, font_size=55, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Process steps (vertical layout for mobile)
                    step_list = steps if steps else [narration[:30], "Step 2", "Step 3"]
                    y_start = int(height * 0.22)
                    step_height = 120
                    
                    for idx, step in enumerate(step_list[:4]):
                        # Step number circle
                        circle = ColorClip(size=(60, 60), color=accent_color, duration=duration)
                        circle = circle.with_position((int(width * 0.1), y_start + idx * step_height))
                        
                        num = TextClip(text=str(idx+1), font_size=35, color='white', font=font_path).with_duration(duration)
                        num = num.with_position((int(width * 0.12), y_start + idx * step_height + 10))
                        
                        # Step text
                        step_text = TextClip(
                            text=str(step)[:35], font_size=34, color='white', font=font_path
                        ).with_duration(duration)
                        step_text = step_text.with_position((int(width * 0.22), y_start + idx * step_height + 15))
                        
                        layers.extend([circle, num, step_text])
                        
                        # Arrow to next step
                        if idx < len(step_list[:4]) - 1:
                            arrow = TextClip(text="↓", font_size=40, color=accent_color, font=font_path).with_duration(duration)
                            arrow = arrow.with_position((int(width * 0.12), y_start + idx * step_height + 70))
                            layers.append(arrow)

                # === COMPARISON FRAME (improved with title + points) ===
                elif frame_style == "comparison_frame":
                    print(f"   → Rendering COMPARISON FRAME")
                    
                    # Get compare data (new format or old)
                    compare_left = scene.get('compare_left', compare_items.get('left', {'title': 'Option A', 'points': []}))
                    compare_right = scene.get('compare_right', compare_items.get('right', {'title': 'Option B', 'points': []}))
                    
                    # Handle string format (old) vs dict format (new)
                    if isinstance(compare_left, str):
                        compare_left = {'title': compare_left, 'points': []}
                    if isinstance(compare_right, str):
                        compare_right = {'title': compare_right, 'points': []}
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.08)))
                    layers.append(head_clip)
                    
                    box_w = int(width * 0.42)
                    box_h = int(height * 0.4)
                    y_boxes = int(height * 0.2)
                    
                    # Left box
                    left_box = ColorClip(size=(box_w, box_h), color=(60, 60, 80), duration=duration)
                    left_box = left_box.with_position((int(width * 0.04), y_boxes))
                    layers.append(left_box)
                    
                    left_title = truncate_text(str(compare_left.get('title', 'A')), 15)
                    left_title_clip = TextClip(
                        text=left_title, font_size=36, color='white', font=font_path
                    ).with_duration(duration)
                    left_title_clip = left_title_clip.with_position((int(width * 0.08), y_boxes + 15))
                    layers.append(left_title_clip)
                    
                    # Left points
                    left_points = compare_left.get('points', [])
                    for i, pt in enumerate(left_points[:3]):
                        pt_clip = TextClip(
                            text="• " + truncate_text(str(pt), 18), font_size=26, color='#CCCCCC', font=font_path
                        ).with_duration(duration)
                        pt_clip = pt_clip.with_position((int(width * 0.08), y_boxes + 60 + i * 35))
                        layers.append(pt_clip)
                    
                    # VS in center
                    vs_clip = TextClip(text="VS", font_size=40, color=accent_color, font=font_path).with_duration(duration)
                    vs_clip = vs_clip.with_position(('center', y_boxes + box_h // 2 - 20))
                    layers.append(vs_clip)
                    
                    # Right box
                    right_box = ColorClip(size=(box_w, box_h), color=accent_color, duration=duration)
                    right_box = right_box.with_position((int(width * 0.54), y_boxes))
                    layers.append(right_box)
                    
                    right_title = truncate_text(str(compare_right.get('title', 'B')), 15)
                    right_title_clip = TextClip(
                        text=right_title, font_size=36, color='white', font=font_path
                    ).with_duration(duration)
                    right_title_clip = right_title_clip.with_position((int(width * 0.58), y_boxes + 15))
                    layers.append(right_title_clip)
                    
                    # Right points
                    right_points = compare_right.get('points', [])
                    for i, pt in enumerate(right_points[:3]):
                        pt_clip = TextClip(
                            text="• " + truncate_text(str(pt), 18), font_size=26, color='white', font=font_path
                        ).with_duration(duration)
                        pt_clip = pt_clip.with_position((int(width * 0.58), y_boxes + 60 + i * 35))
                        layers.append(pt_clip)
                    
                    # Narration at bottom
                    narr_clip = TextClip(
                        text=truncate_text(narration, 70), font_size=28, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.7)))
                    layers.append(narr_clip)

                # === FACT FRAME (big number with comparison) ===
                elif frame_style == "fact_frame":
                    print(f"   → Rendering FACT FRAME")
                    
                    fact_comparison = scene.get('fact_comparison', '')
                    
                    # Big number (make it fit)
                    number = truncate_text(str(fact_number if fact_number else headline), 12)
                    font_size = 120 if len(number) > 6 else 150
                    num_clip = TextClip(
                        text=number, font_size=font_size, color=accent_color, font=font_path
                    ).with_duration(duration)
                    num_clip = num_clip.with_position(('center', int(height * 0.25)))
                    layers.append(num_clip)
                    
                    # Label (headline)
                    label = truncate_text(headline if fact_number else "FACT", 25)
                    label_clip = TextClip(
                        text=label, font_size=45, color='white', font=font_path
                    ).with_duration(duration)
                    label_clip = label_clip.with_position(('center', int(height * 0.42)))
                    layers.append(label_clip)
                    
                    # Comparison (e.g., "= 1 movie in 3 sec")
                    if fact_comparison:
                        comp_clip = TextClip(
                            text=truncate_text(fact_comparison, 30), font_size=36, color=accent_color, font=font_path
                        ).with_duration(duration)
                        comp_clip = comp_clip.with_position(('center', int(height * 0.52)))
                        layers.append(comp_clip)
                    
                    # Narration
                    narr_clip = TextClip(
                        text=truncate_text(narration, 70), font_size=32, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.65)))
                    layers.append(narr_clip)

                # === FORMULA FRAME (with parts breakdown) ===
                elif frame_style == "formula_frame":
                    print(f"   → Rendering FORMULA FRAME")
                    
                    formula_parts = scene.get('formula_parts', [])
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Formula box
                    box = ColorClip(size=(int(width * 0.85), 120), color=(40, 40, 60), duration=duration)
                    box = box.with_position(('center', int(height * 0.22)))
                    layers.append(box)
                    
                    # Formula text (big)
                    formula = formula_text if formula_text else "Formula"
                    formula_clip = TextClip(
                        text=truncate_text(formula, 20), font_size=65, color=accent_color, font=font_path
                    ).with_duration(duration)
                    formula_clip = formula_clip.with_position(('center', int(height * 0.24)))
                    layers.append(formula_clip)
                    
                    # Formula parts breakdown
                    if formula_parts:
                        y_parts = int(height * 0.4)
                        for idx, part in enumerate(formula_parts[:4]):
                            symbol = str(part.get('symbol', '?'))
                            meaning = truncate_text(str(part.get('meaning', '')), 20)
                            
                            # Symbol
                            sym_clip = TextClip(
                                text=symbol, font_size=50, color=accent_color, font=font_path
                            ).with_duration(duration)
                            sym_clip = sym_clip.with_position((int(width * 0.15), y_parts + idx * 70))
                            
                            # Equals sign
                            eq_clip = TextClip(text="=", font_size=40, color='white', font=font_path).with_duration(duration)
                            eq_clip = eq_clip.with_position((int(width * 0.35), y_parts + idx * 70 + 5))
                            
                            # Meaning
                            mean_clip = TextClip(
                                text=meaning, font_size=32, color='#CCCCCC', font=font_path
                            ).with_duration(duration)
                            mean_clip = mean_clip.with_position((int(width * 0.45), y_parts + idx * 70 + 10))
                            
                            layers.extend([sym_clip, eq_clip, mean_clip])
                    
                    # Narration at bottom
                    narr_clip = TextClip(
                        text=truncate_text(narration, 80), font_size=30, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.75)))
                    layers.append(narr_clip)

                # === ARRAY FRAME (for algorithms: sorting, etc.) ===
                elif frame_style == "array_frame":
                    print(f"   → Rendering ARRAY FRAME")
                    
                    # Get array data
                    array_state = scene.get('array_state', [5, 2, 8, 1, 9])
                    if isinstance(array_state, str):
                        try:
                            array_state = json.loads(array_state)
                        except:
                            array_state = [5, 2, 8, 1, 9]
                    highlight_indices = scene.get('highlight_indices', [])
                    action = scene.get('action', 'none')
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=60, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Array boxes
                    num_elements = len(array_state)
                    box_size = min(100, (width - 100) // max(num_elements, 1) - 15)
                    total_width = num_elements * (box_size + 15) - 15
                    start_x = (width - total_width) // 2
                    y_pos = int(height * 0.35)
                    
                    # Colors
                    compare_color = (255, 230, 109)  # Yellow
                    swap_color = (0, 255, 136)       # Green
                    sorted_color = (78, 205, 196)    # Teal
                    normal_color = (60, 60, 80)      # Dark gray
                    
                    for idx, num in enumerate(array_state):
                        x_pos = start_x + idx * (box_size + 15)
                        
                        # Box color based on action
                        if idx in highlight_indices:
                            if action == 'compare':
                                box_color = compare_color
                            elif action == 'swap':
                                box_color = swap_color
                            elif action == 'sorted':
                                box_color = sorted_color
                            else:
                                box_color = accent_color
                        else:
                            box_color = normal_color
                        
                        # Box
                        box = ColorClip(size=(box_size, box_size), color=box_color, duration=duration)
                        box = box.with_position((x_pos, y_pos))
                        layers.append(box)
                        
                        # Number
                        num_clip = TextClip(
                            text=str(num), font_size=int(box_size * 0.5), color='white', font=font_path
                        ).with_duration(duration)
                        num_clip = num_clip.with_position((x_pos + box_size//4, y_pos + box_size//4))
                        layers.append(num_clip)
                    
                    # Action indicator
                    if action == 'swap' and len(highlight_indices) >= 2:
                        swap_text = TextClip(text="⟷ SWAP", font_size=45, color=swap_color, font=font_path).with_duration(duration)
                        swap_text = swap_text.with_position(('center', y_pos - 60))
                        layers.append(swap_text)
                    elif action == 'compare':
                        comp_text = TextClip(text="👀 COMPARING", font_size=40, color=compare_color, font=font_path).with_duration(duration)
                        comp_text = comp_text.with_position(('center', y_pos - 60))
                        layers.append(comp_text)
                    elif action == 'sorted':
                        done_text = TextClip(text="✓ SORTED!", font_size=50, color=sorted_color, font=font_path).with_duration(duration)
                        done_text = done_text.with_position(('center', y_pos + box_size + 30))
                        layers.append(done_text)
                    
                    # Narration
                    narr_clip = TextClip(
                        text=truncate_text(narration, 80), font_size=32, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.65)))
                    layers.append(narr_clip)

                # === TABLE FRAME (for data) ===
                elif frame_style == "table_frame":
                    print(f"   → Rendering TABLE FRAME")
                    
                    table_headers = scene.get('table_headers', ['Column 1', 'Column 2'])
                    table_rows = scene.get('table_rows', [['Data 1', 'Data 2']])
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Table layout
                    num_cols = len(table_headers)
                    col_width = (width - 100) // max(num_cols, 1)
                    row_height = 60
                    start_x = 50
                    start_y = int(height * 0.22)
                    
                    # Header row (colored)
                    header_bg = ColorClip(size=(width - 100, row_height), color=accent_color, duration=duration)
                    header_bg = header_bg.with_position((start_x, start_y))
                    layers.append(header_bg)
                    
                    for idx, header in enumerate(table_headers[:4]):
                        h_clip = TextClip(
                            text=truncate_text(str(header), 12), font_size=28, color='white', font=font_path
                        ).with_duration(duration)
                        h_clip = h_clip.with_position((start_x + idx * col_width + 10, start_y + 15))
                        layers.append(h_clip)
                    
                    # Data rows
                    for row_idx, row in enumerate(table_rows[:4]):
                        row_y = start_y + (row_idx + 1) * row_height
                        row_bg_color = (40, 40, 50) if row_idx % 2 == 0 else (50, 50, 60)
                        row_bg = ColorClip(size=(width - 100, row_height), color=row_bg_color, duration=duration)
                        row_bg = row_bg.with_position((start_x, row_y))
                        layers.append(row_bg)
                        
                        for col_idx, cell in enumerate(row[:4]):
                            c_clip = TextClip(
                                text=truncate_text(str(cell), 12), font_size=26, color='#DDDDDD', font=font_path
                            ).with_duration(duration)
                            c_clip = c_clip.with_position((start_x + col_idx * col_width + 10, row_y + 18))
                            layers.append(c_clip)
                    
                    # Narration
                    narr_clip = TextClip(
                        text=truncate_text(narration, 70), font_size=30, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.7)))
                    layers.append(narr_clip)

                # === FLOWCHART FRAME (nodes with connections) ===
                elif frame_style == "flowchart_frame":
                    print(f"   → Rendering FLOWCHART FRAME")
                    
                    # Get flowchart data
                    flow_nodes = scene.get('flow_nodes', [])
                    flow_connections = scene.get('flow_connections', [])
                    
                    # Headline at top
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), 
                        font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.08)))
                    layers.append(head_clip)
                    
                    # If no flow_nodes, create from steps
                    if not flow_nodes and steps:
                        flow_nodes = [{"id": i+1, "text": s, "type": "process"} for i, s in enumerate(steps[:4])]
                    elif not flow_nodes:
                        flow_nodes = [
                            {"id": 1, "text": "Input", "type": "input"},
                            {"id": 2, "text": "Process", "type": "process"},
                            {"id": 3, "text": "Output", "type": "output"}
                        ]
                    
                    # Layout nodes vertically for mobile
                    num_nodes = min(len(flow_nodes), 4)
                    node_height = 90
                    node_width = int(width * 0.7)
                    y_start = int(height * 0.18)
                    spacing = int((height * 0.6) / max(num_nodes, 1))
                    
                    # Colors for node types
                    node_colors = {
                        "input": (78, 205, 196),    # Teal
                        "process": accent_color,
                        "output": (0, 255, 136),    # Green
                    }
                    
                    for idx, node in enumerate(flow_nodes[:4]):
                        node_text = truncate_text(str(node.get('text', f'Step {idx+1}')), 25)
                        node_type = node.get('type', 'process')
                        node_color = node_colors.get(node_type, accent_color)
                        
                        y_pos = y_start + idx * spacing
                        x_pos = int((width - node_width) / 2)
                        
                        # Node box
                        node_box = ColorClip(size=(node_width, node_height), color=node_color, duration=duration)
                        node_box = node_box.with_position((x_pos, y_pos))
                        layers.append(node_box)
                        
                        # Node text
                        text_clip = TextClip(
                            text=node_text, font_size=32, color='white', font=font_path
                        ).with_duration(duration)
                        text_clip = text_clip.with_position((x_pos + 20, y_pos + 30))
                        layers.append(text_clip)
                        
                        # Arrow to next node
                        if idx < num_nodes - 1:
                            arrow = TextClip(text="↓", font_size=50, color='white', font=font_path).with_duration(duration)
                            arrow = arrow.with_position(('center', y_pos + node_height + 5))
                            layers.append(arrow)
                    
                    # Narration at bottom
                    narr_clip = TextClip(
                        text=truncate_text(narration, 60), font_size=28, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.85)))
                    layers.append(narr_clip)

                # === TIMELINE FRAME ===
                elif frame_style == "timeline_frame":
                    print(f"   → Rendering TIMELINE FRAME")
                    
                    # Headline
                    head_clip = TextClip(text=headline, font_size=55, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Timeline line
                    line = ColorClip(size=(6, int(height * 0.5)), color=accent_color, duration=duration)
                    line = line.with_position((int(width * 0.15), int(height * 0.2)))
                    layers.append(line)
                    
                    # Timeline items
                    items = timeline_items if timeline_items else [{'year': '2024', 'event': narration[:30]}]
                    y_start = int(height * 0.22)
                    
                    for idx, item in enumerate(items[:4]):
                        year = item.get('year', str(2020 + idx)) if isinstance(item, dict) else str(item)
                        event = truncate_text(item.get('event', str(item)) if isinstance(item, dict) else str(item), 25)
                        
                        # Year
                        year_clip = TextClip(
                            text=str(year)[:10], font_size=40, color=accent_color, font=font_path
                        ).with_duration(duration)
                        year_clip = year_clip.with_position((int(width * 0.2), y_start + idx * 100))
                        
                        # Event
                        event_clip = TextClip(
                            text=event, font_size=30, color='white', font=font_path
                        ).with_duration(duration)
                        event_clip = event_clip.with_position((int(width * 0.2), y_start + idx * 100 + 40))
                        
                        layers.extend([year_clip, event_clip])

                # === DIAGRAM FRAME (with center + surrounding elements) ===
                elif frame_style == "diagram_frame":
                    print(f"   → Rendering DIAGRAM FRAME")
                    
                    diagram_elements = scene.get('diagram_elements', [])
                    diagram_center = scene.get('diagram_center', headline)
                    diagram_type = scene.get('diagram_type', 'cycle')
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=45, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.08)))
                    layers.append(head_clip)
                    
                    # Central concept box
                    center_size = 160
                    center_box = ColorClip(size=(center_size, center_size), color=accent_color, duration=duration)
                    center_x = (width - center_size) // 2
                    center_y = int(height * 0.32)
                    center_box = center_box.with_position((center_x, center_y))
                    layers.append(center_box)
                    
                    # Center text
                    center_text = TextClip(
                        text=truncate_text(str(diagram_center), 10), font_size=28, color='white', font=font_path
                    ).with_duration(duration)
                    center_text = center_text.with_position((center_x + 15, center_y + center_size // 2 - 15))
                    layers.append(center_text)
                    
                    # Surrounding elements (arranged in a grid below)
                    if diagram_elements:
                        num_elements = min(len(diagram_elements), 4)
                        elem_w = int((width - 100) / min(num_elements, 2)) - 20
                        elem_h = 70
                        y_elem = int(height * 0.55)
                        
                        for idx, elem in enumerate(diagram_elements[:4]):
                            row = idx // 2
                            col = idx % 2
                            x_pos = 50 + col * (elem_w + 20)
                            y_pos = y_elem + row * (elem_h + 15)
                            
                            # Element box
                            elem_box = ColorClip(size=(elem_w, elem_h), color=(60, 60, 80), duration=duration)
                            elem_box = elem_box.with_position((x_pos, y_pos))
                            layers.append(elem_box)
                            
                            # Element text
                            elem_text = TextClip(
                                text=truncate_text(str(elem), 20), font_size=24, color='white', font=font_path
                            ).with_duration(duration)
                            elem_text = elem_text.with_position((x_pos + 10, y_pos + 22))
                            layers.append(elem_text)
                    
                    # Narration at bottom
                    narr_clip = TextClip(
                        text=truncate_text(narration, 60), font_size=28, color='#AAAAAA', font=font_path,
                        method='caption', size=(width - 80, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.82)))
                    layers.append(narr_clip)

                # === EXAMPLE FRAME ===
                elif frame_style == "example_frame":
                    print(f"   → Rendering EXAMPLE FRAME")
                    
                    example_text = scene.get('example_text', '')
                    
                    # "EXAMPLE" label
                    label_clip = TextClip(text="📌 EXAMPLE", font_size=40, color=accent_color, font=font_path).with_duration(duration)
                    label_clip = label_clip.with_position(('center', int(height * 0.05)))
                    layers.append(label_clip)
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.12)))
                    layers.append(head_clip)
                    
                    # Fetch relevant image for the example
                    image_query = f"{headline} {example_text or narration[:20]}"
                    print(f"   🖼️ Fetching example image for: {image_query[:40]}...")
                    img_path = fetch_image_for_topic(image_query, width=int(width * 0.85), height=int(height * 0.35))
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.85), int(height * 0.35), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.22)))
                            layers.append(img_clip)
                    else:
                        # Fallback to colored box
                        box = ColorClip(size=(int(width * 0.85), 150), color=(40, 45, 55), duration=duration)
                        box = box.with_position(('center', int(height * 0.38)))
                        layers.append(box)
                        
                        if example_text:
                            ex_clip = TextClip(
                                text=truncate_text(example_text, 35), font_size=36, color=accent_color, font=font_path
                            ).with_duration(duration)
                            ex_clip = ex_clip.with_position(('center', int(height * 0.42)))
                            layers.append(ex_clip)
                    
                    # Narration below
                    narr_clip = TextClip(
                        text=truncate_text(narration, 80), font_size=32, color='#CCCCCC', font=font_path,
                        method='caption', size=(width - 100, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.62)))
                    layers.append(narr_clip)

                # === SUMMARY FRAME (with key_points) ===
                elif frame_style == "summary_frame":
                    print(f"   → Rendering SUMMARY FRAME")
                    
                    key_points = scene.get('key_points', [])
                    
                    # Headline
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), font_size=55, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.1)))
                    layers.append(head_clip)
                    
                    # Big checkmark
                    check = TextClip(text="✓", font_size=100, color=accent_color, font=font_path).with_duration(duration)
                    check = check.with_position(('center', int(height * 0.2)))
                    layers.append(check)
                    
                    # Key points (if provided)
                    if key_points:
                        y_start = int(height * 0.35)
                        for idx, point in enumerate(key_points[:3]):
                            point_clip = TextClip(
                                text="✓ " + truncate_text(str(point), 30), 
                                font_size=36, color='white', font=font_path
                            ).with_duration(duration)
                            point_clip = point_clip.with_position((int(width * 0.12), y_start + idx * 60))
                            layers.append(point_clip)
                        
                        # Narration below points
                        narr_y = y_start + len(key_points[:3]) * 60 + 40
                    else:
                        narr_y = int(height * 0.4)
                    
                    # Narration
                    narr_clip = TextClip(
                        text=truncate_text(narration, 100), font_size=34, color='#CCCCCC', font=font_path,
                        method='caption', size=(width - 100, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', narr_y))
                    layers.append(narr_clip)

                # === FALLBACK (unknown frame type) ===
                else:
                    print(f"   → Rendering FALLBACK FRAME for: {frame_style}")
                    
                    # Simple headline + narration
                    head_clip = TextClip(
                        text=truncate_text(headline, 25), font_size=60, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.3)))
                    
                    text_clip = TextClip(
                        text=truncate_text(narration, 100), font_size=36, color='#CCCCCC', font=font_path,
                        method='caption', size=(width - 100, None)
                    ).with_duration(duration)
                    text_clip = text_clip.with_position(('center', int(height * 0.5)))
                    
                    layers.extend([head_clip, text_clip])

                # Compose the final scene clip (dark bg + all layers)
                final_scene_clip = CompositeVideoClip([
                    bg_clip,
                    *layers
                ], size=(width, height)).with_audio(audio_clip)
                
                clips.append(final_scene_clip)
                total_duration += duration

            # Concatenate all scenes
            final_video = concatenate_videoclips(clips, method="compose")
            output_filename = f"{video_id}.mp4"
            output_path = f"backend/output/{output_filename}"
            
            # Write video file
            print(f"\n📹 Encoding final video...")
            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            
            # ══════════════════════════════════════════════════════════════════
            # ✅ LOG: VIDEO GENERATION COMPLETE
            # ══════════════════════════════════════════════════════════════════
            log_header("✅ VIDEO GENERATION COMPLETE")
            print(f"🎬 Title: {script_data['title']}")
            print(f"⏱️  Total Duration: {total_duration:.1f}s")
            print(f"📁 Output: {output_path}")
            print(f"🌐 URL: http://localhost:8000/output/{output_filename}")
            log_separator()
            
            return VideoResponse(
                video_url=f"http://localhost:8000/output/{output_filename}",
                title=script_data['title'],
                duration=total_duration
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
