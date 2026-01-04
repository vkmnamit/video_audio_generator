"""
🎨 VISUAL RENDERERS - Rich Educational Video Frames
=====================================================
Creates beautiful, educational frames with:
- AI-generated images (Pollinations.ai - FREE!)
- Proper equations with symbols
- Flowcharts with icons
- Dynamic visuals matching narration
"""

import os
import re
import math
import random
import requests
from typing import Dict, List, Tuple, Optional
from urllib.parse import quote
from moviepy import TextClip, ColorClip, CompositeVideoClip, ImageClip
from PIL import Image
from io import BytesIO


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 COLOR PALETTES - Beautiful, varied themes
# ═══════════════════════════════════════════════════════════════════════════════

PALETTES = {
    "nature": {  # For biology, plants, photosynthesis
        "bg": (15, 35, 25),
        "primary": (76, 187, 23),  # Leaf green
        "secondary": (255, 193, 7),  # Sun yellow
        "accent": (33, 150, 243),  # Sky blue
        "text": (255, 255, 255),
        "card": (25, 50, 35),
    },
    "science": {  # For chemistry, physics
        "bg": (10, 15, 30),
        "primary": (0, 188, 212),  # Cyan
        "secondary": (255, 152, 0),  # Orange
        "accent": (156, 39, 176),  # Purple
        "text": (255, 255, 255),
        "card": (20, 30, 50),
    },
    "tech": {  # For CS, algorithms
        "bg": (12, 12, 20),
        "primary": (0, 230, 118),  # Matrix green
        "secondary": (41, 182, 246),  # Blue
        "accent": (255, 64, 129),  # Pink
        "text": (255, 255, 255),
        "card": (25, 25, 40),
    },
    "warm": {  # For history, stories
        "bg": (30, 20, 15),
        "primary": (255, 138, 101),  # Coral
        "secondary": (255, 213, 79),  # Gold
        "accent": (129, 199, 132),  # Mint
        "text": (255, 255, 255),
        "card": (45, 30, 25),
    },
}


def get_palette_for_topic(topic: str) -> Dict:
    """Choose color palette based on topic."""
    topic_lower = topic.lower()
    
    if any(w in topic_lower for w in ['plant', 'photo', 'bio', 'cell', 'nature', 'tree', 'leaf', 'animal']):
        return PALETTES['nature']
    elif any(w in topic_lower for w in ['chem', 'physics', 'atom', 'molecule', 'reaction', 'energy']):
        return PALETTES['science']
    elif any(w in topic_lower for w in ['code', 'algorithm', 'computer', 'program', 'data', 'sort', 'array']):
        return PALETTES['tech']
    elif any(w in topic_lower for w in ['history', 'story', 'civilization', 'war', 'empire', 'culture']):
        return PALETTES['warm']
    else:
        return random.choice(list(PALETTES.values()))


# ═══════════════════════════════════════════════════════════════════════════════
# 🖼️ AI IMAGE GENERATION - Pollinations.ai (FREE!)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, width: int = 512, height: int = 512, style: str = "icon") -> Optional[str]:
    """
    Generate an image using Pollinations.ai (FREE, no API key!)
    
    Args:
        prompt: What to generate
        width: Image width
        height: Image height
        style: "icon" for simple icons, "scene" for detailed scenes
    
    Returns:
        Path to saved image or None
    """
    try:
        # Style the prompt for better results
        if style == "icon":
            full_prompt = f"Simple flat icon of {prompt}, minimal design, solid dark background, vibrant colors, vector art style, no text, centered"
        elif style == "diagram":
            full_prompt = f"Educational diagram of {prompt}, clean scientific illustration, labeled parts, dark background, bright colors"
        else:
            full_prompt = f"{prompt}, educational illustration, clear and simple, vibrant colors, dark background"
        
        # Pollinations.ai URL
        encoded_prompt = quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        print(f"   🖼️ Generating image: {prompt[:30]}...")
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Save to temp file
            img = Image.open(BytesIO(response.content))
            
            # Ensure directory exists
            os.makedirs("backend/temp/images", exist_ok=True)
            
            # Save with unique name
            filename = f"backend/temp/images/gen_{hash(prompt) % 100000}.png"
            img.save(filename)
            print(f"   ✅ Image saved: {filename}")
            return filename
        else:
            print(f"   ⚠️ Image generation failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Image error: {e}")
        return None


def extract_visual_keywords(text: str) -> List[str]:
    """Extract keywords that could be visualized as images."""
    
    # Common visualizable concepts
    visual_words = {
        # Nature
        'sun': 'bright yellow sun with rays',
        'sunlight': 'golden sunlight beams',
        'water': 'blue water droplets',
        'leaf': 'green leaf with veins',
        'plant': 'green plant growing',
        'tree': 'green tree',
        'oxygen': 'O2 molecule blue bubbles',
        'carbon dioxide': 'CO2 molecule gray',
        'glucose': 'glucose sugar molecule',
        'chlorophyll': 'green chlorophyll in leaf cell',
        'chloroplast': 'green chloroplast organelle',
        
        # Science
        'atom': 'colorful atom with electrons',
        'molecule': 'molecular structure 3D',
        'energy': 'bright energy burst',
        'light': 'bright light rays',
        'heat': 'red orange heat waves',
        'electricity': 'blue lightning bolt',
        
        # Tech
        'computer': 'modern computer icon',
        'data': 'digital data flow',
        'code': 'programming code screen',
        'network': 'connected network nodes',
        
        # General
        'brain': 'human brain illustration',
        'heart': 'anatomical heart',
        'earth': 'planet earth from space',
        'arrow': 'direction arrow',
    }
    
    found = []
    text_lower = text.lower()
    
    for keyword, prompt in visual_words.items():
        if keyword in text_lower:
            found.append((keyword, prompt))
    
    return found


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_font():
    """Get available font."""
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "Helvetica", "Arial"
    ]
    for f in fonts:
        if os.path.exists(f):
            return f
    return "Helvetica"


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def wrap_text(text: str, max_chars: int = 35) -> str:
    """Wrap text into multiple lines."""
    words = text.split()
    lines = []
    current = []
    length = 0
    
    for word in words:
        if length + len(word) + 1 <= max_chars:
            current.append(word)
            length += len(word) + 1
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
            length = len(word)
    
    if current:
        lines.append(' '.join(current))
    
    return '\n'.join(lines)


def create_image_clip(path: str, width: int, height: int, duration: float) -> Optional[ImageClip]:
    """Create an ImageClip from file path."""
    try:
        if path and os.path.exists(path):
            clip = ImageClip(path)
            # Resize maintaining aspect ratio
            clip = clip.resized(height=height) if clip.h > clip.w else clip.resized(width=width)
            return clip.with_duration(duration)
    except Exception as e:
        print(f"   ⚠️ Image clip error: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 FRAME RENDERERS - Each scene type gets unique visual treatment
# ═══════════════════════════════════════════════════════════════════════════════

def render_title_with_image(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    🎬 TITLE FRAME - Big title with AI-generated background icon
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'TITLE')
    narration = scene.get('narration', '')
    
    # Generate icon for the topic
    keywords = extract_visual_keywords(headline + ' ' + narration)
    if keywords:
        img_path = generate_image(keywords[0][1], 400, 400, "icon")
        if img_path:
            img_clip = create_image_clip(img_path, 350, 350, duration)
            if img_clip:
                img_clip = img_clip.with_position(('center', int(height * 0.25)))
                layers.append(img_clip)
    
    # Title text
    title_clip = TextClip(
        text=headline.upper(),
        font_size=72,
        color=rgb_to_hex(palette['text']),
        font=font,
        stroke_color=rgb_to_hex(palette['primary']),
        stroke_width=2
    ).with_duration(duration)
    title_clip = title_clip.with_position(('center', int(height * 0.55)))
    layers.append(title_clip)
    
    # Accent line
    line = ColorClip(size=(300, 6), color=palette['primary'], duration=duration)
    line = line.with_position(('center', int(height * 0.65)))
    layers.append(line)
    
    # Narrator bubble at bottom
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_equation(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    🧪 EQUATION FRAME - Chemical/Math equations with icons
    
    Example: 6CO₂ + 6H₂O + Light → C₆H₁₂O₆ + 6O₂
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'EQUATION')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=48,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 80))
    layers.append(title)
    
    # Check if this is photosynthesis
    if 'photosynth' in narration.lower() or 'co2' in narration.lower() or 'carbon dioxide' in narration.lower():
        # Photosynthesis equation with icons
        y_pos = height // 2 - 100
        
        # Reactants side
        # CO2 icon
        co2_path = generate_image("CO2 carbon dioxide molecule gray cloud", 120, 120, "icon")
        if co2_path:
            co2_clip = create_image_clip(co2_path, 100, 100, duration)
            if co2_clip:
                co2_clip = co2_clip.with_position((80, y_pos))
                layers.append(co2_clip)
        
        co2_text = TextClip(text="6CO₂", font_size=28, color='white', font=font).with_duration(duration)
        co2_text = co2_text.with_position((90, y_pos + 110))
        layers.append(co2_text)
        
        # Plus sign
        plus1 = TextClip(text="+", font_size=50, color=rgb_to_hex(palette['accent']), font=font).with_duration(duration)
        plus1 = plus1.with_position((200, y_pos + 30))
        layers.append(plus1)
        
        # H2O icon
        h2o_path = generate_image("water droplet blue H2O", 120, 120, "icon")
        if h2o_path:
            h2o_clip = create_image_clip(h2o_path, 100, 100, duration)
            if h2o_clip:
                h2o_clip = h2o_clip.with_position((250, y_pos))
                layers.append(h2o_clip)
        
        h2o_text = TextClip(text="6H₂O", font_size=28, color='white', font=font).with_duration(duration)
        h2o_text = h2o_text.with_position((260, y_pos + 110))
        layers.append(h2o_text)
        
        # Plus sign
        plus2 = TextClip(text="+", font_size=50, color=rgb_to_hex(palette['accent']), font=font).with_duration(duration)
        plus2 = plus2.with_position((370, y_pos + 30))
        layers.append(plus2)
        
        # Sun/Light icon
        sun_path = generate_image("bright sun sunlight energy yellow", 120, 120, "icon")
        if sun_path:
            sun_clip = create_image_clip(sun_path, 100, 100, duration)
            if sun_clip:
                sun_clip = sun_clip.with_position((420, y_pos))
                layers.append(sun_clip)
        
        light_text = TextClip(text="Light", font_size=28, color=rgb_to_hex(palette['secondary']), font=font).with_duration(duration)
        light_text = light_text.with_position((435, y_pos + 110))
        layers.append(light_text)
        
        # Arrow
        arrow = TextClip(text="→", font_size=80, color=rgb_to_hex(palette['primary']), font=font).with_duration(duration)
        arrow = arrow.with_position(('center', y_pos + 150))
        layers.append(arrow)
        
        # Products side
        y_prod = y_pos + 220
        
        # Glucose icon
        glucose_path = generate_image("glucose sugar molecule hexagon", 120, 120, "icon")
        if glucose_path:
            glu_clip = create_image_clip(glucose_path, 100, 100, duration)
            if glu_clip:
                glu_clip = glu_clip.with_position((200, y_prod))
                layers.append(glu_clip)
        
        glu_text = TextClip(text="C₆H₁₂O₆", font_size=28, color='white', font=font).with_duration(duration)
        glu_text = glu_text.with_position((200, y_prod + 110))
        layers.append(glu_text)
        
        glu_label = TextClip(text="(Glucose)", font_size=20, color=rgb_to_hex(palette['secondary']), font=font).with_duration(duration)
        glu_label = glu_label.with_position((205, y_prod + 140))
        layers.append(glu_label)
        
        # Plus
        plus3 = TextClip(text="+", font_size=50, color=rgb_to_hex(palette['accent']), font=font).with_duration(duration)
        plus3 = plus3.with_position((350, y_prod + 30))
        layers.append(plus3)
        
        # Oxygen icon
        o2_path = generate_image("oxygen O2 molecule blue bubbles", 120, 120, "icon")
        if o2_path:
            o2_clip = create_image_clip(o2_path, 100, 100, duration)
            if o2_clip:
                o2_clip = o2_clip.with_position((420, y_prod))
                layers.append(o2_clip)
        
        o2_text = TextClip(text="6O₂", font_size=28, color='white', font=font).with_duration(duration)
        o2_text = o2_text.with_position((445, y_prod + 110))
        layers.append(o2_text)
        
        o2_label = TextClip(text="(Oxygen)", font_size=20, color=rgb_to_hex(palette['secondary']), font=font).with_duration(duration)
        o2_label = o2_label.with_position((430, y_prod + 140))
        layers.append(o2_label)
    
    else:
        # Generic equation display
        equation_text = scene.get('equation', scene.get('formula_text', 'A + B → C'))
        eq_clip = TextClip(
            text=equation_text,
            font_size=56,
            color='white',
            font=font
        ).with_duration(duration)
        eq_clip = eq_clip.with_position(('center', height // 2))
        layers.append(eq_clip)
    
    # Narrator bubble
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_process_with_icons(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    🔄 PROCESS FRAME - Flowchart with AI-generated icons
    
    [Icon1] → [Icon2] → [Icon3] → [Icon4]
      Sun      Leaf     Glucose   Oxygen
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'PROCESS')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=48,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 60))
    layers.append(title)
    
    # Get process steps
    steps = scene.get('steps', scene.get('flow_nodes', []))
    if not steps:
        # Extract from narration
        keywords = extract_visual_keywords(narration)
        steps = [k[0] for k in keywords[:4]] if keywords else ['Input', 'Process', 'Output']
    
    # Render process steps with icons
    num_steps = min(len(steps), 4)
    step_width = (width - 100) // max(num_steps, 1)
    y_pos = height // 2 - 80
    
    for i, step in enumerate(steps[:4]):
        x_pos = 50 + i * step_width + step_width // 2 - 60
        
        # Try to generate icon for this step
        step_text = step.get('text', step) if isinstance(step, dict) else str(step)
        keywords = extract_visual_keywords(step_text)
        
        if keywords:
            img_path = generate_image(keywords[0][1], 120, 120, "icon")
            if img_path:
                img_clip = create_image_clip(img_path, 100, 100, duration)
                if img_clip:
                    img_clip = img_clip.with_position((x_pos, y_pos))
                    layers.append(img_clip)
        else:
            # Fallback: colored box
            box = ColorClip(size=(100, 100), color=palette['card'], duration=duration)
            box = box.with_position((x_pos, y_pos))
            layers.append(box)
        
        # Step label
        label = TextClip(
            text=step_text[:15],
            font_size=24,
            color='white',
            font=font
        ).with_duration(duration)
        label = label.with_position((x_pos, y_pos + 115))
        layers.append(label)
        
        # Arrow to next step
        if i < num_steps - 1:
            arrow = TextClip(
                text="→",
                font_size=50,
                color=rgb_to_hex(palette['secondary']),
                font=font
            ).with_duration(duration)
            arrow = arrow.with_position((x_pos + 110, y_pos + 30))
            layers.append(arrow)
    
    # Narrator bubble
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_definition_with_image(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    📖 DEFINITION FRAME - Term with icon and explanation
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'DEFINITION')
    narration = scene.get('narration', '')
    
    # Generate icon for the concept
    keywords = extract_visual_keywords(headline + ' ' + narration)
    if keywords:
        img_path = generate_image(keywords[0][1], 250, 250, "icon")
        if img_path:
            img_clip = create_image_clip(img_path, 200, 200, duration)
            if img_clip:
                img_clip = img_clip.with_position(('center', 120))
                layers.append(img_clip)
    
    # Term
    term = TextClip(
        text=headline.upper(),
        font_size=56,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    term = term.with_position(('center', 350))
    layers.append(term)
    
    # Definition line
    line = ColorClip(size=(400, 4), color=palette['secondary'], duration=duration)
    line = line.with_position(('center', 420))
    layers.append(line)
    
    # Definition text (first sentence of narration)
    if narration:
        first_sentence = narration.split('.')[0] + '.'
        wrapped = wrap_text(first_sentence, 40)
        def_clip = TextClip(
            text=wrapped,
            font_size=32,
            color='white',
            font=font,
            method='caption',
            size=(width - 80, None)
        ).with_duration(duration)
        def_clip = def_clip.with_position(('center', 460))
        layers.append(def_clip)
    
    # Full narration bubble
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_comparison_with_images(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    ⚖️ COMPARISON FRAME - Two things side by side with icons
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'COMPARISON')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=44,
        color=rgb_to_hex(palette['text']),
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 60))
    layers.append(title)
    
    # Divider
    divider = ColorClip(size=(4, height - 300), color=palette['accent'], duration=duration)
    divider = divider.with_position((width // 2 - 2, 150))
    layers.append(divider)
    
    # VS badge
    vs = TextClip(text="VS", font_size=36, color=rgb_to_hex(palette['secondary']), font=font).with_duration(duration)
    vs = vs.with_position(('center', height // 2 - 20))
    layers.append(vs)
    
    # Get comparison items
    left = scene.get('compare_left', scene.get('left', {}))
    right = scene.get('compare_right', scene.get('right', {}))
    
    left_title = left.get('title', 'Option A') if isinstance(left, dict) else str(left)[:20]
    right_title = right.get('title', 'Option B') if isinstance(right, dict) else str(right)[:20]
    
    # Left side icon
    left_kw = extract_visual_keywords(left_title)
    if left_kw:
        left_img = generate_image(left_kw[0][1], 180, 180, "icon")
        if left_img:
            left_clip = create_image_clip(left_img, 150, 150, duration)
            if left_clip:
                left_clip = left_clip.with_position((width // 4 - 75, 200))
                layers.append(left_clip)
    
    # Left title
    left_text = TextClip(
        text=left_title.upper(),
        font_size=32,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    left_text = left_text.with_position((width // 4 - 60, 370))
    layers.append(left_text)
    
    # Right side icon
    right_kw = extract_visual_keywords(right_title)
    if right_kw:
        right_img = generate_image(right_kw[0][1], 180, 180, "icon")
        if right_img:
            right_clip = create_image_clip(right_img, 150, 150, duration)
            if right_clip:
                right_clip = right_clip.with_position((width * 3 // 4 - 75, 200))
                layers.append(right_clip)
    
    # Right title
    right_text = TextClip(
        text=right_title.upper(),
        font_size=32,
        color=rgb_to_hex(palette['secondary']),
        font=font
    ).with_duration(duration)
    right_text = right_text.with_position((width * 3 // 4 - 60, 370))
    layers.append(right_text)
    
    # Narrator
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_diagram_with_parts(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    🔬 DIAGRAM FRAME - Central image with labeled parts
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'DIAGRAM')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=44,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 50))
    layers.append(title)
    
    # Generate main diagram image
    diagram_prompt = f"{headline} diagram with labeled parts, educational illustration"
    img_path = generate_image(diagram_prompt, 500, 400, "diagram")
    
    if img_path:
        img_clip = create_image_clip(img_path, 450, 350, duration)
        if img_clip:
            img_clip = img_clip.with_position(('center', 180))
            layers.append(img_clip)
    
    # Get parts/elements
    parts = scene.get('diagram_elements', scene.get('parts', []))
    if parts:
        # Show parts as labels around the image
        for i, part in enumerate(parts[:4]):
            part_text = str(part)[:20]
            
            # Position labels around the diagram
            positions = [
                (80, 200),
                (width - 180, 200),
                (80, 450),
                (width - 180, 450),
            ]
            
            x, y = positions[i % 4]
            
            # Label background
            label_bg = ColorClip(size=(150, 40), color=palette['card'], duration=duration)
            label_bg = label_bg.with_position((x, y))
            layers.append(label_bg)
            
            # Label text
            label = TextClip(
                text=part_text,
                font_size=20,
                color='white',
                font=font
            ).with_duration(duration)
            label = label.with_position((x + 10, y + 8))
            layers.append(label)
    
    # Narrator
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_fact_with_icon(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    📊 FACT/STAT FRAME - Big number or fact with icon
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'FACT')
    narration = scene.get('narration', '')
    fact_number = scene.get('fact_number', '')
    
    # Icon
    keywords = extract_visual_keywords(headline + ' ' + narration)
    if keywords:
        img_path = generate_image(keywords[0][1], 200, 200, "icon")
        if img_path:
            img_clip = create_image_clip(img_path, 180, 180, duration)
            if img_clip:
                img_clip = img_clip.with_position(('center', 150))
                layers.append(img_clip)
    
    # Big number/fact
    display_text = fact_number if fact_number else headline
    big_text = TextClip(
        text=display_text.upper(),
        font_size=80,
        color=rgb_to_hex(palette['secondary']),
        font=font
    ).with_duration(duration)
    big_text = big_text.with_position(('center', 380))
    layers.append(big_text)
    
    # Context
    context = TextClip(
        text=headline if fact_number else '',
        font_size=36,
        color='white',
        font=font
    ).with_duration(duration)
    context = context.with_position(('center', 480))
    layers.append(context)
    
    # Narrator
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def render_summary(scene: Dict, width: int, height: int, duration: float, palette: Dict) -> List:
    """
    ✅ SUMMARY FRAME - Key takeaways with checkmarks
    """
    layers = []
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=palette['bg'], duration=duration)
    layers.append(bg)
    
    headline = scene.get('headline', 'SUMMARY')
    narration = scene.get('narration', '')
    key_points = scene.get('key_points', [])
    
    # Title with icon
    icon = TextClip(text="📋", font_size=60, font=font).with_duration(duration)
    icon = icon.with_position(('center', 80))
    layers.append(icon)
    
    title = TextClip(
        text="KEY TAKEAWAYS",
        font_size=40,
        color=rgb_to_hex(palette['primary']),
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 160))
    layers.append(title)
    
    # Key points with checkmarks
    if not key_points and narration:
        # Extract from narration
        key_points = [s.strip() for s in narration.split('.') if len(s.strip()) > 10][:3]
    
    y_pos = 250
    for i, point in enumerate(key_points[:4]):
        # Checkmark
        check = TextClip(
            text="✓",
            font_size=36,
            color=rgb_to_hex(palette['secondary']),
            font=font
        ).with_duration(duration)
        check = check.with_position((60, y_pos))
        layers.append(check)
        
        # Point text
        point_text = TextClip(
            text=point[:50],
            font_size=28,
            color='white',
            font=font
        ).with_duration(duration)
        point_text = point_text.with_position((110, y_pos + 5))
        layers.append(point_text)
        
        y_pos += 70
    
    # Narrator
    if narration:
        layers.extend(create_narrator_bubble(narration, width, height, duration, palette))
    
    return layers


def create_narrator_bubble(text: str, width: int, height: int, duration: float, palette: Dict) -> List:
    """Create a styled narrator bubble at the bottom of the frame."""
    layers = []
    font = get_font()
    
    # Bubble background
    bubble_h = 120
    bubble_y = height - bubble_h - 20
    
    bubble_bg = ColorClip(
        size=(width - 40, bubble_h),
        color=palette['card'],
        duration=duration
    )
    bubble_bg = bubble_bg.with_opacity(0.9)
    bubble_bg = bubble_bg.with_position((20, bubble_y))
    layers.append(bubble_bg)
    
    # Accent line on left
    accent = ColorClip(size=(4, bubble_h - 20), color=palette['primary'], duration=duration)
    accent = accent.with_position((30, bubble_y + 10))
    layers.append(accent)
    
    # Text
    wrapped = wrap_text(text, 50)
    text_clip = TextClip(
        text=wrapped,
        font_size=24,
        color=rgb_to_hex(palette['text']),
        font=font,
        method='caption',
        size=(width - 100, None)
    ).with_duration(duration)
    text_clip = text_clip.with_position((50, bubble_y + 15))
    layers.append(text_clip)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 MAIN DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

VISUAL_RENDERERS = {
    'title': render_title_with_image,
    'title_intro': render_title_with_image,
    'hook': render_title_with_image,
    'definition': render_definition_with_image,
    'explanation': render_definition_with_image,
    'equation': render_equation,
    'formula': render_equation,
    'process': render_process_with_icons,
    'process_flow': render_process_with_icons,
    'flowchart': render_process_with_icons,
    'comparison': render_comparison_with_images,
    'split_compare': render_comparison_with_images,
    'diagram': render_diagram_with_parts,
    'hierarchy': render_diagram_with_parts,
    'fact': render_fact_with_icon,
    'stats_number': render_fact_with_icon,
    'summary': render_summary,
    'example': render_process_with_icons,
}


def render_visual_frame(scene: Dict, width: int, height: int, topic: str = "") -> CompositeVideoClip:
    """
    Main entry point - render a scene with rich visuals.
    
    Args:
        scene: Scene dictionary
        width: Video width
        height: Video height
        topic: Video topic (for color palette selection)
    
    Returns:
        CompositeVideoClip
    """
    scene_type = scene.get('scene_type', 'definition').lower()
    frame_type = scene.get('frame_type', scene_type).lower()
    duration = scene.get('duration', 5.0)
    
    # Get appropriate palette
    palette = get_palette_for_topic(topic)
    
    # Get renderer
    renderer = VISUAL_RENDERERS.get(frame_type, VISUAL_RENDERERS.get(scene_type, render_definition_with_image))
    
    print(f"   🎨 Visual Renderer: {frame_type} ({renderer.__name__})")
    
    try:
        layers = renderer(scene, width, height, duration, palette)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
    except Exception as e:
        print(f"   ⚠️ Render error: {e}")
        # Fallback
        layers = render_definition_with_image(scene, width, height, duration, palette)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
