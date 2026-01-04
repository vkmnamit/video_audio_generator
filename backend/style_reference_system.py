"""
🎨 STYLE REFERENCE SYSTEM - Image-Conditioned Generation
=========================================================
Uses user-uploaded reference images to maintain visual consistency.
AI extends YOUR visual language instead of inventing a new one.

Flow:
1. User uploads 4-5 reference images (or use default theme)
2. System extracts: style, colors, shapes, layout patterns
3. AI generates new frames matching that exact style
4. Your layout logic arranges them
5. Final consistent video
"""

import os
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from PIL import Image
import colorsys
from collections import Counter

# ═══════════════════════════════════════════════════════════════════════════════
# 📁 REFERENCE IMAGE STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCE_DIR = "backend/references"
THEMES_DIR = "backend/themes"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(THEMES_DIR, exist_ok=True)

# Default theme reference images (bundled with app)
DEFAULT_THEMES = {
    "algorithm": {
        "name": "Algorithm Explainer",
        "description": "Dark background, neon boxes, clean arrows",
        "colors": {
            "bg": (15, 20, 30),
            "primary": (0, 255, 136),      # Matrix green
            "secondary": (64, 196, 255),   # Blue
            "accent": (255, 100, 150),     # Pink
            "text": (255, 255, 255),
            "card": (25, 35, 50),
            "inactive": (60, 70, 90),
        },
        "style": {
            "shape": "rectangular",        # rectangular, rounded, circular
            "stroke_width": 3,
            "has_glow": True,
            "has_gradient": False,
            "icon_style": "minimal",       # minimal, detailed, emoji
            "arrow_style": "straight",     # straight, curved, animated
        },
        "layout": {
            "box_padding": 20,
            "box_spacing": 40,
            "arrow_length": 60,
            "title_position": "top",
        }
    },
    "science": {
        "name": "Science Explainer",
        "description": "Nature colors, organic shapes, educational",
        "colors": {
            "bg": (10, 25, 20),
            "primary": (76, 217, 100),     # Green
            "secondary": (255, 204, 0),    # Yellow
            "accent": (90, 200, 250),      # Sky blue
            "text": (255, 255, 255),
            "card": (25, 45, 35),
            "inactive": (50, 80, 60),
        },
        "style": {
            "shape": "rounded",
            "stroke_width": 2,
            "has_glow": True,
            "has_gradient": False,
            "icon_style": "emoji",
            "arrow_style": "curved",
        },
        "layout": {
            "box_padding": 25,
            "box_spacing": 50,
            "arrow_length": 70,
            "title_position": "top",
        }
    },
    "minimal": {
        "name": "Minimal Clean",
        "description": "Simple, black and white with accent",
        "colors": {
            "bg": (20, 20, 25),
            "primary": (255, 255, 255),
            "secondary": (150, 150, 160),
            "accent": (255, 100, 100),
            "text": (255, 255, 255),
            "card": (35, 35, 40),
            "inactive": (80, 80, 90),
        },
        "style": {
            "shape": "rectangular",
            "stroke_width": 1,
            "has_glow": False,
            "has_gradient": False,
            "icon_style": "minimal",
            "arrow_style": "straight",
        },
        "layout": {
            "box_padding": 15,
            "box_spacing": 30,
            "arrow_length": 50,
            "title_position": "center",
        }
    },
    "vibrant": {
        "name": "Vibrant Educational",
        "description": "Colorful, engaging, youth-friendly",
        "colors": {
            "bg": (25, 15, 35),
            "primary": (255, 100, 200),    # Pink
            "secondary": (100, 255, 200),  # Mint
            "accent": (255, 200, 100),     # Gold
            "text": (255, 255, 255),
            "card": (40, 30, 55),
            "inactive": (80, 60, 100),
        },
        "style": {
            "shape": "rounded",
            "stroke_width": 3,
            "has_glow": True,
            "has_gradient": True,
            "icon_style": "emoji",
            "arrow_style": "animated",
        },
        "layout": {
            "box_padding": 20,
            "box_spacing": 45,
            "arrow_length": 60,
            "title_position": "top",
        }
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 COLOR EXTRACTION FROM REFERENCE IMAGES
# ═══════════════════════════════════════════════════════════════════════════════

def extract_dominant_colors(image_path: str, num_colors: int = 6) -> List[Tuple[int, int, int]]:
    """Extract dominant colors from an image."""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((150, 150))  # Resize for speed
        
        pixels = list(img.getdata())
        
        # Quantize colors
        color_counts = Counter()
        for pixel in pixels:
            # Round to nearest 20 to group similar colors
            quantized = (
                (pixel[0] // 20) * 20,
                (pixel[1] // 20) * 20,
                (pixel[2] // 20) * 20
            )
            color_counts[quantized] += 1
        
        # Get top colors
        top_colors = [color for color, count in color_counts.most_common(num_colors)]
        
        return top_colors
    except Exception as e:
        print(f"Error extracting colors: {e}")
        return [(30, 30, 40), (100, 200, 255), (255, 255, 255)]


def categorize_colors(colors: List[Tuple[int, int, int]]) -> Dict:
    """Categorize extracted colors into semantic roles."""
    if not colors:
        return DEFAULT_THEMES["algorithm"]["colors"]
    
    # Sort by brightness
    def brightness(c):
        return (c[0] * 299 + c[1] * 587 + c[2] * 114) / 1000
    
    sorted_colors = sorted(colors, key=brightness)
    
    # Darkest = background
    bg = sorted_colors[0] if sorted_colors else (20, 20, 30)
    
    # Brightest = text
    text = sorted_colors[-1] if len(sorted_colors) > 1 else (255, 255, 255)
    
    # Find most saturated for primary
    def saturation(c):
        r, g, b = c[0]/255, c[1]/255, c[2]/255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        return (max_c - min_c) / max_c if max_c > 0 else 0
    
    saturated = sorted(colors, key=saturation, reverse=True)
    primary = saturated[0] if saturated else (0, 200, 255)
    secondary = saturated[1] if len(saturated) > 1 else (255, 150, 100)
    accent = saturated[2] if len(saturated) > 2 else (255, 100, 150)
    
    # Card color = slightly lighter than bg
    card = tuple(min(255, c + 20) for c in bg)
    
    return {
        "bg": bg,
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "text": text,
        "card": card,
        "inactive": tuple((c + bg[i]) // 2 for i, c in enumerate(text)),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 📐 STYLE EXTRACTION FROM REFERENCE IMAGES
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_image_style(image_path: str) -> Dict:
    """Analyze visual style of a reference image."""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        width, height = img.size
        
        # Check for rounded corners (sample corner regions)
        # This is a heuristic - check if corners are uniform (likely rounded/clipped)
        corner_sample = img.crop((0, 0, 20, 20))
        corner_colors = list(corner_sample.getdata())
        corner_uniform = len(set(corner_colors)) < 5
        
        # Check contrast for glow detection
        pixels = list(img.resize((50, 50)).getdata())
        brightnesses = [(p[0] + p[1] + p[2]) / 3 for p in pixels]
        contrast = max(brightnesses) - min(brightnesses)
        has_glow = contrast > 200
        
        # Determine shape style
        shape = "rounded" if corner_uniform else "rectangular"
        
        return {
            "shape": shape,
            "stroke_width": 2,  # Default
            "has_glow": has_glow,
            "has_gradient": False,  # Hard to detect
            "icon_style": "minimal",
            "arrow_style": "straight",
        }
    except Exception as e:
        print(f"Error analyzing style: {e}")
        return DEFAULT_THEMES["algorithm"]["style"]


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 THEME CREATION FROM REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

def create_theme_from_references(image_paths: List[str], theme_name: str = "custom") -> Dict:
    """
    Create a complete theme from user-uploaded reference images.
    
    Args:
        image_paths: List of 4-5 reference image paths
        theme_name: Name for the custom theme
    
    Returns:
        Complete theme dictionary with colors, style, layout
    """
    if not image_paths:
        print("No reference images provided, using default algorithm theme")
        return DEFAULT_THEMES["algorithm"]
    
    print(f"📸 Analyzing {len(image_paths)} reference images...")
    
    # Collect all colors from all images
    all_colors = []
    all_styles = []
    
    for path in image_paths:
        if os.path.exists(path):
            colors = extract_dominant_colors(path)
            all_colors.extend(colors)
            
            style = analyze_image_style(path)
            all_styles.append(style)
    
    # Aggregate colors
    color_palette = categorize_colors(all_colors)
    
    # Aggregate styles (majority vote)
    if all_styles:
        shape_votes = Counter(s["shape"] for s in all_styles)
        glow_votes = Counter(s["has_glow"] for s in all_styles)
        
        final_style = {
            "shape": shape_votes.most_common(1)[0][0],
            "stroke_width": 2,
            "has_glow": glow_votes.most_common(1)[0][0],
            "has_gradient": False,
            "icon_style": "minimal",
            "arrow_style": "straight",
        }
    else:
        final_style = DEFAULT_THEMES["algorithm"]["style"]
    
    theme = {
        "name": theme_name,
        "description": f"Custom theme from {len(image_paths)} reference images",
        "colors": color_palette,
        "style": final_style,
        "layout": DEFAULT_THEMES["algorithm"]["layout"],
        "reference_images": image_paths,
    }
    
    print(f"✅ Theme created: {theme_name}")
    print(f"   Colors: bg={color_palette['bg']}, primary={color_palette['primary']}")
    print(f"   Style: {final_style['shape']}, glow={final_style['has_glow']}")
    
    return theme


def save_theme(theme: Dict, filename: str = None) -> str:
    """Save a theme to disk."""
    if not filename:
        filename = f"{theme['name'].lower().replace(' ', '_')}.json"
    
    filepath = os.path.join(THEMES_DIR, filename)
    
    # Convert tuples to lists for JSON
    theme_json = json.loads(json.dumps(theme, default=lambda x: list(x) if isinstance(x, tuple) else x))
    
    with open(filepath, 'w') as f:
        json.dump(theme_json, f, indent=2)
    
    print(f"💾 Theme saved: {filepath}")
    return filepath


def load_theme(theme_name: str) -> Dict:
    """Load a theme by name."""
    # Check default themes first
    if theme_name in DEFAULT_THEMES:
        return DEFAULT_THEMES[theme_name]
    
    # Check saved themes
    filepath = os.path.join(THEMES_DIR, f"{theme_name}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            theme = json.load(f)
            # Convert lists back to tuples
            for key in theme.get('colors', {}):
                if isinstance(theme['colors'][key], list):
                    theme['colors'][key] = tuple(theme['colors'][key])
            return theme
    
    # Fallback
    print(f"Theme '{theme_name}' not found, using default")
    return DEFAULT_THEMES["algorithm"]


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 PROMPT GENERATION FOR CONSISTENT STYLE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_style_prompt(theme: Dict, scene_type: str, content: str) -> str:
    """
    Generate an AI prompt that maintains the theme's visual style.
    
    This prompt is designed for img2img or style-conditioned generation.
    """
    colors = theme.get('colors', {})
    style = theme.get('style', {})
    
    # Color descriptions
    bg_desc = f"rgb({colors.get('bg', (20,20,30))})"
    primary_desc = f"rgb({colors.get('primary', (0,200,255))})"
    
    # Style descriptions
    shape_desc = style.get('shape', 'rectangular')
    glow_desc = "with subtle glow effects" if style.get('has_glow') else "flat, no glow"
    
    # Scene-specific content
    scene_prompts = {
        'title': f"Educational title card for '{content}'",
        'definition': f"Definition card explaining '{content}'",
        'process': f"Process flowchart showing steps of '{content}'",
        'formula': f"Visual equation or formula for '{content}'",
        'diagram': f"Hierarchical diagram of '{content}'",
        'comparison': f"Side-by-side comparison for '{content}'",
        'example': f"Real-world example illustration of '{content}'",
        'summary': f"Summary checklist for '{content}'",
    }
    
    scene_content = scene_prompts.get(scene_type, f"Educational visual for '{content}'")
    
    prompt = f"""
{scene_content}

STRICT STYLE REQUIREMENTS:
- Dark background color: {bg_desc}
- Primary accent color: {primary_desc}
- Shape style: {shape_desc} boxes and elements
- Visual effect: {glow_desc}
- Icon style: Simple, minimal, geometric
- NO realistic imagery
- NO photographs
- NO gradients unless specified
- Clean educational infographic style
- Consistent with algorithm/tech explainer aesthetic

DO NOT include any text, words, or numbers in the image.
Focus only on shapes, icons, and visual elements.
"""
    
    return prompt.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 🖼️ VISUAL ELEMENT GENERATOR (Code-based, no AI needed)
# ═══════════════════════════════════════════════════════════════════════════════

def get_theme_colors_for_moviepy(theme: Dict) -> Dict:
    """Convert theme colors to MoviePy-compatible format."""
    colors = theme.get('colors', DEFAULT_THEMES['algorithm']['colors'])
    
    return {
        'bg': colors.get('bg', (20, 20, 30)),
        'primary': colors.get('primary', (0, 200, 255)),
        'secondary': colors.get('secondary', (255, 150, 100)),
        'accent': colors.get('accent', (255, 100, 150)),
        'text': colors.get('text', (255, 255, 255)),
        'card': colors.get('card', (35, 40, 55)),
        'inactive': colors.get('inactive', (80, 90, 110)),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 CURRENT ACTIVE THEME (Global state)
# ═══════════════════════════════════════════════════════════════════════════════

_current_theme = DEFAULT_THEMES["algorithm"]

def set_current_theme(theme_name_or_dict):
    """Set the current active theme by name or dict."""
    global _current_theme
    if isinstance(theme_name_or_dict, str):
        if theme_name_or_dict in DEFAULT_THEMES:
            _current_theme = DEFAULT_THEMES[theme_name_or_dict]
        else:
            _current_theme = load_theme(theme_name_or_dict)
    else:
        _current_theme = theme_name_or_dict
    print(f"🎨 Active theme set: {_current_theme.get('name', 'custom')}")

def get_current_theme() -> Dict:
    """Get the current active theme."""
    return _current_theme

def get_current_colors() -> Dict:
    """Get colors from current theme in MoviePy format."""
    return get_theme_colors_for_moviepy(_current_theme)


def list_available_themes() -> List[Dict]:
    """List all available themes with their info."""
    themes = []
    for name, theme in DEFAULT_THEMES.items():
        themes.append({
            "name": name,
            "display_name": theme.get("name", name),
            "description": theme.get("description", ""),
            "colors": {
                "bg": theme["colors"]["bg"],
                "primary": theme["colors"]["primary"],
                "accent": theme["colors"]["accent"],
            }
        })
    
    # Also check for saved custom themes
    if os.path.exists(THEMES_DIR):
        for filename in os.listdir(THEMES_DIR):
            if filename.endswith('.json'):
                theme_name = filename[:-5]
                if theme_name not in DEFAULT_THEMES:
                    try:
                        theme = load_theme(theme_name)
                        themes.append({
                            "name": theme_name,
                            "display_name": theme.get("name", theme_name),
                            "description": theme.get("description", "Custom theme"),
                            "colors": {
                                "bg": theme["colors"]["bg"],
                                "primary": theme["colors"]["primary"],
                                "accent": theme["colors"]["accent"],
                            }
                        })
                    except:
                        pass
    
    return themes


def get_theme_preview_colors(theme_name: str) -> Dict:
    """Get preview colors for a theme."""
    theme = load_theme(theme_name) if theme_name not in DEFAULT_THEMES else DEFAULT_THEMES[theme_name]
    colors = theme.get("colors", {})
    return {
        "bg": colors.get("bg", (20, 20, 30)),
        "primary": colors.get("primary", (0, 200, 255)),
        "secondary": colors.get("secondary", (255, 150, 100)),
        "accent": colors.get("accent", (255, 100, 150)),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing Style Reference System...")
    
    # Test default themes
    print("\n📋 Available default themes:")
    for name, theme in DEFAULT_THEMES.items():
        print(f"   {name}: {theme['description']}")
    
    # Test theme loading
    theme = load_theme("algorithm")
    print(f"\n🎨 Loaded theme: {theme['name']}")
    print(f"   Primary color: {theme['colors']['primary']}")
    
    # Test prompt generation
    prompt = generate_style_prompt(theme, "process", "Stack operations")
    print(f"\n📝 Generated prompt preview:")
    print(prompt[:200] + "...")
