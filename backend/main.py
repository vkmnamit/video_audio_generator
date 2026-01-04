

# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 SCRIPT-ONLY & VIDEO-FROM-SCRIPT ENDPOINTS (for frontend review/edit)
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import Body
from pydantic import BaseModel
from typing import Optional, List, Literal


class ScriptRequest(BaseModel):
    prompt: str
    themes: Optional[List[Literal[
        "algorithm",
        "conceptual",
        "science",
        "history",
        "finance",
        "general"
    ]]] = ["conceptual"]
    video_type: Optional[str] = "short"
    target_audience: Optional[str] = "students"

class ScriptWithImagesRequest(BaseModel):
    session_id: str
    topic: str
    video_type: Optional[str] = "short"
    themes: Optional[List[Literal[
        "algorithm",
        "conceptual",
        "science",
        "history",
        "finance",
        "general"
    ]]] = ["conceptual"]

class VideoFromScriptRequest(BaseModel):
    script: dict
    theme: Optional[str] = "algorithm"
    prompt: Optional[str] = ""
    video_type: Optional[str] = "short"
    session_id: Optional[str] = ""
    topic: Optional[str] = ""

# Place these endpoints after app is defined
def register_script_endpoints(app):
    @app.post("/generate-script")
    async def generate_script(request: ScriptRequest):
        """
        Generate and return only the AI-generated script (scene list) for a prompt.
        Uses the new 'Modern Premium' flow: Scholar (Facts) + Director (Manim Script).
        """
        if not request.prompt or request.prompt.strip() == "":
            raise HTTPException(status_code=400, detail="Please enter a topic to generate a video script.")
        if not MANIM_AVAILABLE:
            raise HTTPException(status_code=503, detail="Manim not available.")
        
        try:
            from modern_pipeline import generate_modern_premium_script
            script = await generate_modern_premium_script(request.prompt)
            
            # --- Inject scene_policy / semantic framing ---
            try:
                from scene_policy import decide_scene_type
            except ImportError:
                def decide_scene_type(scene, topic=None, scene_id=None):
                    return scene.get('intent', 'explanation')
            
            topic = request.prompt
            for i, scene in enumerate(script.get('scenes', [])):
                scene_id = i + 1
                # Map intent to scene_type if director didn't use scene_type
                if 'scene_type' not in scene:
                    scene['scene_type'] = decide_scene_type(scene, topic=topic, scene_id=scene_id)
                
                # Ensure headline exists (Director script has headline)
                if 'headline' not in scene:
                    scene['headline'] = scene.get('title', topic)

            return script
        except Exception as e:
            print(f"❌ Modern script generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")

    @app.post("/generate-script-with-images")
    async def generate_script_with_images(request: ScriptWithImagesRequest):
        """
        Generate and return a script using user-uploaded images (for review/edit).
        """
        if not request.topic or request.topic.strip() == "":
            raise HTTPException(status_code=400, detail="Please enter a topic to generate a video script.")
        session = image_sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found. Upload images first.")
        script = await generate_script_with_user_images(request.topic, session)
        if not script:
            raise HTTPException(status_code=500, detail="Failed to generate script with images.")
        return script

    @app.post("/generate-video-from-script")
    async def generate_video_from_script(request: VideoFromScriptRequest):
        """
        Generate a video from a reviewed/edited script (scene list).
        """
        if not MANIM_AVAILABLE:
            raise HTTPException(status_code=503, detail="Manim not available.")
        try:
            generator = ManimVideoGenerator(theme_name=request.theme)
            video_path = await generator.generate_from_script(request.script)
            video_filename = os.path.basename(video_path)
            video_url = f"{BASE_URL}/videos/{video_filename}"
            # Calculate actual duration from the scenes provided in the script
            # In the modern pipeline, each scene has a 'duration' field
            total_duration = sum(float(s.get('duration', 5.0)) for s in request.script.get('scenes', []))
            
            return {
                "video_url": video_url,
                "title": request.script.get('title', 'Untitled'),
                "duration": total_duration,
                "quality": "HIGH (Manim)",
                "scenes": len(request.script.get('scenes', [])),
                "theme": request.theme
            }
        except Exception as e:
            print(f"   ❌ Manim rendering failed: {e}")
            raise HTTPException(status_code=500, detail=f"Video rendering failed: {e}")


# Register endpoints after app is defined
# (Move this to after the FastAPI app = FastAPI(...) definition)
import json
from semantic_scene_map import get_semantic_scene_type
import uuid
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
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
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 SMART VIDEO ENGINE - Dynamic, Modern, Varied Frames
# ═══════════════════════════════════════════════════════════════════════════════
from semantic_framing import choose_layout, get_layout_zones, LayoutType
from semantic_renderers import render_semantic_frame, RENDERERS

# NEW: Smart video engine with dynamic styles
from smart_video_engine import (
    create_video_plan,
    parse_ai_explanation,
    VideoStyle,
    generate_explanation_prompt,
    KnowledgeUnit,
    classify_meaning,
    COLOR_PALETTES,
)
from modern_renderers import render_frame, render_all_scenes, FRAME_RENDERERS

# NEW: Visual renderers with AI images, equations, flowcharts
from visual_renderers import render_visual_frame, VISUAL_RENDERERS, get_palette_for_topic

# NEW: Clean renderers (no external API, 100% reliable)
from clean_renderers import render_clean_frame, RENDERERS as CLEAN_RENDERERS

# NEW: AI-enhanced renderer with beautiful flowcharts
from ai_image_renderer import render_ai_frame, RENDERERS as AI_RENDERERS

# NEW: Themed renderer - code-based, 100% reliable, user-controlled themes
from themed_renderer import render_themed_frame

# NEW: Manim + MoviePy engine for HIGH QUALITY animations
# This is the GOLD combo for educational content
try:
    from manim_engine import ManimVideoGenerator, THEMES as MANIM_THEMES
    MANIM_AVAILABLE = True
    print("✅ Manim engine loaded - HIGH QUALITY mode available!")
except ImportError as e:
    MANIM_AVAILABLE = False
    print(f"⚠️ Manim not available: {e}")

from style_reference_system import (
    DEFAULT_THEMES,
    get_current_theme,
    set_current_theme,
    load_theme,
    list_available_themes,
    get_theme_preview_colors,
)


# Flags to control which rendering system to use
USE_MANIM = True           # NEW: Manim for professional animations (BEST QUALITY)
USE_THEMED_RENDERER = False  # Code-based, consistent themes  
USE_AI_RENDERER = False     # AI-enhanced with flowcharts
USE_CLEAN_RENDERER = False  # Clean visuals with emojis
USE_VISUAL_RENDERER = False # AI images (may hit rate limits)
USE_SMART_ENGINE = False    # Disabled in favor of clean renderer
USE_SEMANTIC_FRAMING = True
USE_MOTION_CANVAS = False   # <--- Fix: define this flag

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# Get API key from environment or fallback to app_secrets

# Always try to get API_KEY from app_secrets.py if not set in env
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    try:
        from app_secrets import API_KEY as SECRET_API_KEY
        API_KEY = SECRET_API_KEY
    except ImportError:
        raise ValueError("OPENROUTER_API_KEY not found in environment or app_secrets.py")

# OpenAI API Key for DALL-E image generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    try:
        from app_secrets import OPENAI_API_KEY
    except ImportError:
        OPENAI_API_KEY = None
        print("⚠️ OPENAI_API_KEY not found - will use Unsplash for images instead of DALL-E")

# Google API Key for Imagen image generation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDtYX_1gdrVYP9i21K4jiSgnuOqpLYG7n8")


# Create directories if they don't exist
os.makedirs("output", exist_ok=True)
os.makedirs("temp/audio", exist_ok=True)
os.makedirs("temp/images", exist_ok=True)

# Serve videos for download/playback
from fastapi.staticfiles import StaticFiles

# ══════════════════════════════════════════════════════════════════════════════
# 🖼️ IMAGE GENERATION - Pollinations.ai (FREE, no API key!) + Fallbacks
# ══════════════════════════════════════════════════════════════════════════════

def generate_image_stable_diffusion(prompt: str, scene_type: str = "explanation") -> str:
    """Generate an AI image using Pollinations.ai (FREE, no API key needed!)
    
    Following the SHORTS FRAMING BLUEPRINT:
    - Icons only (sun, leaf, water, etc.)
    - Clean, minimal, dark background
    - NO text, NO arrows (those are added by code)
    """
    try:
        # Build icon-focused prompts based on scene type
        scene_prompts = {
            "title": f"Single bold iconic symbol representing {prompt}, centered, minimal flat design, dark background, vibrant accent color, no text, vector style icon",
            "inputs": f"Simple flat icon of {prompt}, minimal design, dark background, bright color, no text, centered, clean vector illustration",
            "process": f"Simple diagram icon showing {prompt}, flat design, dark background, glowing accent color, no text, minimal shapes",
            "output": f"Result icon representing {prompt}, bright accent color, dark background, minimal flat design, no text",
            "definition": f"Single bold icon representing {prompt}, centered, modern flat design, dark background, bright accent color, no text",
            "explanation": f"Educational icon illustrating {prompt}, clean flat design, dark background, accent color glow, no text",
            "example": f"Real-world icon of {prompt}, friendly cartoon style, dark background, bright colors, no text",
            "flowchart": f"Simple flowchart diagram for {prompt}, flat design, dark background, cyan and white, no text",
            "diagram": f"Scientific diagram of {prompt}, dark background, clean lines, accent colors, no text",
            "formula": f"Mathematical concept icon for {prompt}, abstract geometric shapes, dark background, no text",
            "array": f"Data boxes visualization for {prompt}, colorful numbered boxes, dark background, neon accents",
            "summary": f"Checkmark success icon, green accent, dark background, minimal flat design, no text",
            "comparison": f"Two contrasting icons side by side for {prompt}, versus style, dark background",
            "timeline": f"Timeline marker icon for {prompt}, horizontal line with markers, dark background",
            "fact": f"Big bold icon representing {prompt}, impressive scale, dark background, bright accent, no text",
            "code": f"Code snippet icon representing {prompt}, dark background, clean flat design, bright accent color, no text",
            "DSA": f"Data structure and algorithm icon for {prompt}, clean flat design, dark background, bright accent color, no text",
            "SST": f"Superscalar architecture icon for {prompt}, modern flat design, dark background, vibrant accent color, no text",
            "website": f"Website icon representing {prompt}, modern flat design, dark background, bright accent color, no text",
            "visulaization": f"Data visualization icon for {prompt}, colorful shapes, dark background, bright accent colors, no text",
            "maths": f"Mathematics icon for {prompt}, geometric shapes, dark background, bright accent colors, no text",
            "diagram": f"Scientific diagram of {prompt}, dark background, clean lines, accent colors, no text",
            "flowchart": f"Simple flowchart diagram for {prompt}, flat design, dark background, cyan and white, no text",
            "list": f"Bullet points icon representing {prompt}, checklist style, dark background, bright accent colors, no text",
            "tree": f"Tree data structure icon for {prompt}, clean flat design, dark background, bright accent colors, no text",
            "linked list": f"Linked list data structure icon for {prompt}, clean flat design, dark background, bright accent colors, no text",
            "graph": f"Graph data structure icon for {prompt}, nodes and edges, dark background, bright accent colors, no text",
            "table": f"Data table icon for {prompt}, rows and columns, dark background, bright accent colors, no text",
            "stack": f"Stack data structure icon for {prompt}, clean flat design, dark background, bright accent colors, no text",
            "queue": f"Queue data structure icon for {prompt}, clean flat design, dark background, bright accent colors, no text",
        }
        
        base_prompt = scene_prompts.get(scene_type, f"Clean minimal icon of {prompt}, flat design, dark background, accent color, no text")
        style_suffix = ", high quality, professional icon design, digital art, dribbble style"
        full_prompt = base_prompt + style_suffix
        
        print(f"   🎨 Pollinations AI [{scene_type}]: {prompt[:40]}...")
        
        # Use Pollinations.ai - FREE image generation with Stable Diffusion
        # URL encode the prompt
        import urllib.parse
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Pollinations API - completely free!
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1024&model=flux&nologo=true"
        
        response = requests.get(url, timeout=120)
        
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
            img_path = f"temp/images/{uuid.uuid4()}.png"
            with open(img_path, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Pollinations AI image saved: {img_path}")
            return img_path
        else:
            error_msg = response.text[:200] if response.text else "Unknown error"
            print(f"   ⚠️ Pollinations error ({response.status_code}): {error_msg[:50]}")
    except Exception as e:
        print(f"   ⚠️ Pollinations failed: {e}")
    
    return None

def generate_image_google(prompt: str, scene_type: str = "explanation") -> str:
    """Generate an AI image using Google Gemini 2.0 Flash with image generation"""
    try:
        # Build a detailed prompt based on scene type
        scene_prompts = {
            "flowchart": f"Educational flowchart diagram showing {prompt}. Clean boxes connected with arrows, minimal text labels, modern flat design style, dark navy background, white and cyan colored elements, professional infographic style",
            "process": f"Step-by-step process infographic for {prompt}. Numbered circular steps with simple icons, connected by arrows, modern minimalist design, dark background with bright accent colors",
            "comparison": f"Side-by-side comparison infographic of {prompt}. Two columns with icons and bullet points, versus layout, dark theme with contrasting colors, clean professional design",
            "diagram": f"Educational labeled diagram of {prompt}. Clear labels with lines pointing to parts, clean vector style, dark background with bright accents, scientific illustration style",
            "formula": f"Visual mathematical concept illustration for {prompt}. Abstract geometric shapes representing the concept, clean modern design, dark background with glowing accents",
            "array": f"Data visualization showing {prompt}. Colorful boxes with numbers, arrows indicating movement, algorithm visualization style, dark background with neon accents",
            "timeline": f"Horizontal timeline infographic about {prompt}. Events marked with icons on a line, clean modern design, dark theme with colorful markers",
            "definition": f"Iconic symbol illustration representing {prompt}. Single bold icon or symbol, modern flat design, centered composition, dark background with bright colored accent",
            "example": f"Real-world illustration of {prompt}. Friendly cartoon style scene, relatable everyday setting, bright cheerful colors, simple clean design",
            "code": f"Code snippet icon representing {prompt}, dark background, clean flat design, bright accent color, no text",
            "list": f"Bullet points icon representing {prompt}, checklist style, dark background, bright accent colors, no text",
            "linked list": f"Linked list data structure icon for {prompt}, clean flat design, dark background, bright accent colors, no text",
        }
        
        image_prompt = scene_prompts.get(scene_type, f"Clean educational illustration about {prompt}. Modern flat design, simple geometric shapes, dark background, vibrant accent colors, professional infographic style")
        
        print(f"   🎨 Google Gemini [{scene_type}]: {prompt[:40]}...")
        
        # Try Gemini 2.0 Flash (experimental image generation)
        # This model can generate images when properly configured
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={GOOGLE_API_KEY}"
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": image_prompt
                    }]
                }],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        import base64
                        b64_data = part["inlineData"].get("data", "")
                        mime_type = part["inlineData"].get("mimeType", "image/png")
                        if b64_data:
                            img_bytes = base64.b64decode(b64_data)
                            ext = "png" if "png" in mime_type else "jpg"
                            img_path = f"temp/images/{uuid.uuid4()}.{ext}"
                            with open(img_path, 'wb') as f:
                                f.write(img_bytes)
                            print(f"   ✅ Google Gemini image saved: {img_path}")
                            return img_path
            print(f"   ⚠️ No image in Google Gemini response")
        else:
            error_msg = response.text[:300] if response.text else "Unknown error"
            print(f"   ⚠️ Google Gemini error ({response.status_code}): {error_msg}")
    except Exception as e:
        print(f"   ⚠️ Google image generation failed: {e}")
    
    return None

def generate_image_openrouter(prompt: str, scene_type: str = "explanation") -> str:
    """Generate an AI image using OpenRouter API - creates topic-specific educational visuals"""
    try:
        # Build a detailed prompt based on scene type
        if scene_type == "flowchart":
            image_prompt = f"Create a clean flowchart diagram showing: {prompt}. Use boxes connected with arrows, minimal text, modern flat design, dark background (#121218), white and colored elements."
        elif scene_type == "process":
            image_prompt = f"Create a step-by-step process diagram for: {prompt}. Show numbered steps with icons, connected flow, modern minimalist style, dark background."
        elif scene_type == "comparison":
            image_prompt = f"Create a side-by-side comparison infographic for: {prompt}. Two columns, clean icons, versus layout, dark theme with accent colors."
        elif scene_type == "diagram":
            image_prompt = f"Create an educational diagram illustrating: {prompt}. Labeled parts, clean lines, modern flat design, dark background with bright accents."
        elif scene_type == "formula":
            image_prompt = f"Create a visual representation of the concept: {prompt}. Show the mathematical or logical relationship, clean modern design, dark background."
        elif scene_type == "array":
            image_prompt = f"Create a visualization of data/array showing: {prompt}. Boxes with numbers, arrows showing movement, algorithm visualization style, dark background."
        elif scene_type == "timeline":
            image_prompt = f"Create a timeline infographic for: {prompt}. Horizontal or vertical timeline with events marked, clean modern design, dark theme."
        elif scene_type == "definition":
            image_prompt = f"Create an iconic illustration representing: {prompt}. Single clear symbol or icon, modern flat design, centered, dark background with colored accent."
        elif scene_type == "example":
            image_prompt = f"Create a real-world illustration showing: {prompt}. Relatable everyday scene, cartoon style, bright colors on dark background."
        
        else:
            image_prompt = f"Create a clean educational illustration for: {prompt}. Modern flat design, simple shapes, dark background (#121218), vibrant accent colors."
        
        print(f"   🎨 Generating AI image [{scene_type}]: {prompt[:40]}...")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Aetheris Video Generator"
            },
            json={
                "model": "google/gemini-2.5-flash-image",
                "messages": [
                    {
                        "role": "user",
                        "content": image_prompt
                    }
                ],
                "max_tokens": 2000  # Limit tokens to stay within credit budget
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            # Extract image from message content
            if data.get("choices") and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                images = message.get("images", [])
                
                if images and len(images) > 0:
                    image_data = images[0]
                    image_url = None
                    
                    # Handle nested image_url structure
                    if isinstance(image_data, dict):
                        if image_data.get("image_url"):
                            image_url = image_data["image_url"].get("url")
                        elif image_data.get("url"):
                            image_url = image_data.get("url")
                    
                    if image_url:
                        # Check if it's base64 data URL
                        if image_url.startswith("data:image"):
                            import base64
                            # Extract base64 data after the comma
                            header, b64_data = image_url.split(",", 1)
                            img_bytes = base64.b64decode(b64_data)
                            img_path = f"backend/temp/images/{uuid.uuid4()}.png"
                            with open(img_path, 'wb') as f:
                                f.write(img_bytes)
                            print(f"   ✅ AI image saved: {img_path}")
                            return img_path
                        else:
                            # Regular URL - download it
                            img_response = requests.get(image_url, timeout=30)
                            if img_response.status_code == 200:
                                img_path = f"temp/images/{uuid.uuid4()}.png"
                                with open(img_path, 'wb') as f:
                                    f.write(img_response.content)
                                print(f"   ✅ AI image saved: {img_path}")
                                return img_path
                else:
                    print(f"   ⚠️ No images in response")
        else:
            error_msg = response.text[:200] if response.text else "Unknown error"
            print(f"   ⚠️ OpenRouter image error ({response.status_code}): {error_msg}")
    except Exception as e:
        print(f"   ⚠️ Image generation failed: {e}")
    
    return None

def generate_dalle_image(prompt: str, size: str = "1024x1024") -> str:
    """Generate an image using OpenAI DALL-E 3 (fallback)"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        print(f"   🎨 Trying DALL-E: {prompt[:50]}...")
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "dall-e-3",
                "prompt": f"Educational illustration, clean modern style, minimalist: {prompt}",
                "n": 1,
                "size": size,
                "quality": "standard"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            image_url = data["data"][0]["url"]
            
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                img_path = f"temp/images/{uuid.uuid4()}.png"
                with open(img_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"   ✅ DALL-E image saved")
                return img_path
        else:
            print(f"   ⚠️ DALL-E error: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ DALL-E failed: {e}")
    
    return None

def fetch_stock_image(query: str, width: int = 600, height: int = 400, scene_type: str = "explanation") -> str:
    """Fetch TOPIC-SPECIFIC stock image from multiple free sources"""
    
    # Clean and enhance query based on scene type
    search_query = query.lower().strip()
    
    # Add visual keywords based on scene type to get better results
    scene_keywords = {
        "flowchart": "diagram process chart",
        "process": "steps workflow",
        "comparison": "versus comparison",
        "diagram": "illustration infographic",
        "formula": "mathematics science",
        "array": "data numbers technology",
        "timeline": "history timeline events",
        "definition": "concept icon symbol",
        "example": "real world practical",
        "explanation": "educational learning"
    }
    extra_keywords = scene_keywords.get(scene_type, "")
    enhanced_query = f"{search_query} {extra_keywords}".strip()
    
    # Source 1: Pexels API (FREE with topic search!)
    try:
        print(f"   📷 Trying Pexels: {enhanced_query[:40]}...")
        # Pexels offers free API with 200 req/hour
        pexels_url = f"https://api.pexels.com/v1/search?query={enhanced_query}&per_page=5&orientation=portrait"
        headers = {
            "Authorization": "9c5qmFOsJKd32VCCi4cYODBnRdJUqjSCW8pYdVlMxYeMaG9aUOKMXiKc"  # Free API key
        }
        response = requests.get(pexels_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            if photos:
                # Pick random from top results for variety
                photo = random.choice(photos[:min(3, len(photos))])
                img_url = photo.get("src", {}).get("large", photo.get("src", {}).get("medium"))
                if img_url:
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200 and len(img_response.content) > 5000:
                        img_path = f"temp/images/{uuid.uuid4()}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        print(f"   ✅ Pexels image saved (topic: {search_query[:20]})")
                        return img_path
    except Exception as e:
        print(f"   ⚠️ Pexels failed: {e}")
    
    # Source 2: Pixabay API (FREE with topic search!)
    try:
        print(f"   📷 Trying Pixabay: {enhanced_query[:40]}...")
        # Pixabay free API
        pixabay_key = "50788160-c48f6f81f44f9ac66ac6b5e70"  # Free API key
        pixabay_url = f"https://pixabay.com/api/?key={pixabay_key}&q={enhanced_query.replace(' ', '+')}&image_type=illustration&per_page=5"
        response = requests.get(pixabay_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", [])
            if hits:
                hit = random.choice(hits[:min(3, len(hits))])
                img_url = hit.get("webformatURL") or hit.get("largeImageURL")
                if img_url:
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200 and len(img_response.content) > 3000:
                        img_path = f"temp/images/{uuid.uuid4()}.jpg"
                        with open(img_path, 'wb') as f:
                            f_write = img_response.content
                            f.write(f_write)
                        print(f"   ✅ Pixabay image saved (topic: {search_query[:20]})")
                        return img_path
    except Exception as e:
        print(f"   ⚠️ Pixabay failed: {e}")
    
    # Source 3: Unsplash (topic-based, may have rate limits)
    try:
        print(f"   📷 Trying Unsplash: {enhanced_query[:40]}...")
        clean_query = enhanced_query.replace(" ", ",").lower()[:50]
        image_url = f"https://source.unsplash.com/{width}x{height}/?{clean_query}"
        
        response = requests.get(image_url, timeout=10, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:
            img_path = f"temp/images/{uuid.uuid4()}.jpg"
            with open(img_path, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Unsplash image saved (topic: {search_query[:20]})")
            return img_path
    except Exception as e:
        print(f"   ⚠️ Unsplash failed: {e}")
    
    # Source 4: Placeholder with topic text (always works)
    try:
        print(f"   📷 Using placeholder...")
        # Create placeholder with the actual topic name
        topic_short = query[:15].replace(" ", "+")
        response = requests.get(f"https://placehold.co/{width}x{height}/1a1a2e/ffffff?text={topic_short}", timeout=10)
        if response.status_code == 200 and len(response.content) > 500:
            img_path = f"temp/images/{uuid.uuid4()}.png"
            with open(img_path, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Placeholder image saved")
            return img_path
    except Exception as e:
        print(f"   ⚠️ Placeholder failed: {e}")
    
    return None

def fetch_image_for_topic(query: str, width: int = 600, height: int = 400, use_ai: bool = True, scene_type: str = "explanation") -> str:
    """Fetch image following the SHORTS FRAMING BLUEPRINT
    
    Priority order:
    1. Stable Diffusion via Hugging Face (FREE!)
    2. Google Gemini (fallback)
    3. OpenRouter (fallback)  
    4. Stock images (final fallback)
    """
    
    # 1. Try Stable Diffusion via Hugging Face (FREE - best for clean icons)
    if use_ai:
        sd_path = generate_image_stable_diffusion(query, scene_type)
        if sd_path:
            return sd_path
    
    # 2. Try Google Gemini (fallback)
    if use_ai and GOOGLE_API_KEY:
        google_path = generate_image_google(query, scene_type)
        if google_path:
            return google_path
    
    # 3. Try OpenRouter image generation (fallback)
    if use_ai:
        ai_path = generate_image_openrouter(query, scene_type)
        if ai_path:
            return ai_path
    
    # 4. Try DALL-E if OpenAI key available
    if OPENAI_API_KEY:
        dalle_path = generate_dalle_image(query, "1024x1024")
        if dalle_path:
            return dalle_path
    
    # 5. Fallback to stock images
    stock_path = fetch_stock_image(query, width, height, scene_type)
    if stock_path:
        return stock_path
    
    print(f"   ⚠️ No image found for: {query[:30]}")
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
# � YOUTUBE SHORTS FRAMING BLUEPRINT
# ══════════════════════════════════════════════════════════════════════════════
# Format: 1080 × 1920 (vertical)
# Background: Dark (#0E0E0E)
# Rule: ONE frame = ONE idea
#
# UNIVERSAL FRAME LAYOUT:
# ┌──────────────────────────┐
# │        HEADLINE          │  ← Big, bold (top 20%)
# │──────────────────────────│
# │                          │
# │     VISUAL ZONE          │  ← Icons / shapes / arrows (middle 60%)
# │                          │
# │──────────────────────────│
# │     SUPPORT TEXT         │  ← Small, optional (bottom 20%)
# └──────────────────────────┘

# Scene Type → Frame Style mapping (UNIVERSAL - works for any topic)
FRAME_STYLES = {
    # Basic frames (per blueprint)
    "title": "title_frame",         # 🎬 HOOK - Grab attention in 1 second
    "intro": "title_frame",         # 🎬 Same as title
    "outro": "title_frame",         # 🎬 End frame
    "inputs": "inputs_frame",       # ⬇️ INPUTS - What goes in (ingredients)
    "process": "process_frame",     # ⚙️ PROCESS - Core explanation (HOW)
    "output": "output_frame",       # ⬆️ OUTPUT - Result / what comes out
    "summary": "summary_frame",     # ✅ SUMMARY - Memory lock (checkmarks)
    
    # Content frames
    "definition": "definition_frame",  # 📖 Define a term
    "explanation": "explanation_frame", # 💡 Explain a concept
    "example": "example_frame",        # 📌 Show an example
    "fact": "fact_frame",              # 🔢 Big number/statistic
    
    # Structured content
    "list": "list_frame",           # 📋 Bullet points
    "comparison": "comparison_frame", # ⚖️ Side-by-side comparison
    "timeline": "timeline_frame",   # 📅 Timeline events
    "formula": "formula_frame",     # 🧮 Math formula
    "diagram": "diagram_frame",     # 📊 Simple diagram
    "flowchart": "flowchart_frame", # 🔀 Flowchart with nodes
    "array": "array_frame",         # 📊 Array visualization
    "table": "table_frame",         # 📋 Data table
    
    # Legacy/fallback
    "step": "process_frame",
    "result": "output_frame",
}

# Accent colors for variety (per blueprint - ONE per frame)
ACCENT_COLORS = [
    (0, 255, 136),    # Neon Green
    (255, 107, 107),  # Coral Red
    (78, 205, 196),   # Teal
    (255, 230, 109),  # Yellow
    (199, 125, 255),  # Purple
    (255, 159, 67),   # Orange
]

# Dark background color (per blueprint: #0E0E0E)
DARK_BG = (14, 14, 14)  # #0E0E0E - true dark as per blueprint

# Frame layout zones (percentage of 1920 height)
ZONE_HEADLINE = 0.15      # Top 15% for headline
ZONE_VISUAL_START = 0.18  # Visual zone starts at 18%
ZONE_VISUAL_END = 0.70    # Visual zone ends at 70%
ZONE_SUPPORT = 0.75       # Support text starts at 75%

# Helper functions for text handling
def infer_theme_from_topic(topic: str) -> str:
    """Guess the best visual theme based on the topic keywords."""
    t = topic.lower()
    if any(k in t for k in ["war", "empire", "history", "century", "king", "revolution", "civics", "law", "government"]):
        return "retro"
    if any(k in t for k in ["math", "formula", "logic", "proof", "number", "geometry"]):
        return "maths"
    if any(k in t for k in ["bio", "science", "physics", "chem", "atom", "dna", "space", "planet", "bmi", "health", "body", "muscle", "calorie", "disease", "medical", "anatomy", "biology"]):
        return "science"
    if any(k in t for k in ["digital", "ai", "robo", "future", "cyber"]):
        return "neon"
    return None

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
# Mount /videos for video playback and download
app.mount("/videos", StaticFiles(directory="output"), name="videos")

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


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 THEME MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/themes")
async def get_themes():
    """Get all available themes with preview colors."""
    themes = list_available_themes()
    return {
        "themes": themes,
        "current": get_current_theme().get('name', 'algorithm_explainer'),
        "message": "Available themes for video generation"
    }

class ThemeRequest(BaseModel):
    theme_name: str

@app.post("/themes/select")
async def select_theme(request: ThemeRequest):
    """Select a theme for video generation."""
    theme_name = request.theme_name
    if theme_name in DEFAULT_THEMES:
        set_current_theme(theme_name)
        theme = get_current_theme()
        return {
            "success": True,
            "theme": theme_name,
            "colors": theme.get('colors', {}),
            "message": f"Theme '{theme_name}' selected successfully"
        }
    else:
        available = list(DEFAULT_THEMES.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Theme '{theme_name}' not found. Available: {available}"
        )

@app.get("/themes/current")
async def get_current_theme_info():
    """Get the current theme details."""
    theme = get_current_theme()
    return {
        "name": theme.get('name', 'algorithm_explainer'),
        "colors": theme.get('colors', {}),
        "style": theme.get('style', {}),
        "description": theme.get('description', 'Default theme')
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 📸 USER IMAGE UPLOAD SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
from fastapi import UploadFile, File, Form
from user_image_system import (
    ImageSession, 
    analyze_all_images, 
    generate_script_with_user_images,
    render_user_image_array
)

# Store active sessions
image_sessions: Dict[str, ImageSession] = {}

@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload 4-8 images for video generation.
    AI will analyze each image and use them in the video.
    
    Returns session_id to use with /generate-video-with-images
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 images")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    
    # Create new session
    session = ImageSession()
    
    print(f"\n📸 New image session: {session.session_id}")
    print(f"   Uploading {len(files)} images...")
    
    for file in files:
        content = await file.read()
        session.add_image(content, file.filename)
    
    # Analyze all images with AI
    await analyze_all_images(session)
    
    # Store session
    image_sessions[session.session_id] = session
    
    # Return session info
    return {
        "session_id": session.session_id,
        "images": [
            {
                "index": img["index"],
                "filename": img["filename"],
                "analysis": img.get("analysis", {})
            }
            for img in session.images
        ],
        "message": f"Uploaded {len(files)} images. Use session_id with /generate-video-with-images"
    }


class ImageVideoRequest(BaseModel):
    session_id: str
    topic: str
    video_type: Optional[str] = "short"

@app.post("/generate-video-with-images")
async def generate_video_with_images(request: ImageVideoRequest):
    """
    Generate a video using previously uploaded images.
    
    The AI will:
    1. Use your images as visual examples
    2. Generate script referencing YOUR images
    3. Show your images being sorted/moved/compared
    """
    session = image_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload images first.")
    
    if len(session.images) < 2:
        raise HTTPException(status_code=400, detail="Session has less than 2 images")
    
    print(f"\n🎬 Generating video with user images")
    print(f"   Session: {request.session_id}")
    print(f"   Topic: {request.topic}")
    print(f"   Images: {len(session.images)}")
    
    # Generate script using user's images
    script = await generate_script_with_user_images(request.topic, session)
    
    if not script:
        raise HTTPException(status_code=500, detail="Failed to generate script")
    
    # ═══════════════════════════════════════════════════════════════
    # 🎬 VIDEO RENDERING PIPELINE
    # ═══════════════════════════════════════════════════════════════
    
    video_id = str(uuid.uuid4())
    clips = []
    total_duration = 0
    total_duration_motion_canvas = 0
    
    # Video settings
    voice = "en-US-ChristopherNeural"
    width, height = (1080, 1920) if request.video_type == "short" else (1920, 1080)
    
    print(f"\n🚀 Rendering {len(script['scenes'])} scenes...")
    
    try:
        for i, scene in enumerate(script['scenes']):
            print(f"   🎬 Scene {i+1}: {scene.get('scene_type', 'unknown')}")
            
            # 1. Generate Audio
            audio_path = f"temp/audio/{video_id}_{i}.mp3"
            narration_text = scene.get('narration', '')
            
            try:
                communicate = edge_tts.Communicate(narration_text, voice)
                await communicate.save(audio_path)
            except Exception as e:
                print(f"   ⚠️ Edge TTS failed: {e}")
                tts = gTTS(text=narration_text, lang='en')
                tts.save(audio_path)
            
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 0.5  # Add small pause
            scene['duration'] = duration  # Update scene duration
            
            # 2. Render Visuals
            scene_type = scene.get('scene_type', 'explanation').lower()
            
            # CHECK: Does this scene use user images?
            user_indices = scene.get('user_images_shown', [])
            
            if user_indices:
                print(f"     📸 Using {len(user_indices)} user images")
                
                # Use User Image Renderer
                visual_clip = render_user_image_array(
                    session=session,
                    image_indices=user_indices,
                    width=width,
                    height=height,
                    duration=duration,
                    highlight_index=scene.get('highlight_index', -1),
                    show_values=True,
                    show_swap_animation="swap" in narration_text.lower()
                )
                
                # Add headline overlay
                headline = scene.get('headline', '')
                if headline:
                    txt_clip = TextClip(
                        text=headline,
                        font_size=80,
                        color='white',
                        font="/System/Library/Fonts/Helvetica.ttc",
                        stroke_color='black',
                        stroke_width=2
                    ).with_duration(duration)
                    txt_clip = txt_clip.with_position(('center', 150))
                    visual_clip = CompositeVideoClip([visual_clip, txt_clip])
                    
            else:
                # Use Standard Themed Renderer for other scenes
                print(f"     🎨 Using themed renderer")
                
                # Ensure theme is loaded
                if not get_current_theme():
                    set_current_theme('algorithm_explainer')
                
                # Add required fields for themed renderer
                scene['narration'] = narration_text
                
                visual_clip = render_themed_frame(
                    scene=scene,
                    width=width,
                    height=height,
                    topic=request.topic
                )
            
            # Combine with audio
            final_clip = visual_clip.with_audio(audio_clip)
            clips.append(final_clip)
            total_duration += duration
            
        # 3. Concatenate and Write Video
        print(f"\n💾 Saving video ({total_duration:.1f}s)...")
        final_video = concatenate_videoclips(clips)
        
        output_filename = f"{video_id}.mp4"
        output_path = f"output/{output_filename}"
        
        # Write video file
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger="bar",
            preset="ultrafast"
        )
        
        print(f"✅ Video generated: {output_path}")
        
        return {
            "video_url": f"http://localhost:8000/output/{output_filename}",
            "title": script.get('title', request.topic),
            "duration": total_duration
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get info about an image upload session."""
    session = image_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "num_images": len(session.images),
        "images": [
            {
                "index": img["index"],
                "filename": img["filename"],
                "analysis": img.get("analysis", {})
            }
            for img in session.images
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MANIM HIGH-QUALITY VIDEO GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

class ManimVideoRequest(BaseModel):
    prompt: str
    theme: Optional[str] = "algorithm"
    video_type: Optional[str] = "short"

@app.post("/generate-video-hq")
async def generate_video_high_quality(request: ManimVideoRequest):
    """
    Generate HIGH QUALITY video using Manim + MoviePy + Edge-TTS.
    
    This is the GOLD combo for educational YouTube content:
    - Manim: Professional mathematical/DSA animations/scenes/science/GENERAL scenes/classroom visuals
    - MoviePy: Merge voice + scenes
    - Edge-TTS: Natural voice synthesis
    
    Perfect for: DSA, Algorithms, Math, CS concepts/science topics/boards students info like sst gk hindi english explation.
    2-3 minutes of content with detailed explanations and smooth animations.
    40-50 seconds for short explainer videos.
    """
    if not MANIM_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Manim not available. Install with: pip install manim"
        )
    
    # Semantic Theme Choice: Change the theme automatically if the user topic matches a domain
    inferred = infer_theme_from_topic(request.prompt)
    if inferred and request.theme == 'algorithm':
        print(f"   💡 Topic matches '{inferred}' domain. Switching theme...")
        request.theme = inferred

    print(f"\n🎬 HIGH QUALITY VIDEO GENERATED (Manim - Deep Analysis Mode)")
    print(f"   Topic: {request.prompt}")
    print(f"   Theme: {request.theme}")
    
    try:
        from modern_pipeline import generate_modern_premium_script
        from manim_engine import THEMES, DEFAULT_THEME, ManimVideoGenerator
        
        # This function now performs: Research -> Structural Planning -> One-by-One Frame Design
        script = await generate_modern_premium_script(request.prompt)
        
        # Inject theme-specific colors into the script if not present
        if 'bg_color' not in script:
            theme_obj = THEMES.get(request.theme, DEFAULT_THEME)
            script['bg_color'] = theme_obj.bg_color

        print(f"   ✅ Ultra-Detail Script generated: {len(script.get('scenes', []))} frames designed one-by-one.")
        
    except Exception as e:
        print(f"❌ Modern premium script generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deep analysis script generation failed: {e}")
    
    # Generate video with Manim using Parallel Depth Rendering
    try:
        generator = ManimVideoGenerator(theme_name=request.theme)
        # Use generate_from_script for parallel, high-quality rendering of each designed frame
        video_path = await generator.generate_from_script(script)
        
        # Get video URL
        video_filename = os.path.basename(video_path)
        video_url = f"{BASE_URL}/videos/{video_filename}"

        
        return {
            "video_url": video_url,
            "title": script.get('title', request.prompt),
            "script": script, # Return the full script for the frontend player
            "duration": sum(5 for _ in script.get('scenes', [])),  # Estimate
            "quality": "HIGH (Manim)",
            "scenes": len(script.get('scenes', [])),
            "theme": request.theme
        }
        
    except Exception as e:
        print(f"   ❌ Manim rendering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {e}")


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

    # Models to try (first paid, then free fallbacks)
    MODELS_TO_TRY = [
        "google/gemini-2.0-flash-001",      # Fast, cheap
        "mistralai/devstral-2512:free",     # Free fallback
        "nvidia/nemotron-3-nano-30b-a3b:free", # Free fallback
    ]

    payload = {
        "model": MODELS_TO_TRY[0],  # Start with primary
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
        script_data = None
        last_error = None
        
        # Try each model until one works
        for model_name in MODELS_TO_TRY:
            try:
                print(f"   🤖 Trying model: {model_name}")
                payload["model"] = model_name
                
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
                print(f"   ✅ Success with: {model_name}")
                break  # Success! Exit loop
                
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 402:
                    print(f"   ⚠️ {model_name}: Out of credits, trying next...")
                    continue
                else:
                    print(f"   ⚠️ {model_name}: HTTP {e.response.status_code}")
                    continue
            except Exception as e:
                last_error = e
                print(f"   ⚠️ {model_name}: {str(e)[:50]}")
                continue
        
        if script_data is None:
            raise HTTPException(status_code=500, detail=f"All models failed: {last_error}")
        
        try:
            
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
            

            # --- INTENT-BASED SCENE SELECTION PIPELINE ---
            try:
                from scene_policy import decide_scene_type
            except ImportError:
                def decide_scene_type(scene, topic=None, scene_id=None):
                    return scene.get('type', 'explanation')

            topic = script_data.get('title', request.prompt).lower().strip()
            if 'scenes' in script_data:
                for idx, scene in enumerate(script_data['scenes']):
                    scene_id = idx + 1
                    # 1. Semantic map override (CRITICAL)
                    override = get_semantic_scene_type(topic, scene_id)
                    if override:
                        scene['scene_type'] = override
                        continue
                    # 2. Intent-based dynamic selection
                    scene['scene_type'] = decide_scene_type(scene, topic=topic, scene_id=scene_id)
                    # 3. Fallback: never allow ai: 0/null/filler
                    if not scene['scene_type'] or scene['scene_type'] in [None, '', 'null', 0, 'ai:0', 'filler']:
                        scene['scene_type'] = 'concept_flow_scene'

            video_id = str(uuid.uuid4())
            clips = []
            processed_scenes = [] # For Motion Canvas
            audio_clips_list = [] # For Motion Canvas
            total_duration = 0
            
            # Voice options for more human-like sound
            # Male: en-US-GuyNeural, en-US-ChristopherNeural
            # Female: en-US-JennyNeural, en-US-AriaNeural
            voice = "en-US-ChristopherNeural"  # Natural male voice
            
            total_duration_motion_canvas = 0
            
            for i, scene in enumerate(script_data['scenes']):
                # 1. Generate Audio with Edge TTS (more human-like)
                audio_path = f"temp/audio/{video_id}_{i}.mp3"
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
                
                # ═══════════════════════════════════════════════════════════════
                # 🧠 SEMANTIC FRAMING: Auto-detect the best layout for content
                # ═══════════════════════════════════════════════════════════════
                scene_type = scene.get('scene_type', 'explanation').lower()
                headline = scene.get('headline', scene.get('narration', 'TOPIC')[:30].upper())
                
                if USE_SEMANTIC_FRAMING:
                    # Let the semantic classifier choose the best layout
                    semantic_layout = choose_layout(
                        text=narration_text,
                        headline=headline,
                        scene_data=scene
                    )
                    frame_style = semantic_layout  # Use semantic layout type
                    print(f"   🧠 SEMANTIC LAYOUT DETECTED: {semantic_layout.upper()}")
                else:
                    # Use original scene_type → frame_style mapping
                    frame_style = FRAME_STYLES.get(scene_type, 'concept_frame')
                
                # Get accent color from scene or pick random
                accent_name = scene.get('accent_color', 'green').lower()
                accent_map = {'green': 0, 'red': 1, 'teal': 2, 'yellow': 3, 'purple': 4, 'orange': 5}
                accent_color = ACCENT_COLORS[accent_map.get(accent_name, random.randint(0, 5))]
                
                visual_elements = scene.get('visual_elements', [])
                
                # ══════════════════════════════════════════════════════════════
                # 🎬 LOG: RENDERING SCENE
                # ══════════════════════════════════════════════════════════════
                print(f"\n🎬 RENDERING SCENE {i+1}/{len(script_data['scenes'])}")
                print(f"   📌 Scene Type: {scene_type.upper()}")
                print(f"   🎨 Frame Style: {frame_style.upper()}")
                print(f"   📝 Headline: {headline}")
                print(f"   🎨 Accent Color: {accent_name}")
                print(f"   ⏱️  Duration: {duration:.1f}s")
                print(f"   🗣️  Narration: \"{scene.get('narration', '')[:60]}...\"")
                print(f"   🔷 Visual Elements: {visual_elements}")

                # Store data for Motion Canvas
                processed_scenes.append({
                    **scene,
                    'duration': duration,
                    'scene_type': scene_type,
                    'headline': headline,
                    'narration': narration_text
                })
                audio_clips_list.append(audio_clip)

                if USE_MOTION_CANVAS:
                    total_duration_motion_canvas += duration
                    # No longer skipping standard rendering, so we get an MP4 AND a Motion Canvas preview

                # ═══════════════════════════════════════════════════════════════
                # 🎨 DARK BACKGROUND (base for all frames)
                # ═══════════════════════════════════════════════════════════════
                bg_clip = ColorClip(size=(width, height), color=DARK_BG, duration=duration)
                
                # ═══════════════════════════════════════════════════════════════
                # � THEMED RENDERER (Code-based, 100% reliable, user themes)
                # ═══════════════════════════════════════════════════════════════
                if USE_THEMED_RENDERER:
                    print(f"   🎨 Using THEMED RENDERER (scene_type={scene_type})")
                    
                    # Build scene with all necessary data
                    themed_scene = {
                        **scene,
                        'scene_type': scene_type,
                        'headline': headline,
                        'narration': narration_text,
                        'duration': duration,
                    }
                    
                    # Render with themed renderer (code-based, consistent theme)
                    scene_clip = render_themed_frame(themed_scene, width, height, request.prompt)
                    final_scene_clip = scene_clip.with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip other renderers
                
                # ═══════════════════════════════════════════════════════════════
                # �🎬 AI-ENHANCED RENDERER (Beautiful flowcharts & visuals)
                # ═══════════════════════════════════════════════════════════════
                elif USE_AI_RENDERER:
                    print(f"   🎬 Using AI RENDERER (scene_type={scene_type})")
                    
                    # Build scene with all necessary data
                    ai_scene = {
                        **scene,
                        'scene_type': scene_type,
                        'headline': headline,
                        'narration': narration_text,
                        'duration': duration,
                    }
                    
                    # Render with AI-enhanced renderer (flowcharts, equations, etc.)
                    scene_clip = render_ai_frame(ai_scene, width, height, request.prompt)
                    final_scene_clip = scene_clip.with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip other renderers
                
                # ═══════════════════════════════════════════════════════════════
                # ✨ CLEAN RENDERER (No external APIs, 100% reliable)
                # ═══════════════════════════════════════════════════════════════
                elif USE_CLEAN_RENDERER:
                    print(f"   ✨ Using CLEAN RENDERER (scene_type={scene_type})")
                    
                    # Build scene with all necessary data
                    clean_scene = {
                        **scene,
                        'scene_type': scene_type,
                        'headline': headline,
                        'narration': narration_text,
                        'duration': duration,
                    }
                    
                    # Render with clean renderer (emoji icons, shapes, no API calls)
                    scene_clip = render_clean_frame(clean_scene, width, height, request.prompt)
                    final_scene_clip = scene_clip.with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip other renderers
                
                # 🖼️ VISUAL RENDERER (Rich visuals with AI images, equations, etc.)
                # ═══════════════════════════════════════════════════════════════
                elif USE_VISUAL_RENDERER:
                    print(f"   🖼️ Using VISUAL RENDERER with AI images")
                    
                    # Build scene with all necessary data
                    visual_scene = {
                        **scene,
                        'scene_type': scene_type,
                        'headline': headline,
                        'narration': narration_text,
                        'duration': duration,
                    }
                    
                    # Render with visual renderer (includes AI image generation)
                    scene_clip = render_visual_frame(visual_scene, width, height, request.prompt)
                    final_scene_clip = scene_clip.with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip other renderers
                
                # ═══════════════════════════════════════════════════════════════
                # 🚀 SMART VIDEO ENGINE (Fallback)
                # ═══════════════════════════════════════════════════════════════
                elif USE_SMART_ENGINE:
                    print(f"   🚀 Using SMART VIDEO ENGINE")
                    
                    # Classify the meaning of this scene (pass scene_type from AI for better accuracy)
                    meaning, detected_frame_type = classify_meaning(narration_text, scene_type)
                    print(f"   📊 Detected: scene_type={scene_type} → meaning={meaning} → frame={detected_frame_type.value}")
                    
                    # Generate unique style for this video
                    video_style = VideoStyle.generate_for_topic(request.prompt)
                    
                    # Build scene data for modern renderer
                    smart_scene = {
                        **scene,
                        'frame_type': detected_frame_type.value,
                        'meaning': meaning,
                        'headline': headline,
                        'narration': narration_text,
                        'duration': duration,
                        'style': {
                            'palette': video_style.palette_name,
                            'colors': video_style.colors,
                            'font_style': video_style.font_style,
                            'box_style': video_style.box_style,
                        }
                    }
                    
                    # Render with modern renderer
                    scene_clip = render_frame(smart_scene, width, height)
                    final_scene_clip = scene_clip.with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip old rendering
                
                # ═══════════════════════════════════════════════════════════════
                # 🧠 SEMANTIC FRAME RENDERING (Old System - Fallback)
                # ═══════════════════════════════════════════════════════════════
                elif USE_SEMANTIC_FRAMING and frame_style in RENDERERS:
                    print(f"   🧠 Using SEMANTIC RENDERER: {frame_style}")
                    
                    # Use semantic renderer for this layout type
                    layers = render_semantic_frame(
                        layout_type=frame_style,
                        scene=scene,
                        width=width,
                        height=height,
                        duration=duration,
                        fetch_image_fn=fetch_image_for_topic
                    )
                    
                    # Compose the final scene clip
                    final_scene_clip = CompositeVideoClip([
                        bg_clip,
                        *layers
                    ], size=(width, height)).with_audio(audio_clip)
                    
                    clips.append(final_scene_clip)
                    total_duration += duration
                    continue  # Skip the old rendering logic
                
                # ═══════════════════════════════════════════════════════════════
                # 🎨 LEGACY RENDERING (Fallback if semantic not available)
                # ═══════════════════════════════════════════════════════════════
                layers = []
                
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

                # === TITLE FRAME (HOOK) ===
                # Purpose: Grab attention in 1 second
                # Layout: Big text centered + single icon
                if frame_style == "title_frame":
                    print(f"   → Rendering TITLE FRAME (Hook)")
                    
                    # Generate icon using Stable Diffusion
                    print(f"   🖼️ Generating title icon for: {headline}...")
                    img_path = fetch_image_for_topic(headline, width=int(width * 0.5), height=int(width * 0.5), scene_type="title")
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.4), int(width * 0.4), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.25)))
                            layers.append(img_clip)
                    elif icon:
                        # Fallback to emoji icon
                        icon_clip = TextClip(text=icon, font_size=120, color='white', font=font_path).with_duration(duration)
                        icon_clip = icon_clip.with_position(('center', int(height * 0.30)))
                        layers.append(icon_clip)
                    
                    # Main headline (HEADLINE ZONE - top area)
                    title_clip = TextClip(text=headline, font_size=90, color='white', font=font_path).with_duration(duration)
                    title_clip = title_clip.with_position(('center', int(height * 0.52)))
                    
                    # Accent underline
                    underline_w = min(len(headline) * 50, width - 150)
                    underline = ColorClip(size=(underline_w, 8), color=accent_color, duration=duration)
                    underline = underline.with_position(('center', int(height * 0.60)))
                    
                    layers.extend([title_clip, underline])
                    
                    # Support text (optional subtitle)
                    if narration and len(narration) < 50:
                        support_clip = TextClip(
                            text=narration, font_size=32, color='#888888', font=font_path
                        ).with_duration(duration)
                        support_clip = support_clip.with_position(('center', int(height * 0.68)))
                        layers.append(support_clip)

                # === INPUTS FRAME ===
                # Purpose: Show ingredients / requirements (what goes in)
                # Layout: 3 icons evenly spaced in VISUAL ZONE
                elif frame_style == "inputs_frame":
                    print(f"   → Rendering INPUTS FRAME")
                    
                    # Headline at top
                    head_clip = TextClip(text="INPUTS", font_size=70, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.10)))
                    layers.append(head_clip)
                    
                    # Get input items
                    input_items = scene.get('input_items', scene.get('visual_elements', []))
                    if not input_items and narration:
                        # Extract from narration
                        input_items = [narration[:20]]
                    
                    # Generate icons for each input (max 3)
                    num_inputs = min(len(input_items), 3) if input_items else 1
                    icon_size = int(width * 0.25)
                    spacing = width // (num_inputs + 1)
                    
                    for idx, item in enumerate(input_items[:3]):
                        x_pos = spacing * (idx + 1) - icon_size // 2
                        
                        # Try to generate AI icon for this input
                        print(f"   🖼️ Generating input icon {idx+1}: {str(item)[:20]}...")
                        img_path = fetch_image_for_topic(str(item), width=icon_size, height=icon_size, scene_type="inputs")
                        
                        if img_path:
                            img_clip = create_image_clip(img_path, icon_size, icon_size, duration)
                            if img_clip:
                                img_clip = img_clip.with_position((x_pos, int(height * 0.30)))
                                layers.append(img_clip)
                        else:
                            # Fallback: colored circle with text
                            circle = ColorClip(size=(icon_size, icon_size), color=accent_color, duration=duration)
                            circle = circle.with_position((x_pos, int(height * 0.30)))
                            layers.append(circle)
                        
                        # Label below icon
                        label = TextClip(
                            text=truncate_text(str(item), 12), font_size=28, color='white', font=font_path
                        ).with_duration(duration)
                        label = label.with_position((x_pos + icon_size // 4, int(height * 0.55)))
                        layers.append(label)
                    
                    # Support text
                    support_clip = TextClip(
                        text=truncate_text(narration, 40), font_size=30, color='#888888', font=font_path
                    ).with_duration(duration)
                    support_clip = support_clip.with_position(('center', int(height * 0.75)))
                    layers.append(support_clip)

                # === OUTPUT FRAME ===
                # Purpose: Show result clearly (what comes out)
                # Layout: Arrows moving outward, bright accent
                elif frame_style == "output_frame":
                    print(f"   → Rendering OUTPUT FRAME")
                    
                    # Headline at top
                    head_clip = TextClip(text="OUTPUT", font_size=70, color='white', font=font_path).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.10)))
                    layers.append(head_clip)
                    
                    # Get output items
                    output_items = scene.get('output_items', scene.get('visual_elements', [headline]))
                    
                    # Generate icon for the output
                    output_query = " ".join(str(o) for o in output_items[:2]) if output_items else headline
                    print(f"   🖼️ Generating output icon: {output_query[:30]}...")
                    img_path = fetch_image_for_topic(output_query, width=int(width * 0.5), height=int(width * 0.5), scene_type="output")
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.45), int(width * 0.45), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.28)))
                            layers.append(img_clip)
                    
                    # Output labels with outward arrows
                    if output_items:
                        y_pos = int(height * 0.58)
                        for idx, item in enumerate(output_items[:2]):
                            arrow_text = f"→ {truncate_text(str(item), 20)}"
                            item_clip = TextClip(
                                text=arrow_text, font_size=40, color=accent_color, font=font_path
                            ).with_duration(duration)
                            item_clip = item_clip.with_position(('center', y_pos + idx * 60))
                            layers.append(item_clip)
                    
                    # Support text
                    support_clip = TextClip(
                        text=truncate_text(narration, 50), font_size=28, color='#888888', font=font_path
                    ).with_duration(duration)
                    support_clip = support_clip.with_position(('center', int(height * 0.78)))
                    layers.append(support_clip)

                # === DEFINITION FRAME ===
                elif frame_style == "definition_frame":
                    print(f"   → Rendering DEFINITION FRAME")
                    
                    # Headline (the term)
                    term_clip = TextClip(text=headline, font_size=70, color=accent_color, font=font_path).with_duration(duration)
                    term_clip = term_clip.with_position(('center', int(height * 0.08)))
                    layers.append(term_clip)
                    
                    # Fetch AI-generated image for the term
                    print(f"   🖼️ Generating definition image for: {headline}...")
                    img_path = fetch_image_for_topic(headline, width=int(width * 0.8), height=int(height * 0.30), scene_type="definition")
                    
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
                    
                    # Generate AI image for the explanation
                    image_query = f"{headline} {narration[:30]}"
                    print(f"   🖼️ Generating explanation image for: {image_query[:40]}...")
                    img_path = fetch_image_for_topic(image_query, width=int(width * 0.85), height=int(height * 0.35), scene_type="explanation")
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.85), int(height * 0.35), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.18)))
                            layers.append(img_clip)
                    
                    # Narration text at bottom (no colored box fallback)
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

                # === FLOWCHART FRAME (AI-generated flowchart image) ===
                elif frame_style == "flowchart_frame":
                    print(f"   → Rendering FLOWCHART FRAME")
                    
                    # Get flowchart data for the prompt
                    flow_nodes = scene.get('flow_nodes', [])
                    steps_desc = " → ".join([str(n.get('text', f'Step {i}'))[:20] for i, n in enumerate(flow_nodes[:5])]) if flow_nodes else ""
                    if not steps_desc and steps:
                        steps_desc = " → ".join([str(s)[:20] for s in steps[:5]])
                    
                    # Headline at top
                    head_clip = TextClip(
                        text=truncate_text(headline, 20), 
                        font_size=50, color='white', font=font_path
                    ).with_duration(duration)
                    head_clip = head_clip.with_position(('center', int(height * 0.06)))
                    layers.append(head_clip)
                    
                    # Generate AI flowchart image
                    flowchart_query = f"{headline}: {steps_desc}" if steps_desc else headline
                    print(f"   🖼️ Generating flowchart for: {flowchart_query[:50]}...")
                    img_path = fetch_image_for_topic(flowchart_query, width=int(width * 0.9), height=int(height * 0.55), scene_type="flowchart")
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.9), int(height * 0.55), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.14)))
                            layers.append(img_clip)
                    
                    # Narration at bottom
                    narr_clip = TextClip(
                        text=truncate_text(narration, 80), font_size=32, color='#CCCCCC', font=font_path,
                        method='caption', size=(width - 100, None)
                    ).with_duration(duration)
                    narr_clip = narr_clip.with_position(('center', int(height * 0.75)))
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
                        y_elem = int(height * 0.55);
                        
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
                    
                    # Generate AI image for the example (real-world illustration)
                    image_query = f"{headline} {example_text or narration[:20]}"
                    print(f"   🖼️ Generating example image for: {image_query[:40]}...")
                    img_path = fetch_image_for_topic(image_query, width=int(width * 0.85), height=int(height * 0.35), scene_type="example")
                    
                    if img_path:
                        img_clip = create_image_clip(img_path, int(width * 0.85), int(height * 0.35), duration)
                        if img_clip:
                            img_clip = img_clip.with_position(('center', int(height * 0.22)))
                            layers.append(img_clip)
                    
                    # Narration below (no colored box fallback)
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

            final_video = None
            mc_url = None # Initialize variable
            if USE_MOTION_CANVAS:
                from moviepy import VideoFileClip, concatenate_audioclips
                log_header("🎨 STARTING MOTION CANVAS RENDER")
                
                # Generate Project
                current_theme = get_current_theme()
                project_dir = generate_motion_canvas_project(processed_scenes, current_theme, script_data['title'])
                
                # Render Video / Start Server
                # We moved to "Serve Mode" - render_motion_canvas_video was standardized to serving
                mc_url = serve_motion_canvas_project(project_dir)
                
                # We no longer generate a placeholder video here. 
                # Instead, we allow the pipeline to continue to the standard renderer
                # so the user gets a real video file to view/download while the 
                # Motion Canvas interactive preview is also available.
                print(f"\nℹ️  Motion Canvas Project launching at: {mc_url}")
                print(f"   👉 Project saved at: {project_dir}")
                
                # We leave final_video as None so it falls through to the standard renderer below
                final_video = None
                
            if final_video is None:
                # Concatenate all scenes (Standard Renderer Fallback)
                print("Using standard renderer fallback...")
                if clips:
                    final_video = concatenate_videoclips(clips, method="compose")
                else:
                    print("❌ Error: No clips generated for fallback. Creating error video.")
                    final_video = TextClip(text="Video Generation Failed\nNo frames rendered", font_size=50, color='red', size=(width, height), method='caption').with_duration(5)
            output_filename = f"{video_id}.mp4"
            output_path = f"output/{output_filename}"
            
            # Write video file
            print(f"\n📹 Encoding final video...")
            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            
            # ══════════════════════════════════════════════════════════════════
            # ✅ LOG: VIDEO GENERATION COMPLETE
            # ══════════════════════════════════════════════════════════════════
            log_header("✅ VIDEO GENERATION COMPLETE")
            print(f"🎬 Title: {script_data['title']}")
            print(f"⏱️  Total Duration: {final_video.duration if final_video else total_duration:.1f}s")
            print(f"📁 Output: {output_path}")
            print(f"🌐 URL: http://localhost:8000/output/{output_filename}")
            log_separator()
            
            return {
                "status": "success",
                "video_id": video_id,
                "title": script_data['title'],
                "duration": final_video.duration if final_video else total_duration,
                "video_url": f"{BASE_URL}/output/{output_filename}",
                "motion_canvas_url": mc_url
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

# Register script endpoints for review/edit workflow
register_script_endpoints(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
