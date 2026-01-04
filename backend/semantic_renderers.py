"""
🎬 SEMANTIC FRAME RENDERERS
============================
This module contains MoviePy-based rendering functions for each layout type.

Each renderer takes scene data and creates a list of MoviePy clips that
compose the visual frame according to the layout's visual grammar.

ENHANCED FEATURES:
- Bubble Sort style array visualizations
- Speech bubble styled narrator text
- Polished visual design with rounded corners feel
- Step indicators with progress bars
"""

import os
import math
from typing import Dict, List, Tuple, Any, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip, ImageClip
from semantic_framing import (
    LayoutType, 
    get_layout_info, 
    get_all_zones_pixels,
    ACCENT_COLORS,
    get_suggested_accent,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ENHANCED CONSTANTS & COLORS
# ═══════════════════════════════════════════════════════════════════════════════

DARK_BG = (14, 14, 14)  # #0E0E0E
CARD_BG = (28, 28, 35)  # Slightly lighter for cards
BUBBLE_BG = (40, 44, 52)  # Speech bubble background
NARRATOR_BG = (25, 28, 36)  # Narrator box background

# Box colors for array visualization (like the Bubble Sort image)
ARRAY_BOX_COLOR = (130, 170, 210)  # Light blue like in the image
ARRAY_BOX_HIGHLIGHT = (255, 200, 100)  # Yellow/orange for active
ARRAY_BOX_SORTED = (100, 200, 150)  # Green for sorted
ARRAY_BOX_COMPARING = (255, 150, 150)  # Red for comparing/swapping

# Font paths (macOS)
FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
]

def get_font():
    """Get available font path"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            return path
    return "Helvetica"


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ENHANCED UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def wrap_text_smart(text: str, max_width: int, font_size: int) -> str:
    """Smart text wrapping based on approximate character width"""
    if not text:
        return ""
    
    # Approximate characters per line based on font size
    chars_per_pixel = 0.5 / font_size * 12
    max_chars = int(max_width * chars_per_pixel)
    max_chars = max(max_chars, 20)  # Minimum 20 chars per line
    
    words = str(text).split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line = (current_line + " " + word).strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = word[:max_chars] if len(word) > max_chars else word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines[:4])  # Max 4 lines


def wrap_text(text: str, max_chars: int = 25) -> str:
    """Wrap text to fit within boxes"""
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
    return "\n".join(lines[:4])


def truncate_text(text: str, max_chars: int = 40) -> str:
    """Truncate text with ellipsis"""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."


def get_accent_color(scene: Dict, default: str = 'green') -> Tuple[int, int, int]:
    """Get accent color from scene or default"""
    color_name = scene.get('accent_color', default).lower()
    return ACCENT_COLORS.get(color_name, ACCENT_COLORS['green'])


def create_safe_image_clip(image_path: str, target_width: int, target_height: int, duration: float):
    """Safely create an ImageClip with proper sizing"""
    try:
        if image_path and os.path.exists(image_path):
            img_clip = ImageClip(image_path).with_duration(duration)
            img_clip = img_clip.resized(width=target_width)
            return img_clip
    except Exception as e:
        print(f"   ⚠️ Error creating image clip: {e}")
    return None


def create_narrator_box(narration: str, width: int, height: int, duration: float,
                        y_position: int, accent_color: Tuple = None) -> List:
    """
    Create a professional narrator text box at the bottom of the screen
    with speech bubble styling
    """
    font = get_font()
    layers = []
    
    if not narration:
        return layers
    
    accent = accent_color or ACCENT_COLORS.get('teal', (78, 205, 196))
    
    # Wrap text properly
    max_chars_per_line = 42
    wrapped = wrap_text_smart(narration, max_chars_per_line * 12, 30)
    num_lines = min(wrapped.count('\n') + 1, 4)
    box_height = num_lines * 42 + 40
    
    # Main narrator container (dark with gradient feel)
    narrator_bg = ColorClip(
        size=(int(width * 0.92), box_height),
        color=NARRATOR_BG,
        duration=duration
    )
    narrator_bg = narrator_bg.with_position(('center', y_position))
    layers.append(narrator_bg)
    
    # Top accent line
    accent_line = ColorClip(
        size=(int(width * 0.92), 3),
        color=accent,
        duration=duration
    )
    accent_line = accent_line.with_position(('center', y_position))
    layers.append(accent_line)
    
    # Left quote mark (using regular quote)
    quote_clip = TextClip(
        text='"',
        font_size=50,
        color='#555555',
        font=font
    ).with_duration(duration)
    quote_clip = quote_clip.with_position((int(width * 0.06), y_position + 5))
    layers.append(quote_clip)
    
    # Narrator text
    narrator_text = TextClip(
        text=wrapped,
        font_size=32,
        color='#E0E0E0',
        font=font,
        method='caption',
        size=(int(width * 0.82), None)
    ).with_duration(duration)
    narrator_text = narrator_text.with_position(('center', y_position + 20))
    layers.append(narrator_text)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🔢 ARRAY VISUALIZATION (Bubble Sort Style)
# ═══════════════════════════════════════════════════════════════════════════════

def render_array_visualization(scene: Dict, width: int, height: int, duration: float,
                               fetch_image_fn=None) -> List:
    """
    📊 ARRAY VISUALIZATION FRAME (Like Bubble Sort image)
    
    Creates a visual like the attached image showing:
    - Array boxes with numbers
    - Highlighted elements being compared/swapped
    - Arrows showing movement
    - Step progress indicator
    
    ┌──────────────────────────────────────┐
    │          BUBBLE SORT                 │
    ├──────────────────────────────────────┤
    │              ╭───╮                   │
    │          2 ← │ 5 │ → 2               │  ← Swap indicator
    │              ╰───╯                   │
    │  ┌───┬───┬───┬───┬───┬───┐          │
    │  │ 5 │ 2 │ 4 │ 1 │ 3 │ 6 │          │  ← Array boxes
    │  └───┴───┴───┴───┴───┴───┘          │
    │  ○───────○───────○───────○          │  ← Steps progress
    │           Steps                      │
    ├──────────────────────────────────────┤
    │  💬 "Narrator text in speech bubble" │
    └──────────────────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'teal')
    
    headline = scene.get('headline', 'ARRAY')
    narration = scene.get('narration', '')
    
    # Get array data
    array_data = scene.get('array_data', scene.get('array_state', [5, 2, 4, 1, 3, 6]))
    if isinstance(array_data, str):
        try:
            import json
            array_data = json.loads(array_data)
        except:
            array_data = [5, 2, 4, 1, 3, 6]
    
    highlight_indices = scene.get('highlight_indices', [])
    compare_indices = scene.get('compare_indices', [])
    swap_indices = scene.get('swap_indices', [])
    sorted_indices = scene.get('sorted_indices', [])
    current_step = scene.get('current_step', 1)
    total_steps = scene.get('total_steps', 4)
    
    # === HEADLINE ===
    head_clip = TextClip(
        text=headline,
        font_size=65,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', int(height * 0.06)))
    layers.append(head_clip)
    
    # Underline
    underline = ColorClip(
        size=(min(len(headline) * 38, int(width * 0.6)), 4),
        color=accent,
        duration=duration
    )
    underline = underline.with_position(('center', int(height * 0.12)))
    layers.append(underline)
    
    # === ARRAY BOXES (Main visualization) ===
    num_elements = len(array_data)
    box_size = min(100, (width - 120) // max(num_elements, 1) - 15)
    total_array_width = num_elements * (box_size + 12) - 12
    start_x = (width - total_array_width) // 2
    array_y = int(height * 0.32)
    
    # Draw swap indicator if swapping
    if swap_indices and len(swap_indices) >= 2:
        swap_idx = swap_indices[0]
        if swap_idx < num_elements:
            swap_x = start_x + swap_idx * (box_size + 12) + box_size // 2
            
            # Elevated box showing swap
            elevated_box = ColorClip(
                size=(box_size - 10, box_size - 10),
                color=ARRAY_BOX_HIGHLIGHT,
                duration=duration
            )
            elevated_box = elevated_box.with_position((swap_x - box_size // 2 + 5, array_y - 80))
            layers.append(elevated_box)
            
            # Number in elevated box
            elevated_num = TextClip(
                text=str(array_data[swap_idx]),
                font_size=int(box_size * 0.45),
                color='#333333',
                font=font
            ).with_duration(duration)
            elevated_num = elevated_num.with_position((swap_x - 12, array_y - 70))
            layers.append(elevated_num)
            
            # Curved arrows (simplified with text arrows)
            left_arrow = TextClip(
                text="↙",
                font_size=35,
                color='#666666',
                font=font
            ).with_duration(duration)
            left_arrow = left_arrow.with_position((swap_x - 60, array_y - 50))
            layers.append(left_arrow)
            
            right_arrow = TextClip(
                text="↘",
                font_size=35,
                color='#666666',
                font=font
            ).with_duration(duration)
            right_arrow = right_arrow.with_position((swap_x + 25, array_y - 50))
            layers.append(right_arrow)
    
    # Draw array boxes
    for idx, num in enumerate(array_data):
        x_pos = start_x + idx * (box_size + 12)
        
        # Determine box color based on state
        if idx in swap_indices:
            box_color = ARRAY_BOX_COMPARING  # Red for swapping
        elif idx in compare_indices:
            box_color = ARRAY_BOX_HIGHLIGHT  # Yellow for comparing
        elif idx in sorted_indices:
            box_color = ARRAY_BOX_SORTED  # Green for sorted
        elif idx in highlight_indices:
            box_color = ARRAY_BOX_HIGHLIGHT
        else:
            box_color = ARRAY_BOX_COLOR  # Default light blue
        
        # Box shadow (creates depth)
        shadow = ColorClip(
            size=(box_size, box_size),
            color=(box_color[0] - 40, box_color[1] - 40, box_color[2] - 40),
            duration=duration
        )
        shadow = shadow.with_position((x_pos + 4, array_y + 4))
        layers.append(shadow)
        
        # Main box
        box = ColorClip(
            size=(box_size, box_size),
            color=box_color,
            duration=duration
        )
        box = box.with_position((x_pos, array_y))
        layers.append(box)
        
        # Number inside box
        text_color = '#FFFFFF' if idx in (swap_indices + compare_indices) else '#333333'
        num_clip = TextClip(
            text=str(num),
            font_size=int(box_size * 0.55),
            color=text_color,
            font=font
        ).with_duration(duration)
        # Center the number in the box
        num_clip = num_clip.with_position((x_pos + box_size // 3, array_y + box_size // 4))
        layers.append(num_clip)
    
    # === STEPS PROGRESS INDICATOR ===
    progress_y = array_y + box_size + 50
    progress_width = int(width * 0.7)
    progress_start_x = (width - progress_width) // 2
    
    # Progress line
    progress_line = ColorClip(
        size=(progress_width, 2),
        color=(80, 80, 100),
        duration=duration
    )
    progress_line = progress_line.with_position((progress_start_x, progress_y + 8))
    layers.append(progress_line)
    
    # Progress dots
    num_dots = min(total_steps, 6)
    dot_spacing = progress_width // max(num_dots - 1, 1) if num_dots > 1 else 0
    
    for i in range(num_dots):
        dot_x = progress_start_x + i * dot_spacing - 6
        dot_color = accent if i < current_step else (60, 60, 80)
        dot_size = 16 if i < current_step else 12
        
        dot = ColorClip(
            size=(dot_size, dot_size),
            color=dot_color,
            duration=duration
        )
        dot = dot.with_position((dot_x, progress_y + 8 - dot_size // 2 + 1))
        layers.append(dot)
    
    # "Steps" label
    steps_label = TextClip(
        text="Steps",
        font_size=24,
        color='#888888',
        font=font
    ).with_duration(duration)
    steps_label = steps_label.with_position(('center', progress_y + 25))
    layers.append(steps_label)
    
    # === NARRATOR BOX (Speech bubble style) ===
    if narration:
        narrator_y = int(height * 0.62)
        narrator_layers = create_narrator_box(
            narration, width, height, duration, narrator_y, accent
        )
        layers.extend(narrator_layers)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 ENHANCED FRAME RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_list_array(scene: Dict, width: int, height: int, duration: float,
                      fetch_image_fn=None) -> List:
    """
    📋 LIST / ARRAY FRAME
    
    Visual: Vertical stacked items with bullets
    Use when: Listing items, features, advantages, types
    
    ┌──────────────────────────┐
    │      HEADLINE            │
    ├──────────────────────────┤
    │ ● [ Item 1             ] │
    │ ● [ Item 2             ] │
    │ ● [ Item 3             ] │
    │ ● [ Item 4             ] │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'teal')
    zones = get_all_zones_pixels(LayoutType.LIST_ARRAY, width, height)
    
    headline = scene.get('headline', 'LIST')
    narration = scene.get('narration', '')
    items = scene.get('list_items', scene.get('visual_elements', []))
    
    # If no items, try to extract from narration
    if not items:
        items = [narration[:50]] if narration else ['Item 1', 'Item 2', 'Item 3']
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 25),
        font_size=60,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 20))
    layers.append(head_clip)
    
    # === LIST ITEMS ===
    items_zone = zones['items']
    y_start = items_zone['y']
    item_height = min(90, items_zone['height'] // max(len(items[:6]), 1))
    
    for idx, item in enumerate(items[:6]):  # Max 6 items
        y_pos = y_start + idx * item_height
        
        # Item background box
        item_box = ColorClip(
            size=(int(width * 0.84), item_height - 10),
            color=(30, 30, 40),
            duration=duration
        )
        item_box = item_box.with_position((int(width * 0.08), y_pos))
        layers.append(item_box)
        
        # Bullet/number
        bullet_text = f"{idx + 1}"
        bullet = TextClip(
            text=bullet_text,
            font_size=32,
            color=accent,
            font=font
        ).with_duration(duration)
        bullet = bullet.with_position((int(width * 0.10), y_pos + 15))
        layers.append(bullet)
        
        # Item text
        item_text = TextClip(
            text=truncate_text(str(item), 35),
            font_size=32,
            color='white',
            font=font
        ).with_duration(duration)
        item_text = item_text.with_position((int(width * 0.18), y_pos + 18))
        layers.append(item_text)
        
        # Accent bar on left
        accent_bar = ColorClip(
            size=(4, item_height - 15),
            color=accent,
            duration=duration
        )
        accent_bar = accent_bar.with_position((int(width * 0.08), y_pos + 3))
        layers.append(accent_bar)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_process_flow(scene: Dict, width: int, height: int, duration: float,
                        fetch_image_fn=None) -> List:
    """
    ⚙️ PROCESS / FLOW FRAME
    
    Visual: Boxes connected with arrows
    Use when: Showing steps, workflows, pipelines
    
    ┌──────────────────────────┐
    │      HEADLINE            │
    ├──────────────────────────┤
    │  ┌───┐       ┌───┐       │
    │  │ 1 │   →   │ 2 │       │
    │  └───┘       └───┘       │
    │    ↓           ↓         │
    │  ┌───┐       ┌───┐       │
    │  │ 3 │   →   │ 4 │       │
    │  └───┘       └───┘       │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'green')
    zones = get_all_zones_pixels(LayoutType.PROCESS_FLOW, width, height)
    
    headline = scene.get('headline', 'PROCESS')
    narration = scene.get('narration', '')
    
    # Get steps from various sources
    flow_nodes = scene.get('flow_nodes', [])
    steps = scene.get('steps', [])
    if flow_nodes:
        steps = [n.get('text', f'Step {i+1}') for i, n in enumerate(flow_nodes)]
    # Guarantee at least two steps for process scenes
    if not steps or len(steps) < 2:
        # Try to use flow_nodes if available
        if flow_nodes and len(flow_nodes) >= 2:
            steps = [n.get('text', f'Step {i+1}') for i, n in enumerate(flow_nodes[:2])]
        else:
            # Fallback: always at least two steps
            steps = ['Step 1', 'Step 2']
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 20),
        font_size=55,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === FLOW BOXES ===
    flow_zone = zones['flow']
    num_steps = min(len(steps), 5)
    
    # Determine layout: 2 columns if > 3 steps, else vertical
    if num_steps <= 3:
        # Vertical layout
        box_size = 100
        y_start = flow_zone['y'] + 20
        step_spacing = (flow_zone['height'] - 40) // max(num_steps, 1)
        
        for idx, step in enumerate(steps[:3]):
            y_pos = y_start + idx * step_spacing
            x_pos = width // 2 - box_size // 2
            
            # Step box
            step_box = ColorClip(
                size=(int(width * 0.75), box_size - 20),
                color=(40, 40, 55),
                duration=duration
            )
            step_box = step_box.with_position((int(width * 0.125), y_pos))
            layers.append(step_box)
            
            # Step number circle
            num_circle = ColorClip(
                size=(50, 50),
                color=accent,
                duration=duration
            )
            num_circle = num_circle.with_position((int(width * 0.14), y_pos + 12))
            layers.append(num_circle)
            
            # Step number
            num_text = TextClip(
                text=str(idx + 1),
                font_size=28,
                color='white',
                font=font
            ).with_duration(duration)
            num_text = num_text.with_position((int(width * 0.155), y_pos + 20))
            layers.append(num_text)
            
            # Step text
            step_text = TextClip(
                text=truncate_text(str(step), 30),
                font_size=30,
                color='white',
                font=font
            ).with_duration(duration)
            step_text = step_text.with_position((int(width * 0.24), y_pos + 22))
            layers.append(step_text)
            
            # Arrow to next
            if idx < num_steps - 1:
                arrow = TextClip(
                    text="↓",
                    font_size=40,
                    color=accent,
                    font=font
                ).with_duration(duration)
                arrow = arrow.with_position(('center', y_pos + box_size - 10))
                layers.append(arrow)
    else:
        # 2x2 or 2x3 grid layout
        box_w = int(width * 0.40)
        box_h = 80
        gap_x = int(width * 0.06)
        gap_y = 30
        
        start_x = int(width * 0.07)
        start_y = flow_zone['y'] + 10
        
        positions = [
            (start_x, start_y),
            (start_x + box_w + gap_x, start_y),
            (start_x, start_y + box_h + gap_y),
            (start_x + box_w + gap_x, start_y + box_h + gap_y),
            (start_x, start_y + 2 * (box_h + gap_y)),
        ]
        
        for idx, step in enumerate(steps[:5]):
            x_pos, y_pos = positions[idx]
            
            # Box
            step_box = ColorClip(
                size=(box_w, box_h),
                color=(40, 40, 55),
                duration=duration
            )
            step_box = step_box.with_position((x_pos, y_pos))
            layers.append(step_box)
            
            # Number badge
            num_badge = ColorClip(
                size=(35, 35),
                color=accent,
                duration=duration
            )
            num_badge = num_badge.with_position((x_pos + 8, y_pos + 8))
            layers.append(num_badge)
            
            num_text = TextClip(
                text=str(idx + 1),
                font_size=22,
                color='white',
                font=font
            ).with_duration(duration)
            num_text = num_text.with_position((x_pos + 18, y_pos + 12))
            layers.append(num_text)
            
            # Step text
            step_text = TextClip(
                text=truncate_text(str(step), 20),
                font_size=26,
                color='white',
                font=font
            ).with_duration(duration)
            step_text = step_text.with_position((x_pos + 50, y_pos + 28))
            layers.append(step_text)
        
        # Arrows between boxes
        arrow_positions = [
            (start_x + box_w + 5, start_y + box_h // 2 - 10, "→"),
            (start_x + box_w // 2, start_y + box_h + 2, "↓"),
            (start_x + box_w + gap_x + box_w // 2, start_y + box_h + 2, "↓"),
        ]
        for ax, ay, arrow_char in arrow_positions[:min(len(steps)-1, 3)]:
            arrow = TextClip(
                text=arrow_char,
                font_size=30,
                color=accent,
                font=font
            ).with_duration(duration)
            arrow = arrow.with_position((ax, ay))
            layers.append(arrow)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_comparison(scene: Dict, width: int, height: int, duration: float,
                      fetch_image_fn=None) -> List:
    """
    ⚖️ COMPARISON FRAME
    
    Visual: Side-by-side panels with contrasting colors
    Use when: Comparing options, A vs B, pros vs cons
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├────────────┬─────────────┤
    │   OPTION A │   OPTION B  │
    │ ──────────-│-─────────── │
    │ • Point 1  │ • Point 1   │
    │ • Point 2  │ • Point 2   │
    │ • Point 3  │ • Point 3   │
    ├────────────┴─────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    zones = get_all_zones_pixels(LayoutType.COMPARISON, width, height)
    
    headline = scene.get('headline', 'COMPARISON')
    narration = scene.get('narration', '')
    
    # Get comparison data
    compare_left = scene.get('compare_left', {'title': 'Option A', 'points': []})
    compare_right = scene.get('compare_right', {'title': 'Option B', 'points': []})
    
    # Handle string format
    if isinstance(compare_left, str):
        compare_left = {'title': compare_left, 'points': []}
    if isinstance(compare_right, str):
        compare_right = {'title': compare_right, 'points': []}
    
    # Colors
    left_color = (60, 80, 120)   # Blue-ish
    right_color = (120, 60, 80)  # Red-ish
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=48,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 10))
    layers.append(head_clip)
    
    # === LEFT PANEL ===
    left_zone = zones['left_panel']
    left_box = ColorClip(
        size=(left_zone['width'], left_zone['height']),
        color=left_color,
        duration=duration
    )
    left_box = left_box.with_position((left_zone['x'], left_zone['y']))
    layers.append(left_box)
    
    # Left title
    left_title = TextClip(
        text=truncate_text(str(compare_left.get('title', 'A')), 15),
        font_size=36,
        color='white',
        font=font
    ).with_duration(duration)
    left_title = left_title.with_position((left_zone['x'] + 20, left_zone['y'] + 15))
    layers.append(left_title)
    
    # Left underline
    left_line = ColorClip(
        size=(left_zone['width'] - 40, 3),
        color=(255, 255, 255),
        duration=duration
    )
    left_line = left_line.with_position((left_zone['x'] + 20, left_zone['y'] + 60))
    layers.append(left_line)
    
    # Left points
    left_points = compare_left.get('points', [])
    for i, pt in enumerate(left_points[:5]):
        pt_clip = TextClip(
            text="• " + truncate_text(str(pt), 18),
            font_size=26,
            color='#DDDDDD',
            font=font
        ).with_duration(duration)
        pt_clip = pt_clip.with_position((left_zone['x'] + 20, left_zone['y'] + 80 + i * 40))
        layers.append(pt_clip)
    
    # === VS DIVIDER ===
    vs_zone = zones['vs_divider']
    vs_clip = TextClip(
        text="VS",
        font_size=36,
        color=(255, 230, 109),  # Yellow
        font=font
    ).with_duration(duration)
    vs_clip = vs_clip.with_position(('center', vs_zone['y']))
    layers.append(vs_clip)
    
    # === RIGHT PANEL ===
    right_zone = zones['right_panel']
    right_box = ColorClip(
        size=(right_zone['width'], right_zone['height']),
        color=right_color,
        duration=duration
    )
    right_box = right_box.with_position((right_zone['x'], right_zone['y']))
    layers.append(right_box)
    
    # Right title
    right_title = TextClip(
        text=truncate_text(str(compare_right.get('title', 'B')), 15),
        font_size=36,
        color='white',
        font=font
    ).with_duration(duration)
    right_title = right_title.with_position((right_zone['x'] + 20, right_zone['y'] + 15))
    layers.append(right_title)
    
    # Right underline
    right_line = ColorClip(
        size=(right_zone['width'] - 40, 3),
        color=(255, 255, 255),
        duration=duration
    )
    right_line = right_line.with_position((right_zone['x'] + 20, right_zone['y'] + 60))
    layers.append(right_line)
    
    # Right points
    right_points = compare_right.get('points', [])
    for i, pt in enumerate(right_points[:5]):
        pt_clip = TextClip(
            text="• " + truncate_text(str(pt), 18),
            font_size=26,
            color='#DDDDDD',
            font=font
        ).with_duration(duration)
        pt_clip = pt_clip.with_position((right_zone['x'] + 20, right_zone['y'] + 80 + i * 40))
        layers.append(pt_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], left_color
        )
        layers.extend(narrator_layers)
    
    return layers


def render_timeline(scene: Dict, width: int, height: int, duration: float,
                    fetch_image_fn=None) -> List:
    """
    📅 TIMELINE FRAME
    
    Visual: Vertical line with markers and events
    Use when: Showing history, evolution, sequence of events
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├──────────────────────────┤
    │  │                       │
    │  ●── 2020: Event 1       │
    │  │                       │
    │  ●── 2021: Event 2       │
    │  │                       │
    │  ●── 2022: Event 3       │
    │  │                       │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'purple')
    zones = get_all_zones_pixels(LayoutType.TIMELINE, width, height)
    
    headline = scene.get('headline', 'TIMELINE')
    narration = scene.get('narration', '')
    timeline_items = scene.get('timeline_items', [])
    
    if not timeline_items:
        timeline_items = [
            {'year': '2020', 'event': 'First event'},
            {'year': '2021', 'event': 'Second event'},
            {'year': '2022', 'event': 'Third event'},
        ]
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=55,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === TIMELINE ===
    timeline_zone = zones['timeline']
    line_x = int(width * 0.12)
    
    # Vertical line
    line = ColorClip(
        size=(4, timeline_zone['height'] - 20),
        color=accent,
        duration=duration
    )
    line = line.with_position((line_x, timeline_zone['y'] + 10))
    layers.append(line)
    
    # Timeline items
    num_items = min(len(timeline_items), 5)
    item_spacing = (timeline_zone['height'] - 30) // max(num_items, 1)
    
    for idx, item in enumerate(timeline_items[:5]):
        y_pos = timeline_zone['y'] + 20 + idx * item_spacing
        
        # Handle dict or string format
        if isinstance(item, dict):
            year = str(item.get('year', f'{2020 + idx}'))
            event = str(item.get('event', 'Event'))
        else:
            year = str(2020 + idx)
            event = str(item)
        
        # Marker dot
        dot = ColorClip(
            size=(18, 18),
            color=accent,
            duration=duration
        )
        dot = dot.with_position((line_x - 7, y_pos))
        layers.append(dot)
        
        # Year
        year_clip = TextClip(
            text=truncate_text(year, 10),
            font_size=36,
            color=accent,
            font=font
        ).with_duration(duration)
        year_clip = year_clip.with_position((line_x + 30, y_pos - 8))
        layers.append(year_clip)
        
        # Event
        event_clip = TextClip(
            text=truncate_text(event, 30),
            font_size=28,
            color='white',
            font=font
        ).with_duration(duration)
        event_clip = event_clip.with_position((line_x + 30, y_pos + 30))
        layers.append(event_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_definition(scene: Dict, width: int, height: int, duration: float,
                      fetch_image_fn=None) -> List:
    """
    📖 DEFINITION FRAME
    
    Visual: Big icon + term + meaning
    Use when: Defining a concept, "What is X?"
    
    ┌──────────────────────────┐
    │                          │
    │        [ ICON ]          │
    │                          │
    ├──────────────────────────┤
    │     CONCEPT NAME         │
    │     ══════════════       │
    │                          │
    │  "Definition text that   │
    │   explains the concept"  │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'yellow')
    zones = get_all_zones_pixels(LayoutType.DEFINITION, width, height)
    
    headline = scene.get('headline', 'DEFINITION')
    narration = scene.get('narration', '')
    icon = scene.get('icon', '📖')
    
    # === ICON ===
    icon_zone = zones['icon']
    
    # Try to fetch AI image
    if fetch_image_fn:
        img_path = fetch_image_fn(headline, width=icon_zone['width'], height=icon_zone['height'], scene_type="definition")
        if img_path:
            img_clip = create_safe_image_clip(img_path, icon_zone['width'], icon_zone['height'], duration)
            if img_clip:
                img_clip = img_clip.with_position(('center', icon_zone['y']))
                layers.append(img_clip)
    
    if not layers and icon:
        # Fallback to emoji
        icon_clip = TextClip(
            text=icon,
            font_size=120,
            color='white',
            font=font
        ).with_duration(duration)
        icon_clip = icon_clip.with_position(('center', icon_zone['y'] + 40))
        layers.append(icon_clip)
    
    # === TERM ===
    term_zone = zones['term']
    term_clip = TextClip(
        text=headline,
        font_size=65,
        color=accent,
        font=font
    ).with_duration(duration)
    term_clip = term_clip.with_position(('center', term_zone['y']))
    layers.append(term_clip)
    
    # Underline
    underline = ColorClip(
        size=(min(len(headline) * 40, int(width * 0.8)), 5),
        color=accent,
        duration=duration
    )
    underline = underline.with_position(('center', term_zone['y'] + 70))
    layers.append(underline)
    
    # === MEANING ===
    meaning_zone = zones['meaning']
    if narration:
        meaning_clip = TextClip(
            text=narration[:180],
            font_size=36,
            color='white',
            font=font,
            method='caption',
            size=(int(width * 0.84), None)
        ).with_duration(duration)
        meaning_clip = meaning_clip.with_position(('center', meaning_zone['y']))
        layers.append(meaning_clip)
    
    return layers


def render_fact_stat(scene: Dict, width: int, height: int, duration: float,
                     fetch_image_fn=None) -> List:
    """
    🔢 FACT / STATISTIC FRAME
    
    Visual: Big bold number with context
    Use when: Showing impressive numbers, statistics, facts
    
    ┌──────────────────────────┐
    │                          │
    │       9.6 Gbps           │  ← BIG accent number
    │     ─────────────        │
    │      SPEED CHECK         │  ← Label
    │   = 1 movie in 3 sec     │  ← Comparison
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'yellow')
    zones = get_all_zones_pixels(LayoutType.FACT_STAT, width, height)
    
    headline = scene.get('headline', 'FACT')
    narration = scene.get('narration', '')
    fact_number = scene.get('fact_number', headline)
    fact_comparison = scene.get('fact_comparison', '')
    
    # === BIG NUMBER ===
    num_zone = zones['number']
    number_text = truncate_text(str(fact_number), 15)
    font_size = 100 if len(number_text) > 8 else 130
    
    num_clip = TextClip(
        text=number_text,
        font_size=font_size,
        color=accent,
        font=font
    ).with_duration(duration)
    num_clip = num_clip.with_position(('center', num_zone['y'] + 40))
    layers.append(num_clip)
    
    # === LABEL ===
    label_zone = zones['label']
    label_clip = TextClip(
        text=truncate_text(headline, 25) if fact_number else "FACT",
        font_size=42,
        color='white',
        font=font
    ).with_duration(duration)
    label_clip = label_clip.with_position(('center', label_zone['y']))
    layers.append(label_clip)
    
    # === COMPARISON ===
    if fact_comparison:
        comp_zone = zones['comparison']
        comp_clip = TextClip(
            text=truncate_text(fact_comparison, 35),
            font_size=34,
            color=accent,
            font=font
        ).with_duration(duration)
        comp_clip = comp_clip.with_position(('center', comp_zone['y']))
        layers.append(comp_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_formula(scene: Dict, width: int, height: int, duration: float,
                   fetch_image_fn=None) -> List:
    """
    🧮 FORMULA FRAME
    
    Visual: Math equation with parts breakdown
    Use when: Explaining formulas, equations
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├──────────────────────────┤
    │   ┌──────────────────┐   │
    │   │    E = mc²       │   │
    │   └──────────────────┘   │
    │   E = Energy             │
    │   m = Mass               │
    │   c² = Speed of light²   │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'cyan')
    zones = get_all_zones_pixels(LayoutType.FORMULA, width, height)
    
    headline = scene.get('headline', 'FORMULA')
    narration = scene.get('narration', '')
    formula_text = scene.get('formula_text', 'E = mc²')
    formula_parts = scene.get('formula_parts', [])
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=50,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === FORMULA BOX ===
    formula_zone = zones['formula_box']
    
    # Box background
    box = ColorClip(
        size=(int(width * 0.84), formula_zone['height']),
        color=(35, 35, 50),
        duration=duration
    )
    box = box.with_position(('center', formula_zone['y']))
    layers.append(box)
    
    # Formula text
    formula_clip = TextClip(
        text=truncate_text(formula_text, 25),
        font_size=55,
        color=accent,
        font=font
    ).with_duration(duration)
    formula_clip = formula_clip.with_position(('center', formula_zone['y'] + 30))
    layers.append(formula_clip)
    
    # === BREAKDOWN ===
    breakdown_zone = zones['breakdown']
    if formula_parts:
        y_start = breakdown_zone['y']
        for idx, part in enumerate(formula_parts[:5]):
            symbol = str(part.get('symbol', '?'))
            meaning = truncate_text(str(part.get('meaning', '')), 28)
            
            y_pos = y_start + idx * 60
            
            # Symbol
            sym_clip = TextClip(
                text=symbol,
                font_size=42,
                color=accent,
                font=font
            ).with_duration(duration)
            sym_clip = sym_clip.with_position((int(width * 0.12), y_pos))
            layers.append(sym_clip)
            
            # Equals
            eq_clip = TextClip(
                text="=",
                font_size=36,
                color='white',
                font=font
            ).with_duration(duration)
            eq_clip = eq_clip.with_position((int(width * 0.28), y_pos + 5))
            layers.append(eq_clip)
            
            # Meaning
            mean_clip = TextClip(
                text=meaning,
                font_size=30,
                color='#CCCCCC',
                font=font
            ).with_duration(duration)
            mean_clip = mean_clip.with_position((int(width * 0.36), y_pos + 8))
            layers.append(mean_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_simple_explain(scene: Dict, width: int, height: int, duration: float,
                          fetch_image_fn=None) -> List:
    """
    💡 SIMPLE EXPLANATION FRAME (Default)
    
    Visual: Headline + visual + text
    Use when: General explanations, concepts
    
    ┌──────────────────────────┐
    │      HEADLINE            │
    ├──────────────────────────┤
    │                          │
    │    [ VISUAL / ICON ]     │
    │                          │
    ├──────────────────────────┤
    │  "Explanation text that  │
    │   describes the concept  │
    │   in a clear way"        │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'teal')
    zones = get_all_zones_pixels(LayoutType.SIMPLE_EXPLAIN, width, height)
    
    headline = scene.get('headline', 'EXPLANATION')
    narration = scene.get('narration', '')
    icon = scene.get('icon', '💡')
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=60,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 20))
    layers.append(head_clip)
    
    # Accent underline
    underline = ColorClip(
        size=(min(len(headline) * 35, int(width * 0.7)), 4),
        color=accent,
        duration=duration
    )
    underline = underline.with_position(('center', head_zone['y'] + head_zone['height'] - 10))
    layers.append(underline)
    
    # === VISUAL ===
    visual_zone = zones['visual']
    
    # Try to fetch AI image
    if fetch_image_fn:
        image_query = f"{headline} {narration[:40]}"
        img_path = fetch_image_fn(image_query, width=visual_zone['width'], height=visual_zone['height'], scene_type="explanation")
        if img_path:
            img_clip = create_safe_image_clip(img_path, visual_zone['width'], visual_zone['height'], duration)
            if img_clip:
                img_clip = img_clip.with_position(('center', visual_zone['y']))
                layers.append(img_clip)
    
    if len(layers) <= 2 and icon:
        # Fallback to emoji
        icon_clip = TextClip(
            text=icon,
            font_size=100,
            color='white',
            font=font
        ).with_duration(duration)
        icon_clip = icon_clip.with_position(('center', visual_zone['y'] + 80))
        layers.append(icon_clip)
    
    # === TEXT ===
    text_zone = zones['text']
    if narration:
        text_clip = TextClip(
            text=narration[:180],
            font_size=34,
            color='#DDDDDD',
            font=font,
            method='caption',
            size=(int(width * 0.84), None)
        ).with_duration(duration)
        text_clip = text_clip.with_position(('center', text_zone['y']))
        layers.append(text_clip)
    
    return layers


def render_classification(scene: Dict, width: int, height: int, duration: float,
                          fetch_image_fn=None) -> List:
    """
    📂 CLASSIFICATION FRAME
    
    Visual: Parent category with child elements
    Use when: Showing types, categories, taxonomy
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├──────────────────────────┤
    │      [ CATEGORY ]        │
    │     ┌────┬────┬────┐     │
    │     │    │    │    │     │
    │    [A]  [B]  [C]  [D]    │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'purple')
    zones = get_all_zones_pixels(LayoutType.CLASSIFICATION, width, height)
    
    headline = scene.get('headline', 'CLASSIFICATION')
    narration = scene.get('narration', '')
    parent = scene.get('category', scene.get('parent', headline))
    children = scene.get('types', scene.get('children', scene.get('list_items', [])))
    
    if not children:
        children = ['Type A', 'Type B', 'Type C']
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=50,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === PARENT BOX ===
    parent_zone = zones['parent']
    parent_box = ColorClip(
        size=(parent_zone['width'], parent_zone['height']),
        color=accent,
        duration=duration
    )
    parent_box = parent_box.with_position(('center', parent_zone['y']))
    layers.append(parent_box)
    
    parent_text = TextClip(
        text=truncate_text(str(parent), 18),
        font_size=32,
        color='white',
        font=font
    ).with_duration(duration)
    parent_text = parent_text.with_position(('center', parent_zone['y'] + 30))
    layers.append(parent_text)
    
    # === CHILDREN ===
    children_zone = zones['children']
    num_children = min(len(children), 4)
    child_width = (children_zone['width'] - 60) // max(num_children, 1)
    child_height = 100
    
    start_x = children_zone['x'] + 30
    y_pos = children_zone['y'] + 60
    
    # Connecting lines from parent
    for idx, child in enumerate(children[:4]):
        x_pos = start_x + idx * child_width + 10
        child_center_x = x_pos + child_width // 2 - 30
        
        # Vertical line from parent
        line = ColorClip(
            size=(2, 40),
            color=accent,
            duration=duration
        )
        line = line.with_position((child_center_x, parent_zone['y'] + parent_zone['height']))
        layers.append(line)
        
        # Child box
        child_box = ColorClip(
            size=(child_width - 20, child_height),
            color=(45, 45, 60),
            duration=duration
        )
        child_box = child_box.with_position((x_pos, y_pos))
        layers.append(child_box)
        
        # Child text
        child_text = TextClip(
            text=truncate_text(str(child), 12),
            font_size=26,
            color='white',
            font=font
        ).with_duration(duration)
        child_text = child_text.with_position((x_pos + 10, y_pos + 35))
        layers.append(child_text)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_cycle(scene: Dict, width: int, height: int, duration: float,
                 fetch_image_fn=None) -> List:
    """
    🔄 CYCLE FRAME
    
    Visual: Circular arrangement with arrows
    Use when: Showing cycles, loops, recurring processes
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├──────────────────────────┤
    │         [A]              │
    │        ↗   ↘             │
    │      [D]   [B]           │
    │        ↖   ↙             │
    │         [C]              │
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'cyan')
    zones = get_all_zones_pixels(LayoutType.CYCLE, width, height)
    
    headline = scene.get('headline', 'CYCLE')
    narration = scene.get('narration', '')
    cycle_items = scene.get('cycle_items', scene.get('steps', scene.get('list_items', [])))
    
    if not cycle_items:
        cycle_items = ['Step 1', 'Step 2', 'Step 3', 'Step 4']
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=55,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === CYCLE ===
    cycle_zone = zones['cycle']
    center_x = width // 2
    center_y = cycle_zone['y'] + cycle_zone['height'] // 2
    radius = min(cycle_zone['width'], cycle_zone['height']) // 3
    
    import math
    num_items = min(len(cycle_items), 6)
    box_size = 100
    
    # Position items in a circle
    for idx, item in enumerate(cycle_items[:6]):
        angle = (2 * math.pi * idx / num_items) - math.pi / 2  # Start from top
        x = int(center_x + radius * math.cos(angle) - box_size // 2)
        y = int(center_y + radius * math.sin(angle) - box_size // 2)
        
        # Item box
        item_box = ColorClip(
            size=(box_size, box_size // 2),
            color=accent if idx == 0 else (50, 50, 65),
            duration=duration
        )
        item_box = item_box.with_position((x, y))
        layers.append(item_box)
        
        # Item text
        item_text = TextClip(
            text=truncate_text(str(item), 12),
            font_size=22,
            color='white',
            font=font
        ).with_duration(duration)
        item_text = item_text.with_position((x + 8, y + 12))
        layers.append(item_text)
    
    # Arrows between items (simplified - just show cycle direction)
    arrow_clip = TextClip(
        text="↻",
        font_size=80,
        color=accent,
        font=font
    ).with_duration(duration)
    arrow_clip = arrow_clip.with_position(('center', center_y - 40))
    layers.append(arrow_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


def render_matrix(scene: Dict, width: int, height: int, duration: float,
                  fetch_image_fn=None) -> List:
    """
    📊 MATRIX / TABLE FRAME
    
    Visual: Grid layout with headers
    Use when: Showing tabular data, matrices
    
    ┌──────────────────────────┐
    │       HEADLINE           │
    ├──────────────────────────┤
    │ ┌─────┬─────┬─────┬─────┐│
    │ │ HDR │ HDR │ HDR │ HDR ││
    │ ├─────┼─────┼─────┼─────┤│
    │ │ A1  │ A2  │ A3  │ A4  ││
    │ │ B1  │ B2  │ B3  │ B4  ││
    │ └─────┴─────┴─────┴─────┘│
    ├──────────────────────────┤
    │     Support text         │
    └──────────────────────────┘
    """
    layers = []
    font = get_font()
    accent = get_accent_color(scene, 'teal')
    zones = get_all_zones_pixels(LayoutType.MATRIX, width, height)
    
    headline = scene.get('headline', 'TABLE')
    narration = scene.get('narration', '')
    headers = scene.get('table_headers', ['Col 1', 'Col 2', 'Col 3'])
    rows = scene.get('table_rows', [['A', 'B', 'C'], ['D', 'E', 'F']])
    
    # === HEADLINE ===
    head_zone = zones['headline']
    head_clip = TextClip(
        text=truncate_text(headline, 22),
        font_size=50,
        color='white',
        font=font
    ).with_duration(duration)
    head_clip = head_clip.with_position(('center', head_zone['y'] + 15))
    layers.append(head_clip)
    
    # === TABLE ===
    table_zone = zones['table']
    num_cols = min(len(headers), 4)
    num_rows = min(len(rows) + 1, 5)  # +1 for header
    
    col_width = (table_zone['width'] - 40) // max(num_cols, 1)
    row_height = min(60, table_zone['height'] // max(num_rows, 1))
    
    start_x = table_zone['x'] + 20
    start_y = table_zone['y'] + 10
    
    # Header row
    header_bg = ColorClip(
        size=(table_zone['width'] - 40, row_height),
        color=accent,
        duration=duration
    )
    header_bg = header_bg.with_position((start_x, start_y))
    layers.append(header_bg)
    
    for idx, header in enumerate(headers[:4]):
        h_clip = TextClip(
            text=truncate_text(str(header), 12),
            font_size=26,
            color='white',
            font=font
        ).with_duration(duration)
        h_clip = h_clip.with_position((start_x + idx * col_width + 15, start_y + 15))
        layers.append(h_clip)
    
    # Data rows
    for row_idx, row in enumerate(rows[:4]):
        row_y = start_y + (row_idx + 1) * row_height
        row_color = (40, 40, 50) if row_idx % 2 == 0 else (50, 50, 60)
        
        row_bg = ColorClip(
            size=(table_zone['width'] - 40, row_height),
            color=row_color,
            duration=duration
        )
        row_bg = row_bg.with_position((start_x, row_y))
        layers.append(row_bg)
        
        for col_idx, cell in enumerate(row[:4]):
            c_clip = TextClip(
                text=truncate_text(str(cell), 12),
                font_size=24,
                color='#DDDDDD',
                font=font
            ).with_duration(duration)
            c_clip = c_clip.with_position((start_x + col_idx * col_width + 15, row_y + 18))
            layers.append(c_clip)
    
    # === NARRATOR BOX (Speech bubble style) ===
    support_zone = zones['support']
    if narration:
        narrator_layers = create_narrator_box(
            narration, width, height, duration, support_zone['y'], accent
        )
        layers.extend(narrator_layers)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 MAIN RENDER DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

RENDERERS = {
    'list_array': render_list_array,
    'process_flow': render_process_flow,
    'comparison': render_comparison,
    'timeline': render_timeline,
    'definition': render_definition,
    'classification': render_classification,
    'cycle': render_cycle,
    'fact_stat': render_fact_stat,
    'formula': render_formula,
    'simple_explain': render_simple_explain,
    'hierarchy': render_classification,  # Similar to classification
    'matrix': render_matrix,
    'array': render_array_visualization,  # Bubble Sort style array viz
    'array_visualization': render_array_visualization,
}


def render_semantic_frame(layout_type: str, scene: Dict, width: int, height: int,
                          duration: float, fetch_image_fn=None) -> List:
    """
    🎬 MAIN ENTRY POINT
    
    Renders a frame based on the semantic layout type.
    
    Args:
        layout_type: The layout type string (e.g., "list_array", "comparison")
        scene: Scene data dictionary
        width: Canvas width
        height: Canvas height
        duration: Duration in seconds
        fetch_image_fn: Optional function to fetch AI images
    
    Returns:
        List of MoviePy clips to composite
    """
    renderer = RENDERERS.get(layout_type, render_simple_explain)
    
    print(f"   🎨 SEMANTIC RENDERER: {layout_type.upper()}")
    
    try:
        return renderer(scene, width, height, duration, fetch_image_fn)
    except Exception as e:
        print(f"   ⚠️ Render error: {e}, falling back to simple_explain")
        return render_simple_explain(scene, width, height, duration, fetch_image_fn)
