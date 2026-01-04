"""
🎨 THEMED VISUAL RENDERER - Code-Based, No External API
========================================================
Generates beautiful educational visuals using code, not AI images.
Uses the style reference system for consistent theming.

Benefits:
- 100% reliable (no rate limits)
- Instant generation
- Perfect consistency
- User-controlled themes
"""

import os
import math
from typing import Dict, List, Tuple, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# Import theme system
from style_reference_system import (
    get_current_theme, 
    get_current_colors, 
    DEFAULT_THEMES,
    set_current_theme,
    load_theme
)

# Import term bubbles
from term_bubbles import create_term_bubbles_overlay, find_terms_in_text


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


def wrap_text(text: str, max_chars: int = 40) -> str:
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


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def create_glow_box(width: int, height: int, color: Tuple[int, int, int], 
                    glow_size: int = 15, opacity: float = 0.5) -> Image.Image:
    """Create a box with glow effect using PIL."""
    # Create larger image for glow
    full_w = width + glow_size * 2
    full_h = height + glow_size * 2
    
    img = Image.new('RGBA', (full_w, full_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw the glow (multiple rectangles with decreasing opacity)
    for i in range(glow_size, 0, -3):
        alpha = int(255 * opacity * (i / glow_size) * 0.3)
        glow_color = (*color, alpha)
        draw.rectangle(
            [glow_size - i, glow_size - i, full_w - glow_size + i, full_h - glow_size + i],
            fill=glow_color
        )
    
    # Draw the main box
    draw.rectangle(
        [glow_size, glow_size, full_w - glow_size, full_h - glow_size],
        fill=(*color, int(255 * 0.9))
    )
    
    return img


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 SHAPE GENERATORS (Themed)
# ═══════════════════════════════════════════════════════════════════════════════

def create_themed_box(width: int, height: int, theme: Dict, 
                      box_type: str = "primary") -> ColorClip:
    """Create a themed box clip."""
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    
    color_map = {
        'primary': colors.get('primary', (0, 200, 255)),
        'secondary': colors.get('secondary', (255, 150, 100)),
        'accent': colors.get('accent', (255, 100, 150)),
        'card': colors.get('card', (35, 40, 55)),
    }
    
    color = color_map.get(box_type, colors.get('card', (35, 40, 55)))
    
    return ColorClip(size=(width, height), color=color)


def create_arrow_text(direction: str = "right", size: int = 40, 
                     color: str = "white") -> TextClip:
    """Create an arrow text clip."""
    arrows = {
        'right': '→',
        'left': '←',
        'up': '↑',
        'down': '↓',
        'double': '⟷',
    }
    arrow = arrows.get(direction, '→')
    font = get_font()
    return TextClip(text=arrow, font_size=size, color=color, font=font)


# ═══════════════════════════════════════════════════════════════════════════════
# 📦 ARRAY/LIST RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_array_visual(items: List[str], width: int, height: int, 
                        duration: float, theme: Dict,
                        highlight_index: int = -1) -> List:
    """
    Render a visual array with boxes for each element.
    
    Args:
        items: List of items to display
        width, height: Frame dimensions
        duration: Clip duration
        theme: Visual theme
        highlight_index: Index to highlight (-1 for none)
    """
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    # Calculate box dimensions
    num_items = len(items)
    if num_items == 0:
        return layers
    
    max_box_width = min(120, (width - 100) // num_items - 20)
    box_height = 80
    box_spacing = 15
    
    total_width = num_items * max_box_width + (num_items - 1) * box_spacing
    start_x = (width - total_width) // 2
    box_y = height // 2 - box_height // 2
    
    # Draw index labels at top
    for i in range(num_items):
        x = start_x + i * (max_box_width + box_spacing)
        
        # Index label
        index_text = TextClip(
            text=str(i),
            font_size=18,
            color=rgb_to_hex(colors.get('inactive', (100, 100, 120))),
            font=font
        ).with_duration(duration)
        index_text = index_text.with_position((x + max_box_width // 2 - 8, box_y - 35))
        layers.append(index_text)
    
    # Draw boxes
    for i, item in enumerate(items):
        x = start_x + i * (max_box_width + box_spacing)
        
        # Determine color
        if i == highlight_index:
            box_color = colors.get('primary', (0, 200, 255))
            text_color = 'white'
        else:
            box_color = colors.get('card', (35, 45, 60))
            text_color = rgb_to_hex(colors.get('text', (255, 255, 255)))
        
        # Glow for highlighted
        if i == highlight_index and style.get('has_glow', True):
            glow = ColorClip(size=(max_box_width + 10, box_height + 10), 
                           color=box_color, duration=duration)
            glow = glow.with_opacity(0.4).with_position((x - 5, box_y - 5))
            layers.append(glow)
        
        # Box
        box = ColorClip(size=(max_box_width, box_height), 
                       color=box_color, duration=duration)
        box = box.with_position((x, box_y))
        layers.append(box)
        
        # Top accent bar
        if i == highlight_index:
            accent = ColorClip(size=(max_box_width, 4), 
                             color=colors.get('accent', (255, 100, 150)), 
                             duration=duration)
            accent = accent.with_position((x, box_y))
            layers.append(accent)
        
        # Item text
        item_text = TextClip(
            text=str(item)[:8],  # Limit length
            font_size=28,
            color=text_color,
            font=font
        ).with_duration(duration)
        item_text = item_text.with_position((x + 15, box_y + 25))
        layers.append(item_text)
    
    # Pointer arrow if highlighted
    if highlight_index >= 0 and highlight_index < num_items:
        pointer_x = start_x + highlight_index * (max_box_width + box_spacing) + max_box_width // 2 - 15
        pointer = TextClip(
            text="↓",
            font_size=35,
            color=rgb_to_hex(colors.get('primary', (0, 200, 255))),
            font=font
        ).with_duration(duration)
        pointer = pointer.with_position((pointer_x, box_y - 70))
        layers.append(pointer)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ PROCESS/FLOWCHART RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_process_visual(steps: List[str], width: int, height: int,
                         duration: float, theme: Dict) -> List:
    """
    Render a process flowchart with connected steps.
    """
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    if not steps:
        return layers
    
    num_steps = min(len(steps), 5)  # Max 5 steps
    steps = steps[:num_steps]
    
    # Layout calculation
    if num_steps <= 3:
        # Horizontal layout
        box_width = min(250, (width - 150) // num_steps)
        box_height = 100
        box_spacing = 60
        total_width = num_steps * box_width + (num_steps - 1) * box_spacing
        start_x = (width - total_width) // 2
        box_y = height // 2 - box_height // 2
        layout = "horizontal"
    else:
        # Two-row layout
        cols = (num_steps + 1) // 2
        box_width = min(220, (width - 100) // cols - 30)
        box_height = 90
        box_spacing = 40
        row_spacing = 100
        start_x = (width - (cols * box_width + (cols - 1) * box_spacing)) // 2
        box_y = height // 2 - box_height - row_spacing // 2
        layout = "grid"
    
    # Color cycle for steps
    step_colors = [
        colors.get('primary', (0, 200, 255)),
        colors.get('secondary', (255, 180, 100)),
        colors.get('accent', (255, 100, 150)),
        (100, 220, 200),  # Teal
        (200, 150, 255),  # Purple
    ]
    
    step_positions = []
    
    # Draw steps
    for i, step in enumerate(steps):
        if layout == "horizontal":
            x = start_x + i * (box_width + box_spacing)
            y = box_y
        else:
            row = i // ((num_steps + 1) // 2)
            col = i % ((num_steps + 1) // 2)
            x = start_x + col * (box_width + box_spacing)
            y = box_y + row * (box_height + row_spacing)
        
        step_positions.append((x, y))
        color = step_colors[i % len(step_colors)]
        
        # Glow
        if style.get('has_glow', True):
            glow = ColorClip(size=(box_width + 12, box_height + 12), 
                           color=color, duration=duration)
            glow = glow.with_opacity(0.3).with_position((x - 6, y - 6))
            layers.append(glow)
        
        # Box
        box = ColorClip(size=(box_width, box_height), 
                       color=colors.get('card', (30, 40, 55)), duration=duration)
        box = box.with_position((x, y))
        layers.append(box)
        
        # Top accent
        accent = ColorClip(size=(box_width, 5), color=color, duration=duration)
        accent = accent.with_position((x, y))
        layers.append(accent)
        
        # Step number
        num_bg = ColorClip(size=(30, 30), color=color, duration=duration)
        num_bg = num_bg.with_position((x + box_width - 40, y + 10))
        layers.append(num_bg)
        
        num_text = TextClip(text=str(i + 1), font_size=18, color='white', font=font)
        num_text = num_text.with_duration(duration).with_position((x + box_width - 32, y + 14))
        layers.append(num_text)
        
        # Step text
        wrapped = wrap_text(step[:50], max_chars=22)
        step_text = TextClip(
            text=wrapped,
            font_size=16,
            color=rgb_to_hex(colors.get('text', (255, 255, 255))),
            font=font
        ).with_duration(duration)
        step_text = step_text.with_position((x + 12, y + 30))
        layers.append(step_text)
    
    # Draw arrows between steps
    for i in range(len(step_positions) - 1):
        x1, y1 = step_positions[i]
        x2, y2 = step_positions[i + 1]
        
        if y1 == y2:  # Same row - horizontal arrow
            arrow_x = x1 + box_width + 10
            arrow_y = y1 + box_height // 2 - 20
            arrow_char = "→"
        else:  # Different row - down arrow
            arrow_x = x1 + box_width // 2 - 15
            arrow_y = y1 + box_height + 20
            arrow_char = "↓"
        
        arrow = TextClip(
            text=arrow_char,
            font_size=35,
            color=rgb_to_hex(colors.get('primary', (0, 200, 255))),
            font=font
        ).with_duration(duration)
        arrow = arrow.with_position((arrow_x, arrow_y))
        layers.append(arrow)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 📐 EQUATION/FORMULA RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_equation_visual(parts: List[Tuple[str, str]], width: int, height: int,
                          duration: float, theme: Dict) -> List:
    """
    Render a visual equation with labeled parts.
    
    Args:
        parts: List of (icon, label) tuples representing equation parts
    """
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    if not parts:
        parts = [("?", "Input"), ("⚙️", "Process"), ("✓", "Output")]
    
    num_parts = min(len(parts), 5)
    parts = parts[:num_parts]
    
    # Layout
    part_width = min(140, (width - 200) // num_parts)
    part_height = 90
    spacing = 50
    
    total_width = num_parts * part_width + (num_parts - 1) * spacing
    start_x = (width - total_width) // 2
    part_y = height // 2 - part_height // 2
    
    part_colors = [
        colors.get('primary', (0, 200, 255)),
        colors.get('secondary', (255, 180, 100)),
        colors.get('accent', (255, 100, 150)),
        (100, 220, 200),
        (200, 150, 255),
    ]
    
    for i, (icon, label) in enumerate(parts):
        x = start_x + i * (part_width + spacing)
        color = part_colors[i % len(part_colors)]
        
        # Glow
        if style.get('has_glow', True):
            glow = ColorClip(size=(part_width + 10, part_height + 10), 
                           color=color, duration=duration)
            glow = glow.with_opacity(0.35).with_position((x - 5, part_y - 5))
            layers.append(glow)
        
        # Box
        box = ColorClip(size=(part_width, part_height), 
                       color=colors.get('card', (30, 40, 55)), duration=duration)
        box = box.with_position((x, part_y))
        layers.append(box)
        
        # Top accent
        accent = ColorClip(size=(part_width, 4), color=color, duration=duration)
        accent = accent.with_position((x, part_y))
        layers.append(accent)
        
        # Icon
        icon_text = TextClip(text=icon, font_size=32, font=font).with_duration(duration)
        icon_text = icon_text.with_position((x + part_width // 2 - 18, part_y + 12))
        layers.append(icon_text)
        
        # Label
        label_text = TextClip(
            text=label[:15],
            font_size=14,
            color=rgb_to_hex(colors.get('text', (255, 255, 255))),
            font=font
        ).with_duration(duration)
        label_text = label_text.with_position((x + 10, part_y + 55))
        layers.append(label_text)
        
        # Operator between parts
        if i < num_parts - 1:
            if i == num_parts - 2:
                operator = "="
            else:
                operator = "+"
            
            op_x = x + part_width + spacing // 2 - 12
            op_text = TextClip(
                text=operator,
                font_size=40,
                color=rgb_to_hex(colors.get('primary', (0, 200, 255))),
                font=font
            ).with_duration(duration)
            op_text = op_text.with_position((op_x, part_y + 25))
            layers.append(op_text)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 SCENE RENDERERS (Title, Definition, Summary, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

def render_themed_title(headline: str, narration: str, width: int, height: int,
                       duration: float, theme: Dict) -> List:
    """Render a themed title screen."""
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    # Central glow
    if style.get('has_glow', True):
        glow = ColorClip(size=(600, 150), color=colors.get('primary', (0, 200, 255)), duration=duration)
        glow = glow.with_opacity(0.15).with_position(('center', height // 2 - 80))
        layers.append(glow)
    
    # Title
    title = TextClip(
        text=headline,
        font_size=64,
        color='white',
        font=font,
        stroke_color=rgb_to_hex(colors.get('primary', (0, 200, 255))),
        stroke_width=3
    ).with_duration(duration)
    title = title.with_position(('center', height // 2 - 50))
    layers.append(title)
    
    # Underline
    underline = ColorClip(size=(400, 5), color=colors.get('primary', (0, 200, 255)), duration=duration)
    underline = underline.with_position(('center', height // 2 + 25))
    layers.append(underline)
    
    # Subtitle
    if narration:
        subtitle = TextClip(
            text=wrap_text(narration[:80], 50),
            font_size=22,
            color='#bbbbbb',
            font=font
        ).with_duration(duration)
        subtitle = subtitle.with_position(('center', height // 2 + 55))
        layers.append(subtitle)
    
    return layers


def render_themed_definition(term: str, definition: str, width: int, height: int,
                            duration: float, theme: Dict) -> List:
    """Render a themed definition card."""
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    # Card dimensions
    card_w = min(width - 100, 850)
    card_h = 260
    card_x = (width - card_w) // 2
    card_y = height // 2 - card_h // 2
    
    # Card glow
    if style.get('has_glow', True):
        glow = ColorClip(size=(card_w + 14, card_h + 14), 
                        color=colors.get('primary', (0, 200, 255)), duration=duration)
        glow = glow.with_opacity(0.25).with_position((card_x - 7, card_y - 7))
        layers.append(glow)
    
    # Card
    card = ColorClip(size=(card_w, card_h), 
                    color=colors.get('card', (30, 40, 55)), duration=duration)
    card = card.with_position((card_x, card_y))
    layers.append(card)
    
    # Left accent
    accent = ColorClip(size=(8, card_h), color=colors.get('primary', (0, 200, 255)), duration=duration)
    accent = accent.with_position((card_x, card_y))
    layers.append(accent)
    
    # Term
    term_text = TextClip(
        text=term,
        font_size=40,
        color='white',
        font=font
    ).with_duration(duration)
    term_text = term_text.with_position((card_x + 35, card_y + 25))
    layers.append(term_text)
    
    # Separator
    sep = ColorClip(size=(card_w - 70, 2), color=colors.get('primary', (0, 200, 255)), duration=duration)
    sep = sep.with_opacity(0.5).with_position((card_x + 35, card_y + 85))
    layers.append(sep)
    
    # Definition
    def_text = TextClip(
        text=wrap_text(definition, 55),
        font_size=22,
        color='#dddddd',
        font=font
    ).with_duration(duration)
    def_text = def_text.with_position((card_x + 35, card_y + 105))
    layers.append(def_text)
    
    return layers


def render_themed_summary(headline: str, points: List[str], width: int, height: int,
                         duration: float, theme: Dict) -> List:
    """Render a themed summary with checkpoints."""
    layers = []
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    font = get_font()
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    # Title
    title = TextClip(
        text=f"✅ {headline}",
        font_size=42,
        color='white',
        font=font
    ).with_duration(duration)
    title = title.with_position(('center', 45))
    layers.append(title)
    
    if not points:
        return layers
    
    # Checklist
    card_w = min(width - 100, 800)
    card_x = (width - card_w) // 2
    start_y = 130
    point_height = 65
    
    point_colors = [
        colors.get('primary', (0, 200, 255)),
        colors.get('secondary', (255, 180, 100)),
        colors.get('accent', (255, 100, 150)),
    ]
    
    for i, point in enumerate(points[:4]):
        y = start_y + i * (point_height + 12)
        color = point_colors[i % len(point_colors)]
        
        # Point background
        point_bg = ColorClip(size=(card_w, point_height), 
                            color=colors.get('card', (30, 40, 55)), duration=duration)
        point_bg = point_bg.with_position((card_x, y))
        layers.append(point_bg)
        
        # Left accent
        accent = ColorClip(size=(5, point_height), color=color, duration=duration)
        accent = accent.with_position((card_x, y))
        layers.append(accent)
        
        # Check icon
        check = TextClip(text="✓", font_size=28, color='#00ff88', font=font).with_duration(duration)
        check = check.with_position((card_x + 18, y + 18))
        layers.append(check)
        
        # Point text
        point_text = TextClip(
            text=point[:60],
            font_size=20,
            color='white',
            font=font
        ).with_duration(duration)
        point_text = point_text.with_position((card_x + 55, y + 20))
        layers.append(point_text)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MAIN RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_themed_frame(scene: Dict, width: int, height: int, topic: str = "") -> CompositeVideoClip:
    """
    Main entry point - render a scene with themed visuals.
    No external APIs, 100% reliable.
    """
    scene_type = scene.get('scene_type', 'definition').lower()
    duration = scene.get('duration', 5.0)
    headline = scene.get('headline', 'TITLE')
    narration = scene.get('narration', scene.get('text', ''))
    
    # Get current theme
    theme = get_current_theme()
    
    print(f"   🎨 Themed Renderer: {scene_type} (theme: {theme.get('name', 'default')})")
    
    # Select renderer based on scene type
    if scene_type in ['title', 'title_intro', 'hook']:
        layers = render_themed_title(headline, narration, width, height, duration, theme)
    
    elif scene_type in ['definition', 'explanation']:
        layers = render_themed_definition(headline, narration, width, height, duration, theme)
    
    elif scene_type in ['process', 'process_flow', 'flowchart']:
        # Extract steps from narration
        steps = extract_steps_from_text(narration)
        layers = render_process_visual(steps, width, height, duration, theme)
        # Add headline at top
        font = get_font()
        title = TextClip(text=headline, font_size=36, color='white', font=font).with_duration(duration)
        title = title.with_position(('center', 35))
        layers.append(title)
    
    elif scene_type in ['array', 'list']:
        # Extract items
        items = extract_items_from_text(narration)
        layers = render_array_visual(items, width, height, duration, theme)
        font = get_font()
        title = TextClip(text=headline, font_size=36, color='white', font=font).with_duration(duration)
        title = title.with_position(('center', 35))
        layers.append(title)
    
    elif scene_type in ['equation', 'formula']:
        parts = extract_equation_parts(narration)
        layers = render_equation_visual(parts, width, height, duration, theme)
        font = get_font()
        title = TextClip(text=headline, font_size=36, color='white', font=font).with_duration(duration)
        title = title.with_position(('center', 35))
        layers.append(title)
    
    elif scene_type in ['summary', 'recap', 'conclusion']:
        points = extract_steps_from_text(narration)
        layers = render_themed_summary(headline, points, width, height, duration, theme)
    
    else:
        # Default to definition style
        layers = render_themed_definition(headline, narration, width, height, duration, theme)
    
    # Add term bubbles for technical vocabulary
    terms_found = find_terms_in_text(narration)
    if terms_found:
        term_bubbles = create_term_bubbles_overlay(narration, width, height, duration)
        layers.extend(term_bubbles)
        print(f"   💬 Term bubbles: {[t[0] for t in terms_found]}")
    
    return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 TEXT EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_steps_from_text(text: str) -> List[str]:
    """Extract process steps from narration."""
    import re
    
    steps = []
    
    # Pattern 1: Numbered steps
    numbered = re.findall(r'\d+[.)]\s*([^.!?]+)', text)
    if numbered:
        return [s.strip()[:50] for s in numbered if len(s.strip()) > 5][:5]
    
    # Pattern 2: Step words
    step_words = ['first', 'then', 'next', 'after', 'finally', 'lastly']
    sentences = re.split(r'[.!?]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if any(word in sentence.lower() for word in step_words):
            # Clean step
            for word in step_words:
                sentence = re.sub(rf'\b{word}\b,?\s*', '', sentence, flags=re.IGNORECASE)
            if len(sentence) > 5:
                steps.append(sentence[:50])
    
    if steps:
        return steps[:5]
    
    # Fallback: split by punctuation
    parts = re.split(r'[.!?,]', text)
    return [p.strip()[:50] for p in parts if len(p.strip()) > 10][:4]


def extract_items_from_text(text: str) -> List[str]:
    """Extract array items from text."""
    import re
    
    # Look for quoted items
    quoted = re.findall(r"'([^']+)'", text)
    if quoted:
        return quoted[:8]
    
    # Look for comma-separated items
    items = re.findall(r'\b(\d+|[A-Z])\b', text)
    if items:
        return items[:8]
    
    # Default sample
    return ['A', 'B', 'C', 'D', 'E']


def extract_equation_parts(text: str) -> List[Tuple[str, str]]:
    """Extract equation parts from text."""
    parts = []
    text_lower = text.lower()
    
    # Common patterns
    patterns = {
        'sun': ('☀️', 'Sunlight'),
        'light': ('💡', 'Light'),
        'water': ('💧', 'Water'),
        'h2o': ('💧', 'H₂O'),
        'co2': ('💨', 'CO₂'),
        'carbon': ('⚫', 'Carbon'),
        'oxygen': ('🫧', 'O₂'),
        'glucose': ('🍬', 'Glucose'),
        'energy': ('⚡', 'Energy'),
        'input': ('📥', 'Input'),
        'output': ('📤', 'Output'),
        'process': ('⚙️', 'Process'),
    }
    
    for keyword, (icon, label) in patterns.items():
        if keyword in text_lower and label not in [p[1] for p in parts]:
            parts.append((icon, label))
    
    if len(parts) >= 2:
        return parts[:5]
    
    return [('📥', 'Input'), ('⚙️', 'Process'), ('📤', 'Output')]


# ═══════════════════════════════════════════════════════════════════════════════
# 📋 REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

THEMED_RENDERERS = {
    'title': render_themed_title,
    'definition': render_themed_definition,
    'process': render_process_visual,
    'array': render_array_visual,
    'equation': render_equation_visual,
    'summary': render_themed_summary,
}
