"""
🎨 MODERN FRAME RENDERERS
==========================
Dynamic, varied, modern visual renderers for each frame type.

Key principles:
1. Each frame type has its OWN distinct look
2. Colors come from the video's unique palette
3. Layouts are driven by MEANING, not decoration
4. Every video looks different (varied colors, styles)
"""

import os
import re
import math
import random
from typing import Dict, List, Tuple, Any, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip, ImageClip

from smart_video_engine import FrameType, COLOR_PALETTES


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_font():
    """Get available font."""
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/SFNSText.ttf",
        "Helvetica",
        "Arial",
    ]
    for f in fonts:
        if os.path.exists(f):
            return f
    return "Helvetica"


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def truncate(text: str, max_len: int = 50) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def wrap_text(text: str, max_chars: int = 40) -> str:
    """Wrap text into multiple lines."""
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    
    for word in words:
        if current_len + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_len = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)


def get_colors(scene: Dict) -> Dict[str, Tuple]:
    """Extract colors from scene style."""
    if 'style' in scene and 'colors' in scene['style']:
        return scene['style']['colors']
    # Default palette
    return COLOR_PALETTES['minimal']


# ═══════════════════════════════════════════════════════════════════════════════
# 📦 ELEMENT CREATORS - Reusable visual elements
# ═══════════════════════════════════════════════════════════════════════════════

def create_background(width: int, height: int, colors: Dict, duration: float) -> ColorClip:
    """Create solid background."""
    return ColorClip(size=(width, height), color=colors['bg'], duration=duration)


def create_box(
    x: int, y: int, w: int, h: int,
    color: Tuple[int, int, int],
    duration: float,
    style: str = "sharp"  # "sharp", "glow", "outline"
) -> List:
    """Create a box with optional styles."""
    layers = []
    
    if style == "glow":
        # Glow effect - slightly larger, semi-transparent
        glow = ColorClip(size=(w + 8, h + 8), color=color, duration=duration)
        glow = glow.with_opacity(0.3)
        glow = glow.with_position((x - 4, y - 4))
        layers.append(glow)
    
    # Main box
    box = ColorClip(size=(w, h), color=color, duration=duration)
    box = box.with_position((x, y))
    layers.append(box)
    
    if style == "outline":
        # Just outline effect - darker inside
        inner_color = tuple(max(0, c - 80) for c in color)
        inner = ColorClip(size=(w - 4, h - 4), color=inner_color, duration=duration)
        inner = inner.with_position((x + 2, y + 2))
        layers.append(inner)
    
    return layers


def create_text_box(
    text: str,
    x: int, y: int,
    font_size: int,
    text_color: Tuple[int, int, int],
    bg_color: Optional[Tuple[int, int, int]],
    duration: float,
    padding: int = 20,
    min_width: int = 80,
) -> List:
    """Create a text box with background."""
    layers = []
    font = get_font()
    
    # Create text first to measure
    text_clip = TextClip(
        text=text,
        font_size=font_size,
        color=rgb_to_hex(text_color),
        font=font
    ).with_duration(duration)
    
    # Get text dimensions
    tw, th = text_clip.size
    
    # Box dimensions with padding
    box_w = max(min_width, tw + padding * 2)
    box_h = th + padding
    
    # Background box
    if bg_color:
        box = ColorClip(size=(box_w, box_h), color=bg_color, duration=duration)
        box = box.with_position((x, y))
        layers.append(box)
    
    # Center text in box
    text_x = x + (box_w - tw) // 2
    text_y = y + (box_h - th) // 2
    text_clip = text_clip.with_position((text_x, text_y))
    layers.append(text_clip)
    
    return layers


def create_array_boxes(
    items: List,
    start_x: int, y: int,
    box_size: int,
    gap: int,
    colors: Dict,
    duration: float,
    highlight_indices: List[int] = None,
    comparing_indices: List[int] = None,
    sorted_indices: List[int] = None,
) -> List:
    """Create array visualization with boxes."""
    layers = []
    font = get_font()
    
    highlight_indices = highlight_indices or []
    comparing_indices = comparing_indices or []
    sorted_indices = sorted_indices or []
    
    total_width = len(items) * box_size + (len(items) - 1) * gap
    x = start_x
    
    for i, item in enumerate(items):
        # Choose color based on state
        if i in comparing_indices:
            box_color = colors.get('accent', (255, 150, 150))
        elif i in highlight_indices:
            box_color = colors.get('highlight', (255, 220, 100))
        elif i in sorted_indices:
            box_color = colors.get('secondary', (100, 200, 150))
        else:
            box_color = colors.get('muted', (70, 70, 80))
        
        # Box
        box = ColorClip(size=(box_size, box_size), color=box_color, duration=duration)
        box = box.with_position((x, y))
        layers.append(box)
        
        # Text in box
        text_clip = TextClip(
            text=str(item),
            font_size=box_size // 2,
            color='white' if sum(box_color) < 400 else 'black',
            font=font
        ).with_duration(duration)
        
        tw, th = text_clip.size
        text_clip = text_clip.with_position((
            x + (box_size - tw) // 2,
            y + (box_size - th) // 2
        ))
        layers.append(text_clip)
        
        x += box_size + gap
    
    return layers


def create_arrow(
    x1: int, y1: int, x2: int, y2: int,
    color: Tuple[int, int, int],
    duration: float,
    thickness: int = 4
) -> List:
    """Create an arrow between two points."""
    layers = []
    font = get_font()
    
    # Simple arrow using text (→, ↓, ↔, etc.)
    if abs(x2 - x1) > abs(y2 - y1):
        # Horizontal arrow
        arrow_char = "→" if x2 > x1 else "←"
        arrow_x = (x1 + x2) // 2 - 15
        arrow_y = y1 - 15
    else:
        # Vertical arrow
        arrow_char = "↓" if y2 > y1 else "↑"
        arrow_x = x1 - 15
        arrow_y = (y1 + y2) // 2 - 15
    
    arrow = TextClip(
        text=arrow_char,
        font_size=40,
        color=rgb_to_hex(color),
        font=font
    ).with_duration(duration)
    arrow = arrow.with_position((arrow_x, arrow_y))
    layers.append(arrow)
    
    return layers


def create_narrator_bubble(
    text: str,
    width: int, height: int,
    y_pos: int,
    colors: Dict,
    duration: float,
) -> List:
    """Create narrator text in a styled bubble."""
    layers = []
    font = get_font()
    
    # Bubble background
    bubble_w = int(width * 0.9)
    bubble_h = 100
    bubble_x = (width - bubble_w) // 2
    
    # Semi-transparent bubble
    bubble_color = tuple(min(255, c + 30) for c in colors['bg'])
    bubble = ColorClip(size=(bubble_w, bubble_h), color=bubble_color, duration=duration)
    bubble = bubble.with_opacity(0.85)
    bubble = bubble.with_position((bubble_x, y_pos))
    layers.append(bubble)
    
    # Accent line on left
    accent_line = ColorClip(size=(4, bubble_h - 20), color=colors['primary'], duration=duration)
    accent_line = accent_line.with_position((bubble_x + 10, y_pos + 10))
    layers.append(accent_line)
    
    # Narrator text
    wrapped = wrap_text(text, max_chars=60)
    text_clip = TextClip(
        text=wrapped,
        font_size=24,
        color=rgb_to_hex(colors['text']),
        font=font,
        method='caption',
        size=(bubble_w - 40, None)
    ).with_duration(duration)
    text_clip = text_clip.with_position((bubble_x + 25, y_pos + 15))
    layers.append(text_clip)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 FRAME RENDERERS - One for each frame type
# ═══════════════════════════════════════════════════════════════════════════════

def render_title_intro(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    🎬 TITLE / INTRO FRAME
    Big centered title with optional subtitle
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Decorative accent elements
    accent1 = ColorClip(size=(width, 6), color=colors['primary'], duration=duration)
    accent1 = accent1.with_position((0, height // 3 - 50))
    layers.append(accent1)
    
    accent2 = ColorClip(size=(width, 6), color=colors['primary'], duration=duration)
    accent2 = accent2.with_position((0, height * 2 // 3 + 50))
    layers.append(accent2)
    
    # Main title
    title = scene.get('headline', scene.get('topic', 'Title'))
    title_clip = TextClip(
        text=title.upper(),
        font_size=72,
        color=rgb_to_hex(colors['text']),
        font=font,
        stroke_color=rgb_to_hex(colors['primary']),
        stroke_width=2
    ).with_duration(duration)
    title_clip = title_clip.with_position(('center', height // 2 - 60))
    layers.append(title_clip)
    
    # Subtitle
    subtitle = scene.get('subtitle', '')
    if subtitle:
        sub_clip = TextClip(
            text=subtitle,
            font_size=32,
            color=rgb_to_hex(colors['secondary']),
            font=font
        ).with_duration(duration)
        sub_clip = sub_clip.with_position(('center', height // 2 + 40))
        layers.append(sub_clip)
    
    return layers


def render_array_display(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    📊 ARRAY DISPLAY FRAME
    Shows items in boxes: [4] [1] [3] [2]
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Array')
    head_clip = TextClip(
        text=headline,
        font_size=48,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 80))
    layers.append(head_clip)
    
    # Get items
    items = scene.get('numbers', scene.get('items', [4, 1, 3, 2]))
    if not items:
        items = [4, 1, 3, 2]
    
    # Array boxes
    box_size = min(100, (width - 100) // max(len(items), 1) - 20)
    total_w = len(items) * box_size + (len(items) - 1) * 15
    start_x = (width - total_w) // 2
    
    array_layers = create_array_boxes(
        items=items,
        start_x=start_x,
        y=height // 2 - box_size // 2,
        box_size=box_size,
        gap=15,
        colors=colors,
        duration=duration
    )
    layers.extend(array_layers)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_array_highlight(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    🔍 ARRAY HIGHLIGHT FRAME
    Same as array but one item highlighted
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Finding...')
    head_clip = TextClip(
        text=headline,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 80))
    layers.append(head_clip)
    
    # Items
    items = scene.get('numbers', scene.get('items', [4, 1, 3, 2]))
    if not items:
        items = [4, 1, 3, 2]
    
    # Determine highlight
    highlight_pos = scene.get('highlight_pos', 0)
    highlight_type = scene.get('highlight_type', '')
    
    # Auto-detect min/max if specified
    if highlight_type == 'min' and items:
        highlight_pos = items.index(min(items))
    elif highlight_type == 'max' and items:
        highlight_pos = items.index(max(items))
    
    # Array with highlight
    box_size = min(100, (width - 100) // max(len(items), 1) - 20)
    total_w = len(items) * box_size + (len(items) - 1) * 15
    start_x = (width - total_w) // 2
    
    array_layers = create_array_boxes(
        items=items,
        start_x=start_x,
        y=height // 2 - box_size // 2,
        box_size=box_size,
        gap=15,
        colors=colors,
        duration=duration,
        highlight_indices=[highlight_pos]
    )
    layers.extend(array_layers)
    
    # Highlight indicator (arrow pointing down)
    arrow_x = start_x + highlight_pos * (box_size + 15) + box_size // 2 - 15
    arrow_clip = TextClip(
        text="▼",
        font_size=36,
        color=rgb_to_hex(colors['highlight']),
        font=font
    ).with_duration(duration)
    arrow_clip = arrow_clip.with_position((arrow_x, height // 2 - box_size // 2 - 50))
    layers.append(arrow_clip)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_array_compare(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    ⚖️ ARRAY COMPARE FRAME
    Two items being compared with indicators
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Comparing...')
    head_clip = TextClip(
        text=headline,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 80))
    layers.append(head_clip)
    
    # Items
    items = scene.get('numbers', scene.get('items', [4, 1, 3, 2]))
    if not items:
        items = [4, 1, 3, 2]
    
    # Get comparing indices (default: first two)
    comparing = scene.get('comparing', [0, 1])
    
    # Array with comparison highlight
    box_size = min(100, (width - 100) // max(len(items), 1) - 20)
    total_w = len(items) * box_size + (len(items) - 1) * 15
    start_x = (width - total_w) // 2
    
    array_layers = create_array_boxes(
        items=items,
        start_x=start_x,
        y=height // 2 - box_size // 2,
        box_size=box_size,
        gap=15,
        colors=colors,
        duration=duration,
        comparing_indices=comparing
    )
    layers.extend(array_layers)
    
    # Comparison symbol between the two
    if len(comparing) >= 2:
        idx1, idx2 = comparing[0], comparing[1]
        sym_x = start_x + (idx1 + idx2) // 2 * (box_size + 15) + box_size // 2
        sym_clip = TextClip(
            text="⟷",
            font_size=40,
            color=rgb_to_hex(colors['accent']),
            font=font
        ).with_duration(duration)
        sym_clip = sym_clip.with_position((sym_x, height // 2 + box_size // 2 + 20))
        layers.append(sym_clip)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_array_swap(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    🔄 ARRAY SWAP FRAME
    Two items swapping positions
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Swapping!')
    head_clip = TextClip(
        text=headline,
        font_size=48,
        color=rgb_to_hex(colors['highlight']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 80))
    layers.append(head_clip)
    
    # Items
    items = scene.get('numbers', scene.get('items', [4, 1, 3, 2]))
    swap_indices = scene.get('swap', [0, 1])
    
    # Array with swap highlight
    box_size = min(100, (width - 100) // max(len(items), 1) - 20)
    total_w = len(items) * box_size + (len(items) - 1) * 15
    start_x = (width - total_w) // 2
    
    array_layers = create_array_boxes(
        items=items,
        start_x=start_x,
        y=height // 2 - box_size // 2,
        box_size=box_size,
        gap=15,
        colors=colors,
        duration=duration,
        highlight_indices=swap_indices
    )
    layers.extend(array_layers)
    
    # Swap arrows
    if len(swap_indices) >= 2:
        idx1, idx2 = swap_indices[0], swap_indices[1]
        arrow_y = height // 2 - box_size // 2 - 40
        
        # Curved swap indicator
        swap_text = TextClip(
            text="⇄",
            font_size=50,
            color=rgb_to_hex(colors['highlight']),
            font=font
        ).with_duration(duration)
        
        mid_x = start_x + (idx1 + idx2) * (box_size + 15) // 2 + box_size // 2 - 15
        swap_text = swap_text.with_position((mid_x, arrow_y))
        layers.append(swap_text)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_array_result(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    ✅ ARRAY RESULT FRAME
    Final sorted/processed array with checkmark
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Success indicator
    check_clip = TextClip(
        text="✓",
        font_size=80,
        color=rgb_to_hex(colors['secondary']),
        font=font
    ).with_duration(duration)
    check_clip = check_clip.with_position(('center', 60))
    layers.append(check_clip)
    
    # Headline
    headline = scene.get('headline', 'Sorted!')
    head_clip = TextClip(
        text=headline,
        font_size=48,
        color=rgb_to_hex(colors['secondary']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 140))
    layers.append(head_clip)
    
    # Items (all marked as sorted)
    items = scene.get('numbers', scene.get('items', [1, 2, 3, 4]))
    
    box_size = min(100, (width - 100) // max(len(items), 1) - 20)
    total_w = len(items) * box_size + (len(items) - 1) * 15
    start_x = (width - total_w) // 2
    
    array_layers = create_array_boxes(
        items=items,
        start_x=start_x,
        y=height // 2 - box_size // 2 + 30,
        box_size=box_size,
        gap=15,
        colors=colors,
        duration=duration,
        sorted_indices=list(range(len(items)))
    )
    layers.extend(array_layers)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_process_flow(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    ➡️ PROCESS FLOW FRAME
    Input → Process → Output
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'How It Works')
    head_clip = TextClip(
        text=headline,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 80))
    layers.append(head_clip)
    
    # Process boxes
    steps = scene.get('steps', scene.get('items', ['Input', 'Process', 'Output']))
    # Guarantee at least two steps for process scenes
    if not steps or len(steps) < 2:
        steps = ['Step 1', 'Step 2']
    
    box_w = min(200, (width - 150) // max(len(steps), 1))
    box_h = 80
    total_w = len(steps) * box_w + (len(steps) - 1) * 60
    start_x = (width - total_w) // 2
    y = height // 2 - box_h // 2
    
    for i, step in enumerate(steps[:5]):  # Max 5 steps
        x = start_x + i * (box_w + 60)
        
        # Box
        box_color = colors['primary'] if i == len(steps) // 2 else colors['muted']
        box = ColorClip(size=(box_w, box_h), color=box_color, duration=duration)
        box = box.with_position((x, y))
        layers.append(box)
        
        # Text
        text_clip = TextClip(
            text=truncate(str(step), 15),
            font_size=24,
            color='white',
            font=font
        ).with_duration(duration)
        tw, th = text_clip.size
        text_clip = text_clip.with_position((x + (box_w - tw) // 2, y + (box_h - th) // 2))
        layers.append(text_clip)
        
        # Arrow to next
        if i < len(steps) - 1:
            arrow = TextClip(
                text="→",
                font_size=40,
                color=rgb_to_hex(colors['secondary']),
                font=font
            ).with_duration(duration)
            arrow = arrow.with_position((x + box_w + 15, y + box_h // 2 - 20))
            layers.append(arrow)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_split_compare(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    ⚔️ SPLIT COMPARE FRAME
    Left vs Right comparison
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Comparison')
    head_clip = TextClip(
        text=headline,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 60))
    layers.append(head_clip)
    
    # Divider line
    divider = ColorClip(size=(4, height - 250), color=colors['muted'], duration=duration)
    divider = divider.with_position((width // 2 - 2, 130))
    layers.append(divider)
    
    # VS badge
    vs_clip = TextClip(
        text="VS",
        font_size=32,
        color=rgb_to_hex(colors['accent']),
        font=font
    ).with_duration(duration)
    vs_clip = vs_clip.with_position(('center', height // 2 - 20))
    layers.append(vs_clip)
    
    # Left side
    left_text = scene.get('left', 'Option A')
    left_clip = TextClip(
        text=wrap_text(left_text, 20),
        font_size=36,
        color=rgb_to_hex(colors['primary']),
        font=font,
        method='caption',
        size=(width // 2 - 60, None)
    ).with_duration(duration)
    left_clip = left_clip.with_position((40, height // 2 - 80))
    layers.append(left_clip)
    
    # Right side
    right_text = scene.get('right', 'Option B')
    right_clip = TextClip(
        text=wrap_text(right_text, 20),
        font_size=36,
        color=rgb_to_hex(colors['secondary']),
        font=font,
        method='caption',
        size=(width // 2 - 60, None)
    ).with_duration(duration)
    right_clip = right_clip.with_position((width // 2 + 30, height // 2 - 80))
    layers.append(right_clip)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_big_statement(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    💬 BIG STATEMENT FRAME
    One important statement, big and centered
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Decorative quotes
    quote_clip = TextClip(
        text='"',
        font_size=150,
        color=rgb_to_hex(colors['primary']),
        font=font
    ).with_duration(duration)
    quote_clip = quote_clip.with_opacity(0.3)
    quote_clip = quote_clip.with_position((50, height // 4))
    layers.append(quote_clip)
    
    # Main statement
    statement = scene.get('headline', scene.get('narration', 'Key Point'))
    wrapped = wrap_text(statement, 30)
    
    stat_clip = TextClip(
        text=wrapped,
        font_size=52,
        color=rgb_to_hex(colors['text']),
        font=font,
        method='caption',
        size=(width - 120, None)
    ).with_duration(duration)
    stat_clip = stat_clip.with_position(('center', 'center'))
    layers.append(stat_clip)
    
    # Accent underline
    underline = ColorClip(size=(200, 4), color=colors['primary'], duration=duration)
    underline = underline.with_position(('center', height * 3 // 4))
    layers.append(underline)
    
    return layers


def render_definition(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    📖 DEFINITION FRAME
    Term: Definition format
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Term
    term = scene.get('term', scene.get('headline', 'Term'))
    term_clip = TextClip(
        text=term,
        font_size=56,
        color=rgb_to_hex(colors['primary']),
        font=font
    ).with_duration(duration)
    term_clip = term_clip.with_position(('center', height // 3 - 40))
    layers.append(term_clip)
    
    # Separator line
    sep = ColorClip(size=(300, 3), color=colors['secondary'], duration=duration)
    sep = sep.with_position(('center', height // 3 + 30))
    layers.append(sep)
    
    # Definition
    definition = scene.get('definition', scene.get('narration', 'Definition here'))
    wrapped = wrap_text(definition, 45)
    
    def_clip = TextClip(
        text=wrapped,
        font_size=32,
        color=rgb_to_hex(colors['text']),
        font=font,
        method='caption',
        size=(width - 100, None)
    ).with_duration(duration)
    def_clip = def_clip.with_position(('center', height // 2 + 20))
    layers.append(def_clip)
    
    return layers


def render_stats_number(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    📊 STATS NUMBER FRAME
    Big number with context
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Extract number from text
    narration = scene.get('narration', '')
    numbers = scene.get('numbers', [])
    
    if numbers:
        big_num = str(numbers[0])
    else:
        # Try to extract from narration
        num_match = re.search(r'(\d+(?:\.\d+)?%?)', narration)
        big_num = num_match.group(1) if num_match else "100"
    
    # Big number
    num_clip = TextClip(
        text=big_num,
        font_size=120,
        color=rgb_to_hex(colors['highlight']),
        font=font
    ).with_duration(duration)
    num_clip = num_clip.with_position(('center', height // 2 - 80))
    layers.append(num_clip)
    
    # Context text
    context = scene.get('headline', 'Key Statistic')
    ctx_clip = TextClip(
        text=context,
        font_size=36,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    ctx_clip = ctx_clip.with_position(('center', height // 2 + 60))
    layers.append(ctx_clip)
    
    # Narrator
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_summary(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    📋 SUMMARY FRAME
    Wrap up / conclusion
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Summary icon
    icon_clip = TextClip(
        text="📋",
        font_size=60,
        font=font
    ).with_duration(duration)
    icon_clip = icon_clip.with_position(('center', 80))
    layers.append(icon_clip)
    
    # "In Summary" label
    label_clip = TextClip(
        text="KEY TAKEAWAY",
        font_size=28,
        color=rgb_to_hex(colors['secondary']),
        font=font
    ).with_duration(duration)
    label_clip = label_clip.with_position(('center', 160))
    layers.append(label_clip)
    
    # Summary text
    summary = scene.get('headline', scene.get('narration', 'Summary'))
    wrapped = wrap_text(summary, 40)
    
    sum_clip = TextClip(
        text=wrapped,
        font_size=40,
        color=rgb_to_hex(colors['text']),
        font=font,
        method='caption',
        size=(width - 80, None)
    ).with_duration(duration)
    sum_clip = sum_clip.with_position(('center', height // 2))
    layers.append(sum_clip)
    
    # Accent lines
    line1 = ColorClip(size=(100, 4), color=colors['primary'], duration=duration)
    line1 = line1.with_position((width // 4 - 50, height - 100))
    layers.append(line1)
    
    line2 = ColorClip(size=(100, 4), color=colors['primary'], duration=duration)
    line2 = line2.with_position((width * 3 // 4 - 50, height - 100))
    layers.append(line2)
    
    return layers


def render_hierarchy(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    🌳 HIERARCHY FRAME
    Parent → Children structure
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Parent
    parent = scene.get('headline', 'Category')
    parent_box_layers = create_text_box(
        parent, width // 2 - 100, 100, 36,
        colors['text'], colors['primary'], duration, padding=25, min_width=200
    )
    layers.extend(parent_box_layers)
    
    # Children
    children = scene.get('items', scene.get('list_items', ['Type A', 'Type B', 'Type C']))
    if not children:
        children = ['Type A', 'Type B', 'Type C']
    
    num_children = min(len(children), 4)
    child_w = min(150, (width - 80) // num_children - 20)
    total_child_w = num_children * child_w + (num_children - 1) * 20
    start_x = (width - total_child_w) // 2
    
    for i, child in enumerate(children[:4]):
        x = start_x + i * (child_w + 20)
        
        # Connection line
        line = ColorClip(size=(2, 60), color=colors['muted'], duration=duration)
        line = line.with_position((x + child_w // 2, 200))
        layers.append(line)
        
        # Child box
        child_box = ColorClip(size=(child_w, 70), color=colors['muted'], duration=duration)
        child_box = child_box.with_position((x, 270))
        layers.append(child_box)
        
        # Child text
        child_clip = TextClip(
            text=truncate(str(child), 12),
            font_size=22,
            color='white',
            font=font
        ).with_duration(duration)
        tw, th = child_clip.size
        child_clip = child_clip.with_position((x + (child_w - tw) // 2, 285))
        layers.append(child_clip)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_question(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    ❓ QUESTION FRAME
    Posing a question
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Question mark
    q_clip = TextClip(
        text="?",
        font_size=150,
        color=rgb_to_hex(colors['accent']),
        font=font
    ).with_duration(duration)
    q_clip = q_clip.with_position(('center', 100))
    layers.append(q_clip)
    
    # Question text
    question = scene.get('headline', scene.get('narration', 'What do you think?'))
    wrapped = wrap_text(question, 35)
    
    q_text = TextClip(
        text=wrapped,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font,
        method='caption',
        size=(width - 80, None)
    ).with_duration(duration)
    q_text = q_text.with_position(('center', height // 2 + 50))
    layers.append(q_text)
    
    return layers


def render_timeline(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    📅 TIMELINE FRAME
    Sequential events
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Timeline')
    head_clip = TextClip(
        text=headline,
        font_size=44,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 60))
    layers.append(head_clip)
    
    # Timeline line
    line = ColorClip(size=(width - 100, 4), color=colors['muted'], duration=duration)
    line = line.with_position((50, height // 2))
    layers.append(line)
    
    # Events
    events = scene.get('items', scene.get('steps', ['Step 1', 'Step 2', 'Step 3']))
    if not events:
        events = ['Step 1', 'Step 2', 'Step 3']
    
    num_events = min(len(events), 5)
    spacing = (width - 100) // max(num_events, 1)
    
    for i, event in enumerate(events[:5]):
        x = 50 + i * spacing + spacing // 2
        
        # Dot
        dot = ColorClip(size=(20, 20), color=colors['primary'], duration=duration)
        dot = dot.with_position((x - 10, height // 2 - 10))
        layers.append(dot)
        
        # Event text (alternating above/below)
        event_clip = TextClip(
            text=truncate(str(event), 15),
            font_size=22,
            color=rgb_to_hex(colors['text']),
            font=font
        ).with_duration(duration)
        
        if i % 2 == 0:
            event_clip = event_clip.with_position((x - 50, height // 2 - 60))
        else:
            event_clip = event_clip.with_position((x - 50, height // 2 + 30))
        
        layers.append(event_clip)
    
    # Narrator
    narration = scene.get('narration', '')
    if narration:
        narrator_layers = create_narrator_bubble(
            narration, width, height, height - 130, colors, duration
        )
        layers.extend(narrator_layers)
    
    return layers


def render_code_block(scene: Dict, width: int, height: int, duration: float) -> List:
    """
    💻 CODE BLOCK FRAME
    Code/formula display
    """
    layers = []
    colors = get_colors(scene)
    font = get_font()
    
    # Background
    layers.append(create_background(width, height, colors, duration))
    
    # Headline
    headline = scene.get('headline', 'Code')
    head_clip = TextClip(
        text=headline,
        font_size=36,
        color=rgb_to_hex(colors['text']),
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', 60))
    layers.append(head_clip)
    
    # Code box background
    code_box = ColorClip(size=(width - 60, 300), color=(30, 30, 40), duration=duration)
    code_box = code_box.with_position((30, 130))
    layers.append(code_box)
    
    # Code text
    code = scene.get('code', scene.get('narration', 'function example() {\n  return true;\n}'))
    
    code_clip = TextClip(
        text=code[:500],  # Limit length
        font_size=24,
        color='#00FF88',
        font=font,
        method='caption',
        size=(width - 100, None)
    ).with_duration(duration)
    code_clip = code_clip.with_position((50, 150))
    layers.append(code_clip)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 RENDERER DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

FRAME_RENDERERS = {
    'array_display': render_array_display,
    'array_highlight': render_array_highlight,
    'array_compare': render_array_compare,
    'array_swap': render_array_swap,
    'array_result': render_array_result,
    'process_flow': render_process_flow,
    'process_step': render_process_flow,  # Same visual
    'process_branch': render_split_compare,  # Use comparison
    'split_compare': render_split_compare,
    'before_after': render_split_compare,
    'big_statement': render_big_statement,
    'definition': render_definition,
    'code_block': render_code_block,
    'hierarchy': render_hierarchy,
    'timeline': render_timeline,
    'grid_items': render_array_display,  # Similar
    'title_intro': render_title_intro,
    'summary': render_summary,
    'question': render_question,
    'stats_number': render_stats_number,
    'icon_explain': render_big_statement,
}


def render_frame(scene: Dict, width: int, height: int) -> CompositeVideoClip:
    """
    Main entry point - render a scene into a video clip.
    
    Args:
        scene: Scene dictionary with frame_type, style, content
        width: Video width
        height: Video height
    
    Returns:
        CompositeVideoClip ready for concatenation
    """
    frame_type = scene.get('frame_type', 'big_statement')
    duration = scene.get('duration', 4.0)
    
    # Get appropriate renderer
    renderer = FRAME_RENDERERS.get(frame_type, render_big_statement)
    
    print(f"   🎨 Rendering: {frame_type.upper()} ({duration:.1f}s)")
    
    try:
        layers = renderer(scene, width, height, duration)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
    except Exception as e:
        print(f"   ⚠️ Render error: {e}, using fallback")
        layers = render_big_statement(scene, width, height, duration)
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)


def render_all_scenes(scenes: List[Dict], width: int = 1080, height: int = 1920) -> List[CompositeVideoClip]:
    """
    Render all scenes into video clips.
    
    Args:
        scenes: List of scene dictionaries
        width: Video width (default 1080 for vertical)
        height: Video height (default 1920 for vertical)
    
    Returns:
        List of CompositeVideoClips
    """
    clips = []
    
    for i, scene in enumerate(scenes):
        print(f"\n🎬 Scene {i + 1}/{len(scenes)}")
        clip = render_frame(scene, width, height)
        clips.append(clip)
    
    return clips
