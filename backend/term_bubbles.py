"""
💬 TERM BUBBLE RENDERER - Highlights and explains technical terms
==================================================================
When narration mentions terms like "push", "pop", "array", etc.
Creates animated bubble explanations with visual definitions.
"""

import re
from typing import Dict, List, Tuple, Optional
from moviepy import TextClip, ColorClip, CompositeVideoClip

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 TECHNICAL TERM DICTIONARY
# ═══════════════════════════════════════════════════════════════════════════════

TECH_TERMS = {
    # Stack operations
    'push': {
        'icon': '⬆️',
        'short': 'Add to top',
        'description': 'Add an item to the top of the stack',
        'color': (76, 217, 100),  # Green
    },
    'pop': {
        'icon': '⬇️',
        'short': 'Remove from top',
        'description': 'Remove the top item from the stack',
        'color': (255, 100, 100),  # Red
    },
    'peek': {
        'icon': '👀',
        'short': 'Look at top',
        'description': 'View the top item without removing it',
        'color': (100, 200, 255),  # Blue
    },
    'lifo': {
        'icon': '📚',
        'short': 'Last In First Out',
        'description': 'The last item added is the first one removed',
        'color': (255, 200, 100),  # Orange
    },
    'fifo': {
        'icon': '🚶',
        'short': 'First In First Out',
        'description': 'The first item added is the first one removed',
        'color': (200, 100, 255),  # Purple
    },
    
    # Queue operations
    'enqueue': {
        'icon': '➡️',
        'short': 'Add to back',
        'description': 'Add an item to the end of the queue',
        'color': (100, 255, 200),  # Teal
    },
    'dequeue': {
        'icon': '⬅️',
        'short': 'Remove from front',
        'description': 'Remove the first item from the queue',
        'color': (255, 150, 100),  # Coral
    },
    
    # Array operations
    'array': {
        'icon': '📊',
        'short': 'Ordered list',
        'description': 'A collection of items stored in order',
        'color': (100, 150, 255),  # Blue
    },
    'index': {
        'icon': '📍',
        'short': 'Position number',
        'description': 'The position of an item (starts at 0)',
        'color': (255, 200, 100),  # Yellow
    },
    'element': {
        'icon': '🔲',
        'short': 'Single item',
        'description': 'One item in an array or collection',
        'color': (200, 200, 200),  # Gray
    },
    
    # Linked list
    'node': {
        'icon': '🔗',
        'short': 'Data container',
        'description': 'A container that holds data and a link to next',
        'color': (150, 200, 255),  # Light blue
    },
    'pointer': {
        'icon': '👉',
        'short': 'Link/Reference',
        'description': 'Points to another location in memory',
        'color': (255, 150, 200),  # Pink
    },
    'head': {
        'icon': '🏁',
        'short': 'Start point',
        'description': 'The first node in a linked list',
        'color': (100, 255, 100),  # Green
    },
    'tail': {
        'icon': '🔚',
        'short': 'End point',
        'description': 'The last node in a linked list',
        'color': (255, 100, 100),  # Red
    },
    
    # Tree operations
    'root': {
        'icon': '🌳',
        'short': 'Top node',
        'description': 'The topmost node in a tree',
        'color': (139, 90, 43),  # Brown
    },
    'leaf': {
        'icon': '🍃',
        'short': 'End node',
        'description': 'A node with no children',
        'color': (100, 200, 100),  # Green
    },
    'parent': {
        'icon': '👆',
        'short': 'Upper node',
        'description': 'The node directly above this one',
        'color': (200, 150, 255),  # Purple
    },
    'child': {
        'icon': '👇',
        'short': 'Lower node',
        'description': 'A node directly below another node',
        'color': (255, 200, 150),  # Peach
    },
    
    # Sorting
    'swap': {
        'icon': '🔄',
        'short': 'Exchange positions',
        'description': 'Exchange the positions of two items',
        'color': (255, 200, 100),  # Yellow
    },
    'compare': {
        'icon': '⚖️',
        'short': 'Check which is bigger',
        'description': 'Check if one value is greater than another',
        'color': (150, 150, 255),  # Light purple
    },
    'pivot': {
        'icon': '📌',
        'short': 'Reference point',
        'description': 'A chosen element to compare others against',
        'color': (255, 100, 150),  # Pink
    },
    
    # Search
    'target': {
        'icon': '🎯',
        'short': 'What we seek',
        'description': 'The value we are looking for',
        'color': (255, 100, 100),  # Red
    },
    'binary search': {
        'icon': '✂️',
        'short': 'Divide in half',
        'description': 'Search by repeatedly dividing in half',
        'color': (100, 200, 255),  # Blue
    },
    
    # Complexity
    'o(1)': {
        'icon': '⚡',
        'short': 'Constant time',
        'description': 'Always takes the same amount of time',
        'color': (100, 255, 100),  # Green
    },
    'o(n)': {
        'icon': '📈',
        'short': 'Linear time',
        'description': 'Time grows with the size of input',
        'color': (255, 200, 100),  # Yellow
    },
    'o(n²)': {
        'icon': '🐌',
        'short': 'Quadratic time',
        'description': 'Time grows with square of input size',
        'color': (255, 100, 100),  # Red
    },
    
    # Graph
    'vertex': {
        'icon': '⭕',
        'short': 'Point/Node',
        'description': 'A point in a graph',
        'color': (100, 200, 255),  # Blue
    },
    'edge': {
        'icon': '➖',
        'short': 'Connection',
        'description': 'A line connecting two vertices',
        'color': (200, 200, 200),  # Gray
    },
    
    # Hash
    'hash': {
        'icon': '#️⃣',
        'short': 'Unique code',
        'description': 'Convert data into a fixed-size code',
        'color': (200, 100, 255),  # Purple
    },
    'collision': {
        'icon': '💥',
        'short': 'Same hash',
        'description': 'When two items get the same hash code',
        'color': (255, 100, 100),  # Red
    },
    
    # Recursion
    'recursion': {
        'icon': '🔁',
        'short': 'Calls itself',
        'description': 'A function that calls itself',
        'color': (100, 200, 255),  # Blue
    },
    'base case': {
        'icon': '🛑',
        'short': 'Stop condition',
        'description': 'When recursion should stop',
        'color': (255, 100, 100),  # Red
    },
    
    # General
    'algorithm': {
        'icon': '📝',
        'short': 'Step-by-step plan',
        'description': 'A set of instructions to solve a problem',
        'color': (100, 200, 255),  # Blue
    },
    'data structure': {
        'icon': '🏗️',
        'short': 'Data organizer',
        'description': 'A way to organize and store data',
        'color': (200, 150, 100),  # Brown
    },
    'iterate': {
        'icon': '🔄',
        'short': 'Go through each',
        'description': 'Process each item one by one',
        'color': (100, 200, 200),  # Teal
    },
    'loop': {
        'icon': '🔁',
        'short': 'Repeat',
        'description': 'Execute code multiple times',
        'color': (200, 200, 100),  # Yellow-green
    },
    
    # Science terms
    'photosynthesis': {
        'icon': '🌿',
        'short': 'Plant food-making',
        'description': 'Plants convert sunlight into food',
        'color': (100, 200, 100),  # Green
    },
    'chlorophyll': {
        'icon': '🟢',
        'short': 'Green pigment',
        'description': 'The green color that captures sunlight',
        'color': (50, 200, 50),  # Green
    },
    'glucose': {
        'icon': '🍬',
        'short': 'Sugar/Food',
        'description': 'The sugar plants make for energy',
        'color': (255, 200, 100),  # Yellow
    },
    'oxygen': {
        'icon': '🫧',
        'short': 'O₂ we breathe',
        'description': 'The gas released by plants',
        'color': (150, 200, 255),  # Light blue
    },
    'carbon dioxide': {
        'icon': '💨',
        'short': 'CO₂ gas',
        'description': 'The gas plants absorb from air',
        'color': (150, 150, 150),  # Gray
    },
    'co2': {
        'icon': '💨',
        'short': 'Carbon dioxide',
        'description': 'The gas plants absorb from air',
        'color': (150, 150, 150),  # Gray
    },
}


def get_font():
    """Get available system font."""
    import os
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "Helvetica-Bold",
        "Helvetica",
    ]
    for f in fonts:
        if os.path.exists(f) or not f.startswith("/"):
            return f
    return "Helvetica"


def find_terms_in_text(text: str) -> List[Tuple[str, Dict]]:
    """Find all technical terms in the text."""
    found = []
    text_lower = text.lower()
    
    # Sort by length (longer first) to match multi-word terms first
    sorted_terms = sorted(TECH_TERMS.keys(), key=len, reverse=True)
    
    for term in sorted_terms:
        if term in text_lower:
            # Check if we already have a similar term
            if not any(term in existing[0] or existing[0] in term for existing in found):
                found.append((term, TECH_TERMS[term]))
    
    return found[:3]  # Max 3 terms per scene


def create_term_bubble(term: str, info: Dict, x: int, y: int, duration: float) -> List:
    """Create a bubble explanation for a term."""
    layers = []
    font = get_font()
    
    color = info['color']
    icon = info['icon']
    short_def = info['short']
    
    # Bubble dimensions
    bubble_w = 220
    bubble_h = 90
    
    # Outer glow
    glow = ColorClip(size=(bubble_w + 10, bubble_h + 10), color=color, duration=duration)
    glow = glow.with_opacity(0.4).with_position((x - 5, y - 5))
    layers.append(glow)
    
    # Main bubble background
    bubble_bg = ColorClip(size=(bubble_w, bubble_h), color=(30, 35, 45), duration=duration)
    bubble_bg = bubble_bg.with_position((x, y))
    layers.append(bubble_bg)
    
    # Top accent bar (term color)
    accent = ColorClip(size=(bubble_w, 5), color=color, duration=duration)
    accent = accent.with_position((x, y))
    layers.append(accent)
    
    # Icon
    icon_clip = TextClip(text=icon, font_size=32, font=font).with_duration(duration)
    icon_clip = icon_clip.with_position((x + 10, y + 18))
    layers.append(icon_clip)
    
    # Term name (uppercase, colored)
    term_text = TextClip(
        text=term.upper(),
        font_size=18,
        color=f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
        font=font
    ).with_duration(duration)
    term_text = term_text.with_position((x + 55, y + 15))
    layers.append(term_text)
    
    # Short definition
    def_text = TextClip(
        text=short_def,
        font_size=14,
        color='#cccccc',
        font=font
    ).with_duration(duration)
    def_text = def_text.with_position((x + 55, y + 45))
    layers.append(def_text)
    
    return layers


def create_term_bubbles_overlay(text: str, width: int, height: int, duration: float) -> List:
    """
    Create bubble overlays for all technical terms found in text.
    Returns list of MoviePy clips.
    """
    layers = []
    
    # Find terms in the text
    terms = find_terms_in_text(text)
    
    if not terms:
        return layers
    
    print(f"   💬 Found terms: {[t[0] for t in terms]}")
    
    # Position bubbles along the bottom
    bubble_y = height - 120
    num_bubbles = len(terms)
    
    if num_bubbles == 1:
        positions = [(width // 2 - 110, bubble_y)]
    elif num_bubbles == 2:
        positions = [(width // 4 - 110, bubble_y), (3 * width // 4 - 110, bubble_y)]
    else:
        positions = [
            (50, bubble_y),
            (width // 2 - 110, bubble_y),
            (width - 270, bubble_y)
        ]
    
    for i, (term, info) in enumerate(terms):
        if i < len(positions):
            x, y = positions[i]
            bubble_layers = create_term_bubble(term, info, x, y, duration)
            layers.extend(bubble_layers)
    
    return layers


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 TERM HIGHLIGHT IN TEXT
# ═══════════════════════════════════════════════════════════════════════════════

def highlight_terms_in_text(text: str) -> str:
    """
    Returns text with terms wrapped in markers for highlighting.
    Note: MoviePy TextClip doesn't support inline formatting,
    so this is mainly for detection.
    """
    terms = find_terms_in_text(text)
    
    for term, info in terms:
        # Case-insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(f"【{term.upper()}】", text)
    
    return text


def get_terms_for_scene(text: str) -> List[str]:
    """Get list of technical terms in the scene text."""
    terms = find_terms_in_text(text)
    return [t[0] for t in terms]


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_text = "Adding is 'push', removing is 'pop'. Last in, first out. Like a stack of plates!"
    
    print("Testing term detection...")
    terms = find_terms_in_text(test_text)
    
    for term, info in terms:
        print(f"  {info['icon']} {term.upper()}: {info['short']}")
