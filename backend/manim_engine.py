"""
🎬 MANIM + MOVIEPY VIDEO ENGINE v2.0
=====================================
The GOLD combo for educational YouTube content.

NEW IN v2.0:
- AI-generated creative animation prompts for each scene
- Sync frame timing with audio duration (scene stays until narration ends)
- More interesting, dynamic animations

Flow:
1. Topic → AI generates script WITH animation descriptions
2. AI enhances each scene with creative animation prompts
3. Manim renders with proper duration
4. Edge-TTS generates voice
5. MoviePy syncs audio with video perfectly
6. Final video has frames that stay visible until narration completes
"""

import os
import json
import uuid
import asyncio
import sys
import tempfile
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Manim imports
from manim import *
from manim.utils.rate_functions import ease_out_elastic, ease_out_back

# MoviePy imports  
from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    CompositeVideoClip,
    concatenate_videoclips,
    concatenate_audioclips,
    ColorClip,
    TextClip
)

# Edge TTS for voice
import edge_tts

# Directories
MANIM_OUTPUT = "manim_output"
AUDIO_OUTPUT = "temp/audio"
FINAL_OUTPUT = "output"

os.makedirs(MANIM_OUTPUT, exist_ok=True)
os.makedirs(AUDIO_OUTPUT, exist_ok=True)
os.makedirs(FINAL_OUTPUT, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 THEME CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VideoTheme:
    """Theme configuration for video styling."""
    bg_color: str = "#141a24"
    primary_color: str = "#00ff88"
    secondary_color: str = "#40c4ff"
    accent_color: str = "#ff6496"
    text_color: str = "#ffffff"
    card_color: str = "#232d3c"
    
    # Manim-specific
    box_fill_opacity: float = 0.8
    stroke_width: float = 3
    animation_speed: float = 1.0


DEFAULT_THEME = VideoTheme()

THEMES = {
    "algorithm": VideoTheme(
        bg_color="#0f1419",
        primary_color="#00ff88",
        secondary_color="#40c4ff", 
        accent_color="#ff6496",
    ),
    "science": VideoTheme(
        bg_color="#0a1914",
        primary_color="#4cd964",
        secondary_color="#ffcc00",
        accent_color="#5ac8fa",
    ),
    "minimal": VideoTheme(
        bg_color="#141419",
        primary_color="#ffffff",
        secondary_color="#999999",
        accent_color="#ff6464",
    ),
    "vibrant": VideoTheme(
        bg_color="#190f23",
        primary_color="#ff64c8",
        secondary_color="#64ffc8",
        accent_color="#ffc864",
    ),
    "dark": VideoTheme(
        bg_color="#121212",
        primary_color="#bb86fc",
        secondary_color="#03dac6",
        accent_color="#cf6679",
    ),
    "light": VideoTheme(
        bg_color="#f0f0f0",
        primary_color="#1a73e8",
        secondary_color="#34a853",
        accent_color="#ea4335",
    ),
    "pastel": VideoTheme(
        bg_color="#fff8e1",
        primary_color="#ffab91",
        secondary_color="#80deea",
        accent_color="#a5d6a7",
    ),
    "neon": VideoTheme(
        bg_color="#000000",
        primary_color="#39ff14",
        secondary_color="#ff073a",
        accent_color="#0ff0fc",
    ),
    "retro": VideoTheme(
        bg_color="#2e1a47",
        primary_color="#ff6f61",
        secondary_color="#6b5b95",
        accent_color="#88b04b",
    ),
    "maths": VideoTheme(
        bg_color="#1e1e1e",
        primary_color="#d4d4d4",
        secondary_color="#569cd6",
        accent_color="#c586c0",
    ),  
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🎤 VOICE GENERATION (Edge TTS)
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_voice(text: str, output_path: str, 
                         voice: str = "en-US-ChristopherNeural") -> str:
    """Generate natural voice using Edge TTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def generate_voice_sync(text: str, output_path: str,
                       voice: str = "en-US-ChristopherNeural") -> str:
    """Synchronous wrapper for voice generation using subprocess."""
    import subprocess
    import sys
    
    # Use subprocess to avoid async loop conflicts
    # Use base64 encoding to safely pass the text to the subprocess
    import base64
    encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    script = f'''
import asyncio
import edge_tts
import base64

async def main():
    text = base64.b64decode("{encoded_text}").decode("utf-8")
    communicate = edge_tts.Communicate(text, "{voice}")
    await communicate.save("{output_path}")

asyncio.run(main())
'''
    
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"   ⚠️ TTS error: {result.stderr}")
        # Fallback to gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save(output_path)
        except Exception as e:
            print(f"   ⚠️ gTTS fallback failed: {e}")
    
    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(audio_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"   ⚠️ Could not get audio duration: {e}")
        return 5.0  # Default 5 seconds

def safe_wrap_text(text: str, max_width: int = 35) -> str:
    """Wraps text to prevent horizontal overflow."""
    if not text: return ""
    words = str(text).split()
    lines = []
    curr = []
    for w in words:
        if len(' '.join(curr + [w])) <= max_width:
            curr.append(w)
        else:
            if curr: lines.append(' '.join(curr))
            curr = [w]
    if curr: lines.append(' '.join(curr))
    return '\n'.join(lines)

class PremiumScene(Scene):
    """Base class for all high-aesthetic scenes with caption support."""
    def __init__(self, captions: List[str] = None, visual_manifest: Dict = None, **kwargs):
        # Filter kwargs to avoid TypeError in manim.Scene
        valid_scene_kwargs = ['renderer', 'camera_class', 'always_update_mobjects', 'random_seed']
        scene_kwargs = {k: v for k, v in kwargs.items() if k in valid_scene_kwargs}
        super().__init__(**scene_kwargs)
        self.captions = captions or []
        self.manifest = visual_manifest or {}
        
    def get_caption_group(self):
        """Returns a VGroup containing captions with modern minimal styling."""
        if not self.captions: return VGroup()
        
        full_text = " ".join(self.captions)
        text_color = self.manifest.get('accent_color', GRAY_A)
        font_size = 20
        
        wrapped = safe_wrap_text(full_text, max_width=45)
        
        caption = Text(
            wrapped,
            font_size=font_size,
            color=text_color,
            line_spacing=1.3,
            weight=LIGHT
        )
        
        # Hyper-minimalist background
        bg = RoundedRectangle(
            width=caption.width + 0.8,
            height=caption.height + 0.4,
            corner_radius=0.02,
            fill_color=BLACK,
            fill_opacity=0.2,
            stroke_width=0.3,
            stroke_color=WHITE,
            stroke_opacity=0.1
        )
        
        return VGroup(bg, caption).to_edge(DOWN, buff=0.4)

    def play_live_captions(self, cap_group, run_time=None):
        """Animates captions appearing as the scene plays."""
        if not cap_group: return
        if run_time is None: run_time = self.target_duration * 0.9
        
        bg, text = cap_group[0], cap_group[1]
        self.add(bg.set_opacity(0))
        self.play(bg.animate.set_opacity(0.2), run_time=0.5)
        self.play(Write(text, rate_func=linear, run_time=run_time))

    def safe_add_text(self, text, font_size=32, color=WHITE, weight=NORMAL, max_width=config.frame_width-2):
        """Creates text that scales down to fit the width."""
        txt = Text(text, font_size=font_size, color=color, weight=weight)
        if txt.width > max_width:
            txt.scale(max_width / txt.width)
        return txt

    def get_minimal_colors(self):
        """Extracts colors from LLM manifest or theme."""
        primary = self.manifest.get('colors', [self.theme.primary_color])[0]
        accent = self.manifest.get('colors', [self.theme.accent_color])[-1]
        return primary, accent


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 AI ANIMATION PROMPT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_animation_prompt(scene_type: str, headline: str, narration: str) -> Dict:
    """
    Use OpenRouter AI to generate creative animation descriptions for the scene.
    Returns enhanced animation parameters.
    """
    try:
        from app_secrets import OPENROUTER_API_KEY
    except:
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    if not OPENROUTER_API_KEY:
        # Return default animation params
        return get_default_animation_params(scene_type, headline, narration)

    # New dynamic AI prompt for full video script generation
    prompt = f"""
You are an expert educational video scriptwriter and animation director.
Given a topic and (optionally) a target audience (e.g. '10th board student'), break the topic into a sequence of scenes. For each scene, choose the most suitable frame type from this list:

- title: Catchy title with big icons
- definition: Term and clear description
- usage: Real-world applications (requires 'points' or 'usages' list)
- complexity: Time/Space complexity (requires 'time' and 'space' fields)
- summary: Key takeaways/checklist
- table: Comparison or data grid
- divide_merge_scene: Recursive algorithm splitting
- merge_process_scene: Sorted array merging
- code: Syntax-highlighted code block
- queue: First-In-First-Out data visualization
- tree: Classification/Hierarchy

For each scene, output a JSON object with:
    - type: (one of the above)
    - headline: (string)
    - narration: (what the narrator says)
    - points/items/usages/levels/time/space: (appropriate data)
    - animation_style: (pop, fade, slide)
    - duration_seconds: (estimated)

- Provide actual data structures (e.g. "branches": ["History", "Art"], "sequence": ["Step A", "Step B"]).
- Never use a static template.
- Use 'visual_logic' field to describe the structure (e.g., 'hierarchy', 'sequential', 'comparative', 'symbolic').
- CRITICAL: Never repeat the Headline as an item in the data list.
- Output a JSON object for the scene, no extra text or explanation.

Example for topic: Types of Clouds:
[
    {"type": "headline", "text": "TYPES OF CLOUDS", "duration_seconds": 2.0},
    {"type": "tree", "headline": "Classification", "root": "Clouds", "branches": ["High-level", "Mid-level", "Low-level"], "narration": "Clouds are categorized based on altitude into three main levels.", "duration_seconds": 5.0}
]

Now, for this topic and audience:
SCENE TYPE: {scene_type}
HEADLINE: {headline}
NARRATION: {narration}
Return ONLY valid JSON for the scene, no explanation.
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/devstral-2512:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    # Fallback if too complex
                    pass
        
    except Exception as e:
        print(f"   ⚠️ AI animation prompt failed: {e}")
    
    return get_default_animation_params(scene_type, headline, narration)


def get_default_animation_params(scene_type: str, headline: str, narration: str) -> Dict:
    """Return sensible default animation parameters."""
    import re
    
    # Extract numbers from narration
    numbers = [int(n) for n in re.findall(r'\b(\d+)\b', narration)][:8]
    if not numbers:
        numbers = [5, 3, 8, 1, 2]  # Default demo numbers
    
    # Extract key items
    items = []
    if ":" in narration:
        after_colon = narration.split(":")[-1]
        items = [s.strip() for s in after_colon.split(",") if s.strip()][:5]
    
    defaults = {
        "title": {
            "animation_style": "dramatic",
            "entrance_effect": "scale_up",
            "highlight_effect": "glow",
            "transition_out": "fade",
            "pacing": "medium",
            "emotion": "exciting"
        },
        "definition": {
            "animation_style": "smooth",
            "entrance_effect": "fade",
            "highlight_effect": "pulse",
            "transition_out": "fade",
            "pacing": "slow",
            "emotion": "calm"
        },
        "array": {
            "animation_style": "bouncy",
            "entrance_effect": "pop",
            "highlight_effect": "bounce",
            "transition_out": "fade",
            "pacing": "medium",
            "emotion": "playful"
        },
        "process": {
            "animation_style": "smooth",
            "entrance_effect": "slide_left",
            "highlight_effect": "color_shift",
            "transition_out": "slide_up",
            "pacing": "medium",
            "emotion": "serious"
        },
        "summary": {
            "animation_style": "gentle",
            "entrance_effect": "fade",
            "highlight_effect": "pulse",
            "transition_out": "fade",
            "pacing": "slow",
            "emotion": "calm"
        }
    }
    
    base = defaults.get(scene_type, defaults["definition"])
    base["key_numbers"] = numbers
    base["items_to_visualize"] = items if items else [headline]
    base["special_effects"] = []
    
    return base
    
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MANIM SCENE CLASSES (Duration-Aware + AI-Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

class TitleScene(PremiumScene):
    """High-aesthetic title scene with live captions."""
    def __init__(self, headline: str, subtitle: str = "", theme: VideoTheme = None, 
                 target_duration: float = 5.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.headline = headline
        self.subtitle = subtitle[:80]
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Minimalist Title
        title = self.safe_add_text(self.headline, font_size=56, color=WHITE, weight=BOLD)
        title.shift(UP * 0.5)
        
        # Subtitle or Accent Line
        line = Line(LEFT, RIGHT, color=accent, stroke_width=2).scale(2).next_to(title, DOWN, buff=0.3)
        
        caps = self.get_caption_group()
        
        # Animation sequence
        self.play(
            FadeIn(title, shift=UP*0.2),
            Create(line),
            run_time=1.2
        )
        
        # Live captions start
        self.play_live_captions(caps)
        
        # Hold
        wait_time = max(0.1, self.target_duration - 1.2 - 0.5)
        self.wait(wait_time)
        
        self.play(FadeOut(VGroup(title, line, caps)), run_time=0.5)


class ArrayScene(PremiumScene):
    """Minimalist array visualization with live captions."""
    def __init__(self, items: List, headline: str = "", theme: VideoTheme = None, 
                 target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}
    
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(FadeIn(title, shift=UP*0.3))
        
        # Boxes
        box_size = min(1.0, 7.5 / max(len(self.items), 1))
        boxes = VGroup()
        for i, val in enumerate(self.items):
            box = RoundedRectangle(
                width=box_size, height=box_size, corner_radius=0.05,
                fill_color=BLACK, fill_opacity=0.2,
                stroke_width=1, stroke_color=accent
            )
            label = self.safe_add_text(str(val), font_size=24)
            label.move_to(box)
            boxes.add(VGroup(box, label))
        
        boxes.arrange(RIGHT, buff=0.2).center().shift(UP*0.5)
        caps = self.get_caption_group()
        
        if len(boxes) > 0:
            self.play(LaggedStart(*[FadeIn(b, scale=0.8) for b in boxes], lag_ratio=0.1))
        else:
            self.wait(0.1)
        
        self.play_live_captions(caps)
        
        self.wait(max(0.5, self.target_duration - 2.0))
        self.play(FadeOut(boxes), FadeOut(caps), run_time=0.4)


class CodeScene(PremiumScene):
    """Minimalist code block visualization with live captions."""
    def __init__(self, code: str, headline: str = "", theme: VideoTheme = None, 
                 target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.code = code
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}
        
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title))
        
        # Minimal Code Block
        code_mobj = Code(
            code_string=self.code,
            tab_width=4,
            background="window",
            language="python",
            formatter_style="monokai",
            add_line_numbers=True,
            background_config={
                "stroke_width": 1,
                "stroke_color": accent,
                "fill_opacity": 0.2
            }
        ).center().shift(UP*0.3)
        
        # Scale for font size effect
        code_mobj.scale(0.8)
        
        if code_mobj.height > 5:
            code_mobj.scale(5 / code_mobj.height)
            
        caps = self.get_caption_group()
        
        self.play(FadeIn(code_mobj, shift=DOWN*0.2))
        self.play_live_captions(caps)
        
        self.wait(max(0.1, self.target_duration - 1.5))
        self.play(FadeOut(code_mobj), FadeOut(caps), run_time=0.4)

class LinkedListScene(PremiumScene):
    """Animated linked list visualization - synced to audio duration."""
    
    def __init__(self, nodes: List, headline: str = "",
                 theme: VideoTheme = None, 
                 target_duration: float = 6.0,
                 animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.nodes = nodes
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}
    
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        
        # Calculate timing
        intro_time = min(1.0, self.target_duration * 0.15)
        node_time = min(3.0, self.target_duration * 0.4)
        hold_time = max(2.0, self.target_duration - intro_time - node_time - 0.5)
        
        time_per_node = node_time / max(len(self.nodes), 1)
        
        # Title
        title = None
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time))
        
        # Create nodes
        node_group = VGroup()
        arrows = VGroup()
        
        for i, value in enumerate(self.nodes):
            # Node box (data + next pointer)
            data_box = Rectangle(
                width=1.2, height=0.8,
                fill_color=self.theme.card_color,
                fill_opacity=0.8,
                stroke_color=self.theme.primary_color,
                stroke_width=2
            )
            
            next_box = Rectangle(
                width=0.6, height=0.8,
                fill_color=self.theme.card_color,
                fill_opacity=0.6,
                stroke_color=self.theme.secondary_color,
                stroke_width=2
            )
            next_box.next_to(data_box, RIGHT, buff=0)
            
            # Value text (Safe)
            value_text = self.safe_add_text(str(value), font_size=24)
            value_text.move_to(data_box)
            
            # Dot in next pointer
            dot = Dot(radius=0.1, color=self.theme.secondary_color)
            dot.move_to(next_box)
            
            node = VGroup(data_box, next_box, value_text, dot)
            node_group.add(node)
        
        # Arrange and add arrows
        node_group.arrange(RIGHT, buff=1.0)
        node_group.center()
        
        for i in range(len(self.nodes) - 1):
            arrow = Arrow(
                node_group[i][1].get_right(),
                node_group[i+1][0].get_left(),
                color=self.theme.secondary_color,
                buff=0.1,
                stroke_width=3
            )
            arrows.add(arrow)
        
        # Add NULL at end
        null_text = Text("NULL", font_size=20, color=GRAY)
        null_text.next_to(node_group[-1], RIGHT, buff=0.5)
        
        # Captions
        caps = self.get_caption_group()

        # Animate with better pacing
        self.play(FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1), run_time=0.5)
        
        for i, node in enumerate(node_group):
            self.play(FadeIn(node, shift=RIGHT * 0.3), run_time=time_per_node * 0.6)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=time_per_node * 0.3)
        
        self.play(FadeIn(null_text), run_time=0.3)
        
        # HOLD - scene stays visible during narration
        self.wait(hold_time)
        
        # Fade out
        if title:
            self.play(FadeOut(title), run_time=0.2)
        self.play(
            FadeOut(node_group),
            FadeOut(arrows),
            FadeOut(null_text),
            FadeOut(caps) if caps else Wait(0.1),
            run_time=0.3
        )


class ProcessFlowScene(PremiumScene):
    """High-aesthetic process flow with live captions and dynamic arrows."""
    def __init__(self, steps: List[str], headline: str = "", theme: VideoTheme = None, 
                 target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.steps = steps
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(FadeIn(title, shift=UP*0.3))
            
        # Steps Group
        step_group = VGroup()
        for i, step in enumerate(self.steps[:5]):  # Limit to 5 for clarity
            box = RoundedRectangle(
                width=6, height=0.8, corner_radius=0.1,
                fill_color=BLACK, fill_opacity=0.2,
                stroke_width=1, stroke_color=accent
            )
            txt = self.safe_add_text(self.safe_wrap_text(step, 30), font_size=20)
            txt.move_to(box)
            step_group.add(VGroup(box, txt))
            
        step_group.arrange(DOWN, buff=0.5).center().shift(DOWN*0.2)
        
        arrows = VGroup()
        for i in range(len(step_group)-1):
            arr = Arrow(step_group[i].get_bottom(), step_group[i+1].get_top(), 
                        buff=0.1, color=accent, stroke_width=2).scale(0.8)
            arrows.add(arr)
            
        caps = self.get_caption_group()
        
        # Animation: One-by-one with narration
        time_per = (self.target_duration - 2) / max(len(step_group), 1)
        
        self.play_live_captions(caps)
        
        for i, scene_step in enumerate(step_group):
            self.play(FadeIn(scene_step, shift=RIGHT*0.2), run_time=time_per*0.7)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=time_per*0.3)
                
        self.wait(max(0.1, self.target_duration - (time_per * len(step_group)) - 1))
        self.play(FadeOut(VGroup(step_group, arrows, caps)), run_time=0.4)


class DefinitionScene(PremiumScene):
    """Refined definition card with collision-free layout."""
    def __init__(self, term: str, definition: str,
                 theme: VideoTheme = None, 
                 target_duration: float = 6.0,
                 animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.term = term
        self.definition = definition[:250]
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}
    
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # 1. Headline (Self-wrapping for long titles)
        wrapped_title = self.safe_wrap_text(self.term, max_width=25)
        title = self.safe_add_text(wrapped_title, font_size=40, color=primary, weight=BOLD)
        title.to_edge(UP, buff=0.6)
        
        # 2. Definition Card
        wrapped_def = self.safe_wrap_text(self.definition, max_width=45)
        def_text = self.safe_add_text(wrapped_def, font_size=26, color=WHITE, weight=LIGHT)
        
        card_w = min(11, def_text.width + 1.2)
        card_h = min(5, def_text.height + 1.0)
        
        card_bg = RoundedRectangle(
            width=card_w, height=card_h, corner_radius=0.1,
            fill_color=BLACK, fill_opacity=0.3,
            stroke_width=1.5, stroke_color=accent
        )
        
        # Group card items
        card_group = VGroup(card_bg, def_text)
        def_text.move_to(card_bg.get_center())
        
        # Position card group relative to title to avoid overlap
        card_group.next_to(title, DOWN, buff=0.8)
        
        # If card goes off screen, scale it down
        if card_group.get_bottom()[1] < -3.5:
            card_group.scale(0.8).next_to(title, DOWN, buff=0.5)
            
        caps = self.get_caption_group()
        
        # Animation
        self.play(FadeIn(title, shift=UP*0.3))
        self.play(Create(card_bg), FadeIn(def_text, shift=DOWN*0.1), run_time=1.0)
        
        self.play_live_captions(caps)
        
        self.wait(max(0.1, self.target_duration - 1.5))
        self.play(FadeOut(VGroup(title, card_group, caps)), run_time=0.4)


class SummaryScene(PremiumScene):
    """Ultra-modern summary with live captions and staggering points."""
    def __init__(self, headline: str, points: List[str],
                 theme: VideoTheme = None, 
                 target_duration: float = 6.0,
                 animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.headline = headline
        self.points = points[:4]
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        title = self.safe_add_text(f"✅ {self.headline}", font_size=40, weight=BOLD)
        title.to_edge(UP, buff=0.8)
        self.play(FadeIn(title, shift=UP*0.3))
        
        # Points with minimalist glass bars
        points_group = VGroup()
        for p in self.points:
            bar = RoundedRectangle(width=8, height=0.7, corner_radius=0.1,
                                   fill_color=BLACK, fill_opacity=0.2,
                                   stroke_width=1, stroke_color=accent)
            dot = Circle(radius=0.1, fill_color=accent, fill_opacity=1, stroke_width=0)
            dot.move_to(bar.get_left() + RIGHT*0.4)
            wrapped = self.safe_wrap_text(p, 35)
            txt = self.safe_add_text(wrapped, font_size=22)
            txt.next_to(dot, RIGHT, buff=0.3)
            points_group.add(VGroup(bar, dot, txt))
            
        points_group.arrange(DOWN, buff=0.4).center().shift(DOWN*0.2)
        caps = self.get_caption_group()
        
        time_per = (self.target_duration - 1.5) / max(len(points_group), 1)
        
        self.play_live_captions(caps)
        
        for point in points_group:
            self.play(
                FadeIn(point[0], shift=LEFT*0.2),
                FadeIn(point[1], scale=1.5),
                FadeIn(point[2], shift=RIGHT*0.1),
                run_time=time_per
            )
            
        self.wait(max(0.1, self.target_duration - (time_per * len(points_group)) - 1))
        self.play(FadeOut(VGroup(title, points_group, caps)), run_time=0.4)


class HeadlineScene(Scene):
    """Big headline or text for single-idea frames (e.g., section titles)."""
    def __init__(self, text: str, theme: VideoTheme = None, target_duration: float = 4.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(2.0, target_duration)
        self.anim_params = animation_params or {}
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        anim_time = min(1.5, self.target_duration * 0.3)
        hold_time = max(1.0, self.target_duration - anim_time - 0.5)
        style = self.anim_params.get("animation_style", "bouncy")
        entrance = self.anim_params.get("entrance_effect", "pop")
        headline = Text(self.text, font_size=64, color=self.theme.text_color, weight=BOLD)
        headline.move_to(UP * 1)
        if entrance == "pop":
            headline.scale(0.1)
            self.play(headline.animate.scale(10), run_time=anim_time * 0.5, rate_func=there_and_back_with_pause)
        elif entrance == "scale_up":
            self.play(headline.animate.scale(1.1), run_time=anim_time * 0.5)
            self.play(headline.animate.scale(1/1.1), run_time=0.2)
        else:
            self.play(Write(headline, run_time=anim_time * 0.5))
        self.wait(hold_time)
        self.play(FadeOut(headline), run_time=0.3)


# Insert new scene classes after theme config and Manim import

class TableScene(PremiumScene):
    """Animated table visualization - synced to audio duration."""
    def __init__(self, table: list, headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.table = table  # List of lists: [[header1, header2], [row1col1, row1col2], ...]
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(1.0, self.target_duration - intro_time - 0.5)
        
        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time * 0.5))
            
        if self.table:
            table_mobj = Table(self.table, include_outer_lines=True, line_config={"color": self.theme.primary_color})
            table_mobj.scale_to_fit_height(min(5, 7-caps.height if caps else 5))
            table_mobj.center()
            self.play(
                FadeIn(table_mobj, shift=UP * 0.3, run_time=intro_time * 0.5),
                FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1)
            )
            self.wait(hold_time)
            self.play(FadeOut(table_mobj), FadeOut(caps) if caps else Wait(0.1), run_time=0.3)
        if self.headline:
            self.play(FadeOut(title), run_time=0.2)

class FormulaScene(PremiumScene):
    """Animated formula visualization - synced to audio duration."""
    def __init__(self, formula: str, headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.formula = formula
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(1.0, self.target_duration - intro_time - 0.5)
        
        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time * 0.5))
            
        try:
            formula_mobj = MathTex(self.formula, font_size=60)
        except Exception:
            # Fallback to Text if LaTeX is missing
            formula_mobj = self.safe_add_text(self.formula, font_size=50, color=accent, weight=BOLD)
            
        if formula_mobj.width > config.frame_width - 1.5:
            formula_mobj.scale((config.frame_width - 1.5) / formula_mobj.width)
        formula_mobj.center()
        
        self.play(
            FadeIn(formula_mobj, shift=UP * 0.3, run_time=intro_time * 0.5),
            FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1)
        )
        self.wait(hold_time)
        self.play(FadeOut(formula_mobj), FadeOut(caps) if caps else Wait(0.1), run_time=0.3)
        if self.headline:
            self.play(FadeOut(title), run_time=0.2)

class DiagramScene(PremiumScene):
    """Animated diagram visualization - synced to audio duration."""
    def __init__(self, diagram_desc: str, headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.diagram_desc = diagram_desc
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}
    def construct(self):
        self.camera.background_color = self.theme.bg_color
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(1.0, self.target_duration - intro_time - 0.5)
        
        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time * 0.5))
            
        desc = self.safe_add_text(self.diagram_desc, font_size=32, color=self.theme.primary_color)
        desc.center()
        self.play(
            FadeIn(desc, shift=UP * 0.3, run_time=intro_time * 0.5),
            FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1)
        )
        self.wait(hold_time)
        self.play(FadeOut(desc), FadeOut(caps) if caps else Wait(0.1), run_time=0.3)
        if self.headline:
            self.play(FadeOut(title), run_time=0.2)

class ExampleScene(PremiumScene):
    """Minimalist example visualization with live captions."""
    def __init__(self, example_text: str, headline: str = "", theme: VideoTheme = None, 
                 target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.example_text = example_text
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(FadeIn(title, shift=UP*0.3))
            
        # Example Card (Glassmorphism)
        wrapped_txt = self.safe_wrap_text(self.example_text, max_width=45)
        text_mobj = self.safe_add_text(wrapped_txt, font_size=32, color=WHITE)
        
        card = RoundedRectangle(
            width=text_mobj.width + 1, height=text_mobj.height + 1,
            corner_radius=0.1, fill_color=BLACK, fill_opacity=0.2,
            stroke_width=1, stroke_color=accent
        ).center()
        
        text_mobj.move_to(card)
        
        caps = self.get_caption_group()
        
        self.play(Create(card), FadeIn(text_mobj), run_time=1.0)
        self.play_live_captions(caps)
        
        self.wait(max(0.1, self.target_duration - 1.5))
        self.play(FadeOut(VGroup(card, text_mobj, caps)), run_time=0.4)

class ComparisonScene(PremiumScene):
    """High-aesthetic comparison visualization with live captions."""
    def __init__(self, left: str, right: str, headline: str = "", theme: VideoTheme = None, 
                 target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(3.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        primary, accent = self.get_minimal_colors()
        
        # Headline
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(FadeIn(title, shift=UP*0.3))
            
        # Comparison Columns
        left_mobj = self.safe_add_text(self.safe_wrap_text(self.left, 20), font_size=28, color=WHITE)
        right_mobj = self.safe_add_text(self.safe_wrap_text(self.right, 20), font_size=28, color=WHITE)
        
        vs_text = self.safe_add_text("VS", font_size=36, color=accent, weight=BOLD)
        
        left_mobj.to_edge(LEFT, buff=1.2).shift(UP*0.3)
        right_mobj.to_edge(RIGHT, buff=1.2).shift(UP*0.3)
        vs_text.center().shift(UP*0.3)
        
        caps = self.get_caption_group()
        
        self.play(
            FadeIn(left_mobj, shift=RIGHT*0.5),
            FadeIn(vs_text, scale=1.2),
            FadeIn(right_mobj, shift=LEFT*0.5),
            run_time=1.2
        )
        
        self.play_live_captions(caps)
        self.wait(max(0.1, self.target_duration - 1.5))
        self.play(FadeOut(VGroup(left_mobj, right_mobj, vs_text, caps)), run_time=0.4)

class DivideMergeScene(PremiumScene):
    """Visualizes the divide-and-conquer principle (splitting arrays)."""
    def __init__(self, items: List, headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        
        # Calculate timing
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(2.0, self.target_duration - 4.0)

        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time), FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1))

        # We will show recursive splitting
        all_levels = []
        all_arrows = []
        
        current_level_items = [self.items]
        max_levels = 3 # 0, 1, 2
        
        # Level 0
        l0_group = VGroup(*[self._create_array(it, color=self.theme.primary_color, size=1.0) for it in current_level_items])
        l0_group.move_to(UP * 1.8)
        all_levels.append(l0_group)
        self.play(FadeIn(l0_group, shift=DOWN * 0.3), run_time=0.8)
        
        # Recursive splitting animation
        for l in range(1, max_levels):
            next_level_items = []
            has_split = False
            for it in current_level_items:
                if len(it) > 1:
                    mid = len(it) // 2
                    next_level_items.append(it[:mid])
                    next_level_items.append(it[mid:])
                    has_split = True
                else:
                    next_level_items.append(it)
            
            if not has_split:
                break
                
            scale = 0.8 ** l
            l_group = VGroup()
            # Create sub-arrays for this level
            for i, it in enumerate(next_level_items):
                arr = self._create_array(it, color=self.theme.secondary_color, size=scale)
                l_group.add(arr)
            
            # Arrange horizontally
            l_group.arrange(RIGHT, buff=0.4).next_to(all_levels[-1], DOWN, buff=1.0)
            
            # Arrows from parent level to child level
            l_arrows = VGroup()
            parent_level = all_levels[-1]
            child_idx = 0
            for p_idx, p_arr in enumerate(parent_level):
                # If parent had more than 1 item, it split into two
                if len(current_level_items[p_idx]) > 1:
                    a1 = Arrow(p_arr.get_bottom(), l_group[child_idx].get_top(), color=GRAY, stroke_width=2, buff=0.1)
                    a2 = Arrow(p_arr.get_bottom(), l_group[child_idx+1].get_top(), color=GRAY, stroke_width=2, buff=0.1)
                    l_arrows.add(a1, a2)
                    child_idx += 2
                else:
                    # Just one child (no split)
                    a = Arrow(p_arr.get_bottom(), l_group[child_idx].get_top(), color=GRAY, stroke_width=2, buff=0.1)
                    l_arrows.add(a)
                    child_idx += 1
            
            self.play(Create(l_arrows), run_time=0.5)
            self.play(FadeIn(l_group, shift=DOWN * 0.2), run_time=0.8)
            
            all_levels.append(l_group)
            all_arrows.append(l_arrows)
            current_level_items = next_level_items

        self.wait(hold_time)
        
        # Fade out
        fade_group = VGroup(*all_levels, *all_arrows)
        if self.headline:
            fade_group.add(title)
        self.play(FadeOut(fade_group), FadeOut(caps) if caps else Wait(0.1), run_time=0.5)

    def _create_array(self, items, color, size=1.0):
        group = VGroup()
        if not items: return group
        
        # Calculate box size to fit
        box_width = min(1.0, 6.0 / (len(items) * size + 0.1)) * size
        
        for item in items:
            square = Square(side_length=box_width, stroke_color=color, fill_color=self.theme.card_color, fill_opacity=0.6)
            label = Text(str(item), font_size=int(22 * box_width))
            label.move_to(square)
            group.add(VGroup(square, label))
        return group.arrange(RIGHT, buff=0.03)

class MergeProcessScene(PremiumScene):
    """Visualizes the merging phase of algorithms."""
    def __init__(self, items: List, headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items # Merged result
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        
        # Calculate timing
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(2.0, self.target_duration - 4.0)

        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=intro_time), FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1))

        if not self.items:
            self.items = [1, 3, 5, 8, 2, 4, 6, 7]

        # Multi-level merging visualization
        # We start with single elements or small pairs and merge up
        all_levels = []
        all_arrows = []
        
        # Let's simulate the tiers
        # Level 0 (bottom): individual or small groups
        # Level 1 (mid): larger sorted groups
        # Level 2 (result): final sorted array
        
        final_sorted = sorted(self.items)
        mid = len(final_sorted) // 2
        q1 = mid // 2
        q3 = mid + (len(final_sorted) - mid) // 2
        
        # Tier 0: 4 groups
        t0_items = [
            sorted(final_sorted[:q1]),
            sorted(final_sorted[q1:mid]),
            sorted(final_sorted[mid:q3]),
            sorted(final_sorted[q3:])
        ]
        t0_items = [it for it in t0_items if it] # Remove empty
        
        t0_group = VGroup(*[self._create_array(it, color=self.theme.secondary_color, size=0.6) for it in t0_items])
        t0_group.arrange(RIGHT, buff=0.4).move_to(UP * 1.5)
        all_levels.append(t0_group)
        self.play(FadeIn(t0_group, shift=DOWN * 0.2), run_time=0.8)
        
        # Tier 1: 2 groups
        t1_items = [sorted(final_sorted[:mid]), sorted(final_sorted[mid:])]
        t1_group = VGroup(*[self._create_array(it, color=self.theme.secondary_color, size=0.8) for it in t1_items])
        t1_group.arrange(RIGHT, buff=1.0).next_to(t0_group, DOWN, buff=1.0)
        
        # Arrows from T0 to T1
        t1_arrows = VGroup()
        if len(t0_items) >= 2:
            a1 = Arrow(t0_group[0].get_bottom(), t1_group[0].get_top(), color=GRAY, stroke_width=2)
            a2 = Arrow(t0_group[1].get_bottom(), t1_group[0].get_top(), color=GRAY, stroke_width=2)
            t1_arrows.add(a1, a2)
        if len(t0_items) >= 4:
            a3 = Arrow(t0_group[2].get_bottom(), t1_group[1].get_top(), color=GRAY, stroke_width=2)
            a4 = Arrow(t0_group[3].get_bottom(), t1_group[1].get_top(), color=GRAY, stroke_width=2)
            t1_arrows.add(a3, a4)
            
        self.play(Create(t1_arrows), run_time=0.5)
        self.play(FadeIn(t1_group, shift=DOWN * 0.3), run_time=0.8)
        all_levels.append(t1_group)
        all_arrows.append(t1_arrows)
        
        # Tier 2: Final
        t2_group = self._create_array(final_sorted, color=self.theme.primary_color, size=1.0)
        t2_group.next_to(t1_group, DOWN, buff=1.0)
        
        t2_arrows = VGroup(
            Arrow(t1_group[0].get_bottom(), t2_group.get_top(), color=GRAY, stroke_width=2),
            Arrow(t1_group[1].get_bottom(), t2_group.get_top(), color=GRAY, stroke_width=2)
        )
        
        self.play(Create(t2_arrows), run_time=0.5)
        self.play(FadeIn(t2_group, shift=DOWN * 0.3), run_time=0.8)
        all_levels.append(t2_group)
        all_arrows.append(t2_arrows)

        self.wait(hold_time)
        
        fade_group = VGroup(*all_levels, *all_arrows)
        if self.headline:
            fade_group.add(title)
        self.play(FadeOut(fade_group), FadeOut(caps) if caps else Wait(0.1), run_time=0.5)

    def _create_array(self, items, color, size=1.0):
        group = VGroup()
        if not items: return group
        box_width = min(1.0, 6.0 / (len(items) * size + 0.1)) * size
        for item in items:
            square = Square(side_length=box_width, stroke_color=color, fill_color=self.theme.card_color, fill_opacity=0.6)
            label = Text(str(item), font_size=int(22 * box_width))
            label.move_to(square)
            group.add(VGroup(square, label))
        return group.arrange(RIGHT, buff=0.03)

class SequentialManimScene(Scene):
    """
    UNIVERSAL CARRY-FORWARD SCENE (v3.0)
    Renders multiple script scenes in one continuous shot without clearing the frame.
    """
    def __init__(self, scenes: List[Dict], theme: VideoTheme = None, extractors: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.scenes = scenes
        self.theme = theme or DEFAULT_THEME
        self.extractors = extractors or {} # Dictionary of extraction functions
        self.active_mobjects = {} # Key: type, Value: Mobject
        self.current_headline = None

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        
        # --- 0. PREMIUM BACKGROUND DECOR ---
        # Add subtle floating particles to make it feel 'alive'
        bg_decor = VGroup()
        for _ in range(15):
            dot = Dot(radius=np.random.uniform(0.04, 0.1), color=self.theme.primary_color, fill_opacity=np.random.uniform(0.1, 0.3))
            dot.move_to([np.random.uniform(-4, 4), np.random.uniform(-7, 7), 0])
            bg_decor.add(dot)
        
        self.add(bg_decor)
        for dot in bg_decor:
            dot.add_updater(lambda d, dt: d.shift(UP * 0.15 * dt))
            dot.add_updater(lambda d: d.set_y(-7) if d.get_y() > 7 else None)
            d_val = np.random.uniform(0.2, 0.5)
            dot.add_updater(lambda d, dt, v=d_val: d.set_fill(opacity=0.2 + 0.1 * np.sin(self.renderer.time * v)))
        
        for i, scene in enumerate(self.scenes):
            start_time = self.renderer.time if hasattr(self.renderer, 'time') else 0
            
            stype = scene.get('scene_type', 'definition').lower()
            headline = scene.get('headline', '')
            narration = scene.get('narration', '')
            target_duration = scene.get('duration', 5.0)
            anim_params = scene.get('animation_params', {})
            
            # Tracking animation time
            current_step_anim_time = 0
            
            # --- 1. HEADLINE HANDLING ---
            if headline:
                h_time = 0.8
                if self.current_headline:
                    if headline != self.current_headline.text:
                        new_head = Text(headline, font_size=40, color=WHITE).to_edge(UP, buff=0.8)
                        self.play(ReplacementTransform(self.current_headline, new_head), run_time=h_time)
                        self.current_headline = new_head
                        current_step_anim_time += h_time
                else:
                    self.current_headline = Text(headline, font_size=40, color=WHITE).to_edge(UP, buff=0.8)
                    self.play(Write(self.current_headline), run_time=h_time)
                    current_step_anim_time += h_time

            # --- 2. DATA VISUALIZATION ---
            new_visual = self._render_visual_step(scene)
            
            if new_visual:
                old_visual = self.active_mobjects.get('main_visual')
                v_time = 1.0 # Standard timing
                
                # ADDING JUICE: Bouncy & Dynamic Transitions
                if old_visual:
                    if stype in ['array', 'divide_merge_scene', 'merge_process_scene', 'list', 'queue']:
                        # Bouncy transform for algorithms
                        self.play(ReplacementTransform(old_visual, new_visual), run_time=1.2, rate_func=ease_out_back)
                    else:
                        self.play(FadeOut(old_visual, scale=0.8), FadeIn(new_visual, scale=1.2, shift=UP*0.2), run_time=0.8)
                else:
                    self.play(FadeIn(new_visual, scale=0.5, shift=DOWN*0.5), run_time=1.0, rate_func=ease_out_elastic)
                
                # 5. AUTO-FIT TO SCREEN
                self._fit_to_screen(new_visual)

                # 6. LEAD EFFECT: SHINE TRANSITION
                # A quick 'shine' streak that passes over the visual to lead the eye
                shine = Line(new_visual.get_left() + LEFT, new_visual.get_right() + RIGHT, color=WHITE, stroke_width=4, stroke_opacity=0.6).move_to(new_visual)
                shine.set_width(0.1)
                self.play(shine.animate.set_width(new_visual.width).shift(RIGHT*0.2), run_time=0.4, rate_func=linear)
                self.remove(shine)

                # 7. POINTABLE: Focus indicator
                # If it's a list or array, add a pointer to the first or 'lead' element
                if stype in ['array', 'process', 'summary', 'usage']:
                    pointer = self._get_pointer(new_visual)
                    self.play(FadeIn(pointer, shift=DOWN*0.2), run_time=0.3)
                    self.play(pointer.animate.shift(UP*0.1), run_time=0.2, rate_func=there_and_back)
                    self.remove(pointer)
                
                # SUBTLE GLOW/PULSE ON FINISH
                if stype in ['complexity', 'usage', 'definition']:
                    self.play(new_visual.animate.set_stroke(opacity=1).set_color(self.theme.accent_color), run_time=0.3)
                    self.play(new_visual.animate.set_stroke(opacity=0.5).set_color(self.theme.primary_color), run_time=0.3)
                
                current_step_anim_time += v_time
                self.active_mobjects['main_visual'] = new_visual


            # --- 3. PRECISE WAIT ---
            # Calculate how much time is left for this scene's narration
            remaining_wait = target_duration - current_step_anim_time
            if remaining_wait > 0:
                self.wait(remaining_wait)
            else:
                self.wait(0.1) # Minimum breather

        # Final Fade out
        to_fade = [m for m in self.active_mobjects.values()]
        if self.current_headline:
            to_fade.append(self.current_headline)
        
        if to_fade:
            self.play(*[FadeOut(m) for m in to_fade], run_time=0.8)


    def _fit_to_screen(self, mobject, padding=0.5):
        """Scale down mobject if it exceeds the frame width/height."""
        frame_width = config.frame_width - padding
        frame_height = config.frame_height - 2.0 # Extra padding for headline/narration
        
        if mobject.width > frame_width:
            mobject.scale(frame_width / mobject.width)
        if mobject.height > frame_height:
            mobject.scale(frame_height / mobject.height)
        return mobject

    def _render_visual_step(self, scene):
        stype = scene.get('scene_type', 'definition').lower()
        # PRIORITY: Look in top-level scene first, then animation_params
        params = scene.get('animation_params', {})
        items = scene.get('items', params.get('key_numbers', params.get('items', params.get('levels', []))))
        headline = scene.get('headline', '')
        narration = scene.get('narration', '')
        
        if stype == 'array' or stype == 'list' or stype == 'queue':
            it = items or self.extractors.get('items', lambda x: [38, 27, 43, 3, 9, 82, 10])(narration)
            arr = self._create_array(it, color=self.theme.primary_color)
            if stype == 'queue':
                # Add Queue specific markers (Front/Rear) with icons
                f_label = VGroup(
                    Triangle(color=RED, fill_opacity=1).scale(0.12).rotate(-90*DEGREES),
                    Text("FRONT", font_size=18, color=RED, weight=BOLD)
                ).arrange(UP, buff=0.1).next_to(arr[0], UP, buff=0.3)
                
                r_label = VGroup(
                    Triangle(color=BLUE, fill_opacity=1).scale(0.12).rotate(90*DEGREES),
                    Text("REAR", font_size=18, color=BLUE, weight=BOLD)
                ).arrange(UP, buff=0.1).next_to(arr[-1], UP, buff=0.3)
                
                # Add background track
                track = RoundedRectangle(width=arr.width+0.5, height=arr.height+0.5, stroke_width=1, stroke_opacity=0.3).move_to(arr)
                return VGroup(track, arr, f_label, r_label).center()
            return arr.center()
            
        elif stype == 'divide_merge_scene':
            # ENHANCED MULTI-LEVEL SPLITTING
            it = items or [38, 27, 43, 3, 9, 82, 10]
            level_1 = self._create_array(it, color=self.theme.primary_color, size=0.8).move_to(UP * 2)
            mid = len(it) // 2
            it_l, it_r = it[:mid], it[mid:]
            level_2_l = self._create_array(it_l, color=self.theme.secondary_color, size=0.6)
            level_2_r = self._create_array(it_r, color=self.theme.secondary_color, size=0.6)
            level_2 = VGroup(level_2_l, level_2_r).arrange(RIGHT, buff=1.0).next_to(level_1, DOWN, buff=0.8)
            
            look_deep = any(w in headline.lower() or w in narration.lower() for w in ["further", "deep", "one", "single", "down", "base"])
            if look_deep:
                level_3 = VGroup()
                splits = [it_l[:len(it_l)//2], it_l[len(it_l)//2:], it_r[:len(it_r)//2], it_r[len(it_r)//2:]]
                for sub in splits:
                    if sub: level_3.add(self._create_array(sub, color=self.theme.accent_color, size=0.4))
                level_3.arrange(RIGHT, buff=0.3).next_to(level_2, DOWN, buff=0.6)
                return VGroup(level_1, level_2, level_3).center().shift(UP * 0.4)
            return VGroup(level_1, level_2).center().shift(UP * 0.4)
            
        elif stype == 'merge_process_scene' or stype == 'merge_scene':
            # MULTI-LEVEL MERGING
            it = sorted(items or [3, 9, 10, 27, 38, 43, 82])
            mid = len(it) // 2
            
            # Bottom (the halves)
            l_half = self._create_array(it[:mid], color=self.theme.secondary_color, size=0.7)
            r_half = self._create_array(it[mid:], color=self.theme.secondary_color, size=0.7)
            halves = VGroup(l_half, r_half).arrange(RIGHT, buff=2.0).move_to(UP * 0.5)
            
            # Top (the merged result)
            merged = self._create_array(it, color=self.theme.primary_color, size=0.9).next_to(halves, DOWN, buff=1.2)
            
            # Arrows merging down
            a1 = Arrow(l_half.get_bottom(), merged.get_top(), color=GRAY, stroke_width=2)
            a2 = Arrow(r_half.get_bottom(), merged.get_top(), color=GRAY, stroke_width=2)
            
            return VGroup(halves, merged, a1, a2).center()

        elif stype == 'usage':
            # PREMIUM USAGE GRID
            points = scene.get('usages', params.get('usages', params.get('points', [])))
            if not points and self.extractors.get('steps'): points = self.extractors['steps'](narration)
            if not points: points = ["Enterprise Systems", "Web Apps", "Mobile Dev"]
            
            grid = VGroup()
            for p in points[:3]:
                # Layered card design
                glow = RoundedRectangle(width=3.6, height=2.6, corner_radius=0.15, stroke_width=1, stroke_opacity=0.3, stroke_color=self.theme.primary_color)
                card = RoundedRectangle(width=3.5, height=2.5, corner_radius=0.1, fill_color=self.theme.card_color, fill_opacity=0.9, stroke_width=1, stroke_color=self.theme.primary_color)
                accent = Line(card.get_left(), card.get_right(), color=self.theme.primary_color, stroke_width=2, stroke_opacity=0.5).shift(UP*0.5)
                icon = Text("★", font_size=30, color=self.theme.accent_color).move_to(card.get_top() + DOWN*0.6)
                txt = Text(str(p), font_size=20, line_spacing=1.5).move_to(card.get_bottom() + UP*0.8)
                grid.add(VGroup(glow, card, accent, icon, txt))
            return grid.arrange(RIGHT, buff=0.5).center()

        elif stype == 'complexity':
            # THEMED COMPLEXITY BOARD
            time = scene.get('time', params.get('time', r'O(n \log n)'))
            space = scene.get('space', params.get('space', 'O(1)'))
            glow = RoundedRectangle(width=7.2, height=4.2, corner_radius=0.2, stroke_width=1, stroke_color=self.theme.secondary_color, stroke_opacity=0.3)
            board = RoundedRectangle(width=7, height=4, corner_radius=0.1, fill_color=self.theme.card_color, fill_opacity=0.8, stroke_width=2, stroke_color=self.theme.secondary_color)
            accent = Line(board.get_top() + DOWN*0.8, board.get_top() + DOWN*0.8, color=self.theme.secondary_color).scale(3.5).set_stroke(opacity=0.5)
            t_label = Text("Time Complexity:", font_size=24, color=WHITE).move_to(board.get_top() + DOWN*1.0)
            
            # Using MathTex for complexity values
            try:
                t_val = MathTex(str(time), color=self.theme.primary_color).scale(1.5).next_to(t_label, DOWN)
            except:
                t_val = Text(str(time), font_size=36, color=self.theme.primary_color).next_to(t_label, DOWN)
                
            s_label = Text("Space:", font_size=20, color=GRAY).next_to(t_val, DOWN, buff=0.5)
            try:
                s_val = MathTex(str(space), color=self.theme.secondary_color).scale(1.1).next_to(s_label, RIGHT)
            except:
                s_val = Text(str(space), font_size=24, color=self.theme.secondary_color).next_to(s_label, RIGHT)
                
            return VGroup(board, t_label, t_val, s_label, s_val).center()

        elif stype == 'formula':
            f_str = params.get('formula', scene.get('formula', r'E = mc^2'))
            title = params.get('name', 'Formula')
            card = RoundedRectangle(width=8, height=4, corner_radius=0.1, fill_color=self.theme.card_color, fill_opacity=0.9)
            t_label = Text(title, font_size=28, color=self.theme.accent_color).move_to(card.get_top() + DOWN*0.6)
            try:
                formula = MathTex(f_str).scale(2.0).next_to(t_label, DOWN, buff=0.5)
            except:
                formula = Text(f_str, font_size=40).next_to(t_label, DOWN, buff=0.5)
            return VGroup(card, t_label, formula).center()

        elif stype == 'tree' or stype == 'hierarchy':
            root = params.get('root', scene.get('headline', 'System'))
            branches = params.get('branches', [])
            
            # FALLBACK: If AI didn't provide branches, extract categories from narration
            if not branches:
                branches = self.extractors.get('items', lambda x: [])(narration)
                if not branches:
                    # Look for colon-separated lists: "Categories: A, B, and C"
                    import re
                    match = re.search(r':\s*([^.]+)', narration)
                    if match:
                        branches = [i.strip() for i in re.split(r',|and', match.group(1)) if len(i.strip()) > 2]
                if not branches: branches = ['Category A', 'Category B'] # Hard fallback

            # PREMIUM TREE DESIGN - More vertical for 9:16
            r_node = self._create_node(root, color=self.theme.primary_color)
            r_node.move_to(UP * 2.5) # Top center
            
            b_group = VGroup()
            for i, b in enumerate(branches[:5]):
                color = self.theme.secondary_color if i % 2 == 0 else self.theme.accent_color
                b_group.add(self._create_node(b, color=color, size=0.85))
            
            b_group.arrange_in_grid(rows=None, cols=2, buff=0.4).move_to(DOWN * 1.5)
            
            # Curved lines for a more 'organic' tree feel
            lines = VGroup()
            for b in b_group:
                start = r_node.get_bottom()
                end = b.get_top()
                line = CubicBezier(
                    start, 
                    start + DOWN*1.5, 
                    end + UP*1.5, 
                    end, 
                    color=GRAY, 
                    stroke_width=2, 
                    stroke_opacity=0.4
                )
                lines.add(line)
                
            return VGroup(r_node, b_group, lines).center()

        elif stype == 'comparison':
            left = params.get('left', params.get('compare_left', 'A'))
            right = params.get('right', params.get('compare_right', 'B'))
            l_box = self._create_node(str(left), color=self.theme.primary_color)
            r_box = self._create_node(str(right), color=self.theme.secondary_color)
            vs = Text("VS", font_size=32, color=RED)
            group = VGroup(l_box, vs, r_box).arrange(RIGHT, buff=1.0).center()
            return group

        elif stype == 'summary' or stype == 'process':
            points = scene.get('points', params.get('points', params.get('steps', [])))
            if not points and self.extractors.get('steps'): points = self.extractors['steps'](narration)
            if not points: points = ["Efficient", "Reliable", "Scalable"]
            
            group = VGroup()
            for p in points[:5]:
                if str(p).strip().upper() == headline.strip().upper(): continue
                # Premium Pill Style
                pill = RoundedRectangle(width=max(4.0, len(str(p))*0.22), height=0.7, corner_radius=0.1, fill_color=self.theme.card_color, fill_opacity=0.7, stroke_width=1, stroke_color=self.theme.primary_color)
                dot = Star(n=5, color=self.theme.accent_color, fill_opacity=1).scale(0.12).move_to(pill.get_left() + RIGHT*0.4)
                txt = Text(str(p)[:45], font_size=20, color=WHITE).next_to(dot, RIGHT, buff=0.3)
                group.add(VGroup(pill, dot, txt))
            return group.arrange(DOWN, aligned_edge=LEFT, buff=0.3).center()
            
        elif stype in ['definition', 'explanation', 'title', 'concept_flow_scene', 'fact', 'intro']:
            # PREMIUM GLASSMORPHISM CARD
            card_w, card_h = 8.8, 5.5
            
            # 1. Outer Glow
            glow = RoundedRectangle(width=card_w + 0.15, height=card_h + 0.15, corner_radius=0.2, stroke_width=2, stroke_color=self.theme.primary_color, stroke_opacity=0.3)
            
            # 2. Main Card Body
            card = RoundedRectangle(width=card_w, height=card_h, corner_radius=0.15, fill_color=self.theme.card_color, fill_opacity=0.85, stroke_width=1, stroke_color=self.theme.primary_color, stroke_opacity=0.6)
            
            # 3. Accent Bar (Top)
            accent_bar = Line(card.get_top() + LEFT*2, card.get_top() + RIGHT*2, color=self.theme.secondary_color, stroke_width=4).shift(DOWN*0.1)
            
            # 4. Icon (Geometric or themed)
            icon = VGroup(
                Circle(radius=0.4, color=self.theme.accent_color, stroke_width=2),
                Star(n=5, color=self.theme.accent_color, fill_opacity=1).scale(0.15)
            ).next_to(card.get_top(), DOWN, buff=0.4)
            
            # 5. Headline with Background Plate
            label_text = headline or "CONCEPT"
            l_txt = Text(label_text, font_size=34, color=WHITE, weight=BOLD).next_to(icon, DOWN, buff=0.3)
            underline = Underline(l_txt, color=self.theme.primary_color, buff=0.1)
            
            # 6. Hybrid Content Layout (Points + Sub-Captions)
            points = params.get('points', scene.get('points', []))
            
            # --- Point Highlights (Center) ---
            body_content = VGroup()
            if points:
                for p in points[:3]:
                    dot = Star(n=5, color=self.theme.accent_color, fill_opacity=1).scale(0.08)
                    p_txt = Text(str(p)[:40], font_size=20, color=WHITE, weight=BOLD)
                    row = VGroup(dot, p_txt).arrange(RIGHT, buff=0.2)
                    body_content.add(row)
                body_content.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            
            # --- Narration Caption (Bottom Footer) ---
            # We wrap the narration into a smaller, semi-transparent footer block
            words = narration.split()
            nav_lines = []
            curr_line = []
            for w in words:
                curr_line.append(w)
                if len(' '.join(curr_line)) > 45: 
                    nav_lines.append(' '.join(curr_line))
                    curr_line = []
            if curr_line: nav_lines.append(' '.join(curr_line))
            
            caption_txt = Text('\n'.join(nav_lines[:3]), font_size=16, line_spacing=1.4, color=GRAY_A, slant=ITALIC)
            caption_box = RoundedRectangle(width=card_w - 1, height=caption_txt.height + 0.4, corner_radius=0.1, fill_color=BLACK, fill_opacity=0.3, stroke_width=0)
            footer = VGroup(caption_box, caption_txt).move_to(card.get_bottom() + UP*0.8)

            # Center the highlights in the remaining space
            if body_content.height > 0:
                body_content.move_to(VGroup(l_txt, footer).get_center())

            # Header + Highlights + Footer
            content = VGroup(icon, l_txt, underline, body_content, footer)
            
            return VGroup(glow, card, accent_bar, content).center()
            
        return None

    def _create_node(self, text, color, size=1.0):
        # PREMIUM NODE WITH GLOW & SHADOW
        node_width = max(2.5, len(text)*0.18)*size
        node_height = 0.8*size
        
        # 1. Lead Glow Effect
        glow = RoundedRectangle(width=node_width + 0.15, height=node_height + 0.15, corner_radius=0.15, stroke_width=2, stroke_color=color, stroke_opacity=0.3)
        
        # 2. Glass Card
        rect = RoundedRectangle(width=node_width, height=node_height, corner_radius=0.1, stroke_width=2, stroke_color=color, fill_color=self.theme.card_color, fill_opacity=0.9)
        
        # 3. Text with subtle shadow
        txt = Text(text, font_size=24*size, color=WHITE).move_to(rect)
        
        node = VGroup(glow, rect, txt)
        
        # Subtle animation for 'life'
        glow.add_updater(lambda g, dt: g.set_stroke(opacity=0.2 + 0.1 * np.sin(self.renderer.time * 2)))
        
        return node

    def _create_array(self, items, color, size=1.0):
        # PREMIUM ARRAY WITH INDEX POINTERS
        group = VGroup()
        if not items: return group
        box_width = min(1.0, 6.0 / (len(items) * size + 0.1)) * size
        
        for i, item in enumerate(items):
            # Square with glow
            sq_glow = Square(side_length=box_width + 0.05, stroke_width=1, stroke_color=color, stroke_opacity=0.3)
            square = Square(side_length=box_width, stroke_color=color, fill_color=self.theme.card_color, fill_opacity=0.7)
            label = Text(str(item), font_size=int(22 * box_width), color=WHITE)
            label.move_to(square)
            
            # Tiny index indicator (Pointable)
            idx = Text(str(i), font_size=int(10 * box_width), color=GRAY).next_to(square, DOWN, buff=0.1)
            
            cell = VGroup(sq_glow, square, label, idx)
            group.add(cell)
            
        array = group.arrange(RIGHT, buff=0.03)
        return array

    def _get_pointer(self, target):
        """Returns a glowing pointer icon directing to a target."""
        pointer = VGroup(
            Arrow(UP, DOWN, color=self.theme.accent_color, buff=0).scale(0.3),
            Dot(color=self.theme.accent_color, radius=0.05).set_stroke(self.theme.accent_color, opacity=0.5, width=4)
        ).next_to(target, UP, buff=0.2)
        return pointer
        
class TreeScene(PremiumScene):
    """Visualizes hierarchies or classifications as a tree structure."""
    def __init__(self, root_text: str, branches: List[str], headline: str = "", theme: VideoTheme = None, target_duration: float = 6.0, animation_params: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.root_text = root_text or "Hierarchy"
        self.branches = branches[:5] if branches else []
        self.headline = headline
        self.theme = theme or DEFAULT_THEME
        self.target_duration = max(4.0, target_duration)
        self.anim_params = animation_params or {}

    def construct(self):
        self.camera.background_color = self.theme.bg_color
        intro_time = min(1.0, self.target_duration * 0.2)
        hold_time = max(1.0, self.target_duration - intro_time - 0.5)
        
        caps = self.get_caption_group()
        if self.headline:
            title = self.safe_add_text(self.headline, font_size=40)
            title.to_edge(UP, buff=0.8)
            self.play(Write(title, run_time=1))

        # Root node
        root_node = self._create_node(self.root_text, color=self.theme.primary_color)
        
        if not self.branches:
            root_node.center()
            self.play(FadeIn(root_node, scale=0.8), FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1))
            self.wait(max(1.0, self.target_duration - 2))
            self.play(FadeOut(root_node), FadeOut(caps) if caps else Wait(0.1))
            return

        root_node.move_to(UP * 1.5)

        # Child nodes
        child_nodes = VGroup()
        for branch in self.branches:
            child_nodes.add(self._create_node(branch, color=self.theme.secondary_color, size=0.7))
        
        child_nodes.arrange(RIGHT, buff=0.5).move_to(DOWN * 1.5)

        # Connect with lines
        lines = VGroup()
        for child in child_nodes:
            line = Line(root_node.get_bottom(), child.get_top(), color=GRAY, stroke_width=2)
            lines.add(line)

        # Animation
        self.play(FadeIn(root_node, scale=0.8), FadeIn(caps, shift=UP*0.1) if caps else Wait(0.1))
        self.wait(0.5)
        self.play(Create(lines), run_time=1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in child_nodes], lag_ratio=0.2), run_time=1.5)
        
        self.wait(max(1.0, self.target_duration - 4))
        self.play(FadeOut(VGroup(root_node, child_nodes, lines)), FadeOut(caps) if caps else Wait(0.1))

    def _create_node(self, text, color, size=1.0):
        rect = RoundedRectangle(width=max(2.5, len(text)*0.15)*size, height=0.8*size, corner_radius=0.1, stroke_color=color, fill_color=self.theme.card_color, fill_opacity=0.8)
        label = Text(text[:20], font_size=int(22 * size))
        label.move_to(rect)
        return VGroup(rect, label)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 VIDEO GENERATOR (v2.0 - Duration-Aware + AI-Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

class ManimVideoGenerator:
    """
    Main video generator using Manim + MoviePy + Edge-TTS.
    
    v2.0 Features:
    - AI-generated animation prompts for each scene
    - Duration syncing (scenes stay visible until narration ends)
    - Better pacing based on content
    
    Usage:
        generator = ManimVideoGenerator(theme="algorithm")
        video_path = generator.generate_from_script(script_json)
    """
    
    def __init__(self, theme_name: str = "algorithm"):
        self.theme = THEMES.get(theme_name, DEFAULT_THEME)
        self.temp_dir = tempfile.mkdtemp()
        self.scene_clips = []
        self.audio_clips = []
    
    def render_scene(self, scene_class, **kwargs) -> str:
        """Render a single Manim scene to video file."""
        # Add theme to kwargs
        kwargs['theme'] = self.theme
        
        # Create unique filename
        scene_id = str(uuid.uuid4())[:8]
        output_file = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")
        
        # Configure Manim
        config.pixel_width = 1080
        config.pixel_height = 1920
        config.frame_rate = 30
        config.output_file = output_file
        config.write_to_movie = True
        config.disable_caching = True
        
        # Render
        scene = scene_class(**kwargs)
        scene.render()
        
        return output_file
    
    def generate_scene_video(self, scene_data: Dict) -> Tuple[str, str, float]:
        """
        Generate video and audio for a single scene.
        
        v2.0: First generates audio to get duration, then renders scene to match.
        
        Returns: (video_path, audio_path, duration)
        """
        scene_type = scene_data.get('scene_type', 'definition').lower()
        headline = scene_data.get('headline', '')
        narration = scene_data.get('narration', '')
        
        # STEP 1: Generate voice FIRST to get duration
        audio_id = str(uuid.uuid4())[:8]
        audio_path = os.path.join(self.temp_dir, f"audio_{audio_id}.mp3")
        generate_voice_sync(narration, audio_path)
        
        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        print(f"      🎤 Audio duration: {audio_duration:.1f}s")
        
        # STEP 2: Generate AI animation prompts (now also asks for duration)
        print(f"      🤖 Generating AI animation prompt...")
        animation_params = generate_animation_prompt(scene_type, headline, narration)
        print(f"      ✨ Style: {animation_params.get('animation_style', 'default')}, Entrance: {animation_params.get('entrance_effect', 'fade')}")

        # Use AI duration if present and longer than audio
        ai_duration = None
        try:
            ai_duration = int(animation_params.get('duration_seconds', 0))
        except Exception:
            ai_duration = None
        target_duration = max(audio_duration, ai_duration) if ai_duration and ai_duration > 0 else audio_duration
        print(f"      ⏱️ Scene duration: {target_duration:.1f}s (audio: {audio_duration:.1f}s, ai: {ai_duration})")

        # STEP 3: Render Manim scene with target duration and AI params
        if scene_type in ['headline', 'text']:
            text = scene_data.get('text', headline or narration)
            video_path = self.render_scene(
                HeadlineScene,
                text=text,
                target_duration=target_duration,
                animation_params=animation_params
            )

        elif scene_type == 'title':
            video_path = self.render_scene(
                TitleScene,
                headline=headline,
                subtitle=narration[:80],
                target_duration=target_duration,
                animation_params=animation_params
            )

        elif scene_type == 'definition':
            video_path = self.render_scene(
                DefinitionScene,
                term=headline,
                definition=narration,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'array':
            # Extract items from manifest primary_object or AI params
            items = scene_data.get('visual_manifest', {}).get('primary_object', animation_params.get('key_numbers', self._extract_items(narration)))
            video_path = self.render_scene(
                ArrayScene,
                items=items,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'code':
            # Priority: manifest primary_object > scene_data['code'] > narration
            code = ""
            if 'visual_manifest' in scene_data and scene_data['visual_manifest'].get('primary_object'):
                code = str(scene_data['visual_manifest']['primary_object'])
            
            if not code or len(code) < 10: # If manifest is empty or too short, fallback
                code = scene_data.get('code', narration)

            video_path = self.render_scene(
                CodeScene,
                code=code,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'linked_list':
            nodes = animation_params.get('primary_object', animation_params.get('key_numbers', self._extract_items(narration)))
            video_path = self.render_scene(
                LinkedListScene,
                nodes=nodes,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type in ['process', 'flowchart']:
            steps = animation_params.get('steps', animation_params.get('items_to_visualize', self._extract_steps(narration)))
            steps = self._filter_redundant_points(steps, headline)
            video_path = self.render_scene(
                ProcessFlowScene,
                steps=steps,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'summary':
            points = animation_params.get('primary_object', animation_params.get('points', animation_params.get('items_to_visualize', self._extract_steps(narration))))
            if isinstance(points, str): points = [points]
            points = self._filter_redundant_points(points, headline)
            video_path = self.render_scene(
                SummaryScene,
                headline=headline,
                points=points,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'table':
            # Table: expects a 2D list (rows), optional headline
            table = animation_params.get('primary_object', scene_data.get('table', animation_params.get('table', [])))
            video_path = self.render_scene(
                TableScene,
                table=table,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type in ['formula', 'math']:
            # Formula: expects a LaTeX string, optional headline
            formula = animation_params.get('primary_object', scene_data.get('formula', narration))
            video_path = self.render_scene(
                FormulaScene,
                formula=str(formula),
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'diagram':
            # Diagram: expects a description or SVG path, optional headline
            diagram_desc = animation_params.get('primary_object', scene_data.get('diagram_desc', narration))
            video_path = self.render_scene(
                DiagramScene,
                diagram_desc=str(diagram_desc),
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'example':
            # Example: expects example text, optional headline
            example_text = animation_params.get('primary_object', scene_data.get('example_text', narration))
            video_path = self.render_scene(
                ExampleScene,
                example_text=str(example_text),
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type == 'comparison':
            # Comparison: expects left/right text, optional headline
            left = animation_params.get('left', '')
            right = animation_params.get('right', '')
            if not left or not right: # Fallback: check primary_object if it's a list/dict
                obj = animation_params.get('primary_object', {})
                if isinstance(obj, dict):
                    left, right = list(obj.keys())[0], list(obj.values())[0]
                elif isinstance(obj, list) and len(obj) >= 2:
                    left, right = obj[0], obj[1]

            video_path = self.render_scene(
                ComparisonScene,
                left=str(left),
                right=str(right),
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type in ['divide_merge_scene', 'divide_and_merge_scene']:
            items = animation_params.get('primary_object', animation_params.get('key_numbers', self._extract_items(narration)))
            video_path = self.render_scene(
                DivideMergeScene,
                items=items,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        elif scene_type in ['merge_process_scene', 'merge_scene']:
            items = animation_params.get('key_numbers', self._extract_items(narration))
            video_path = self.render_scene(
                MergeProcessScene,
                items=items,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params
            )

        elif scene_type == 'concept_flow_scene':
            # Map complex concept flow to process for now, or just definition
            steps = animation_params.get('items_to_visualize', self._extract_steps(narration))
            if steps:
                video_path = self.render_scene(
                    ProcessFlowScene,
                    steps=steps,
                    headline=headline,
                    target_duration=target_duration,
                    animation_params=animation_params
                )
            else:
                video_path = self.render_scene(
                    DefinitionScene,
                    term=headline,
                    definition=narration,
                    target_duration=target_duration,
                    animation_params=animation_params
                )

        elif scene_type == 'tree':
            branches = animation_params.get('branches', animation_params.get('items_to_visualize', self._extract_steps(narration)))
            root_text = animation_params.get('root', headline or "Classification")
            video_path = self.render_scene(
                TreeScene,
                root_text=root_text,
                branches=branches,
                headline=headline,
                target_duration=target_duration,
                animation_params=animation_params,
                captions=scene_data.get('captions', []),
                visual_manifest=scene_data.get('visual_manifest', {})
            )

        else:
            # Default to definition
            video_path = self.render_scene(
                DefinitionScene,
                term=headline,
                definition=narration,
                target_duration=target_duration,
                animation_params=animation_params
            )

        return video_path, audio_path, target_duration

    async def generate_from_script(self, script: Dict) -> str:
        """
        Stage 3: Manim Auto-Rendering.
        Renders each scene as an individual high-quality MP4 clip in parallel.
        Uses render_worker.py to bypass Manim's global config limitations.
        """
        scenes = script.get('scenes', [])
        print(f"\n🎬 Generating premium video from script with {len(scenes)} scenes in PARALLEL...")
        
        # 1. Pre-process scenes (Audio + AI Prompts)
        processed_scenes = []
        for i, scene_data in enumerate(scenes):
            headline = scene_data.get('headline', '')
            narration = scene_data.get('narration', '')
            print(f"   🎧 Preparing Scene {i+1}/{len(scenes)}: {headline}")
            
            # Voice generation
            audio_id = str(uuid.uuid4())[:8]
            audio_path = os.path.join(self.temp_dir, f"audio_{audio_id}.mp3")
            generate_voice_sync(narration, audio_path)
            audio_duration = get_audio_duration(audio_path)
            
            # AI Animation Prompts (Only fallback if manifest not present)
            manifest = scene_data.get('visual_manifest', {})
            if not manifest:
                animation_params = generate_animation_prompt(
                    scene_data.get('scene_type', 'definition'), 
                    headline, 
                    narration
                )
            else:
                animation_params = manifest # Treat manifest as params
            
            # Technical Buffer: Complex scenes need more time to process
            words = len(scene_data.get('narration', '').split())
            narration_duration = max(4.0, (words / 2.0) + 1.5)
            
            # AI Duration from manifest or script
            ai_duration = scene_data.get('duration', scene_data.get('target_duration', 0))
            
            target_duration = max(narration_duration, ai_duration)
            
            # Logic Extraction: Prioritize visual_manifest.primary_object
            manifest = scene_data.get('visual_manifest', {})
            primary_data = manifest.get('primary_object')
            
            # Data Cleaning: If the data is a string that looks like a list, parse it
            if isinstance(primary_data, str) and primary_data.startswith('[') and primary_data.endswith(']'):
                try:
                    import ast
                    primary_data = ast.literal_eval(primary_data)
                except:
                    pass
            
            # Prepare data for worker
            scene_type = scene_data.get('scene_type', 'definition')
            worker_data = {
                'scene_type': scene_type,
                'headline': headline,
                'narration': narration,
                'captions': self._split_narration(narration),
                'target_duration': target_duration,
                'visual_manifest': manifest,
                'items': primary_data if isinstance(primary_data, list) else self._extract_items(narration),
                'code': str(primary_data) if scene_type == 'code' else "",
                'audio_path': audio_path,  # REQUIRED for parallel stitching
            }
            
            # Populate items/steps for legacy scene types if not present
            if 'items' not in worker_data:
                worker_data['items'] = manifest.get('primary_object', self._extract_items(scene_data.get('narration', '')))
            if 'steps' not in worker_data:
                worker_data['steps'] = manifest.get('steps', self._extract_steps(scene_data.get('narration', '')))
                
            # Handle list points
            worker_data['steps'] = self._filter_redundant_points(worker_data.get('steps', []), scene_data.get('headline', ''))
            
            processed_scenes.append(worker_data)

        # 2. Render Videos in Parallel using subprocesses
        print(f"   🚀 Spawning {len(processed_scenes)} Manim workers...")
        
        async def render_scene_parallel(index, scene_data):
            output_file = os.path.join(self.temp_dir, f"scene_{index}.mp4")
            scene_json = json.dumps(scene_data)
            
            # Call the worker script
            cmd = [
                sys.executable, 
                "render_worker.py", 
                scene_json, 
                "algorithm", # Default theme name, can be dynamic
                output_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"      ❌ Worker {index} failed: {stderr.decode()}")
                return None, scene_data['audio_path']
            
            return output_file, scene_data['audio_path']

        # Run all renders in parallel
        render_tasks = [render_scene_parallel(i, data) for i, data in enumerate(processed_scenes)]
        results = await asyncio.gather(*render_tasks)
        
        # 3. Stitch each video with its audio
        final_clips = []
        for i, (v_path, a_path) in enumerate(results):
            if not v_path: continue
            
            video = VideoFileClip(v_path)
            audio = AudioFileClip(a_path)
            final_scene = video.with_audio(audio)
            
            temp_path = os.path.join(self.temp_dir, f"final_clip_{i}.mp4")
            final_scene.write_videofile(temp_path, codec="libx264", audio_codec="aac", fps=30)
            final_clips.append(temp_path)
            
            video.close()
            audio.close()
            final_scene.close()

        # 4. Final composition with movie_helper (Stage 4)
        from movie_helper import compose_final_video
        
        output_id = str(uuid.uuid4())[:8]
        final_output_path = os.path.join(FINAL_OUTPUT, f"premium_{output_id}.mp4")
        
        bg_music = None
        if os.path.exists("media/background_music.mp3"):
            bg_music = "media/background_music.mp3"

        return compose_final_video(final_clips, final_output_path, background_music_path=bg_music)

    def generate_continuous_from_script(self, script: Dict) -> str:
        """
        NEW: Generate a single continuous video with Carry-Forward state.
        One Manim Scene renders EVERYTHING.
        """
        scenes = script.get('scenes', [])
        print(f"\n🎬 Generating CONTINUOUS video with {len(scenes)} scenes...")
        
        # 1. Pre-generate all audio to get durations
        total_audio_path = os.path.join(self.temp_dir, "full_audio.mp3")
        scene_audios = []
        
        processed_scenes = []
        for i, scene in enumerate(scenes):
            narration = scene.get('narration', '')
            audio_path = os.path.join(self.temp_dir, f"part_{i}.mp3")
            generate_voice_sync(narration, audio_path)
            duration = get_audio_duration(audio_path)
            
            # Get AI params for visuals
            anim_params = generate_animation_prompt(scene.get('scene_type', 'explanation'), scene.get('headline', ''), narration)
            
            processed_scenes.append({
                **scene,
                'duration': duration,
                'audio_path': audio_path,
                'animation_params': anim_params
            })
            scene_audios.append(AudioFileClip(audio_path))

        # 2. Combine audio
        final_audio = concatenate_audioclips(scene_audios)
        final_audio.write_audiofile(total_audio_path)

        # 3. Render single continuous scene
        video_path = self.render_scene(
            SequentialManimScene,
            scenes=processed_scenes,
            extractors={
                'steps': self._extract_steps,
                'items': self._extract_items
            }
        )

        # 4. Mix final
        video_clip = VideoFileClip(video_path)
        final_video = video_clip.with_audio(final_audio)
        
        output_id = str(uuid.uuid4())
        output_path = os.path.join(FINAL_OUTPUT, f"continuous_{output_id}.mp4")
        
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=30)
        return output_path
    
    def _split_narration(self, text: str) -> List[str]:
        """Split narration into digestible caption chunks for live display."""
        if not text:
            return []
        
        # Simple word-count based splitting (approx 6-8 words per caption)
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            # If chunk is long enough or word ends in punctuation
            if len(current_chunk) >= 6 or word.endswith(('.', '?', '!', ';')):
                chunk_str = " ".join(current_chunk)
                if len(chunk_str) > 50: # Cap length
                    chunk_str = chunk_str[:47] + "..."
                chunks.append(chunk_str)
                current_chunk = []
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks if chunks else [text[:50]]
    
    def _extract_items(self, text: str) -> List:
        """Universal item extractor: Numbers, Names, or Short Phrases."""
        import re
        
        # 1. Check for quoted items (e.g. 'Apple', 'Banana')
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", text)
        if quoted:
            return [q.strip()[:15] for q in quoted[:8]]
            
        # 2. Check for comma-separated lists of title-case words (e.g. India, Japan, France)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b', text)
        if len(capitalized) > 1:
            return capitalized[:8]

        # 3. Look for numbers
        numbers = re.findall(r'\b(\d+)\b', text)
        if numbers:
            return [int(n) for n in numbers[:8]]
        
        # 4. Fallback: Split by common separators if the text is short
        if "," in text and len(text) < 100:
            parts = [p.strip() for p in text.split(",")]
            return [p[:15] for p in parts if len(p) > 1][:8]
        
        return ["Concept A", "Concept B", "Concept C"]
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract process steps or key points from text."""
        import re
        
        # New: Split by colon FIRST (e.g. "Key points: one, two")
        if ":" in text:
            parts = text.split(":", 1)
            # If the part after colon and before first period is long enough, split it
            post_colon = parts[1].strip()
            # If there are already bullets or numbers, the re search will find them
        else:
            post_colon = text

        # Numbered steps
        numbered = re.findall(r'\d+[.)]\s*([^.!?\n]+)', text)
        if numbered:
            return [s.strip()[:40] for s in numbered if len(s.strip()) > 3][:5]
        
        # Bullet points
        bullets = re.findall(r'[•\-*]\s*([^.!?\n]+)', text)
        if bullets:
            return [s.strip()[:40] for s in bullets if len(s.strip()) > 3][:5]
        
        # Split by punctuation
        sentences = re.split(r'[.!?\n]', post_colon)
        return [s.strip()[:40] for s in sentences if len(s.strip()) > 5][:5]

    def _filter_redundant_points(self, points: List[str], headline: str) -> List[str]:
        """Filter out points that are too similar to the headline to avoid redundancy."""
        if not points:
            return points
            
        head_lower = headline.lower().strip()
        filtered = []
        for p in points:
            p_clean = p.lower().strip()
            # Exclude if identical or just a small variation
            if p_clean == head_lower:
                continue
            if head_lower in p_clean and len(p_clean) < len(head_lower) + 5:
                continue
            if p_clean in head_lower and len(head_lower) < len(p_clean) + 5:
                continue
            
            # Exclude common intro phrases
            if p_clean in ["remember these points", "key takeaways", "in summary", "to wrap up", "here is how"]:
                continue
                
            filtered.append(p)
            
        # Fallback if we filtered EVERYTHING out
        if not filtered and points:
            return points[:1]
            
        return filtered


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎬 Manim + MoviePy Video Engine Test")
    print("=" * 50)
    
    # Test script
    test_script = {
        "title": "Bubble Sort Explained",
        "scenes": [
            {
                "scene_type": "title",
                "headline": "Bubble Sort",
                "narration": "Let's learn the simplest sorting algorithm!"
            },
            {
                "scene_type": "definition", 
                "headline": "What is Bubble Sort?",
                "narration": "Bubble sort repeatedly compares adjacent elements and swaps them if they're in the wrong order."
            },
            {
                "scene_type": "array",
                "headline": "Watch It Work",
                "narration": "Let's sort these numbers: 5, 3, 8, 1, 2"
            },
            {
                "scene_type": "process",
                "headline": "The Algorithm",
                "narration": "1. Compare adjacent elements. 2. Swap if needed. 3. Repeat until sorted."
            },
            {
                "scene_type": "summary",
                "headline": "Key Takeaways",
                "narration": "Simple to understand. O(n²) time complexity. Good for small datasets."
            }
        ]
    }
    
    print("\n📝 Test script:")
    print(json.dumps(test_script, indent=2)[:500] + "...")
    
    print("\n🎬 To generate video, run:")
    print("   generator = ManimVideoGenerator('algorithm')")
    print("   generator.generate_from_script(test_script)")
