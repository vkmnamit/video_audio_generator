"""
🖼️ USER IMAGE ANALYSIS SYSTEM
==============================
Users upload their own images → AI analyzes them → Video uses THOSE images

Flow:
1. User uploads 4-8 images for a topic (e.g., bubble sort)
2. AI analyzes each image (what's in it, colors, size)
3. AI generates script using the user's images as examples
4. Video renders with user's actual images being sorted/moved/compared

Example:
- User uploads: apple.jpg, orange.jpg, banana.jpg, grape.jpg
- Topic: "Bubble Sort"
- AI says: "Let's sort these fruits by size! Watch the apple and orange swap..."
- Video shows: User's fruit images actually swapping positions
"""

import os
import json
import uuid
import base64
import httpx
from typing import Dict, List, Optional, Tuple
from PIL import Image
from io import BytesIO

# Storage for uploaded images
UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Try to get API key
try:
    from app_secrets import API_KEY
except ImportError:
    API_KEY = os.getenv("OPENROUTER_API_KEY", "")


# ═══════════════════════════════════════════════════════════════════════════════
# 📤 IMAGE UPLOAD & STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

class ImageSession:
    """Manages a set of user-uploaded images for video generation."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.session_dir = os.path.join(UPLOAD_DIR, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.images: List[Dict] = []
        self.analysis_results: List[Dict] = []
        
    def add_image(self, image_data: bytes, filename: str = None) -> Dict:
        """Add an image to the session."""
        if not filename:
            filename = f"image_{len(self.images) + 1}.png"
        
        # Save image
        filepath = os.path.join(self.session_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Get basic info
        img = Image.open(BytesIO(image_data))
        
        image_info = {
            "index": len(self.images),
            "filename": filename,
            "filepath": filepath,
            "width": img.width,
            "height": img.height,
            "format": img.format or "PNG",
            "analysis": None,  # Will be filled by AI
        }
        
        self.images.append(image_info)
        print(f"📸 Added image {len(self.images)}: {filename} ({img.width}x{img.height})")
        
        return image_info
    
    def get_image_paths(self) -> List[str]:
        """Get list of all image paths."""
        return [img["filepath"] for img in self.images]
    
    def get_image_for_video(self, index: int) -> str:
        """Get image path by index for video rendering."""
        if 0 <= index < len(self.images):
            return self.images[index]["filepath"]
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 AI IMAGE ANALYSIS (Vision Model)
# ═══════════════════════════════════════════════════════════════════════════════

async def analyze_image_with_ai(image_path: str) -> Dict:
    """
    Use AI vision model to analyze what's in an image.
    Returns: object, color, size estimate, description
    """
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Get image format
        img = Image.open(image_path)
        mime_type = f"image/{img.format.lower()}" if img.format else "image/png"
        
        # Use vision model via OpenRouter
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-2.0-flash-001",  # Vision capable
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Analyze this image for educational video creation.
                                    
Return a JSON object with:
{
    "object": "main object name (e.g., 'apple', 'cat', 'book')",
    "description": "brief description (10 words max)",
    "color": "dominant color",
    "size_category": "small/medium/large (relative guess)",
    "sortable_value": number from 1-100 (for sorting demos, based on size/color/etc),
    "visual_label": "short label to show in video (2-3 words)"
}

Only return the JSON, nothing else."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 200,
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON from response
                try:
                    # Clean up response
                    content = content.strip()
                    if content.startswith('```'):
                        content = content.split('```')[1]
                        if content.startswith('json'):
                            content = content[4:]
                    
                    analysis = json.loads(content)
                    print(f"   ✅ Analyzed: {analysis.get('object', 'unknown')} - {analysis.get('description', '')}")
                    return analysis
                except json.JSONDecodeError:
                    print(f"   ⚠️ Could not parse AI response: {content[:100]}")
                    return {
                        "object": "item",
                        "description": "uploaded image",
                        "color": "unknown",
                        "size_category": "medium",
                        "sortable_value": 50,
                        "visual_label": "Item"
                    }
            else:
                print(f"   ⚠️ Vision API error: {response.status_code}")
                
    except Exception as e:
        print(f"   ⚠️ Image analysis error: {e}")
    
    # Fallback
    return {
        "object": "item",
        "description": "uploaded image",
        "color": "unknown", 
        "size_category": "medium",
        "sortable_value": 50,
        "visual_label": "Item"
    }


async def analyze_all_images(session: ImageSession) -> List[Dict]:
    """Analyze all images in a session."""
    print(f"\n🧠 Analyzing {len(session.images)} uploaded images...")
    
    for i, img_info in enumerate(session.images):
        print(f"   📸 Analyzing image {i+1}/{len(session.images)}: {img_info['filename']}")
        analysis = await analyze_image_with_ai(img_info['filepath'])
        img_info['analysis'] = analysis
        session.analysis_results.append(analysis)
    
    return session.analysis_results


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 SCRIPT GENERATION USING USER'S IMAGES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_script_prompt_with_images(topic: str, image_analyses: List[Dict]) -> str:
    """
    Generate a script prompt that uses the user's uploaded images as examples.
    
    Example: For bubble sort with fruit images:
    "Explain bubble sort using these items: Apple (value 30), Orange (value 45), Banana (value 20)..."
    """
    
    # Build description of user's images
    image_descriptions = []
    for i, analysis in enumerate(image_analyses):
        desc = f"Image {i+1}: {analysis.get('object', 'item')} ({analysis.get('description', 'no description')}, sortable value: {analysis.get('sortable_value', 50)})"
        image_descriptions.append(desc)
    
    images_context = "\n".join(image_descriptions)
    
    prompt = f"""You are creating an educational video about: {topic}

THE USER HAS UPLOADED THESE IMAGES TO USE AS EXAMPLES:
{images_context}

IMPORTANT INSTRUCTIONS:
1. USE THE USER'S IMAGES as the items in your explanation
2. Reference them by name (e.g., "the apple", "the orange")
3. When showing sorting/moving/comparing, describe which user images move
4. Make it personal - "YOUR apple is now swapping with YOUR orange"

For example, if explaining Bubble Sort with fruits:
- "Let's sort your fruits! The apple has value 30, the orange has value 45..."
- "First, we compare YOUR apple and YOUR orange. Since 30 < 45, they stay in place!"
- "Now watch YOUR banana move into the correct position..."

Create the video script with these scenes:
1. TITLE - Hook with the user's items
2. DEFINITION - What is {topic}?
3. EXPLANATION - Why it matters
4. PROCESS - Step by step using USER'S IMAGES
5. ARRAY - Show the user's items being sorted/moved (use scene_type: "array")
6. EXAMPLE - Trace through with their specific items
7. SUMMARY - Key takeaways

Each scene should reference the user's uploaded images by name.

Return JSON format:
{{
    "title": "video title",
    "scenes": [
        {{
            "scene_type": "title|definition|explanation|process|array|example|summary",
            "headline": "SHORT HEADLINE",
            "narration": "what to say (reference user's images!)",
            "duration": 5.0,
            "user_images_shown": [0, 1, 2],  // indices of which user images to show
            "image_positions": ["left", "center", "right"],  // where to place them
            "highlight_index": 0  // which image is highlighted (for sorting)
        }}
    ]
}}
"""
    
    return prompt


async def generate_script_with_user_images(topic: str, session: ImageSession) -> Dict:
    """Generate a complete video script using the user's images."""
    
    # First, analyze all images if not done
    if not session.analysis_results:
        await analyze_all_images(session)
    
    # Generate the script prompt
    prompt = generate_script_prompt_with_images(topic, session.analysis_results)
    
    print(f"\n📝 Generating script using {len(session.images)} user images...")
    
    # Call AI to generate script
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/devstral-2512:free",
                "messages": [
                    {"role": "system", "content": "You are an expert educational video creator. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON
            try:
                content = content.strip()
                if '```' in content:
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                    content = content.split('```')[0]
                
                script = json.loads(content)
                print(f"   ✅ Script generated with {len(script.get('scenes', []))} scenes")
                return script
            except json.JSONDecodeError as e:
                print(f"   ⚠️ JSON parse error: {e}")
                return None
        else:
            print(f"   ⚠️ API error: {response.status_code}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 VIDEO FRAME RENDERING WITH USER IMAGES
# ═══════════════════════════════════════════════════════════════════════════════

def render_user_image_array(
    session: ImageSession,
    image_indices: List[int],
    width: int,
    height: int,
    duration: float,
    highlight_index: int = -1,
    show_values: bool = True,
    show_swap_animation: bool = False,
) -> 'CompositeVideoClip':
    """
    Render user's images as an array (like for sorting visualization).
    
    Args:
        session: ImageSession with user's images
        image_indices: Which images to show (in order)
        width, height: Frame size
        duration: Clip duration
        highlight_index: Which image is currently highlighted
        show_values: Show sortable values under images
        show_swap_animation: Show swap arrows
    """
    from moviepy import ImageClip, TextClip, ColorClip, CompositeVideoClip
    from style_reference_system import get_current_theme
    
    theme = get_current_theme()
    colors = theme.get('colors', {})
    
    layers = []
    
    # Background
    bg = ColorClip(size=(width, height), color=colors.get('bg', (20, 25, 35)), duration=duration)
    layers.append(bg)
    
    # Calculate layout
    num_images = len(image_indices)
    if num_images == 0:
        return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)
    
    # Image size and spacing
    max_img_size = min(150, (width - 100) // num_images - 30)
    spacing = 40
    total_width = num_images * max_img_size + (num_images - 1) * spacing
    start_x = (width - total_width) // 2
    img_y = height // 2 - max_img_size // 2 - 20
    
    font = "/System/Library/Fonts/Helvetica.ttc"
    
    # Render each image
    for i, img_idx in enumerate(image_indices):
        x = start_x + i * (max_img_size + spacing)
        
        # Get image path
        img_path = session.get_image_for_video(img_idx)
        if not img_path or not os.path.exists(img_path):
            continue
        
        # Highlight glow
        if i == highlight_index:
            glow_color = colors.get('primary', (0, 255, 136))
            glow = ColorClip(size=(max_img_size + 20, max_img_size + 20), 
                           color=glow_color, duration=duration)
            glow = glow.with_opacity(0.5).with_position((x - 10, img_y - 10))
            layers.append(glow)
        
        # User's image
        try:
            img_clip = ImageClip(img_path, duration=duration)
            # Resize to fit
            img_clip = img_clip.resized(height=max_img_size)
            if img_clip.w > max_img_size:
                img_clip = img_clip.resized(width=max_img_size)
            img_clip = img_clip.with_position((x, img_y))
            layers.append(img_clip)
        except Exception as e:
            print(f"   ⚠️ Could not load image {img_idx}: {e}")
            continue
        
        # Border for highlighted
        if i == highlight_index:
            # Top border
            border = ColorClip(size=(max_img_size, 4), 
                             color=colors.get('primary', (0, 255, 136)), 
                             duration=duration)
            border = border.with_position((x, img_y - 4))
            layers.append(border)
        
        # Value label below image
        if show_values and session.images[img_idx].get('analysis'):
            analysis = session.images[img_idx]['analysis']
            value = analysis.get('sortable_value', 50)
            label = analysis.get('visual_label', analysis.get('object', 'Item'))
            
            # Value
            value_text = TextClip(
                text=str(value),
                font_size=24,
                color='white',
                font=font
            ).with_duration(duration)
            value_text = value_text.with_position((x + max_img_size // 2 - 15, img_y + max_img_size + 10))
            layers.append(value_text)
            
            # Label
            label_text = TextClip(
                text=label[:12],
                font_size=16,
                color='#aaaaaa',
                font=font
            ).with_duration(duration)
            label_text = label_text.with_position((x + 5, img_y + max_img_size + 40))
            layers.append(label_text)
        
        # Index
        idx_text = TextClip(
            text=str(i),
            font_size=14,
            color='#666666',
            font=font
        ).with_duration(duration)
        idx_text = idx_text.with_position((x + max_img_size // 2 - 5, img_y - 25))
        layers.append(idx_text)
    
    # Swap arrows if needed
    if show_swap_animation and highlight_index >= 0 and highlight_index < num_images - 1:
        arrow_x = start_x + highlight_index * (max_img_size + spacing) + max_img_size + 5
        arrow_y = img_y + max_img_size // 2 - 15
        
        arrow = TextClip(
            text="⟷",
            font_size=30,
            color='#ffcc00',
            font=font
        ).with_duration(duration)
        arrow = arrow.with_position((arrow_x, arrow_y))
        layers.append(arrow)
    
    return CompositeVideoClip(layers, size=(width, height)).with_duration(duration)


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    print("🖼️ User Image System Test")
    print("=" * 50)
    
    # Create test session
    session = ImageSession()
    print(f"Session ID: {session.session_id}")
    print(f"Upload dir: {session.session_dir}")
    
    print("\nTo test:")
    print("1. Upload images via /upload-images endpoint")
    print("2. Generate video with /generate-video-with-images")
