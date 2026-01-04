"""
🎨 AI IMAGE RENDERER - OpenRouter Image Generation + Beautiful Flowcharts
==========================================================================
Uses OpenRouter API for AI-generated images
Creates stunning animated flowcharts, diagrams, and visual explanations
Includes term bubble explanations for technical vocabulary
"""

import os
import httpx
import random
import math
import hashlib
from typing import Dict, List, Tuple, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip, ImageClip
from PIL import Image
from io import BytesIO

# Import AI image generator
from image_generator import generate_image, get_image_prompt

# Import term bubble system for technical vocabulary
from term_bubbles import create_term_bubbles_overlay, find_terms_in_text, TECH_TERMS

# ═══════════════════════════════════════════════════════════════════════════════
# 🔑 API CONFIGURATION  
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from app_secrets import API_KEY
    OPENROUTER_API_KEY = API_KEY
except ImportError:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Image generation endpoint (using free image models via OpenRouter)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Image cache directory
IMAGE_CACHE_DIR = "backend/temp/images"
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 COLOR PALETTES
# ═══════════════════════════════════════════════════════════════════════════════

PALETTES = {
    "nature": {
        "bg": (10, 25, 20),
        "primary": (76, 217, 100),      # Bright green
        "secondary": (255, 204, 0),     # Sun yellow
        "accent": (90, 200, 250),       # Sky blue
        "highlight": (255, 120, 80),    # Coral
        "text": (255, 255, 255),
        "card": (25, 50, 40),
        "card2": (35, 70, 55),
        "gradient1": (40, 120, 80),
        "gradient2": (20, 60, 45),
    },
    "science": {
        "bg": (12, 18, 35),
        "primary": (0, 210, 255),       # Cyan
        "secondary": (255, 165, 0),     # Orange
        "accent": (200, 100, 255),      # Purple
        "highlight": (255, 80, 120),    # Pink
        "text": (255, 255, 255),
        "card": (20, 35, 60),
        "card2": (30, 50, 80),
        "gradient1": (40, 80, 140),
        "gradient2": (20, 40, 80),
    },
    "tech": {
        "bg": (8, 12, 20),
        "primary": (0, 255, 136),       # Matrix green
        "secondary": (64, 196, 255),    # Blue
        "accent": (255, 64, 129),       # Pink
        "highlight": (255, 200, 64),    # Gold
        "text": (255, 255, 255),
        "card": (18, 28, 42),
        "card2": (28, 42, 60),
        "gradient1": (30, 60, 100),
        "gradient2": (15, 30, 55),
    },
    "warm": {
        "bg": (25, 15, 12),
        "primary": (255, 150, 50),      # Orange
        "secondary": (255, 100, 100),   # Coral red
        "accent": (255, 220, 100),      # Gold
        "highlight": (255, 80, 150),    # Magenta
        "text": (255, 255, 255),
        "card": (45, 30, 25),
        "card2": (60, 40, 35),
        "gradient1": (100, 50, 40),
        "gradient2": (50, 25, 20),
    },
}


def get_palette(topic: str) -> Dict:
    """Choose palette based on topic keywords."""
    t = topic.lower()
    if any(w in t for w in ['plant', 'photo', 'bio', 'leaf', 'tree', 'nature', 'cell', 'oxygen', 'chloro']):
        return PALETTES['nature']
    elif any(w in t for w in ['chem', 'physics', 'atom', 'molecule', 'energy', 'formula', 'equation']):
        return PALETTES['science']
    elif any(w in t for w in ['code', 'algorithm', 'array', 'program', 'data', 'computer', 'leetcode']):
        return PALETTES['tech']
    return PALETTES['warm']


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_font():
    """Get available system font."""
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Helvetica-Bold",
        "Helvetica",
        "Arial"
    ]
    for f in fonts:
        if os.path.exists(f) or not f.startswith("/"):
            return f
    return "Helvetica"


def wrap_text(text: str, max_chars: int = 35) -> str:
    """Wrap text to multiple lines."""
    words = text.split()
    lines, current_line = [], []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 🖼️ AI IMAGE GENERATION (via OpenRouter)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_image_prompt(topic: str, scene_type: str, narration: str) -> str:
    """Generate an image prompt based on the scene context."""
    
    # Extract key concepts
    keywords = []
    text = f"{topic} {narration}".lower()
    
    concept_icons = {
        'sun': 'bright glowing sun with rays, warm yellow light',
        'sunlight': 'golden sunlight beams, warm rays',
        'water': 'clear blue water droplets, refreshing',
        'plant': 'green healthy plant with leaves, vibrant',
        'leaf': 'detailed green leaf with veins, botanical',
        'tree': 'majestic tree with green foliage',
        'oxygen': 'floating oxygen bubbles, O2 molecules, blue',
        'carbon': 'CO2 molecules, carbon dioxide visualization',
        'glucose': 'sugar molecule structure, sweet crystals',
        'photosynthesis': 'plant absorbing sunlight, green energy',
        'energy': 'glowing energy particles, power sparks',
        'chlorophyll': 'green chlorophyll pigment, cellular',
        'array': 'colorful data blocks in a row, programming',
        'algorithm': 'flowchart with nodes and arrows, logic',
        'code': 'clean code on dark screen, programming',
        'number': 'floating numbers, mathematical',
        'sum': 'addition symbols, math equation',
        'loop': 'circular arrows, iteration cycle',
    }
    
    for keyword, description in concept_icons.items():
        if keyword in text:
            keywords.append(description)
    
    if not keywords:
        keywords = ['educational illustration', 'clean modern design']
    
    base_prompt = f"Educational illustration, {', '.join(keywords[:3])}, "
    style = "modern flat design, vibrant colors, dark background, high quality, digital art, minimalist, professional"
    
    return f"{base_prompt}{style}"


async def fetch_ai_image(prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
    """
    Fetch an AI-generated image using OpenRouter.
    Returns path to saved image or None if failed.
    """
    # Create cache key
    cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
    cache_path = os.path.join(IMAGE_CACHE_DIR, f"ai_{cache_key}.png")
    
    # Check cache first
    if os.path.exists(cache_path):
        print(f"   📦 Using cached image: {cache_path}")
        return cache_path
    
    print(f"   🎨 Generating AI image: {prompt[:50]}...")
    
    # Try using Pollinations.ai (free, no API key needed)
    try:
        pollinations_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width={width}&height={height}&nologo=true"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(pollinations_url)
            
            if response.status_code == 200:
                # Check if it's actually an image
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    # Save to cache
                    with open(cache_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   ✅ AI image saved: {cache_path}")
                    return cache_path
                else:
                    print(f"   ⚠️ Not an image response: {content_type}")
    except Exception as e:
        print(f"   ⚠️ Pollinations error: {e}")
    
    return None


def fetch_ai_image_sync(prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
    """Synchronous wrapper for AI image generation."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(fetch_ai_image(prompt, width, height))
                )
                return future.result(timeout=35)
        else:
            return loop.run_until_complete(fetch_ai_image(prompt, width, height))
    except Exception as e:
        print(f"   ⚠️ Sync image fetch error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 ICON SYSTEM (Emoji + Shape fallback)
# ═══════════════════════════════════════════════════════════════════════════════

ICONS = {
    # Nature
    'sun': '☀️', 'sunlight': '☀️', 'light': '💡',
    'water': '💧', 'h2o': '💧', 'rain': '🌧️',
    'plant': '🌱', 'leaf': '🍃', 'tree': '🌳',
    'oxygen': '🫧', 'o2': '🫧', 'air': '💨',
    'carbon': '⚫', 'co2': '💨',
    'glucose': '🍬', 'sugar': '🍬', 'food': '🍽️',
    'energy': '⚡', 'power': '⚡',
    'chlorophyll': '🟢', 'green': '🟢',
    'photosynthesis': '🌿',
    
    # Process
    'arrow': '→', 'right': '→', 'next': '→',
    'down': '↓', 'up': '↑', 'left': '←',
    'check': '✓', 'done': '✅', 'complete': '✅',
    'cross': '❌', 'wrong': '❌',
    'question': '❓', 'think': '🤔',
    'brain': '🧠', 'idea': '💡',
    'start': '▶️', 'begin': '▶️',
    'end': '🏁', 'finish': '🏁',
    'input': '📥', 'output': '📤',
    'process': '⚙️', 'step': '📍',
    'loop': '🔄', 'repeat': '🔁',
    
    # Tech
    'code': '💻', 'program': '💻',
    'array': '📊', 'list': '📋',
    'number': '🔢', 'math': '🔢',
    'search': '🔍', 'find': '🔍',
    'target': '🎯', 'goal': '🎯',
    'key': '🔑', 'value': '📦',
    'pointer': '👆', 'index': '📍',
    
    # General
    'important': '⭐', 'star': '⭐',
    'warning': '⚠️', 'note': '📝',
    'time': '⏱️', 'clock': '🕐',
    'fast': '🚀', 'slow': '🐌',
}


def get_icon(text: str) -> str:
    """Get emoji icon for a concept."""
    text_lower = text.lower()
    for keyword, icon in ICONS.items():
        if keyword in text_lower:
            return icon
    return '📌'


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 FLOWCHART RENDERER (Beautiful animated flowcharts)
# ═══════════════════════════════════════════════════════════════════════════════

def render_flowchart(scene: Dict, width: int, height: int, duration: float, palette: Dict, topic: str = "") -> List:
    """
    Create a beautiful animated flowchart from the narration.
    Extracts steps from text and creates connected boxes with arrows.
    Also generates an AI process image for visual enhancement.
    """
    layers = []
    font = get_font()
    narration = scene.get('narration', scene.get('text', ''))
    headline = scene.get('headline', 'PROCESS')
    
    # Background with gradient effect
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Try to generate AI process image
    image_prompt = get_image_prompt('process', topic or headline, narration)
    image_path = generate_image(image_prompt, 'process')
    
    if image_path and os.path.exists(image_path):
        try:
            img_clip = ImageClip(image_path).with_duration(duration)
            img_w, img_h = img_clip.size
            
            # Small image in corner as decoration
            target_h = 180
            scale = target_h / img_h
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            img_clip = img_clip.resized((new_w, new_h))
            img_clip = img_clip.with_opacity(0.6)
            img_clip = img_clip.with_position((width - new_w - 30, 30))
            layers.append(img_clip)
            
            print(f"   🖼️ AI image added to flowchart frame")
        except Exception as e:
            print(f"   ⚠️ Failed to add flowchart image: {e}")
    
    # Add gradient overlay
    gradient = ColorClip(size=(width, height // 3), color=palette['gradient1'], duration=duration)
    gradient = gradient.with_opacity(0.15).with_position((0, 0))
    layers.append(gradient)
    
    # Title at top
    title = TextClip(
        text=headline,
        font_size=48,
        color='white',
        font=font,
        stroke_color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
        stroke_width=2
    ).with_duration(duration)
    title = title.with_position(('center', 40))
    layers.append(title)
    
    # Extract steps from narration
    steps = extract_steps(narration)
    
    if len(steps) < 2:
        # If no clear steps, create boxes from key phrases
        steps = extract_key_phrases(narration, max_phrases=4)
    
    # Limit to 5 steps max for clean display
    steps = steps[:5]
    
    # Calculate layout
    num_steps = len(steps)
    if num_steps <= 3:
        # Horizontal layout
        layout = "horizontal"
        box_width = min(280, (width - 150) // num_steps)
        box_height = 120
        start_x = (width - (box_width * num_steps + 60 * (num_steps - 1))) // 2
        start_y = height // 2 - box_height // 2
    else:
        # Grid layout (2 rows)
        layout = "grid"
        cols = (num_steps + 1) // 2
        box_width = min(250, (width - 100) // cols)
        box_height = 100
        start_x = (width - (box_width * cols + 50 * (cols - 1))) // 2
        start_y = height // 2 - box_height - 40
    
    # Create step boxes
    step_positions = []
    colors = [palette['primary'], palette['secondary'], palette['accent'], 
              palette['highlight'], palette['primary']]
    
    for i, step in enumerate(steps):
        if layout == "horizontal":
            x = start_x + i * (box_width + 60)
            y = start_y
        else:
            row = i // ((num_steps + 1) // 2)
            col = i % ((num_steps + 1) // 2)
            x = start_x + col * (box_width + 50)
            y = start_y + row * (box_height + 80)
        
        step_positions.append((x, y, box_width, box_height))
        color = colors[i % len(colors)]
        
        # Box glow effect
        glow = ColorClip(size=(box_width + 10, box_height + 10), color=color, duration=duration)
        glow = glow.with_opacity(0.3).with_position((x - 5, y - 5))
        layers.append(glow)
        
        # Main box
        box = ColorClip(size=(box_width, box_height), color=palette['card'], duration=duration)
        box = box.with_position((x, y))
        layers.append(box)
        
        # Top accent bar
        accent_bar = ColorClip(size=(box_width, 6), color=color, duration=duration)
        accent_bar = accent_bar.with_position((x, y))
        layers.append(accent_bar)
        
        # Step number circle
        num_size = 32
        num_bg = ColorClip(size=(num_size, num_size), color=color, duration=duration)
        num_bg = num_bg.with_position((x + box_width - num_size - 8, y + 12))
        layers.append(num_bg)
        
        num_text = TextClip(text=str(i + 1), font_size=18, color='white', font=font).with_duration(duration)
        num_text = num_text.with_position((x + box_width - num_size + 4, y + 18))
        layers.append(num_text)
        
        # Step icon
        icon = get_icon(step)
        icon_clip = TextClip(text=icon, font_size=28, font=font).with_duration(duration)
        icon_clip = icon_clip.with_position((x + 12, y + 20))
        layers.append(icon_clip)
        
        # Step text
        wrapped = wrap_text(step, max_chars=20)
        step_text = TextClip(
            text=wrapped,
            font_size=16,
            color='white',
            font=font
        ).with_duration(duration)
        step_text = step_text.with_position((x + 12, y + 55))
        layers.append(step_text)
    
    # Draw arrows between steps
    for i in range(len(step_positions) - 1):
        x1, y1, w1, h1 = step_positions[i]
        x2, y2, w2, h2 = step_positions[i + 1]
        
        if layout == "horizontal" or (i % ((num_steps + 1) // 2) != ((num_steps + 1) // 2) - 1):
            # Horizontal arrow
            arrow_x = x1 + w1 + 10
            arrow_y = y1 + h1 // 2 - 15
            arrow_text = "→"
        else:
            # Vertical arrow (end of row)
            arrow_x = x1 + w1 // 2 - 15
            arrow_y = y1 + h1 + 15
            arrow_text = "↓"
        
        arrow = TextClip(
            text=arrow_text,
            font_size=40,
            color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
            font=font
        ).with_duration(duration)
        arrow = arrow.with_position((arrow_x, arrow_y))
        layers.append(arrow)
    
    # Bottom narration hint
    hint = TextClip(
        text=wrap_text(narration[:80] + "..." if len(narration) > 80 else narration, 60),
        font_size=18,
        color='#aaaaaa',
        font=font
    ).with_duration(duration)
    hint = hint.with_position(('center', height - 80))
    layers.append(hint)
    
    return layers


def extract_steps(text: str) -> List[str]:
    """Extract process steps from narration text."""
    import re
    
    steps = []
    
    # Pattern 1: "First... Then... Finally..." 
    step_words = ['first', 'then', 'next', 'after', 'finally', 'lastly', 'second', 'third']
    
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if any(word in sentence.lower() for word in step_words):
            # Clean up the step
            step = sentence
            for word in step_words:
                step = re.sub(rf'\b{word}\b,?\s*', '', step, flags=re.IGNORECASE)
            if len(step) > 5:
                steps.append(step.strip()[:50])
    
    # Pattern 2: Numbered steps "1. ... 2. ..."
    if not steps:
        numbered = re.findall(r'\d+[.):]\s*([^.!?]+)', text)
        steps = [s.strip()[:50] for s in numbered if len(s.strip()) > 5]
    
    return steps


def extract_key_phrases(text: str, max_phrases: int = 4) -> List[str]:
    """Extract key phrases from text for flowchart boxes."""
    import re
    
    # Split by punctuation and conjunctions
    phrases = re.split(r'[.!?,;]|\band\b|\bthen\b', text)
    
    # Filter and clean
    cleaned = []
    for phrase in phrases:
        phrase = phrase.strip()
        if 10 < len(phrase) < 60:
            cleaned.append(phrase[:45])
    
    return cleaned[:max_phrases]


# ═══════════════════════════════════════════════════════════════════════════════
# 📐 EQUATION RENDERER (Beautiful math formulas)
# ═══════════════════════════════════════════════════════════════════════════════

def render_equation(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    Render a beautiful equation/formula visualization.
    """
    layers = []
    font = get_font()
    narration = scene.get('narration', scene.get('text', ''))
    headline = scene.get('headline', 'FORMULA')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Title
    title = TextClip(
        text=headline,
        font_size=44,
        color='white',
        font=font,
        stroke_color=f"#{palette['accent'][0]:02x}{palette['accent'][1]:02x}{palette['accent'][2]:02x}",
        stroke_width=2
    ).with_duration(duration)
    title = title.with_position(('center', 50))
    layers.append(title)
    
    # Extract equation parts from narration
    equation_parts = extract_equation_parts(narration)
    
    # Main equation display area
    eq_y = height // 2 - 50
    
    if equation_parts:
        # Create visual equation with boxes
        total_parts = len(equation_parts)
        part_width = min(150, (width - 200) // max(total_parts, 1))
        start_x = (width - (part_width * total_parts + 40 * (total_parts - 1))) // 2
        
        for i, (symbol, label) in enumerate(equation_parts):
            x = start_x + i * (part_width + 40)
            
            # Part box with glow
            color = [palette['primary'], palette['secondary'], palette['accent']][i % 3]
            
            glow = ColorClip(size=(part_width + 8, 90), color=color, duration=duration)
            glow = glow.with_opacity(0.4).with_position((x - 4, eq_y - 4))
            layers.append(glow)
            
            box = ColorClip(size=(part_width, 82), color=palette['card'], duration=duration)
            box = box.with_position((x, eq_y))
            layers.append(box)
            
            # Symbol/icon at top
            icon = get_icon(label) if label else symbol
            icon_text = TextClip(text=icon, font_size=36, font=font).with_duration(duration)
            icon_text = icon_text.with_position((x + part_width // 2 - 20, eq_y + 8))
            layers.append(icon_text)
            
            # Label below
            label_text = TextClip(
                text=label[:12] if label else symbol,
                font_size=16,
                color='white',
                font=font
            ).with_duration(duration)
            label_text = label_text.with_position((x + 10, eq_y + 52))
            layers.append(label_text)
            
            # Add operator between parts (except last)
            if i < total_parts - 1:
                op_x = x + part_width + 8
                # Determine operator
                if i == total_parts - 2:
                    operator = "="
                else:
                    operator = "+"
                
                op_text = TextClip(
                    text=operator,
                    font_size=40,
                    color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
                    font=font
                ).with_duration(duration)
                op_text = op_text.with_position((op_x, eq_y + 20))
                layers.append(op_text)
    
    # Explanation text at bottom
    explanation = TextClip(
        text=wrap_text(narration[:120], 55),
        font_size=20,
        color='#cccccc',
        font=font
    ).with_duration(duration)
    explanation = explanation.with_position(('center', height - 120))
    layers.append(explanation)
    
    return layers


def extract_equation_parts(text: str) -> List[Tuple[str, str]]:
    """Extract equation components from text."""
    import re
    
    parts = []
    text_lower = text.lower()
    
    # Common equation patterns
    patterns = {
        'sunlight': ('☀️', 'Sunlight'),
        'sun': ('☀️', 'Sun'),
        'light': ('💡', 'Light'),
        'water': ('💧', 'Water'),
        'h2o': ('💧', 'H₂O'),
        'co2': ('💨', 'CO₂'),
        'carbon dioxide': ('💨', 'CO₂'),
        'oxygen': ('🫧', 'O₂'),
        'o2': ('🫧', 'O₂'),
        'glucose': ('🍬', 'Glucose'),
        'sugar': ('🍬', 'Sugar'),
        'energy': ('⚡', 'Energy'),
        'food': ('🍽️', 'Food'),
        'chlorophyll': ('🟢', 'Chlorophyll'),
    }
    
    found = []
    for keyword, (icon, label) in patterns.items():
        if keyword in text_lower and label not in [p[1] for p in found]:
            found.append((icon, label))
    
    # If we found reactants and products, organize them
    if len(found) >= 2:
        return found[:5]  # Limit to 5 parts
    
    # Fallback: create generic parts
    return [('📥', 'Input'), ('⚙️', 'Process'), ('📤', 'Output')]


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 TITLE RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_title(scene: Dict, width: int, height: int, duration: float, palette: Dict, topic: str = "") -> List:
    """Render an eye-catching title screen with AI-generated image."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'TITLE')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Try to generate AI image for the title
    image_prompt = get_image_prompt('title', topic or headline, narration)
    image_path = generate_image(image_prompt, 'title')
    
    if image_path and os.path.exists(image_path):
        try:
            # Add AI-generated image as background
            img_clip = ImageClip(image_path).with_duration(duration)
            
            # Resize to fit (left side of screen)
            img_w, img_h = img_clip.size
            target_h = height - 100
            scale = target_h / img_h
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            img_clip = img_clip.resized((new_w, new_h))
            img_clip = img_clip.with_opacity(0.7)
            img_clip = img_clip.with_position((50, 50))
            layers.append(img_clip)
            
            print(f"   🖼️ AI image added to title frame")
        except Exception as e:
            print(f"   ⚠️ Failed to add image: {e}")
    
    # Accent glow behind title (right side)
    glow_width = min(width - 100, 500)
    glow = ColorClip(size=(glow_width, 150), color=palette['primary'], duration=duration)
    glow = glow.with_opacity(0.25).with_position((width - glow_width - 50, height // 2 - 80))
    layers.append(glow)
    
    # Main title (positioned to right side if image present)
    title = TextClip(
        text=headline,
        font_size=64,
        color='white',
        font=font,
        stroke_color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
        stroke_width=3
    ).with_duration(duration)
    title = title.with_position((width // 2, height // 2 - 50))
    layers.append(title)
    
    # Underline accent
    underline = ColorClip(size=(350, 5), color=palette['primary'], duration=duration)
    underline = underline.with_position((width // 2 + 50, height // 2 + 25))
    layers.append(underline)
    
    # Subtitle from narration
    if narration:
        subtitle = TextClip(
            text=wrap_text(narration[:70], 40),
            font_size=22,
            color='#cccccc',
            font=font
        ).with_duration(duration)
        subtitle = subtitle.with_position((width // 2, height // 2 + 55))
        layers.append(subtitle)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 📖 DEFINITION RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_definition(scene: Dict, width: int, height: int, duration: float, palette: Dict, topic: str = "") -> List:
    """Render a term + definition card with AI image."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'DEFINITION')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Try to generate AI image for the definition
    image_prompt = get_image_prompt('definition', topic or headline, narration)
    image_path = generate_image(image_prompt, 'definition')
    
    # Layout depends on whether we have an image
    has_image = image_path and os.path.exists(image_path)
    
    if has_image:
        # Layout: Image on left, text card on right
        try:
            img_clip = ImageClip(image_path).with_duration(duration)
            img_w, img_h = img_clip.size
            
            # Resize image to fit left side
            target_h = min(height - 150, 400)
            scale = target_h / img_h
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            img_clip = img_clip.resized((new_w, new_h))
            img_clip = img_clip.with_position((50, (height - new_h) // 2))
            layers.append(img_clip)
            
            print(f"   🖼️ AI image added to definition frame")
            
            # Position card to the right
            card_x = new_w + 100
            card_width = width - card_x - 50
        except Exception as e:
            print(f"   ⚠️ Failed to add image: {e}")
            has_image = False
            card_width = min(width - 120, 900)
            card_x = (width - card_width) // 2
    
    if not has_image:
        card_width = min(width - 120, 900)
        card_x = (width - card_width) // 2
    
    card_height = 280
    card_y = height // 2 - card_height // 2
    
    # Card glow
    glow = ColorClip(size=(card_width + 12, card_height + 12), color=palette['primary'], duration=duration)
    glow = glow.with_opacity(0.25).with_position((card_x - 6, card_y - 6))
    layers.append(glow)
    
    # Card background
    card = ColorClip(size=(card_width, card_height), color=palette['card'], duration=duration)
    card = card.with_position((card_x, card_y))
    layers.append(card)
    
    # Left accent bar
    accent = ColorClip(size=(8, card_height), color=palette['primary'], duration=duration)
    accent = accent.with_position((card_x, card_y))
    layers.append(accent)
    
    # Term (headline)
    term = TextClip(
        text=headline,
        font_size=38 if has_image else 42,
        color='white',
        font=font
    ).with_duration(duration)
    term = term.with_position((card_x + 30, card_y + 25))
    layers.append(term)
    
    # Separator line
    sep = ColorClip(size=(card_width - 60, 2), color=palette['primary'], duration=duration)
    sep = sep.with_opacity(0.5).with_position((card_x + 30, card_y + 80))
    layers.append(sep)
    
    # Definition text
    max_chars = 45 if has_image else 55
    definition = TextClip(
        text=wrap_text(narration, max_chars),
        font_size=20 if has_image else 24,
        color='#dddddd',
        font=font
    ).with_duration(duration)
    definition = definition.with_position((card_x + 30, card_y + 100))
    layers.append(definition)
    
    # Icon in top right (only if no image)
    if not has_image:
        icon = get_icon(headline + " " + narration)
        icon_clip = TextClip(text=icon, font_size=50, font=font).with_duration(duration)
        icon_clip = icon_clip.with_position((card_x + card_width - 80, card_y + 20))
        layers.append(icon_clip)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DIAGRAM RENDERER (Hierarchy/Tree structure)
# ═══════════════════════════════════════════════════════════════════════════════

def render_diagram(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """Render a hierarchical diagram."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'DIAGRAM')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Title
    title = TextClip(
        text=headline,
        font_size=40,
        color='white',
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 40))
    layers.append(title)
    
    # Extract components from narration
    components = extract_key_phrases(narration, max_phrases=4)
    if not components:
        components = ['Component 1', 'Component 2', 'Component 3']
    
    # Create hierarchical layout: one main box at top, children below
    main_box_w, main_box_h = 300, 80
    main_x = (width - main_box_w) // 2
    main_y = 120
    
    # Main box (topic)
    glow = ColorClip(size=(main_box_w + 8, main_box_h + 8), color=palette['primary'], duration=duration)
    glow = glow.with_opacity(0.4).with_position((main_x - 4, main_y - 4))
    layers.append(glow)
    
    main_box = ColorClip(size=(main_box_w, main_box_h), color=palette['card'], duration=duration)
    main_box = main_box.with_position((main_x, main_y))
    layers.append(main_box)
    
    # Top border
    border = ColorClip(size=(main_box_w, 5), color=palette['primary'], duration=duration)
    border = border.with_position((main_x, main_y))
    layers.append(border)
    
    main_text = TextClip(
        text=headline[:25],
        font_size=24,
        color='white',
        font=font
    ).with_duration(duration)
    main_text = main_text.with_position((main_x + 20, main_y + 28))
    layers.append(main_text)
    
    # Arrow down from main
    arrow_down = TextClip(text="↓", font_size=40, color='white', font=font).with_duration(duration)
    arrow_down = arrow_down.with_position((width // 2 - 15, main_y + main_box_h + 10))
    layers.append(arrow_down)
    
    # Child boxes
    num_children = min(len(components), 4)
    child_w = min(200, (width - 100) // num_children - 20)
    child_h = 100
    child_y = main_y + main_box_h + 80
    
    total_children_width = num_children * child_w + (num_children - 1) * 30
    start_x = (width - total_children_width) // 2
    
    colors = [palette['secondary'], palette['accent'], palette['highlight'], palette['primary']]
    
    for i, comp in enumerate(components[:num_children]):
        x = start_x + i * (child_w + 30)
        color = colors[i % len(colors)]
        
        # Child glow
        c_glow = ColorClip(size=(child_w + 6, child_h + 6), color=color, duration=duration)
        c_glow = c_glow.with_opacity(0.3).with_position((x - 3, child_y - 3))
        layers.append(c_glow)
        
        # Child box
        c_box = ColorClip(size=(child_w, child_h), color=palette['card2'], duration=duration)
        c_box = c_box.with_position((x, child_y))
        layers.append(c_box)
        
        # Top accent
        c_accent = ColorClip(size=(child_w, 4), color=color, duration=duration)
        c_accent = c_accent.with_position((x, child_y))
        layers.append(c_accent)
        
        # Icon
        icon = get_icon(comp)
        icon_clip = TextClip(text=icon, font_size=28, font=font).with_duration(duration)
        icon_clip = icon_clip.with_position((x + 10, child_y + 12))
        layers.append(icon_clip)
        
        # Text
        c_text = TextClip(
            text=wrap_text(comp[:30], 18),
            font_size=14,
            color='white',
            font=font
        ).with_duration(duration)
        c_text = c_text.with_position((x + 10, child_y + 50))
        layers.append(c_text)
    
    # Explanation at bottom
    explanation = TextClip(
        text=wrap_text(narration[:100], 60),
        font_size=18,
        color='#aaaaaa',
        font=font
    ).with_duration(duration)
    explanation = explanation.with_position(('center', height - 80))
    layers.append(explanation)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# ⚖️ COMPARISON RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_comparison(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """Render a side-by-side comparison."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'COMPARISON')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Title
    title = TextClip(
        text=headline,
        font_size=40,
        color='white',
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 40))
    layers.append(title)
    
    # Two comparison boxes
    box_width = (width - 150) // 2
    box_height = 300
    left_x = 50
    right_x = width - box_width - 50
    box_y = height // 2 - box_height // 2
    
    # Left box (Option A)
    left_glow = ColorClip(size=(box_width + 8, box_height + 8), color=palette['primary'], duration=duration)
    left_glow = left_glow.with_opacity(0.3).with_position((left_x - 4, box_y - 4))
    layers.append(left_glow)
    
    left_box = ColorClip(size=(box_width, box_height), color=palette['card'], duration=duration)
    left_box = left_box.with_position((left_x, box_y))
    layers.append(left_box)
    
    left_accent = ColorClip(size=(box_width, 6), color=palette['primary'], duration=duration)
    left_accent = left_accent.with_position((left_x, box_y))
    layers.append(left_accent)
    
    left_title = TextClip(text="Option A", font_size=28, color='white', font=font).with_duration(duration)
    left_title = left_title.with_position((left_x + 20, box_y + 20))
    layers.append(left_title)
    
    # Right box (Option B)
    right_glow = ColorClip(size=(box_width + 8, box_height + 8), color=palette['secondary'], duration=duration)
    right_glow = right_glow.with_opacity(0.3).with_position((right_x - 4, box_y - 4))
    layers.append(right_glow)
    
    right_box = ColorClip(size=(box_width, box_height), color=palette['card'], duration=duration)
    right_box = right_box.with_position((right_x, box_y))
    layers.append(right_box)
    
    right_accent = ColorClip(size=(box_width, 6), color=palette['secondary'], duration=duration)
    right_accent = right_accent.with_position((right_x, box_y))
    layers.append(right_accent)
    
    right_title = TextClip(text="Option B", font_size=28, color='white', font=font).with_duration(duration)
    right_title = right_title.with_position((right_x + 20, box_y + 20))
    layers.append(right_title)
    
    # VS in middle
    vs_text = TextClip(text="VS", font_size=50, color='white', font=font).with_duration(duration)
    vs_text = vs_text.with_position(('center', height // 2 - 30))
    layers.append(vs_text)
    
    # Content in boxes (extract from narration)
    parts = narration.split('.')[:2]
    
    if len(parts) >= 1:
        left_content = TextClip(
            text=wrap_text(parts[0][:100], 22),
            font_size=18,
            color='#dddddd',
            font=font
        ).with_duration(duration)
        left_content = left_content.with_position((left_x + 20, box_y + 70))
        layers.append(left_content)
    
    if len(parts) >= 2:
        right_content = TextClip(
            text=wrap_text(parts[1][:100], 22),
            font_size=18,
            color='#dddddd',
            font=font
        ).with_duration(duration)
        right_content = right_content.with_position((right_x + 20, box_y + 70))
        layers.append(right_content)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 FACT/STATS RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_fact(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """Render a big fact or statistic."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'FACT')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Central glow
    glow = ColorClip(size=(400, 200), color=palette['primary'], duration=duration)
    glow = glow.with_opacity(0.2).with_position(('center', height // 2 - 80))
    layers.append(glow)
    
    # Extract a number or key stat from narration
    import re
    numbers = re.findall(r'\d+%?', narration)
    stat = numbers[0] if numbers else headline
    
    # Big stat display
    stat_text = TextClip(
        text=stat,
        font_size=120,
        color='white',
        font=font,
        stroke_color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
        stroke_width=3
    ).with_duration(duration)
    stat_text = stat_text.with_position(('center', height // 2 - 80))
    layers.append(stat_text)
    
    # Label below
    label = TextClip(
        text=headline,
        font_size=36,
        color=f"#{palette['primary'][0]:02x}{palette['primary'][1]:02x}{palette['primary'][2]:02x}",
        font=font
    ).with_duration(duration)
    label = label.with_position(('center', height // 2 + 60))
    layers.append(label)
    
    # Description
    desc = TextClip(
        text=wrap_text(narration[:100], 50),
        font_size=20,
        color='#aaaaaa',
        font=font
    ).with_duration(duration)
    desc = desc.with_position(('center', height // 2 + 120))
    layers.append(desc)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# ✅ SUMMARY RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_summary(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """Render a summary with checkpoints."""
    layers = []
    font = get_font()
    headline = scene.get('headline', 'KEY TAKEAWAYS')
    narration = scene.get('narration', '')
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    # Title with check icon
    title = TextClip(
        text=f"✅ {headline}",
        font_size=44,
        color='white',
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 50))
    layers.append(title)
    
    # Extract key points from narration
    points = extract_key_phrases(narration, max_phrases=4)
    if not points:
        points = [narration[:60]]
    
    # Create checklist
    start_y = 150
    card_width = min(width - 100, 800)
    card_x = (width - card_width) // 2
    
    for i, point in enumerate(points):
        y = start_y + i * 80
        
        # Point background
        point_bg = ColorClip(size=(card_width, 65), color=palette['card'], duration=duration)
        point_bg = point_bg.with_position((card_x, y))
        layers.append(point_bg)
        
        # Left accent
        color = [palette['primary'], palette['secondary'], palette['accent']][i % 3]
        accent = ColorClip(size=(5, 65), color=color, duration=duration)
        accent = accent.with_position((card_x, y))
        layers.append(accent)
        
        # Check icon
        check = TextClip(text="✓", font_size=30, color='#00ff88', font=font).with_duration(duration)
        check = check.with_position((card_x + 20, y + 15))
        layers.append(check)
        
        # Point text
        point_text = TextClip(
            text=point[:55],
            font_size=22,
            color='white',
            font=font
        ).with_duration(duration)
        point_text = point_text.with_position((card_x + 60, y + 18))
        layers.append(point_text)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 RENDERER REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

RENDERERS = {
    'title': render_title,
    'title_intro': render_title,
    'hook': render_title,
    'definition': render_definition,
    'explanation': render_definition,
    'equation': render_equation,
    'formula': render_equation,
    'process': render_flowchart,
    'process_flow': render_flowchart,
    'flowchart': render_flowchart,
    'array': render_flowchart,
    'comparison': render_comparison,
    'split_compare': render_comparison,
    'diagram': render_diagram,
    'hierarchy': render_diagram,
    'fact': render_fact,
    'stats_number': render_fact,
    'example': render_flowchart,
    'summary': render_summary,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def render_ai_frame(scene: Dict, width: int, height: int, topic: str = "") -> CompositeVideoClip:
    """
    Main entry point - render a scene with AI-enhanced visuals, images, and term bubbles.
    """
    scene_type = scene.get('scene_type', 'definition').lower()
    frame_type = scene.get('frame_type', scene_type).lower()
    duration = scene.get('duration', 5.0)
    narration = scene.get('narration', scene.get('text', ''))
    
    palette = get_palette(topic)
    renderer = RENDERERS.get(frame_type, RENDERERS.get(scene_type, render_definition))
    
    print(f"   🎨 AI Renderer: {frame_type} → {renderer.__name__}")
    
    try:
        # Pass topic to renderer for AI image generation
        import inspect
        sig = inspect.signature(renderer)
        if 'topic' in sig.parameters:
            layers = renderer(scene, width, height, duration, palette, topic=topic)
        else:
            layers = renderer(scene, width, height, duration, palette)
        
        # ═══════════════════════════════════════════════════════════════════
        # 💬 ADD TERM BUBBLES for technical vocabulary
        # ═══════════════════════════════════════════════════════════════════
        # Check for technical terms in narration and add bubble explanations
        terms_found = find_terms_in_text(narration)
        if terms_found:
            term_bubbles = create_term_bubbles_overlay(narration, width, height, duration)
            layers.extend(term_bubbles)
            print(f"   💬 Added term bubbles: {[t[0] for t in terms_found]}")
        
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
    except Exception as e:
        print(f"   ⚠️ Render error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to definition
        layers = render_definition(scene, width, height, duration, palette)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
