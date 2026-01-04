"""
🧠 SEMANTIC-AWARE FRAMING SYSTEM
================================
This module implements intelligent frame layout selection based on content meaning.

The core idea: Concept → Visual Grammar → Frame Layout

Instead of using fixed frames, the layout adapts to what's being explained:
- Lists → Array/stacked layout
- Processes → Boxes + arrows
- Comparisons → Split screen
- Timelines → Horizontal markers
- Definitions → Icon + big text
- Classification → Grouped boxes (hierarchy/tree)
- Cycle → Circular diagram
- Simple Explain → Basic headline + visual + text
- Fact Stat → Big number/statistic
- Formula → Math equation with parts
- Code Snippet → Code block styling
- Hierarchy → Tree structure
- Matrix → Grid/table layout
-matrix
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 VISUAL GRAMMAR DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class LayoutType(Enum):
    """Visual layout types based on semantic meaning"""
    LIST_ARRAY = "list_array"           # Vertical stacked items
    PROCESS_FLOW = "process_flow"       # Boxes + arrows (left → right or top → bottom)
    COMPARISON = "comparison"           # Side-by-side split screen
    TIMELINE = "timeline"               # Horizontal/vertical timeline with markers
    DEFINITION = "definition"           # Icon + big text centered
    CLASSIFICATION = "classification"   # Grouped boxes (hierarchy/tree)
    CYCLE = "cycle"                     # Circular diagram
    SIMPLE_EXPLAIN = "simple_explain"   # Basic headline + visual + text
    FACT_STAT = "fact_stat"            # Big number/statistic
    FORMULA = "formula"                 # Math equation with parts
    CODE_SNIPPET = "code_snippet"       # Code block styling
    HIERARCHY = "hierarchy"             # Tree structure
    MATRIX = "matrix"                   # Grid/table layout


@dataclass
class FrameLayout:
    """Defines the visual structure of a frame"""
    layout_type: LayoutType
    zones: Dict[str, Tuple[float, float, float, float]]  # zone_name: (x%, y%, width%, height%)
    accent_position: str  # Where accent elements should go
    icon_size: str  # small, medium, large
    text_alignment: str  # left, center, right
    description: str


# ═══════════════════════════════════════════════════════════════════════════════
# 📐 FRAME LAYOUT TEMPLATES (Visual Grammar)
# ═══════════════════════════════════════════════════════════════════════════════

FRAME_LAYOUTS = {
    LayoutType.LIST_ARRAY: FrameLayout(
        layout_type=LayoutType.LIST_ARRAY,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.12),
            "items": (0.08, 0.18, 0.84, 0.55),
            "support": (0.05, 0.75, 0.9, 0.2),
        },
        accent_position="bullets",
        icon_size="small",
        text_alignment="left",
        description="""
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
    ),
    
    LayoutType.PROCESS_FLOW: FrameLayout(
        layout_type=LayoutType.PROCESS_FLOW,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "flow": (0.05, 0.16, 0.9, 0.58),
            "support": (0.05, 0.76, 0.9, 0.18),
        },
        accent_position="arrows",
        icon_size="medium",
        text_alignment="center",
        description="""
        ┌──────────────────────────┐
        │      HEADLINE            │
        ├──────────────────────────┤
        │  ┌───┐   ┌───┐   ┌───┐   │
        │  │ 1 │ → │ 2 │ → │ 3 │   │
        │  └───┘   └───┘   └───┘   │
        │     │       │       │     │
        │   Step 1  Step 2  Step 3  │
        ├──────────────────────────┤
        │     Support text          │
        └──────────────────────────┘
        """
    ),
    
    LayoutType.COMPARISON: FrameLayout(
        layout_type=LayoutType.COMPARISON,
        zones={
            "headline": (0.05, 0.03, 0.9, 0.08),
            "left_panel": (0.03, 0.12, 0.44, 0.58),
            "right_panel": (0.53, 0.12, 0.44, 0.58),
            "vs_divider": (0.47, 0.30, 0.06, 0.15),
            "support": (0.05, 0.72, 0.9, 0.23),
        },
        accent_position="panels",
        icon_size="medium",
        text_alignment="center",
        description="""
        ┌──────────────────────────┐
        │       HEADLINE           │
        ├────────────┬─────────────┤
        │   OPTION A │   OPTION B  │
        │ ──────────-│-─────────── │
        │ • Point 1  │ • Point 1   │
        │ • Point 2  │ • Point 2   │
        │ • Point 3  │ • Point 3   │
        │            │             │
        ├────────────┴─────────────┤
        │     Support text         │
        └──────────────────────────┘
        """
    ),
    
    LayoutType.TIMELINE: FrameLayout(
        layout_type=LayoutType.TIMELINE,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "timeline": (0.05, 0.16, 0.9, 0.58),
            "support": (0.05, 0.76, 0.9, 0.18),
        },
        accent_position="markers",
        icon_size="small",
        text_alignment="center",
        description="""
        ┌──────────────────────────┐
        │       HEADLINE           │
        ├──────────────────────────┤
        │ ●────────●────────●────● │
        │ t1      t2       t3   t4 │
        │ Event1  Event2  Event3   │
        ├──────────────────────────┤
        │     Support text         │
        └──────────────────────────┘
        """
    ),
    
    LayoutType.DEFINITION: FrameLayout(
        layout_type=LayoutType.DEFINITION,
        zones={
            "icon": (0.30, 0.12, 0.40, 0.28),
            "term": (0.05, 0.42, 0.9, 0.12),
            "meaning": (0.08, 0.56, 0.84, 0.25),
            "support": (0.05, 0.82, 0.9, 0.14),
        },
        accent_position="underline",
        icon_size="large",
        text_alignment="center",
        description="""
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
    ),
    
    LayoutType.CLASSIFICATION: FrameLayout(
        layout_type=LayoutType.CLASSIFICATION,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "parent": (0.30, 0.16, 0.40, 0.12),
            "children": (0.05, 0.32, 0.9, 0.40),
            "support": (0.05, 0.74, 0.9, 0.20),
        },
        accent_position="parent",
        icon_size="small",
        text_alignment="center",
        description="""
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
    ),
    
    LayoutType.CYCLE: FrameLayout(
        layout_type=LayoutType.CYCLE,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "cycle": (0.10, 0.16, 0.80, 0.55),
            "support": (0.05, 0.73, 0.9, 0.22),
        },
        accent_position="arrows",
        icon_size="medium",
        text_alignment="center",
        description="""
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
    ),
    
    LayoutType.FACT_STAT: FrameLayout(
        layout_type=LayoutType.FACT_STAT,
        zones={
            "number": (0.05, 0.15, 0.9, 0.30),
            "label": (0.10, 0.46, 0.80, 0.12),
            "comparison": (0.10, 0.58, 0.80, 0.10),
            "support": (0.05, 0.70, 0.9, 0.25),
        },
        accent_position="number",
        icon_size="small",
        text_alignment="center",
        description="""
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
    ),
    
    LayoutType.FORMULA: FrameLayout(
        layout_type=LayoutType.FORMULA,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "formula_box": (0.08, 0.16, 0.84, 0.14),
            "breakdown": (0.08, 0.32, 0.84, 0.38),
            "support": (0.05, 0.72, 0.9, 0.22),
        },
        accent_position="formula",
        icon_size="small",
        text_alignment="left",
        description="""
        ┌──────────────────────────┐
        │       HEADLINE           │
        ├──────────────────────────┤
        │   ┌──────────────────┐   │
        │   │    E = mc²       │   │  ← Formula box
        │   └──────────────────┘   │
        │   E = Energy             │
        │   m = Mass               │  ← Breakdown
        │   c² = Speed of light²   │
        ├──────────────────────────┤
        │     Support text         │
        └──────────────────────────┘
        """
    ),
    
    LayoutType.SIMPLE_EXPLAIN: FrameLayout(
        layout_type=LayoutType.SIMPLE_EXPLAIN,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.12),
            "visual": (0.10, 0.18, 0.80, 0.40),
            "text": (0.08, 0.60, 0.84, 0.35),
        },
        accent_position="headline",
        icon_size="large",
        text_alignment="center",
        description="""
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
    ),
    
    LayoutType.HIERARCHY: FrameLayout(
        layout_type=LayoutType.HIERARCHY,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "tree": (0.05, 0.16, 0.9, 0.58),
            "support": (0.05, 0.76, 0.9, 0.18),
        },
        accent_position="root",
        icon_size="small",
        text_alignment="center",
        description="""
        ┌──────────────────────────┐
        │       HEADLINE           │
        ├──────────────────────────┤
        │         [Root]           │
        │        /      \\          │
        │     [A]        [B]       │
        │    / \\         / \\       │
        │  [A1][A2]   [B1][B2]     │
        ├──────────────────────────┤
        │     Support text         │
        └──────────────────────────┘
        """
    ),
    
    LayoutType.MATRIX: FrameLayout(
        layout_type=LayoutType.MATRIX,
        zones={
            "headline": (0.05, 0.05, 0.9, 0.10),
            "table": (0.05, 0.16, 0.9, 0.55),
            "support": (0.05, 0.73, 0.9, 0.22),
        },
        accent_position="header",
        icon_size="small",
        text_alignment="center",
        description="""
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
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 SEMANTIC CLASSIFIER (The Brain)
# ═══════════════════════════════════════════════════════════════════════════════

# Keyword patterns for detecting content meaning
SEMANTIC_PATTERNS = {
    LayoutType.LIST_ARRAY: [
        r'\b(list|types? of|kinds? of|categories|advantages?|disadvantages?|benefits?|features?|elements?|components?|items?|points?|reasons?|ways?|methods?|examples?|things)\b',
        r'\b(include|consists? of|comprises?|contains?|has|have|are|is)\b.*(?:\d+|\bfew\b|\bseveral\b|\bmany\b|\bmultiple\b)',
        r'(?:first|second|third|1\.|2\.|3\.|•|–|→)',
    ],
    
    LayoutType.PROCESS_FLOW: [
        r'\b(step|process|flow|pipeline|workflow|procedure|how to|how it works|stages?|phases?|sequence)\b',
        r'\b(first|then|next|after|finally|start|end|begin|follow|leads? to|results? in)\b',
        r'\b(input|output|transform|convert|change|move)\b.*\b(to|into|from)\b',
    ],
    
    LayoutType.COMPARISON: [
        r'\b(vs\.?|versus|compared? to|difference|differ|between|while|whereas|unlike|similar|contrast)\b',
        r'\b(better|worse|faster|slower|more|less|advantage over|pros? and cons?)\b',
        r'\b(option [ab]|choice [ab]|alternative)\b',
    ],
    
    LayoutType.TIMELINE: [
        r'\b(timeline|history|evolution|over time|years?|decades?|centuries?|era|period|age)\b',
        r'\b(before|after|during|when|then|now|past|present|future|earlier|later)\b',
        r'\b(\d{4}|\d{2}th century|ancient|modern|medieval|recent)\b',
    ],
    
    LayoutType.DEFINITION: [
        r'\b(what is|define|definition|means?|meaning|refers? to|called|known as|term)\b',
        r'\b(is a|are a|was a|were a)\b.*\b(type|kind|form|way)\b',
        r'^[A-Z][a-z]+ is\b',  # Starts with "X is..."
    ],
    
    LayoutType.CLASSIFICATION: [
        r'\b(types? of|kinds? of|categories|classes|groups?|families|classifications?)\b',
        r'\b(divided into|classified as|grouped into|organized into|fall under)\b',
        r'\b(parent|child|subtype|subcategory|branch)\b',
    ],
    
    LayoutType.CYCLE: [
        r'\b(cycle|loop|circular|repeats?|recurring|continuous|round|iterative)\b',
        r'\b(comes? back|returns?|goes around|full circle)\b',
        r'\b(feedback|infinite|endless|perpetual)\b',
    ],
    
    LayoutType.FACT_STAT: [
        r'\b(\d+%|\d+\s*million|\d+\s*billion|\d+\s*trillion|\d+x|\d+\s*times)\b',
        r'\b(statistics?|data|numbers?|facts?|figures?|metrics?|measurements?)\b',
        r'\b(average|median|total|sum|count|rate|ratio|percentage)\b',
    ],
    
    LayoutType.FORMULA: [
        r'\b(formula|equation|expression|calculate|computation|algorithm)\b',
        r'[A-Z]\s*=\s*[A-Za-z0-9\s\+\-\*\/\^\(\)]+',  # A = something
        r'\b(equals?|plus|minus|times|divided|squared|cubed|sqrt|sum of)\b',
    ],
    
    LayoutType.HIERARCHY: [
        r'\b(hierarchy|tree|structure|levels?|tiers?|ranks?|organization)\b',
        r'\b(parent|child|root|leaf|node|branch|subtree)\b',
        r'\b(top|bottom|above|below|under|over)\b.*\b(level|tier|rank)\b',
    ],
    
    LayoutType.MATRIX: [
        r'\b(table|matrix|grid|spreadsheet|rows? and columns?)\b',
        r'\b(data table|comparison table|lookup table)\b',
        r'\b(cell|row|column|header)\b',
    ],
}

# Priority order for layout detection (higher = checked first)
LAYOUT_PRIORITY = [
    LayoutType.FORMULA,         # Very specific
    LayoutType.FACT_STAT,       # Has numbers
    LayoutType.TIMELINE,        # Has dates
    LayoutType.COMPARISON,      # Has vs/compare
    LayoutType.PROCESS_FLOW,    # Has steps
    LayoutType.CYCLE,           # Circular
    LayoutType.HIERARCHY,       # Tree structure
    LayoutType.MATRIX,          # Table
    LayoutType.CLASSIFICATION,  # Types/categories
    LayoutType.LIST_ARRAY,      # Generic list
    LayoutType.DEFINITION,      # What is X
    LayoutType.SIMPLE_EXPLAIN,  # Default fallback
]


def detect_layout_type(text: str, headline: str = "", context: Dict[str, Any] = None) -> LayoutType:
    """
    🧠 SEMANTIC CLASSIFIER
    
    Analyzes text content and determines the best visual layout.
    This is the "brain" that makes frames adapt to meaning.
    
    Args:
        text: The narration or explanation text
        headline: The headline/title of the scene
        context: Optional additional context (scene_type, data, etc.)
    
    Returns:
        LayoutType: The best layout for this content
    """
    context = context or {}
    combined_text = f"{headline} {text}".lower()
    
    # 1. Check if scene already has explicit layout hints in context
    if context.get('scene_type'):
        scene_type = context['scene_type'].lower()
        explicit_mappings = {
            'list': LayoutType.LIST_ARRAY,
            'process': LayoutType.PROCESS_FLOW,
            'flowchart': LayoutType.PROCESS_FLOW,
            'comparison': LayoutType.COMPARISON,
            'timeline': LayoutType.TIMELINE,
            'definition': LayoutType.DEFINITION,
            'fact': LayoutType.FACT_STAT,
            'formula': LayoutType.FORMULA,
            'array': LayoutType.LIST_ARRAY,
            'table': LayoutType.MATRIX,
            'diagram': LayoutType.HIERARCHY,
        }
        if scene_type in explicit_mappings:
            return explicit_mappings[scene_type]
    
    # 2. Check for data-driven hints
    if context.get('flow_nodes') or context.get('steps'):
        return LayoutType.PROCESS_FLOW
    if context.get('compare_left') or context.get('compare_right'):
        return LayoutType.COMPARISON
    if context.get('timeline_items'):
        return LayoutType.TIMELINE
    if context.get('formula_text') or context.get('formula_parts'):
        return LayoutType.FORMULA
    if context.get('table_headers') or context.get('table_rows'):
        return LayoutType.MATRIX
    if context.get('list_items') and len(context.get('list_items', [])) > 2:
        return LayoutType.LIST_ARRAY
    if context.get('fact_number'):
        return LayoutType.FACT_STAT
    
    # 3. Pattern matching on text
    scores = {layout: 0 for layout in LayoutType}
    
    for layout_type in LAYOUT_PRIORITY:
        patterns = SEMANTIC_PATTERNS.get(layout_type, [])
        for pattern in patterns:
            try:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                scores[layout_type] += len(matches)
            except re.error:
                continue
    
    # 4. Find best match (with priority consideration)
    best_layout = LayoutType.SIMPLE_EXPLAIN
    best_score = 0
    
    for layout_type in LAYOUT_PRIORITY:
        # Give slight priority boost to earlier items
        priority_boost = (len(LAYOUT_PRIORITY) - LAYOUT_PRIORITY.index(layout_type)) * 0.1
        adjusted_score = scores[layout_type] + priority_boost
        
        if scores[layout_type] > 0 and adjusted_score > best_score:
            best_score = adjusted_score
            best_layout = layout_type
    
    return best_layout


def get_layout_info(layout_type: LayoutType) -> FrameLayout:
    """Get the layout information for a given type"""
    return FRAME_LAYOUTS.get(layout_type, FRAME_LAYOUTS[LayoutType.SIMPLE_EXPLAIN])


def analyze_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a scene and add semantic layout information.
    
    This enriches the scene with:
    - detected_layout: The auto-detected layout type
    - layout_info: The layout template details
    - zones: Pixel-based zone positions (for rendering)
    """
    headline = scene.get('headline', '')
    narration = scene.get('narration', '')
    
    # Detect the best layout
    layout_type = detect_layout_type(
        text=narration,
        headline=headline,
        context=scene
    )
    
    # Get layout info
    layout_info = get_layout_info(layout_type)
    
    # Add to scene
    scene['detected_layout'] = layout_type.value
    scene['layout_info'] = layout_info
    
    return scene


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ACCENT COLOR SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

ACCENT_COLORS = {
    'green': (0, 255, 136),     # Neon Green
    'red': (255, 107, 107),     # Coral Red  
    'teal': (78, 205, 196),     # Teal
    'yellow': (255, 230, 109),  # Yellow
    'purple': (199, 125, 255),  # Purple
    'orange': (255, 159, 67),   # Orange
    'blue': (100, 149, 237),    # Cornflower Blue
    'pink': (255, 105, 180),    # Hot Pink
    'cyan': (0, 255, 255),      # Cyan
    'lime': (50, 205, 50),      # Lime Green
}

# Layout type → suggested accent colors
LAYOUT_ACCENT_SUGGESTIONS = {
    LayoutType.LIST_ARRAY: ['teal', 'green', 'blue'],
    LayoutType.PROCESS_FLOW: ['green', 'cyan', 'orange'],
    LayoutType.COMPARISON: ['red', 'green', 'purple'],  # Left vs Right
    LayoutType.TIMELINE: ['purple', 'blue', 'teal'],
    LayoutType.DEFINITION: ['yellow', 'orange', 'cyan'],
    LayoutType.CLASSIFICATION: ['purple', 'blue', 'green'],
    LayoutType.CYCLE: ['cyan', 'teal', 'green'],
    LayoutType.FACT_STAT: ['yellow', 'green', 'orange'],
    LayoutType.FORMULA: ['cyan', 'purple', 'yellow'],
    LayoutType.SIMPLE_EXPLAIN: ['teal', 'green', 'purple'],
}


def get_suggested_accent(layout_type: LayoutType, index: int = 0) -> Tuple[int, int, int]:
    """Get a suggested accent color for a layout type"""
    suggestions = LAYOUT_ACCENT_SUGGESTIONS.get(layout_type, ['green'])
    color_name = suggestions[index % len(suggestions)]
    return ACCENT_COLORS.get(color_name, (0, 255, 136))


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_zone_pixels(zone: Tuple[float, float, float, float], 
                          canvas_width: int, canvas_height: int) -> Dict[str, int]:
    """Convert percentage-based zone to pixel coordinates"""
    x_pct, y_pct, w_pct, h_pct = zone
    return {
        'x': int(canvas_width * x_pct),
        'y': int(canvas_height * y_pct),
        'width': int(canvas_width * w_pct),
        'height': int(canvas_height * h_pct),
    }


def get_all_zones_pixels(layout_type: LayoutType, 
                         canvas_width: int = 1080, 
                         canvas_height: int = 1920) -> Dict[str, Dict[str, int]]:
    """Get all zones as pixel coordinates for a layout"""
    layout = get_layout_info(layout_type)
    return {
        zone_name: calculate_zone_pixels(zone_pct, canvas_width, canvas_height)
        for zone_name, zone_pct in layout.zones.items()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DEBUG / LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def log_layout_detection(text: str, headline: str, result: LayoutType):
    """Debug logging for layout detection"""
    print(f"   🧠 SEMANTIC ANALYSIS:")
    print(f"      Headline: {headline[:40]}...")
    print(f"      Text sample: {text[:60]}...")
    print(f"      → Detected: {result.value.upper()}")
    layout = get_layout_info(result)
    print(f"      → Description: {layout.description.strip().split(chr(10))[1] if layout.description else 'N/A'}")


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 INTEGRATION POINT (for main.py)
# ═══════════════════════════════════════════════════════════════════════════════

def choose_layout(text: str, headline: str = "", scene_data: Dict = None) -> str:
    """
    Main entry point for semantic layout selection.
    
    This is the function that main.py should call to get the layout type.
    Returns a string that maps to FRAME_STYLES in main.py.
    
    Usage in main.py:
        from semantic_framing import choose_layout
        
        layout = choose_layout(narration, headline, scene)
        # Returns: "list_array", "process_flow", "comparison", etc.
    """
    layout_type = detect_layout_type(text, headline, scene_data or {})
    log_layout_detection(text, headline, layout_type)
    return layout_type.value


def get_layout_zones(layout_name: str, width: int = 1080, height: int = 1920) -> Dict[str, Dict[str, int]]:
    """
    Get pixel-based zone coordinates for a layout.
    
    Usage in main.py:
        from semantic_framing import get_layout_zones
        
        zones = get_layout_zones("comparison", 1080, 1920)
        # Returns: {'headline': {'x': 54, 'y': 57, ...}, 'left_panel': {...}, ...}
    """
    try:
        layout_type = LayoutType(layout_name)
    except ValueError:
        layout_type = LayoutType.SIMPLE_EXPLAIN
    
    return get_all_zones_pixels(layout_type, width, height)


# Quick test
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("There are 5 types of programming paradigms", "PARADIGMS", {}),
        ("First, we input the data. Then process it. Finally output results.", "HOW IT WORKS", {}),
        ("Python vs JavaScript - which is better for beginners?", "COMPARISON", {}),
        ("In 1969, the first message was sent. In 1991, the web was born.", "INTERNET HISTORY", {}),
        ("Recursion is when a function calls itself", "WHAT IS RECURSION?", {}),
        ("The company grew 500% in just 2 years", "GROWTH", {'fact_number': '500%'}),
        ("E = mc² where E is energy and m is mass", "EINSTEIN'S FORMULA", {'formula_text': 'E=mc²'}),
    ]
    
    print("🧪 SEMANTIC FRAMING TEST\n" + "="*50)
    for text, headline, ctx in test_cases:
        result = choose_layout(text, headline, ctx)
        print()
