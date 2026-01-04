"""
🎬 SMART VIDEO ENGINE
======================
Modern, dynamic, AI-driven video generation system.

This system:
1. Gets detailed 2000 word explanation from AI
2. Extracts knowledge units (micro-steps)
3. Classifies each unit's semantic meaning
4. Picks the RIGHT visual template for that meaning
5. Generates varied, modern, creative frames

NO fixed themes - every video is unique based on content!
"""

import os
import re
import json
import random
import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 MODERN COLOR PALETTES (Randomly selected per video)
# ═══════════════════════════════════════════════════════════════════════════════

COLOR_PALETTES = {
    "ocean": {
        "bg": (10, 25, 47),
        "primary": (0, 180, 216),
        "secondary": (144, 224, 239),
        "accent": (202, 240, 248),
        "highlight": (255, 200, 87),
        "text": (255, 255, 255),
        "muted": (100, 120, 140),
    },
    "sunset": {
        "bg": (30, 15, 25),
        "primary": (255, 107, 107),
        "secondary": (255, 159, 67),
        "accent": (254, 202, 87),
        "highlight": (72, 219, 251),
        "text": (255, 255, 255),
        "muted": (130, 100, 110),
    },
    "forest": {
        "bg": (15, 30, 20),
        "primary": (46, 213, 115),
        "secondary": (123, 237, 159),
        "accent": (200, 247, 197),
        "highlight": (255, 234, 167),
        "text": (255, 255, 255),
        "muted": (80, 110, 90),
    },
    "galaxy": {
        "bg": (20, 10, 35),
        "primary": (165, 94, 234),
        "secondary": (200, 148, 255),
        "accent": (232, 67, 147),
        "highlight": (253, 203, 110),
        "text": (255, 255, 255),
        "muted": (100, 80, 130),
    },
    "minimal": {
        "bg": (18, 18, 18),
        "primary": (255, 255, 255),
        "secondary": (200, 200, 200),
        "accent": (100, 200, 255),
        "highlight": (255, 220, 100),
        "text": (255, 255, 255),
        "muted": (80, 80, 80),
    },
    "neon": {
        "bg": (5, 5, 15),
        "primary": (0, 255, 136),
        "secondary": (0, 212, 255),
        "accent": (255, 0, 128),
        "highlight": (255, 255, 0),
        "text": (255, 255, 255),
        "muted": (60, 60, 80),
    },
    "warm": {
        "bg": (35, 20, 15),
        "primary": (255, 159, 28),
        "secondary": (255, 191, 105),
        "accent": (255, 107, 129),
        "highlight": (100, 220, 200),
        "text": (255, 255, 255),
        "muted": (120, 90, 80),
    },
    "tech": {
        "bg": (12, 20, 30),
        "primary": (0, 200, 255),
        "secondary": (100, 220, 255),
        "accent": (0, 255, 200),
        "highlight": (255, 200, 0),
        "text": (255, 255, 255),
        "muted": (70, 90, 110),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 📐 SEMANTIC FRAME TYPES (Based on MEANING, not decoration)
# ═══════════════════════════════════════════════════════════════════════════════

class FrameType(Enum):
    """Frame type is determined by WHAT we're explaining, not style preference."""
    
    # List/Array based
    ARRAY_DISPLAY = "array_display"          # Show items in boxes: [4] [1] [3] [2]
    ARRAY_HIGHLIGHT = "array_highlight"      # Same but one item highlighted
    ARRAY_COMPARE = "array_compare"          # Two items being compared
    ARRAY_SWAP = "array_swap"                # Two items swapping
    ARRAY_RESULT = "array_result"            # Final sorted/processed array
    
    # Process/Flow based
    PROCESS_FLOW = "process_flow"            # Input → Process → Output
    PROCESS_STEP = "process_step"            # Current step in a process
    PROCESS_BRANCH = "process_branch"        # Decision/branching
    
    # Comparison based
    SPLIT_COMPARE = "split_compare"          # Left vs Right comparison
    BEFORE_AFTER = "before_after"            # Before | After
    
    # Single focus
    BIG_STATEMENT = "big_statement"          # One big text/fact
    DEFINITION = "definition"                # Term: Definition
    CODE_BLOCK = "code_block"                # Code/formula display
    
    # Structural
    HIERARCHY = "hierarchy"                  # Parent → Children
    TIMELINE = "timeline"                    # Sequential events
    GRID_ITEMS = "grid_items"  
    #table
                  # Multiple items in grid
    
    # Narrative
    TITLE_INTRO = "title_intro"              # Video title/intro
    SUMMARY = "summary"                      # Wrap up / conclusion
    QUESTION = "question"                    # Posing a question
    
    # Special
    STATS_NUMBER = "stats_number"            # Big number with context
    ICON_EXPLAIN = "icon_explain"            # Icon + explanation


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 KNOWLEDGE UNIT - Micro-step of explanation
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class KnowledgeUnit:
    """A single micro-step of explanation."""
    
    id: int
    text: str                    # What narrator says
    meaning: str                 # What this step MEANS (list, compare, highlight, etc.)
    frame_type: FrameType        # Which frame template to use
    visual_data: Dict            # Data to render (items, values, etc.)
    duration: float = 4.0        # How long this frame shows
    transition: str = "fade"     # How to transition to next
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "meaning": self.meaning,
            "frame_type": self.frame_type.value,
            "visual_data": self.visual_data,
            "duration": self.duration,
            "transition": self.transition,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 SEMANTIC CLASSIFIER - Detect meaning from text
# ═══════════════════════════════════════════════════════════════════════════════

MEANING_PATTERNS = {
    # Title/Intro - HIGHEST PRIORITY for hooks
    "title_intro": [
        r"(today|in this video|let's learn|welcome|let's talk)",
        r"(ever wondered|what if|did you know)",
        r"(topic|about|going to explain|will show)",
        r"^\s*(what is|how does|why do)",
    ],
    
    # Question - hooks and curiosity
    "question": [
        r"(what|why|how|when|where|which)\s*\?",
        r"(ever wondered|do you know|think about|imagine)",
        r"(curious|question|wonder)",
    ],
    
    # Definition - explaining WHAT something IS
    "definition": [
        r"(is defined as|means|refers to|is basically|is like)",
        r"(what is a?|definition|meaning of)",
        r"(is a type of|is a kind of|is a way to)",
        r"(basically|simply put|in other words)",
        r"(a .* is|the .* is a)",
    ],
    
    # Comparison - comparing two things
    "split_compare": [
        r"(difference between|compare|versus|vs\.?)",
        r"(on one hand|on the other hand)",
        r"(while|whereas|but|however|unlike)",
        r"(better than|worse than|similar to|different from)",
        r"(like .* but|not like)",
    ],
    
    # Process/Flow - how things work step by step
    "process_flow": [
        r"(how .* works|process|the way)",
        r"(steps to|procedure|workflow)",
        r"(input.*output|takes.*returns|goes through)",
        r"(flow|pipeline|chain)",
        r"(points to|connects to|leads to)",
    ],
    
    # Process Step - individual step in sequence
    "process_step": [
        r"(step \d|first step|second step|next step)",
        r"(first,|second,|third,|then,|next,|finally,)",
        r"(now we|after this|following this)",
        r"(start by|begin with|end with)",
    ],
    
    # Hierarchy/Structure - parts and categories
    "hierarchy": [
        r"(types of|kinds of|categories of|parts of)",
        r"(includes|contains|consists of|made up of)",
        r"(has (two|three|four|many) (parts|types|kinds))",
        r"(components|elements of|structure)",
    ],
    
    # Summary/Conclusion - wrapping up
    "summary": [
        r"(in summary|to summarize|conclusion|recap)",
        r"(learned|covered|key takeaway|remember)",
        r"(so basically|the main point|to wrap up)",
        r"(don't forget|most important)",
    ],
    
    # Stats/Numbers - big numbers and facts
    "stats_number": [
        r"(\d+\s*%|\d+\s*percent|\d+\s*times)",
        r"(statistics|data shows|according to|research)",
        r"(billion|million|thousand|hundred)",
        r"(fastest|biggest|smallest|most|least)",
    ],
    
    # Example - real life analogy
    "example": [
        r"(for example|like when|imagine|think of)",
        r"(real life|everyday|in practice)",
        r"(like a|similar to a|same as)",
        r"(treasure hunt|train|chain|playlist)",
    ],
    
    # Array patterns - ONLY for actual algorithm/data stuff
    "array_display": [
        r"(\[\s*\d+(\s*,\s*\d+)+\s*\])",  # Actual array syntax [1,2,3]
        r"(unsorted array|sorted array|the array)",
        r"(elements? in (the|an) array)",
        r"(array of \d+|list of \d+)",
    ],
    "array_highlight": [
        r"(find the (minimum|maximum|smallest|largest))",
        r"(highlight|select|pick) (this|the) (element|value|number)",
        r"(at (index|position) \d+)",
        r"(current element|this element is)",
    ],
    "array_compare": [
        r"(compare \d+ (and|with|to) \d+)",
        r"(is \d+ (greater|less|equal) (than|to) \d+)",
        r"(comparing (the )?(two|these) (elements|values|numbers))",
    ],
    "array_swap": [
        r"(swap|exchange) (the )?(elements|values|numbers|\d+)",
        r"(switch (their )?positions?)",
        r"(move \d+ to)",
    ],
    "array_result": [
        r"(sorted!|result:|final array|output:)",
        r"(now (the )?array is|after sorting)",
        r"(sorted in (ascending|descending))",
    ],
    
    # Big statement - important points
    "big_statement": [
        r"(important|key point|crucial|essential)",
        r"(remember that|note that|keep in mind)",
        r"(the truth is|the reality is|here's the thing)",
    ],
    
    # Timeline - sequential events
    "timeline": [
        r"(history of|evolution of|over time)",
        r"(in \d{4}|years ago|century)",
        r"(progression|stages of|phases of)",
    ],
    
    # Code block - technical/formula
    "code_block": [
        r"(the code|function|algorithm looks)",
        r"(syntax|implementation|pseudo.?code)",
        r"(formula|equation|expression)",
        r"(def |function\(|=>|==|!=)",
    ],
}


def classify_meaning(text: str, scene_type: str = None) -> Tuple[str, FrameType]:
    """
    Classify text into semantic meaning and appropriate frame type.
    
    Args:
        text: The narration text to classify
        scene_type: Optional scene_type from AI (title, definition, etc.)
    
    Returns:
        (meaning_name, FrameType)
    """
    text_lower = text.lower()
    
    # FIRST: Check if AI already gave us a good scene_type
    scene_type_mapping = {
        'title': ('title_intro', FrameType.TITLE_INTRO),
        'hook': ('title_intro', FrameType.TITLE_INTRO),
        'definition': ('definition', FrameType.DEFINITION),
        'explanation': ('big_statement', FrameType.BIG_STATEMENT),
        'comparison': ('split_compare', FrameType.SPLIT_COMPARE),
        'example': ('example', FrameType.PROCESS_FLOW),
        'summary': ('summary', FrameType.SUMMARY),
        'process': ('process_flow', FrameType.PROCESS_FLOW),
        'flowchart': ('process_flow', FrameType.PROCESS_FLOW),
        'diagram': ('hierarchy', FrameType.HIERARCHY),
        'fact': ('stats_number', FrameType.STATS_NUMBER),
        'array': ('array_display', FrameType.ARRAY_DISPLAY),
        'table': ('hierarchy', FrameType.HIERARCHY),
        'formula': ('code_block', FrameType.CODE_BLOCK),
    }
    
    if scene_type and scene_type.lower() in scene_type_mapping:
        return scene_type_mapping[scene_type.lower()]
    
    # SECOND: Score based on patterns
    scores = {}
    for meaning, patterns in MEANING_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        if score > 0:
            scores[meaning] = score
    
    if not scores:
        # Default fallback
        return "big_statement", FrameType.BIG_STATEMENT
    
    # Get highest scoring meaning
    best_meaning = max(scores, key=scores.get)
    
    # Map meaning to frame type
    meaning_to_frame = {
        "title_intro": FrameType.TITLE_INTRO,
        "question": FrameType.QUESTION,
        "definition": FrameType.DEFINITION,
        "split_compare": FrameType.SPLIT_COMPARE,
        "process_flow": FrameType.PROCESS_FLOW,
        "process_step": FrameType.PROCESS_FLOW,  # Use same visual
        "hierarchy": FrameType.HIERARCHY,
        "summary": FrameType.SUMMARY,
        "stats_number": FrameType.STATS_NUMBER,
        "example": FrameType.PROCESS_FLOW,  # Examples as flows
        "array_display": FrameType.ARRAY_DISPLAY,
        "array_highlight": FrameType.ARRAY_HIGHLIGHT,
        "array_compare": FrameType.ARRAY_COMPARE,
        "array_swap": FrameType.ARRAY_SWAP,
        "array_result": FrameType.ARRAY_RESULT,
        "big_statement": FrameType.BIG_STATEMENT,
        "timeline": FrameType.TIMELINE,
        "code_block": FrameType.CODE_BLOCK,
    }
    
    return best_meaning, meaning_to_frame.get(best_meaning, FrameType.BIG_STATEMENT)


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 KNOWLEDGE EXTRACTOR - Parse AI response into knowledge units
# ═══════════════════════════════════════════════════════════════════════════════

def extract_visual_data(text: str, meaning: str) -> Dict:
    """Extract visual data from text based on meaning type."""
    
    data = {}
    
    # Extract numbers/arrays
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        data['numbers'] = [int(n) for n in numbers[:8]]
    
    # Extract quoted items
    quoted = re.findall(r'["\']([^"\']+)["\']', text)
    if quoted:
        data['items'] = quoted[:6]
    
    # Extract list items (after colons or dashes)
    list_items = re.findall(r'[-•]\s*(.+?)(?=[-•]|$)', text)
    if list_items:
        data['list_items'] = [item.strip() for item in list_items[:6]]
    
    # For comparison, try to find two sides
    if meaning in ['split_compare', 'before_after', 'array_compare']:
        vs_match = re.search(r'(.+?)\s+(?:vs|versus|compared to|or)\s+(.+)', text, re.I)
        if vs_match:
            data['left'] = vs_match.group(1).strip()[:30]
            data['right'] = vs_match.group(2).strip()[:30]
    
    # Extract key term for definitions
    if meaning == 'definition':
        def_match = re.search(r'^([^:]+):\s*(.+)', text)
        if def_match:
            data['term'] = def_match.group(1).strip()
            data['definition'] = def_match.group(2).strip()
    
    # Extract highlight position
    if meaning == 'array_highlight':
        pos_match = re.search(r'(position|index)\s*(\d+)', text, re.I)
        if pos_match:
            data['highlight_pos'] = int(pos_match.group(2))
        min_match = re.search(r'(minimum|smallest|min)', text, re.I)
        max_match = re.search(r'(maximum|largest|max)', text, re.I)
        if min_match:
            data['highlight_type'] = 'min'
        elif max_match:
            data['highlight_type'] = 'max'
    
    return data


def parse_ai_explanation(full_text: str, topic: str) -> List[KnowledgeUnit]:
    """
    Parse a long AI explanation into knowledge units.
    
    The AI should provide ~2000 words, which we break into 
    micro-steps for visualization.
    """
    units = []
    
    # Split into sentences/chunks
    # First try to split by numbered points
    numbered = re.split(r'\n\s*\d+[\.\)]\s*', full_text)
    
    if len(numbered) > 3:
        chunks = [c.strip() for c in numbered if c.strip()]
    else:
        # Split by paragraphs, then sentences
        paragraphs = full_text.split('\n\n')
        chunks = []
        for para in paragraphs:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            # Group 2-3 sentences together
            for i in range(0, len(sentences), 2):
                chunk = ' '.join(sentences[i:i+2])
                if len(chunk) > 20:
                    chunks.append(chunk.strip())
    
    # Create knowledge units from chunks
    for i, chunk in enumerate(chunks):
        if len(chunk) < 10:
            continue
            
        meaning, frame_type = classify_meaning(chunk)
        visual_data = extract_visual_data(chunk, meaning)
        
        # Add the main text as headline
        visual_data['headline'] = extract_headline(chunk)
        visual_data['narration'] = chunk
        
        unit = KnowledgeUnit(
            id=i + 1,
            text=chunk,
            meaning=meaning,
            frame_type=frame_type,
            visual_data=visual_data,
            duration=calculate_duration(chunk),
            transition=choose_transition(i, len(chunks))
        )
        units.append(unit)
    
    # Add intro and outro if not present
    if units and units[0].frame_type != FrameType.TITLE_INTRO:
        intro = KnowledgeUnit(
            id=0,
            text=f"Let's learn about {topic}",
            meaning="title_intro",
            frame_type=FrameType.TITLE_INTRO,
            visual_data={'headline': topic, 'subtitle': 'Quick Explanation'},
            duration=3.0,
            transition="fade"
        )
        units.insert(0, intro)
    
    return units


def extract_headline(text: str) -> str:
    """Extract a short headline from text."""
    # Take first meaningful phrase
    text = text.strip()
    
    # If starts with a short phrase before colon, use that
    colon_match = re.match(r'^([^:]{5,40}):', text)
    if colon_match:
        return colon_match.group(1).strip()
    
    # Otherwise take first 6 words
    words = text.split()[:6]
    headline = ' '.join(words)
    if len(headline) > 40:
        headline = headline[:37] + '...'
    return headline


def calculate_duration(text: str) -> float:
    """Calculate appropriate duration based on text length."""
    words = len(text.split())
    # Average speaking rate: ~150 words per minute
    # So ~2.5 words per second
    duration = max(3.0, min(8.0, words / 2.5))
    return round(duration, 1)


def choose_transition(index: int, total: int) -> str:
    """Choose transition type based on position."""
    if index == 0:
        return "fade_in"
    elif index == total - 1:
        return "fade_out"
    else:
        transitions = ["slide_left", "slide_up", "fade", "zoom"]
        return random.choice(transitions)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 VIDEO STYLE GENERATOR - Dynamic style per video
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VideoStyle:
    """Complete style for a video."""
    
    palette_name: str
    colors: Dict[str, Tuple[int, int, int]]
    font_style: str  # "modern", "bold", "minimal", "tech","aesthetic","classic","logpic"

    box_style: str   # "rounded", "sharp", "glow", "outline","bold","minimal"
    animation_speed: str  # "slow", "normal", "fast", "dynamic","creative"
    
    @classmethod
    def generate_for_topic(cls, topic: str) -> 'VideoStyle':
        """Generate a unique style based on topic keywords."""
        
        topic_lower = topic.lower()
        
        # Choose palette based on topic
        if any(w in topic_lower for w in ['code', 'algorithm', 'programming', 'tech', 'computer']):
            palette = random.choice(['tech', 'neon', 'minimal'])
        elif any(w in topic_lower for w in ['nature', 'biology', 'plant', 'animal', 'eco']):
            palette = random.choice(['forest', 'ocean'])
        elif any(w in topic_lower for w in ['space', 'star', 'universe', 'galaxy', 'physics']):
            palette = random.choice(['galaxy', 'ocean'])
        elif any(w in topic_lower for w in ['business', 'money', 'finance', 'marketing']):
            palette = random.choice(['warm', 'sunset'])
        else:
            palette = random.choice(list(COLOR_PALETTES.keys()))
        
        # Choose font style
        if any(w in topic_lower for w in ['code', 'algorithm', 'programming']):
            font_style = "tech"
        elif any(w in topic_lower for w in ['history', 'art', 'culture']):
            font_style = "modern"
        else:
            font_style = random.choice(["modern", "bold", "minimal"])
        
        # Choose box style
        box_styles = ["rounded", "sharp", "glow", "outline"]
        box_style = random.choice(box_styles)
        
        return cls(
            palette_name=palette,
            colors=COLOR_PALETTES[palette],
            font_style=font_style,
            box_style=box_style,
            animation_speed="normal"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 SCENE GENERATOR - Convert knowledge units to renderable scenes
# ═══════════════════════════════════════════════════════════════════════════════

def generate_scenes(units: List[KnowledgeUnit], style: VideoStyle) -> List[Dict]:
    """Convert knowledge units into renderable scene dictionaries."""
    
    scenes = []
    
    for unit in units:
        scene = {
            'id': unit.id,
            'frame_type': unit.frame_type.value,
            'meaning': unit.meaning,
            'headline': unit.visual_data.get('headline', ''),
            'narration': unit.text,
            'duration': unit.duration,
            'transition': unit.transition,
            'style': {
                'palette': style.palette_name,
                'colors': style.colors,
                'font_style': style.font_style,
                'box_style': style.box_style,
            },
            **unit.visual_data
        }
        scenes.append(scene)
    
    return scenes


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN API - Entry point for video generation
# ═══════════════════════════════════════════════════════════════════════════════

def create_video_plan(topic: str, ai_explanation: str) -> Dict:
    """
    Main entry point: Create a complete video plan from topic and AI explanation.
    
    Args:
        topic: The video topic
        ai_explanation: Long-form AI explanation (~2000 words)
    
    Returns:
        Complete video plan with scenes, style, and metadata
    """
    
    # Generate unique style for this video
    style = VideoStyle.generate_for_topic(topic)
    
    # Parse explanation into knowledge units
    units = parse_ai_explanation(ai_explanation, topic)
    
    # Convert to renderable scenes
    scenes = generate_scenes(units, style)
    
    # Calculate total duration
    total_duration = sum(scene['duration'] for scene in scenes)
    
    return {
        'topic': topic,
        'style': {
            'palette': style.palette_name,
            'font_style': style.font_style,
            'box_style': style.box_style,
        },
        'total_duration': total_duration,
        'num_scenes': len(scenes),
        'scenes': scenes,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 AI PROMPT GENERATOR - Generate prompt for detailed explanation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_explanation_prompt(topic: str, duration_minutes: int = 1) -> str:
    """
    Generate a prompt that asks AI for a detailed, structured explanation.
    This explanation will be parsed into visual frames.
    """
    
    is_code_topic = any(w in topic.lower() for w in ['code', 'python', 'java', 'script', 'function', 'class', 'algorithm', 'program', 'snippet', 'syntax'])
    
    code_instruction = ""
    if is_code_topic:
        code_instruction = """
        IMPORTANT - THIS IS A CODING VIDEO:
        - You MUST include a dedicated step showing the actual code snippet/syntax.
        - Start your response with a scene explicitly labeled "CODE:" containing the Python/Java/C++ code.
        - Explain the code line by line if possible.
        - Show input/output examples.
        """

    return f"""You are creating content for an educational SHORT video about: {topic}

Create a detailed explanation in approximately 1500-2000 words that will be converted into visual frames.
{code_instruction}

IMPORTANT STRUCTURE:
1. Start with an engaging hook/question about the topic
2. Break the explanation into clear, numbered micro-steps
3. Each step should explain ONE concept clearly
4. Use concrete examples with actual numbers/values when possible
5. Include comparisons (before/after, A vs B) where relevant
6. End with a memorable summary/takeaway

FORMAT GUIDELINES:
- Use numbered points (1. 2. 3. etc.)
- Each point should be 2-3 sentences
- Include specific examples: "For example, if we have [4, 1, 3, 2]..."
- Use clear language: "First we...", "Then we...", "This means..."
- Include at least one comparison or contrast
- Add one interesting fact or statistic if relevant

The explanation should be:
- Engaging and clear
- Visual-friendly (describe things that can be shown)
- Progressive (build understanding step by step)
- Complete (cover the topic fully)

Write the full explanation now:"""


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test with sample explanation
    test_topic = "Bubble Sort Algorithm"
    test_explanation = """
    1. What is Bubble Sort? Bubble Sort is one of the simplest sorting algorithms. It works by repeatedly comparing adjacent elements and swapping them if they are in the wrong order.
    
    2. Let's start with an unsorted array. Consider this array: [4, 1, 3, 2]. Our goal is to sort it in ascending order.
    
    3. First comparison: Compare 4 and 1. Since 4 is greater than 1, we swap them. The array becomes [1, 4, 3, 2].
    
    4. Next comparison: Compare 4 and 3. Since 4 is greater than 3, we swap them. The array becomes [1, 3, 4, 2].
    
    5. Third comparison: Compare 4 and 2. Since 4 is greater than 2, we swap them. The array becomes [1, 3, 2, 4].
    
    6. Notice that after one complete pass, the largest element (4) has "bubbled up" to its correct position at the end. This is why it's called Bubble Sort!
    
    7. Now we repeat the process for the remaining unsorted portion. We compare and swap until the entire array is sorted.
    
    8. Final result: After all passes, our array is sorted: [1, 2, 3, 4]. Each element is now in its correct position.
    
    9. Time complexity: Bubble Sort has O(n²) time complexity, making it inefficient for large datasets. However, it's great for learning and small arrays.
    
    10. In summary, Bubble Sort repeatedly compares adjacent elements and swaps them, "bubbling" larger elements to the end until the array is sorted.
    """
    
    plan = create_video_plan(test_topic, test_explanation)
    
    print(f"\n🎬 VIDEO PLAN FOR: {plan['topic']}")
    print(f"   Style: {plan['style']}")
    print(f"   Duration: {plan['total_duration']:.1f}s")
    print(f"   Scenes: {plan['num_scenes']}")
    print("\n📋 SCENES:")
    for scene in plan['scenes']:
        print(f"   [{scene['id']}] {scene['frame_type']:20s} | {scene['headline'][:40]}")
