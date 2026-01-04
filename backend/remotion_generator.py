"""
🎬 REMOTION VIDEO GENERATOR
=============================
Generate smooth animated videos using Remotion (React-based).

Why Remotion?
- React-based (familiar to many devs)
- Excellent for programmatic video
- Smooth 60fps animations
- Easy to render on server
- Great for educational content

Installation:
  npx create-video@latest
  npm install @remotion/bundler @remotion/renderer
"""

import os
import json
import uuid
import subprocess
from typing import Dict, List, Optional

REMOTION_DIR = "backend/remotion_projects"
os.makedirs(REMOTION_DIR, exist_ok=True)


def generate_remotion_component(scenes: List[Dict], theme: Dict) -> str:
    """Generate a Remotion React component for the video."""
    
    colors = theme.get('colors', {})
    bg_color = rgb_to_hex(colors.get('bg', (20, 25, 35)))
    primary_color = rgb_to_hex(colors.get('primary', (0, 200, 255)))
    secondary_color = rgb_to_hex(colors.get('secondary', (255, 150, 100)))
    accent_color = rgb_to_hex(colors.get('accent', (255, 100, 150)))
    text_color = rgb_to_hex(colors.get('text', (255, 255, 255)))
    card_color = rgb_to_hex(colors.get('card', (35, 45, 60)))
    
    # Calculate total frames (30fps)
    total_duration = sum(s.get('duration', 5) for s in scenes)
    total_frames = int(total_duration * 30)
    
    # Generate scene components
    scene_components = []
    current_frame = 0
    
    for i, scene in enumerate(scenes):
        scene_type = scene.get('scene_type', 'definition')
        duration = scene.get('duration', 5)
        frames = int(duration * 30)
        headline = scene.get('headline', 'Title').replace("'", "\\'")
        narration = scene.get('narration', '').replace("'", "\\'")[:100]
        
        component = generate_scene_component(
            scene_type, headline, narration, 
            current_frame, frames, i,
            primary_color, card_color, text_color, accent_color
        )
        scene_components.append(component)
        current_frame += frames
    
    # Main composition
    composition = f'''
import {{AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring}} from 'remotion';

// Theme colors
const theme = {{
  bg: '{bg_color}',
  primary: '{primary_color}',
  secondary: '{secondary_color}',
  accent: '{accent_color}',
  text: '{text_color}',
  card: '{card_color}',
}};

// Scene Components
{chr(10).join(scene_components)}

// Main Video Composition
export const MainVideo = () => {{
  const frame = useCurrentFrame();
  const {{fps, width, height}} = useVideoConfig();
  
  return (
    <AbsoluteFill style={{{{backgroundColor: theme.bg}}}}>
      {generate_sequence_jsx(scenes)}
    </AbsoluteFill>
  );
}};

// Video configuration
export const videoConfig = {{
  fps: 30,
  durationInFrames: {total_frames},
  width: 1080,
  height: 1920,
}};
'''
    
    return composition


def generate_scene_component(scene_type: str, headline: str, narration: str,
                             start_frame: int, duration_frames: int, index: int,
                             primary: str, card: str, text_color: str, accent: str) -> str:
    """Generate a React component for a specific scene type."""
    
    component_name = f"Scene{index}"
    
    if scene_type == 'title':
        return f'''
const {component_name} = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {{extrapolateRight: 'clamp'}});
  const titleScale = spring({{frame, fps, from: 0.8, to: 1, durationInFrames: 20}});
  const underlineWidth = interpolate(frame, [15, 30], [0, 400], {{extrapolateRight: 'clamp'}});
  
  return (
    <AbsoluteFill style={{{{
      justifyContent: 'center',
      alignItems: 'center',
    }}}}>
      <div style={{{{
        fontSize: 64,
        fontWeight: 'bold',
        color: 'white',
        opacity: titleOpacity,
        transform: `scale(${{titleScale}})`,
        textAlign: 'center',
      }}}}>
        {headline}
      </div>
      <div style={{{{
        width: underlineWidth,
        height: 5,
        backgroundColor: '{primary}',
        marginTop: 20,
      }}}} />
      <div style={{{{
        fontSize: 24,
        color: '#bbbbbb',
        marginTop: 30,
        opacity: interpolate(frame, [20, 35], [0, 1], {{extrapolateRight: 'clamp'}}),
        maxWidth: 800,
        textAlign: 'center',
      }}}}>
        {narration}
      </div>
    </AbsoluteFill>
  );
}};
'''

    elif scene_type == 'definition':
        return f'''
const {component_name} = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  
  const cardScale = spring({{frame, fps, from: 0.9, to: 1, durationInFrames: 15}});
  const cardOpacity = interpolate(frame, [0, 10], [0, 1], {{extrapolateRight: 'clamp'}});
  const accentHeight = interpolate(frame, [10, 25], [0, 260], {{extrapolateRight: 'clamp'}});
  
  return (
    <AbsoluteFill style={{{{justifyContent: 'center', alignItems: 'center'}}}}>
      <div style={{{{
        width: 900,
        backgroundColor: '{card}',
        borderRadius: 12,
        padding: 40,
        opacity: cardOpacity,
        transform: `scale(${{cardScale}})`,
        position: 'relative',
      }}}}>
        <div style={{{{
          position: 'absolute',
          left: 0,
          top: 0,
          width: 8,
          height: accentHeight,
          backgroundColor: '{primary}',
          borderRadius: '12px 0 0 12px',
        }}}} />
        <div style={{{{fontSize: 40, color: 'white', marginBottom: 20}}}}>
          {headline}
        </div>
        <div style={{{{
          width: '100%',
          height: 2,
          backgroundColor: '{primary}',
          opacity: 0.5,
          marginBottom: 20,
        }}}} />
        <div style={{{{fontSize: 22, color: '#dddddd', lineHeight: 1.6}}}}>
          {narration}
        </div>
      </div>
    </AbsoluteFill>
  );
}};
'''

    elif scene_type == 'array':
        return f'''
const {component_name} = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  
  const items = ['5', '3', '8', '1', '2'];
  const highlightIndex = Math.floor(frame / 30) % items.length;
  
  return (
    <AbsoluteFill style={{{{justifyContent: 'center', alignItems: 'center'}}}}>
      <div style={{{{fontSize: 36, color: 'white', marginBottom: 50}}}}>
        {headline}
      </div>
      <div style={{{{display: 'flex', gap: 20}}}}>
        {{items.map((item, i) => {{
          const isHighlighted = i === highlightIndex;
          const boxScale = isHighlighted ? spring({{frame: frame % 30, fps, from: 1, to: 1.1}}) : 1;
          
          return (
            <div key={{i}} style={{{{
              width: 100,
              height: 100,
              backgroundColor: isHighlighted ? '{primary}' : '{card}',
              borderRadius: 8,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: 32,
              color: 'white',
              transform: `scale(${{boxScale}})`,
              boxShadow: isHighlighted ? '0 0 20px {primary}' : 'none',
            }}}}>
              {{item}}
            </div>
          );
        }}}}
      </div>
      <div style={{{{
        display: 'flex',
        gap: 20,
        marginTop: 15,
      }}}}>
        {{items.map((_, i) => (
          <div key={{i}} style={{{{
            width: 100,
            textAlign: 'center',
            fontSize: 18,
            color: '#666',
          }}}}>
            {{i}}
          </div>
        ))}}
      </div>
    </AbsoluteFill>
  );
}};
'''

    elif scene_type in ['process', 'summary']:
        return f'''
const {component_name} = () => {{
  const frame = useCurrentFrame();
  const {{fps}} = useVideoConfig();
  
  const steps = ['{narration[:30]}', 'Step 2', 'Step 3'];
  
  return (
    <AbsoluteFill style={{{{padding: 60}}}}>
      <div style={{{{fontSize: 42, color: 'white', marginBottom: 40, textAlign: 'center'}}}}>
        {"✅ " if scene_type == "summary" else ""}{headline}
      </div>
      <div style={{{{display: 'flex', flexDirection: 'column', gap: 20}}}}>
        {{steps.map((step, i) => {{
          const delay = i * 15;
          const opacity = interpolate(frame, [delay, delay + 10], [0, 1], {{extrapolateRight: 'clamp'}});
          const translateX = interpolate(frame, [delay, delay + 15], [-50, 0], {{extrapolateRight: 'clamp'}});
          
          return (
            <div key={{i}} style={{{{
              backgroundColor: '{card}',
              padding: 25,
              borderRadius: 8,
              borderLeft: '5px solid {primary}',
              opacity,
              transform: `translateX(${{translateX}}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 15,
            }}}}>
              <span style={{{{color: '#00ff88', fontSize: 28}}}}>✓</span>
              <span style={{{{color: 'white', fontSize: 22}}}}}>{{step}}</span>
            </div>
          );
        }}}}
      </div>
    </AbsoluteFill>
  );
}};
'''

    else:
        # Default component
        return f'''
const {component_name} = () => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {{extrapolateRight: 'clamp'}});
  
  return (
    <AbsoluteFill style={{{{
      justifyContent: 'center',
      alignItems: 'center',
      opacity,
    }}}}>
      <div style={{{{
        fontSize: 36,
        color: 'white',
        textAlign: 'center',
        padding: 40,
      }}}}>
        {headline}
      </div>
    </AbsoluteFill>
  );
}};
'''


def generate_sequence_jsx(scenes: List[Dict]) -> str:
    """Generate Sequence JSX for all scenes."""
    sequences = []
    current_frame = 0
    
    for i, scene in enumerate(scenes):
        duration = scene.get('duration', 5)
        frames = int(duration * 30)
        
        sequences.append(f'''
      <Sequence from={{{current_frame}}} durationInFrames={{{frames}}}>
        <Scene{i} />
      </Sequence>''')
        
        current_frame += frames
    
    return '\n'.join(sequences)


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex."""
    if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return "#ffffff"


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎬 Remotion Generator Test")
    
    theme = {
        "colors": {
            "bg": (20, 25, 35),
            "primary": (0, 255, 136),
            "secondary": (64, 196, 255),
            "accent": (255, 100, 150),
            "text": (255, 255, 255),
            "card": (35, 45, 60),
        }
    }
    
    scenes = [
        {"scene_type": "title", "headline": "Bubble Sort", "narration": "Learn sorting!", "duration": 4},
        {"scene_type": "definition", "headline": "What is it?", "narration": "A simple sorting algorithm", "duration": 5},
        {"scene_type": "array", "headline": "Watch it work", "narration": "5, 3, 8, 1, 2", "duration": 6},
        {"scene_type": "summary", "headline": "Remember", "narration": "Compare, swap, repeat!", "duration": 4},
    ]
    
    code = generate_remotion_component(scenes, theme)
    print(code[:2000])
    print("\n... (truncated)")
