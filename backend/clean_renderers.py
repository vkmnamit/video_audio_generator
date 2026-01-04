"""
🎬 CLEAN VISUAL RENDERERS - No External API, Pure MoviePy
==========================================================
Beautiful educational frames using ONLY:
- Colored shapes
- Emoji icons
- Clean typography
- Smooth flowchart designs

NO external image API - 100% reliable!
"""

import os
import math
import random
from typing import Dict, List, Tuple, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 COLOR PALETTES
# ═══════════════════════════════════════════════════════════════════════════════

PALETTES = {
    "nature": {
        "bg": (15, 40, 30),
        "primary": (76, 217, 100),      # Bright green
        "secondary": (255, 204, 0),     # Sun yellow
        "accent": (90, 200, 250),       # Sky blue
        "text": (255, 255, 255),
        "card": (30, 60, 45),
        "card2": (40, 80, 55),
    },
    "science": {
        "bg": (15, 20, 40),
        "primary": (0, 210, 255),       # Cyan
        "secondary": (255, 165, 0),     # Orange
        "accent": (200, 100, 255),      # Purple
        "text": (255, 255, 255),
        "card": (25, 35, 60),
        "card2": (35, 50, 80),
    },
    "tech": {
        "bg": (10, 15, 25),
        "primary": (0, 255, 136),       # Matrix green
        "secondary": (64, 196, 255),    # Blue
        "accent": (255, 64, 129),       # Pink
        "text": (255, 255, 255),
        "card": (20, 30, 45),
        "card2": (30, 45, 60),
    },
}


def get_palette(topic: str) -> Dict:
    """Choose palette based on topic."""
    t = topic.lower()
    if any(w in t for w in ['plant', 'photo', 'bio', 'leaf', 'tree', 'nature', 'cell']):
        return PALETTES['nature']
    elif any(w in t for w in ['chem', 'physics', 'atom', 'molecule', 'energy']):
        return PALETTES['science']
    return PALETTES['tech']


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_font():
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "Helvetica"
    ]
    for f in fonts:
        if os.path.exists(f):
            return f
    return "Helvetica"


def hex_color(rgb: Tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def wrap(text: str, max_chars: int = 40) -> str:
    words = text.split()
    lines, current, length = [], [], 0
    for word in words:
        if length + len(word) + 1 <= max_chars:
            current.append(word)
            length += len(word) + 1
        else:
            if current:
                lines.append(' '.join(current))
            current, length = [word], len(word)
    if current:
        lines.append(' '.join(current))
    return '\n'.join(lines)


# Emoji icons for common concepts
ICONS = {
    'sun': '☀️', 'sunlight': '☀️', 'light': '💡',
    'water': '💧', 'h2o': '💧', 'rain': '🌧️',
    'plant': '🌱', 'leaf': '🍃', 'tree': '🌳',
    'oxygen': '🫧', 'o2': '🫧', 'air': '💨',
    'carbon': '⚫', 'co2': '💨',
    'glucose': '🍬', 'sugar': '🍬', 'food': '🍽️',
    'energy': '⚡', 'power': '⚡',
    'chlorophyll': '🟢', 'green': '🟢',
    'photosynthesis': '🌿',
    'arrow': '→', 'flow': '→',
    'check': '✓', 'done': '✅',
    'question': '❓', 'think': '🤔',
    'brain': '🧠', 'idea': '💡',
    'start': '▶️', 'end': '🏁',
    'input': '📥', 'output': '📤',
    'process': '⚙️', 'step': '📍',
}


def get_icon(text: str) -> str:
    """Get emoji icon for a concept."""
    text_lower = text.lower()
    for keyword, icon in ICONS.items():
        if keyword in text_lower:
            return icon
    return '📌'


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 SHAPE CREATORS
# ═══════════════════════════════════════════════════════════════════════════════

def create_box(x: int, y: int, w: int, h: int, color: Tuple, duration: float, 
               glow: bool = False, glow_color: Tuple = None) -> List:
    """Create a box with optional glow effect."""
    layers = []
    
    if glow and glow_color:
        # Glow effect (larger, semi-transparent)
        glow_clip = ColorClip(size=(w + 12, h + 12), color=glow_color, duration=duration)
        glow_clip = glow_clip.with_opacity(0.4)
        glow_clip = glow_clip.with_position((x - 6, y - 6))
        layers.append(glow_clip)
    
    box = ColorClip(size=(w, h), color=color, duration=duration)
    box = box.with_position((x, y))
    layers.append(box)
    
    return layers


def create_circle_box(x: int, y: int, size: int, color: Tuple, duration: float,
                      icon: str = "", text: str = "", font_color: str = "white") -> List:
    """Create a rounded-looking box (square with content centered)."""
    layers = []
    font = get_font()
    
    # Outer glow
    glow = ColorClip(size=(size + 8, size + 8), color=color, duration=duration)
    glow = glow.with_opacity(0.3)
    glow = glow.with_position((x - 4, y - 4))
    layers.append(glow)
    
    # Main box
    box = ColorClip(size=(size, size), color=color, duration=duration)
    box = box.with_position((x, y))
    layers.append(box)
    
    # Icon or text inside
    if icon:
        icon_clip = TextClip(text=icon, font_size=size // 2, font=font).with_duration(duration)
        icon_clip = icon_clip.with_position((x + size // 4, y + size // 4))
        layers.append(icon_clip)
    elif text:
        text_clip = TextClip(
            text=text[:6], font_size=size // 3, color=font_color, font=font
        ).with_duration(duration)
        tw = len(text[:6]) * (size // 6)
        text_clip = text_clip.with_position((x + (size - tw) // 2, y + size // 3))
        layers.append(text_clip)
    
    return layers


def create_arrow(x1: int, y1: int, x2: int, y2: int, color: Tuple, duration: float,
                 animated: bool = True) -> List:
    """Create an arrow between two points."""
    layers = []
    font = get_font()
    
    # Determine direction
    if abs(x2 - x1) > abs(y2 - y1):
        arrow = "→" if x2 > x1 else "←"
        ax = (x1 + x2) // 2 - 15
        ay = y1 - 15 if y1 == y2 else min(y1, y2)
    else:
        arrow = "↓" if y2 > y1 else "↑"
        ax = x1 - 15
        ay = (y1 + y2) // 2 - 15
    
    arrow_clip = TextClip(
        text=arrow, font_size=50, color=hex_color(color), font=font
    ).with_duration(duration)
    arrow_clip = arrow_clip.with_position((ax, ay))
    layers.append(arrow_clip)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 FRAME RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_title(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    🎬 TITLE FRAME
    Big centered title with icon and accent
    """
    layers = []
    font = get_font()
    
    # Background
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'TITLE')
    
    # Large icon
    icon = get_icon(headline + ' ' + scene.get('narration', ''))
    icon_clip = TextClip(text=icon, font_size=150, font=font).with_duration(dur)
    icon_clip = icon_clip.with_position(('center', int(h * 0.25)))
    layers.append(icon_clip)
    
    # Title text
    title = TextClip(
        text=headline.upper(),
        font_size=80,
        color=hex_color(pal['text']),
        font=font,
        stroke_color=hex_color(pal['primary']),
        stroke_width=2
    ).with_duration(dur)
    title = title.with_position(('center', int(h * 0.50)))
    layers.append(title)
    
    # Accent line
    line = ColorClip(size=(350, 6), color=pal['primary'], duration=dur)
    line = line.with_position(('center', int(h * 0.60)))
    layers.append(line)
    
    # Narrator
    layers.extend(narrator_bubble(scene.get('narration', ''), w, h, dur, pal))
    
    return layers


def render_definition(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    📖 DEFINITION FRAME
    Term with icon and explanation
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'TERM')
    narration = scene.get('narration', '')
    
    # Icon
    icon = get_icon(headline + ' ' + narration)
    icon_clip = TextClip(text=icon, font_size=120, font=font).with_duration(dur)
    icon_clip = icon_clip.with_position(('center', 100))
    layers.append(icon_clip)
    
    # Term
    term = TextClip(
        text=headline.upper(),
        font_size=60,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    term = term.with_position(('center', 260))
    layers.append(term)
    
    # Separator
    sep = ColorClip(size=(400, 4), color=pal['secondary'], duration=dur)
    sep = sep.with_position(('center', 340))
    layers.append(sep)
    
    # Definition text
    if narration:
        first_part = narration.split('.')[0] + '.'
        wrapped = wrap(first_part, 35)
        def_clip = TextClip(
            text=wrapped,
            font_size=36,
            color=hex_color(pal['text']),
            font=font,
            method='caption',
            size=(w - 100, None)
        ).with_duration(dur)
        def_clip = def_clip.with_position(('center', 400))
        layers.append(def_clip)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_equation(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    🧪 EQUATION FRAME
    Chemical/math equation with emoji icons
    
    For photosynthesis:
    ☀️ + 💧 + 💨 → 🍬 + 🫧
    (Light + Water + CO₂ → Sugar + Oxygen)
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'EQUATION')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=48,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    title = title.with_position(('center', 60))
    layers.append(title)
    
    # Check for photosynthesis
    is_photo = any(word in narration.lower() for word in ['photosynth', 'co2', 'carbon dioxide', 'chlorophyll'])
    
    if is_photo:
        # Photosynthesis equation with icons
        y_react = h // 2 - 150
        box_size = 90
        gap = 30
        
        # Calculate starting x for centering
        total_width = 5 * box_size + 4 * gap + 100  # 5 items + arrows
        start_x = (w - total_width) // 2
        
        # === REACTANTS ROW ===
        # CO2
        x = start_x
        layers.extend(create_circle_box(x, y_react, box_size, pal['card'], dur, icon='💨'))
        co2_label = TextClip(text='CO₂', font_size=24, color='white', font=font).with_duration(dur)
        co2_label = co2_label.with_position((x + 25, y_react + box_size + 10))
        layers.append(co2_label)
        
        # Plus
        plus1 = TextClip(text='+', font_size=50, color=hex_color(pal['accent']), font=font).with_duration(dur)
        plus1 = plus1.with_position((x + box_size + 10, y_react + 20))
        layers.append(plus1)
        
        # H2O
        x += box_size + gap + 40
        layers.extend(create_circle_box(x, y_react, box_size, pal['card'], dur, icon='💧'))
        h2o_label = TextClip(text='H₂O', font_size=24, color='white', font=font).with_duration(dur)
        h2o_label = h2o_label.with_position((x + 25, y_react + box_size + 10))
        layers.append(h2o_label)
        
        # Plus
        plus2 = TextClip(text='+', font_size=50, color=hex_color(pal['accent']), font=font).with_duration(dur)
        plus2 = plus2.with_position((x + box_size + 10, y_react + 20))
        layers.append(plus2)
        
        # SUNLIGHT
        x += box_size + gap + 40
        layers.extend(create_circle_box(x, y_react, box_size, pal['secondary'], dur, icon='☀️'))
        sun_label = TextClip(text='Light', font_size=24, color=hex_color(pal['secondary']), font=font).with_duration(dur)
        sun_label = sun_label.with_position((x + 20, y_react + box_size + 10))
        layers.append(sun_label)
        
        # === BIG ARROW ===
        arrow_y = y_react + box_size + 60
        arrow = TextClip(text='⬇️', font_size=80, font=font).with_duration(dur)
        arrow = arrow.with_position(('center', arrow_y))
        layers.append(arrow)
        
        process_label = TextClip(
            text='PHOTOSYNTHESIS',
            font_size=28,
            color=hex_color(pal['primary']),
            font=font
        ).with_duration(dur)
        process_label = process_label.with_position(('center', arrow_y + 70))
        layers.append(process_label)
        
        # === PRODUCTS ROW ===
        y_prod = arrow_y + 140
        
        # Glucose
        x = (w - 2 * box_size - gap - 40) // 2
        layers.extend(create_circle_box(x, y_prod, box_size, pal['card2'], dur, icon='🍬'))
        glu_label = TextClip(text='Glucose', font_size=22, color='white', font=font).with_duration(dur)
        glu_label = glu_label.with_position((x + 10, y_prod + box_size + 10))
        layers.append(glu_label)
        
        # Plus
        plus3 = TextClip(text='+', font_size=50, color=hex_color(pal['accent']), font=font).with_duration(dur)
        plus3 = plus3.with_position((x + box_size + 10, y_prod + 20))
        layers.append(plus3)
        
        # Oxygen
        x += box_size + gap + 40
        layers.extend(create_circle_box(x, y_prod, box_size, pal['card2'], dur, icon='🫧'))
        o2_label = TextClip(text='O₂', font_size=24, color='white', font=font).with_duration(dur)
        o2_label = o2_label.with_position((x + 30, y_prod + box_size + 10))
        layers.append(o2_label)
    
    else:
        # Generic equation
        eq_text = scene.get('equation', scene.get('formula_text', 'A + B → C'))
        eq = TextClip(
            text=eq_text,
            font_size=60,
            color='white',
            font=font
        ).with_duration(dur)
        eq = eq.with_position(('center', h // 2))
        layers.append(eq)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_flowchart(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    🔄 FLOWCHART FRAME
    Process flow with icons and arrows
    
    [☀️ Sun] → [🌱 Plant] → [⚡ Energy] → [🫧 O₂]
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'PROCESS')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=48,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    title = title.with_position(('center', 60))
    layers.append(title)
    
    # Get steps from scene or extract from narration
    steps = scene.get('steps', scene.get('flow_nodes', []))
    if not steps:
        # Default photosynthesis flow
        if 'photosynth' in narration.lower():
            steps = [
                {'text': 'Sunlight', 'icon': '☀️'},
                {'text': 'Leaf', 'icon': '🍃'},
                {'text': 'Energy', 'icon': '⚡'},
                {'text': 'Oxygen', 'icon': '🫧'},
            ]
        else:
            steps = [
                {'text': 'Input', 'icon': '📥'},
                {'text': 'Process', 'icon': '⚙️'},
                {'text': 'Output', 'icon': '📤'},
            ]
    
    # Normalize steps
    normalized_steps = []
    for s in steps[:4]:
        if isinstance(s, dict):
            normalized_steps.append({
                'text': s.get('text', str(s)),
                'icon': s.get('icon', get_icon(s.get('text', '')))
            })
        else:
            normalized_steps.append({
                'text': str(s)[:12],
                'icon': get_icon(str(s))
            })
    
    # Calculate layout
    num_steps = len(normalized_steps)
    box_size = 100
    h_gap = 60
    total_w = num_steps * box_size + (num_steps - 1) * h_gap
    start_x = (w - total_w) // 2
    y_pos = h // 2 - 80
    
    # Render steps with arrows
    for i, step in enumerate(normalized_steps):
        x = start_x + i * (box_size + h_gap)
        
        # Box with glow
        layers.extend(create_box(x, y_pos, box_size, box_size, pal['card'], dur,
                                 glow=True, glow_color=pal['primary']))
        
        # Icon
        icon = step.get('icon', '📌')
        icon_clip = TextClip(text=icon, font_size=50, font=font).with_duration(dur)
        icon_clip = icon_clip.with_position((x + box_size // 4, y_pos + 15))
        layers.append(icon_clip)
        
        # Label below
        label = TextClip(
            text=step['text'][:12],
            font_size=22,
            color='white',
            font=font
        ).with_duration(dur)
        label = label.with_position((x + 5, y_pos + box_size + 15))
        layers.append(label)
        
        # Arrow to next
        if i < num_steps - 1:
            arrow = TextClip(
                text='→',
                font_size=60,
                color=hex_color(pal['secondary']),
                font=font
            ).with_duration(dur)
            arrow = arrow.with_position((x + box_size + 10, y_pos + 25))
            layers.append(arrow)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_comparison(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    ⚖️ COMPARISON FRAME
    Two sides with icons
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'COMPARISON')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=44,
        color=hex_color(pal['text']),
        font=font
    ).with_duration(dur)
    title = title.with_position(('center', 60))
    layers.append(title)
    
    # Divider
    div = ColorClip(size=(4, h - 350), color=pal['accent'], duration=dur)
    div = div.with_position((w // 2 - 2, 140))
    layers.append(div)
    
    # VS badge
    vs = TextClip(text='VS', font_size=40, color=hex_color(pal['secondary']), font=font).with_duration(dur)
    vs = vs.with_position((w // 2 - 25, h // 2 - 30))
    layers.append(vs)
    
    # Left side
    left = scene.get('compare_left', scene.get('left', 'Option A'))
    left_title = left.get('title', str(left)[:15]) if isinstance(left, dict) else str(left)[:15]
    left_icon = get_icon(left_title)
    
    l_icon = TextClip(text=left_icon, font_size=100, font=font).with_duration(dur)
    l_icon = l_icon.with_position((w // 4 - 40, 200))
    layers.append(l_icon)
    
    l_text = TextClip(
        text=left_title.upper(),
        font_size=32,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    l_text = l_text.with_position((w // 4 - 60, 330))
    layers.append(l_text)
    
    # Right side
    right = scene.get('compare_right', scene.get('right', 'Option B'))
    right_title = right.get('title', str(right)[:15]) if isinstance(right, dict) else str(right)[:15]
    right_icon = get_icon(right_title)
    
    r_icon = TextClip(text=right_icon, font_size=100, font=font).with_duration(dur)
    r_icon = r_icon.with_position((w * 3 // 4 - 40, 200))
    layers.append(r_icon)
    
    r_text = TextClip(
        text=right_title.upper(),
        font_size=32,
        color=hex_color(pal['secondary']),
        font=font
    ).with_duration(dur)
    r_text = r_text.with_position((w * 3 // 4 - 60, 330))
    layers.append(r_text)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_diagram(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    🔬 DIAGRAM FRAME
    Central concept with labeled parts around it
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'DIAGRAM')
    narration = scene.get('narration', '')
    
    # Title
    title = TextClip(
        text=headline.upper(),
        font_size=44,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    title = title.with_position(('center', 50))
    layers.append(title)
    
    # Central icon
    icon = get_icon(headline + ' ' + narration)
    center_icon = TextClip(text=icon, font_size=180, font=font).with_duration(dur)
    center_icon = center_icon.with_position(('center', h // 2 - 120))
    layers.append(center_icon)
    
    # Parts/labels
    parts = scene.get('diagram_elements', scene.get('parts', []))
    if not parts and 'photosynth' in (headline + narration).lower():
        parts = ['Sunlight ☀️', 'Water 💧', 'CO₂ 💨', 'Chlorophyll 🟢']
    
    if parts:
        positions = [
            (100, 180), (w - 200, 180),
            (100, h // 2 + 100), (w - 200, h // 2 + 100)
        ]
        
        for i, part in enumerate(parts[:4]):
            x, y = positions[i]
            
            # Label box
            box = ColorClip(size=(180, 50), color=pal['card'], duration=dur)
            box = box.with_position((x, y))
            layers.append(box)
            
            label = TextClip(
                text=str(part)[:18],
                font_size=22,
                color='white',
                font=font
            ).with_duration(dur)
            label = label.with_position((x + 10, y + 12))
            layers.append(label)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_fact(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    📊 FACT/STAT FRAME
    Big number or fact with icon
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'FACT')
    narration = scene.get('narration', '')
    fact_number = scene.get('fact_number', '')
    
    # Icon
    icon = get_icon(headline + ' ' + narration)
    icon_clip = TextClip(text=icon, font_size=140, font=font).with_duration(dur)
    icon_clip = icon_clip.with_position(('center', 150))
    layers.append(icon_clip)
    
    # Big text
    big_text = fact_number if fact_number else headline
    big = TextClip(
        text=big_text.upper(),
        font_size=80,
        color=hex_color(pal['secondary']),
        font=font
    ).with_duration(dur)
    big = big.with_position(('center', 350))
    layers.append(big)
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def render_summary(scene: Dict, w: int, h: int, dur: float, pal: Dict) -> List:
    """
    ✅ SUMMARY FRAME
    Key takeaways with checkmarks
    """
    layers = []
    font = get_font()
    
    layers.append(ColorClip(size=(w, h), color=pal['bg'], duration=dur))
    
    headline = scene.get('headline', 'SUMMARY')
    narration = scene.get('narration', '')
    key_points = scene.get('key_points', [])
    
    # Icon
    icon_clip = TextClip(text='📋', font_size=80, font=font).with_duration(dur)
    icon_clip = icon_clip.with_position(('center', 80))
    layers.append(icon_clip)
    
    # Title
    title = TextClip(
        text='KEY TAKEAWAYS',
        font_size=40,
        color=hex_color(pal['primary']),
        font=font
    ).with_duration(dur)
    title = title.with_position(('center', 180))
    layers.append(title)
    
    # Extract points from narration if not provided
    if not key_points and narration:
        sentences = [s.strip() for s in narration.split('.') if len(s.strip()) > 8]
        key_points = sentences[:3]
    
    # Render points
    y = 280
    for point in key_points[:4]:
        # Checkmark
        check = TextClip(
            text='✓',
            font_size=40,
            color=hex_color(pal['secondary']),
            font=font
        ).with_duration(dur)
        check = check.with_position((60, y))
        layers.append(check)
        
        # Point text
        pt = TextClip(
            text=point[:45],
            font_size=28,
            color='white',
            font=font
        ).with_duration(dur)
        pt = pt.with_position((120, y + 5))
        layers.append(pt)
        
        y += 70
    
    layers.extend(narrator_bubble(narration, w, h, dur, pal))
    
    return layers


def narrator_bubble(text: str, w: int, h: int, dur: float, pal: Dict) -> List:
    """Create narrator text bubble at bottom."""
    if not text:
        return []
    
    layers = []
    font = get_font()
    
    bubble_h = 120
    bubble_y = h - bubble_h - 25
    
    # Background
    bg = ColorClip(size=(w - 50, bubble_h), color=pal['card'], duration=dur)
    bg = bg.with_opacity(0.92)
    bg = bg.with_position((25, bubble_y))
    layers.append(bg)
    
    # Accent line
    accent = ColorClip(size=(5, bubble_h - 24), color=pal['primary'], duration=dur)
    accent = accent.with_position((35, bubble_y + 12))
    layers.append(accent)
    
    # Text
    wrapped = wrap(text, 50)
    txt = TextClip(
        text=wrapped,
        font_size=24,
        color=hex_color(pal['text']),
        font=font,
        method='caption',
        size=(w - 120, None)
    ).with_duration(dur)
    txt = txt.with_position((55, bubble_y + 18))
    layers.append(txt)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 MAIN DISPATCHER
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
    'comparison': render_comparison,
    'split_compare': render_comparison,
    'diagram': render_diagram,
    'hierarchy': render_diagram,
    'fact': render_fact,
    'stats_number': render_fact,
    'example': render_flowchart,
    'summary': render_summary,
}


def render_clean_frame(scene: Dict, width: int, height: int, topic: str = "") -> CompositeVideoClip:
    """
    Main entry point - render a scene with clean visuals.
    """
    scene_type = scene.get('scene_type', 'definition').lower()
    frame_type = scene.get('frame_type', scene_type).lower()
    duration = scene.get('duration', 5.0)
    
    palette = get_palette(topic)
    renderer = RENDERERS.get(frame_type, RENDERERS.get(scene_type, render_definition))
    
    print(f"   🎨 Clean Renderer: {frame_type} → {renderer.__name__}")
    
    try:
        layers = renderer(scene, width, height, duration, palette)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
    except Exception as e:
        print(f"   ⚠️ Render error: {e}")
        layers = render_definition(scene, width, height, duration, palette)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
