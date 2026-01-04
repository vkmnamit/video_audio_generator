"""
🎬 MOTION CANVAS INTEGRATION
=============================
Generate smooth, animated educational videos using Motion Canvas.

Motion Canvas benefits:
- Smooth animations with easing
- Code-driven (TypeScript/JavaScript)
- Real-time preview
- Professional quality output
- Perfect for algorithm visualizations

Flow:
1. AI generates video script with scenes
2. We convert scenes to Motion Canvas project files
3. Motion Canvas renders the animation
4. Output: High-quality MP4

Requirements:
- Node.js 18+
- Motion Canvas CLI
"""

import os
import json
import subprocess
import uuid
from typing import Dict, List, Optional

# Motion Canvas project template directory
MOTION_CANVAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "motion_canvas_projects")
os.makedirs(MOTION_CANVAS_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 SCENE TO MOTION CANVAS CONVERTER
# ═══════════════════════════════════════════════════════════════════════════════

def scene_to_motion_canvas_code(scene: Dict, scene_index: int, theme: Dict) -> str:
    """
    Convert a video scene to Motion Canvas TypeScript code.
    
    This generates the animation code for one scene.
    """
    scene_type = scene.get('scene_type', 'definition').lower()
    headline = scene.get('headline', 'Title')
    narration = scene.get('narration', '')
    duration = scene.get('duration', 5.0)
    
    # Get theme colors (convert RGB to hex)
    colors = theme.get('colors', {})
    bg_color = rgb_to_hex(colors.get('bg', (20, 25, 35)))
    primary_color = rgb_to_hex(colors.get('primary', (0, 200, 255)))
    secondary_color = rgb_to_hex(colors.get('secondary', (255, 150, 100)))
    accent_color = rgb_to_hex(colors.get('accent', (255, 100, 150)))
    text_color = rgb_to_hex(colors.get('text', (255, 255, 255)))
    card_color = rgb_to_hex(colors.get('card', (35, 45, 60)))
    
    # Generate scene-specific code
    if scene_type == 'title':
        return generate_title_scene(headline, narration, duration, primary_color, text_color, bg_color)
    elif scene_type == 'definition':
        return generate_definition_scene(headline, narration, duration, primary_color, card_color, text_color)
    elif scene_type == 'array':
        items = scene.get('visual_elements', []) or extract_array_items(narration)
        return generate_array_scene(headline, items, duration, primary_color, card_color, text_color, accent_color)
    elif scene_type == 'process':
        # Try to get steps from scene data first, then extract from narration
        steps = scene.get('steps', [])
        if not steps:
            steps = extract_steps(narration)
        return generate_process_scene(headline, steps, duration, primary_color, secondary_color, card_color, text_color, narration)
    elif scene_type == 'summary':
        points = scene.get('key_points', []) or extract_steps(narration)
        return generate_summary_scene(headline, points, duration, primary_color, text_color, card_color)
    elif scene_type == 'timeline':
        items = scene.get('timeline_items', []) or extract_timeline_items(narration)
        return generate_timeline_scene(headline, items, duration, primary_color, secondary_color, card_color, text_color)
    else:
        # Default to definition style
        return generate_definition_scene(headline, narration, duration, primary_color, card_color, text_color)


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color string."""
    if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return "#ffffff"


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 SCENE GENERATORS (Motion Canvas TypeScript)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_title_scene(headline: str, subtitle: str, duration: float, 
                         primary: str, text_color: str, bg: str) -> str:
    """Generate Motion Canvas code for a title scene."""
    return f'''
// Title Scene
yield* sequence(0.1,
    title().text("{headline}", 0.5),
    title().fill("{primary}", 0.3),
);

yield* all(
    title().scale(1.1, 0.3).to(1, 0.2),
    underline().width(400, 0.5),
);

if ("{subtitle}") {{
    yield* subtitle().text("{subtitle[:80]}", 0.4);
    yield* subtitle().opacity(1, 0.3);
}}

yield* waitFor({duration - 1.5});
yield* all(
    title().opacity(0, 0.3),
    subtitle().opacity(0, 0.3),
    underline().width(0, 0.3),
);
'''


def generate_definition_scene(headline: str, definition: str, duration: float,
                              primary: str, card: str, text_color: str) -> str:
    """Generate Motion Canvas code for a definition card."""
    # Clean the definition text
    clean_def = definition.replace('"', '\\"').replace('\n', ' ')[:180]
    
    return f'''
// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("{headline}", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("{clean_def}", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor({duration - 2});

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);
'''


def generate_array_scene(headline: str, items: List[str], duration: float,
                         primary: str, card: str, text_color: str, accent: str) -> str:
    """Generate Motion Canvas code for array visualization with animations."""
    if not items:
        items = ['A', 'B', 'C', 'D', 'E']
    
    items_str = ', '.join(f'"{item}"' for item in items[:8])
    
    return f'''
// Array Scene with Animation
const items = [{items_str}];
const boxes = createRefArray<Rect>();

// Create array boxes
yield* sequence(0.1,
    ...items.map((item, i) => 
        boxes[i].opacity(1, 0.2)
    )
);

// Highlight animation (simulating comparison)
for (let i = 0; i < items.length - 1; i++) {{
    yield* sequence(0.05,
        boxes[i].fill("{primary}", 0.2),
        boxes[i].scale(1.1, 0.1).to(1, 0.1),
    );
    yield* waitFor(0.3);
    yield* boxes[i].fill("{card}", 0.2);
}}

// Show sorted state
yield* sequence(0.1,
    ...items.map((_, i) => 
        boxes[i].fill("{accent}", 0.2)
    )
);

yield* waitFor({duration - 3});
'''


def generate_process_scene(headline: str, steps: List[str], duration: float,
                           primary: str, secondary: str, card: str, text_color: str, subtitle_text: str = "") -> str:
    """Generate Motion Canvas code for process flowchart."""
    # Fallback if no steps found or less than 2 steps
    if not steps or len(steps) < 2:
        if subtitle_text:
            # Try to split subtitle as fallback steps
            steps = [s.strip() for s in subtitle_text.split('.') if len(s.strip()) > 5][:4]
        if not steps or len(steps) < 2:
            steps = ['Step 1', 'Step 2']
    
    steps_code = []
    for i, step in enumerate(steps[:4]):
        clean_step = step.replace('"', '\\"')[:50]
        color = primary if i % 2 == 0 else secondary
        steps_code.append(f'''
    // Step {i + 1}
    yield* sequence(0.1,
        stepBoxes[{i}].opacity(1, 0.3),
        stepBoxes[{i}].scale(0.8, 0).to(1, 0.3),
        stepTexts[{i}].text("{clean_step}", 0.3),
        stepAccents[{i}].width(boxWidth, 0.2),
    );
    {"yield* arrows[" + str(i) + "].opacity(1, 0.2);" if i < len(steps) - 1 else ""}
    yield* waitFor(0.5);
''')
    
    clean_subtitle = subtitle_text.replace('"', '\\"')[:90] if subtitle_text else ""
    
    return f'''
// Process Flow Scene
const steps = {json.dumps([s[:50] for s in steps[:4]])};
const stepBoxes = createRefArray<Rect>();
const stepTexts = createRefArray<Txt>();
const stepAccents = createRefArray<Rect>();
const arrows = createRefArray<Line>();

yield* title().text("{headline}", 0.3);

// Show subtitle (narration) at bottom
if ("{clean_subtitle}") {{
    yield* subtitle().text("{clean_subtitle}", 0.4);
    yield* subtitle().opacity(1, 0.3);
}}

// Add layout to view
view.add(
    <>
        {{steps.map((step, i) => (
            <>
                <Rect
                    ref={{stepBoxes[i]}}
                    width={{600}}
                    height={{100}}
                    fill={{"{card}"}}
                    radius={{10}}
                    opacity={{0}}
                    y={{-100 + i * 150}} // Vertical layout
                >
                     <Rect
                        ref={{stepAccents[i]}}
                        width={{0}}
                        height={{100}}
                        fill={{i % 2 === 0 ? "{primary}" : "{secondary}"}}
                        x={{-300}} // Left edge
                    />
                    <Txt
                        ref={{stepTexts[i]}}
                        text={{step}}
                        fontSize={{32}}
                        fontFamily={{"Arial"}}
                        fill={{"{text_color}"}}
                    />
                </Rect>
                {{i < steps.length - 1 && (
                    <Line
                        ref={{arrows[i]}}
                        points={{{{[[0, -50 + i * 150], [0, -100 + (i + 1) * 150]]}}}}
                        stroke={{"{text_color}"}}
                        lineWidth={{4}}
                        endArrow={{true}}
                        opacity={{0}}
                    />
                )}}
            </>
        ))}}
    </>
);

{''.join(steps_code)}

yield* waitFor({max(0.5, duration - len(steps) * 1.2)});
'''


def generate_summary_scene(headline: str, points: List[str], duration: float,
                           primary: str, text_color: str, card: str) -> str:
    """Generate Motion Canvas code for summary with checkmarks."""
    if not points:
        points = ['Takeaway 1', 'Takeaway 2', 'Takeaway 3']
    
    points_code = []
    for i, point in enumerate(points[:4]):
        clean_point = point.replace('"', '\\"')[:50]
        points_code.append(f'''
    yield* sequence(0.1,
        checkmarks[{i}].opacity(1, 0.2),
        checkmarks[{i}].scale(0, 0).to(1, 0.3),
        pointTexts[{i}].text("{clean_point}", 0.3),
        pointBgs[{i}].opacity(1, 0.2),
    );
    yield* waitFor(0.4);
''')
    
    return f'''
// Summary Scene
yield* title().text("✅ {headline}", 0.4);

const checkmarks = createRefArray<Txt>();
const pointTexts = createRefArray<Txt>();
const pointBgs = createRefArray<Rect>();

{''.join(points_code)}

yield* waitFor({max(0.5, duration - len(points) * 0.9)});
'''


def generate_timeline_scene(headline: str, items: List[any], duration: float,
                          primary: str, secondary: str, card: str, text_color: str) -> str:
    """Generate Motion Canvas code for a vertical timeline."""
    # Normalize items
    normalized_items = []
    # If items is empty or None, use fallback
    if not items:
         items = ['Step 1', 'Step 2', 'Step 3']
         
    for i, item in enumerate(items[:4]):
        if isinstance(item, dict):
             normalized_items.append((item.get('year', f'Step {i+1}'), item.get('event', str(item))))
        elif isinstance(item, tuple) and len(item) == 2:
             normalized_items.append(item)
        else:
             # If just a string, make it Step X: String
             normalized_items.append((f'Step {i+1}', str(item)))

    timeline_code = []
    for i, (year, event) in enumerate(normalized_items):
        clean_year = str(year).replace('"', '\\"')[:15]
        clean_event = str(event).replace('"', '\\"')[:50]
        
        timeline_code.append(f'''
    // Event {i}
    yield* sequence(0.1,
        dots[{i}].scale(0,0).to(1, 0.3),
        yearTexts[{i}].text("{clean_year}", 0.3),
        eventTexts[{i}].text("{clean_event}", 0.4),
    );
    yield* waitFor(0.5);
''')

    return f'''
// Timeline Scene
const dots = createRefArray<Circle>();
const yearTexts = createRefArray<Txt>();
const eventTexts = createRefArray<Txt>();
const line = createRef<Line>();

yield* title().text("{headline}", 0.5);

// Draw main line
yield* line().points([[0, -200], [0, {100 * len(normalized_items)}]], 0.5);

{chr(10).join(timeline_code)}

yield* waitFor({max(0.5, duration - len(normalized_items) * 0.8)});
'''


# ═══════════════════════════════════════════════════════════════════════════════
# 📄 PROJECT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_motion_canvas_project(scenes: List[Dict], theme: Dict, 
                                   title: str = "Educational Video") -> str:
    """
    Generate a complete Motion Canvas project from video scenes.
    
    Returns: Path to the project directory
    """
    project_id = str(uuid.uuid4())[:8]
    project_dir = os.path.join(MOTION_CANVAS_DIR, f"project_{project_id}")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "scenes"), exist_ok=True)
    
    colors = theme.get('colors', {})
    bg_color = rgb_to_hex(colors.get('bg', (20, 25, 35)))
    primary_color = rgb_to_hex(colors.get('primary', (0, 200, 255)))
    
    # Generate main scene file
    scene_codes = []
    for i, scene in enumerate(scenes):
        code = scene_to_motion_canvas_code(scene, i, theme)
        scene_codes.append(f"// Scene {i + 1}: {scene.get('scene_type', 'unknown')}\n{code}")
    
    main_scene = f'''
import {{makeScene2D, Rect, Txt, Line, Circle}} from '@motion-canvas/2d';
import {{createRef, createRefArray, all, sequence, waitFor, easeOutCubic}} from '@motion-canvas/core';

export default makeScene2D(function* (view) {{
    // Theme colors
    const bgColor = "{bg_color}";
    const primaryColor = "{primary_color}";
    
    // Set background
    view.fill(bgColor);
    
    // Video dimensions (9:16 for shorts)
    const width = 1080;
    const height = 1920;
    
    // Common elements
    const title = createRef<Txt>();
    const subtitle = createRef<Txt>();
    const underline = createRef<Rect>();
    const card = createRef<Rect>();
    const termText = createRef<Txt>();
    const defText = createRef<Txt>();
    const separator = createRef<Rect>();
    const leftAccent = createRef<Rect>();
    
    const cardWidth = 900;
    const cardHeight = 400;
    const boxWidth = 200;
    
    // Add base elements to view
    view.add(
        <>
            <Txt
                ref={{title}}
                fontSize={{64}}
                fontFamily={{"Arial"}}
                fill={{"{rgb_to_hex(colors.get('text', (255,255,255)))}"}}
                y={{-200}}
            />
            <Txt
                ref={{subtitle}}
                fontSize={{28}}
                fontFamily={{"Arial"}}
                fill={{"#bbbbbb"}}
                y={{-100}}
                opacity={{0}}
            />
            <Rect
                ref={{underline}}
                width={{0}}
                height={{5}}
                fill={{primaryColor}}
                y={{-140}}
            />
            <Rect
                ref={{card}}
                width={{cardWidth}}
                height={{cardHeight}}
                fill={{"{rgb_to_hex(colors.get('card', (35,45,60)))}"}}
                radius={{10}}
                opacity={{0}}
            >
                <Rect
                    ref={{leftAccent}}
                    width={{8}}
                    height={{0}}
                    fill={{primaryColor}}
                    x={{-cardWidth/2 + 4}}
                />
                <Txt
                    ref={{termText}}
                    fontSize={{40}}
                    fontFamily={{"Arial"}}
                    fill={{"white"}}
                    y={{-80}}
                    x={{-cardWidth/2 + 150}}
                />
                <Rect
                    ref={{separator}}
                    width={{0}}
                    height={{2}}
                    fill={{primaryColor}}
                    y={{-30}}
                    opacity={{0.5}}
                />
                <Txt
                    ref={{defText}}
                    fontSize={{24}}
                    fontFamily={{"Arial"}}
                    fill={{"#dddddd"}}
                    y={{50}}
                    width={{cardWidth - 80}}
                    textWrap={{true}}
                />
            </Rect>
        </>
    );
    
    // Scene animations
    {chr(10).join(scene_codes)}
    
    // End
    yield* waitFor(0.5);
}});
'''
    
    # Write main scene file
    scene_file = os.path.join(project_dir, "src", "scenes", "main.tsx")
    with open(scene_file, 'w') as f:
        f.write(main_scene)
    
    # Write src/project.ts (Entry point)
    project_ts = '''import {makeProject} from '@motion-canvas/core';
import main from './scenes/main?scene';

export default makeProject({
  scenes: [main],
});
'''
    with open(os.path.join(project_dir, "src", "project.ts"), 'w') as f:
        f.write(project_ts)

    # Write vite.config.ts
    vite_config = '''import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';

export default defineConfig({
  plugins: [
    (motionCanvas as any).default ? (motionCanvas as any).default() : (motionCanvas as any)(),
  ],
});
'''
    with open(os.path.join(project_dir, "vite.config.ts"), 'w') as f:
        f.write(vite_config)
    
    # Write package.json (Modern structure)
    package_json = {
        "name": f"aetheris-video-{project_id}",
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build"
        },
        "dependencies": {
            "@motion-canvas/core": "^3.16.0",
            "@motion-canvas/2d": "^3.16.0",
            "@motion-canvas/ui": "^3.16.0"
        },
        "devDependencies": {
            "@motion-canvas/vite-plugin": "^3.16.0",
            "@motion-canvas/ffmpeg": "^3.16.0",
            "puppeteer": "^23.0.0", 
            "typescript": "^5.2.2",
            "vite": "^5.0.0"
        }
    }
    
    package_file = os.path.join(project_dir, "package.json")
    with open(package_file, 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print(f"📁 Motion Canvas project created: {project_dir}")
    return project_dir


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 RENDER VIDEO
# ═══════════════════════════════════════════════════════════════════════════════

def serve_motion_canvas_project(project_dir: str) -> Optional[str]:
    """
    Start the Motion Canvas dev server for the project in the background.
    Returns the localhost URL.
    """
    import socket
    import subprocess
    import time
    
    # Find a free port
    port = 9007
    while port < 9030:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0: # Port is open (connection refused)
            break
        port += 1
    
    if port >= 9030:
        print("❌ No free ports found for Motion Canvas server.")
        return None
        
    print(f"🚀 Starting Motion Canvas server on port {port}...")
    
    # Start server in background
    # Note: We chain install and dev. valid_shell logic needed.
    cmd = f"npm install && npm run dev -- --port {port} --host"
    
    try:
        # We use Popen to let it run in background
        subprocess.Popen(
            cmd, 
            cwd=project_dir, 
            shell=True,
            stdout=subprocess.DEVNULL, # Mute output to keep logs clean
            stderr=subprocess.DEVNULL
        )
        url = f"http://localhost:{port}"
        print(f"✅ Server launching at: {url} (Give it ~30s to start)")
        return url
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_array_items(text: str) -> List[str]:
    """Extract array items from narration text."""
    import re
    
    # Look for quoted items
    quoted = re.findall(r"'([^']+)'", text)
    if quoted:
        return quoted[:8]
    
    # Look for numbers
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        return numbers[:8]
    
    return ['1', '2', '3', '4', '5']


def extract_steps(text: str) -> List[str]:
    """Extract process steps from narration."""
    import re
    
    if not text:
        return []

    # Numbered steps
    numbered = re.findall(r'\d+[.)]\s*([^.!?]+)', text)
    if numbered:
        return [s.strip()[:50] for s in numbered if len(s.strip()) > 3][:5]
    
    # Sentences - split by punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter empty or very short strings
    valid_steps = [s.strip()[:50] for s in sentences if len(s.strip()) > 5][:4]
    
    if valid_steps:
        return valid_steps
        
def extract_timeline_items(text: str) -> List[any]:
    """Extract timeline items (Year/Time, Event) from narration."""
    import re
    if not text:
         return []

    # Look for years (e.g., 1990, 2020)
    years_events = re.findall(r'\b(19\d{2}|20\d{2})\b[:\s-]*([^.!?]+)', text)
    if years_events:
        return [(y, e.strip()[:40]) for y, e in years_events][:4]

    # If no years, extract steps and make them sequential
    steps = extract_steps(text)
    return [(f"Step {i+1}", s[:40]) for i, s in enumerate(steps)]


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎬 Motion Canvas Generator Test")
    print("=" * 50)
    
    # Test theme
    test_theme = {
        "colors": {
            "bg": (20, 25, 35),
            "primary": (0, 255, 136),
            "secondary": (64, 196, 255),
            "accent": (255, 100, 150),
            "text": (255, 255, 255),
            "card": (35, 45, 60),
        }
    }
    
    # Test scenes
    test_scenes = [
        {
            "scene_type": "title",
            "headline": "Bubble Sort",
            "narration": "Learn the simplest sorting algorithm!",
            "duration": 4.0
        },
        {
            "scene_type": "definition",
            "headline": "What is Bubble Sort?",
            "narration": "Bubble sort repeatedly swaps adjacent elements if they are in wrong order.",
            "duration": 5.0
        },
        {
            "scene_type": "array",
            "headline": "Watch It Work",
            "narration": "Let's sort: 5, 3, 8, 1, 2",
            "duration": 6.0
        },
        {
            "scene_type": "summary",
            "headline": "Key Takeaways",
            "narration": "1. Compare adjacent. 2. Swap if needed. 3. Repeat until sorted.",
            "duration": 5.0
        }
    ]
    
    # Generate project
    project_dir = generate_motion_canvas_project(test_scenes, test_theme, "Bubble Sort Tutorial")
    print(f"\n✅ Project generated at: {project_dir}")
    print("\nTo render:")
    print(f"  cd {project_dir}")
    print("  npm install")
    print("  npm run build")
