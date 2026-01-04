"""
🖼️ AI IMAGE GENERATOR - Using OpenRouter Image Models
======================================================
Generates real AI images for video frames using:
- Google Gemini 2.5 Flash Image
- OpenAI GPT-5 Image (fallback)
"""

import os
import httpx
import base64
import hashlib
import asyncio
from typing import Optional, Dict
from io import BytesIO
from PIL import Image

# ═══════════════════════════════════════════════════════════════════════════════
# 🔑 CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from app_secrets import API_KEY
    OPENROUTER_API_KEY = API_KEY
except ImportError:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Image models to try (in order of preference - free/cheap first)
IMAGE_MODELS = [
    "google/gemini-2.5-flash-image-preview",  # Free tier available
    "google/gemini-2.5-flash-image",
    "google/gemini-3-pro-image-preview",
    "openai/gpt-5-image-mini",
]

# Cache directory
IMAGE_CACHE_DIR = "backend/temp/images"
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 PROMPT TEMPLATES FOR DIFFERENT SCENE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATES = {
    'title': """
Create a simple, eye-catching educational thumbnail image for: {topic}
Style: Modern, clean, dark background with vibrant accent colors
Include: A simple iconic representation of the topic
Do NOT include any text or words in the image
""",
    
    'definition': """
Create a simple visual explanation image for: {topic}
Show: A clear, simple diagram or icon representing the concept
Style: Educational, flat design, dark background, bright colors
Do NOT include any text or words
""",
    
    'process': """
Create a simple flowchart-style image showing a process for: {topic}
Show: 3-4 connected boxes or icons with arrows between them
Style: Clean, modern infographic style, dark background
Use bright colors for boxes, white arrows
Do NOT include any text
""",
    
    'formula': """
Create a visual equation/formula image for: {topic}
Show: Icons or symbols representing the parts of the equation
Style: Scientific, clean design, dark background
Use colorful icons connected by + and = symbols
Do NOT include any text or numbers
""",
    
    'diagram': """
Create a hierarchical diagram image for: {topic}
Show: A tree structure with main concept at top, branches below
Style: Modern infographic, dark background, colorful nodes
Do NOT include any text
""",
    
    'comparison': """
Create a side-by-side comparison image for: {topic}
Show: Two distinct sections with contrasting visuals
Style: Split screen design, dark background
Use different colors for each side
Do NOT include any text
""",
    
    'example': """
Create a real-world example illustration for: {topic}
Show: A concrete, relatable visual example
Style: Friendly, educational, slightly cartoonish
Dark background with bright, engaging colors
Do NOT include any text
""",
    
    'summary': """
Create a summary checklist-style image for: {topic}
Show: 3-4 key point icons arranged neatly
Style: Clean, organized layout, dark background
Use checkmark or bullet icons with topic-related visuals
Do NOT include any text
""",
}


def get_image_prompt(scene_type: str, topic: str, narration: str) -> str:
    """Generate an appropriate image prompt based on scene type."""
    template = PROMPT_TEMPLATES.get(scene_type, PROMPT_TEMPLATES['definition'])
    
    # Extract key concepts from narration
    key_words = extract_keywords(narration)
    
    # Combine topic with key concepts
    full_topic = f"{topic} - {', '.join(key_words[:3])}" if key_words else topic
    
    prompt = template.format(topic=full_topic)
    return prompt.strip()


def extract_keywords(text: str) -> list:
    """Extract important keywords from text."""
    # Simple keyword extraction
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                  'as', 'into', 'through', 'during', 'before', 'after', 'above',
                  'below', 'between', 'under', 'again', 'further', 'then', 'once',
                  'it', 'its', 'this', 'that', 'these', 'those', 'and', 'but',
                  'or', 'so', 'if', 'because', 'while', 'although', 'like', 'when',
                  'what', 'how', 'why', 'where', 'who', 'which', 'you', 'your',
                  'they', 'them', 'their', 'we', 'our', 'i', 'me', 'my'}
    
    words = text.lower().split()
    keywords = []
    for word in words:
        # Clean word
        clean = ''.join(c for c in word if c.isalnum())
        if clean and len(clean) > 2 and clean not in stop_words:
            keywords.append(clean)
    
    # Return unique keywords
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    
    return unique[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# 🖼️ IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_image_async(prompt: str, scene_type: str = "definition") -> Optional[str]:
    """
    Generate an image using OpenRouter's image models.
    Returns the path to the saved image, or None if failed.
    """
    # Create cache key
    cache_key = hashlib.md5(f"{prompt}_{scene_type}".encode()).hexdigest()[:12]
    cache_path = os.path.join(IMAGE_CACHE_DIR, f"gen_{cache_key}.png")
    
    # Check cache
    if os.path.exists(cache_path):
        print(f"   📦 Cached image: {cache_path}")
        return cache_path
    
    print(f"   🎨 Generating AI image for {scene_type}...")
    
    # Try each image model
    for model in IMAGE_MODELS:
        try:
            print(f"   🤖 Trying model: {model}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "Aetheris Video Generator"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 4096,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract image from response
                    choices = data.get('choices', [])
                    if choices:
                        message = choices[0].get('message', {})
                        content = message.get('content', '')
                        
                        # Check if there's an image in the response
                        # Image models typically return base64 encoded images
                        if 'data:image' in content or content.startswith('/9j') or content.startswith('iVBOR'):
                            # It's a base64 image
                            img_data = extract_base64_image(content)
                            if img_data:
                                # Save image
                                img = Image.open(BytesIO(img_data))
                                img.save(cache_path, 'PNG')
                                print(f"   ✅ Image saved: {cache_path}")
                                return cache_path
                        
                        # Check for image URL in response
                        if 'http' in content and ('.png' in content or '.jpg' in content):
                            img_url = extract_url(content)
                            if img_url:
                                # Download image
                                img_response = await client.get(img_url)
                                if img_response.status_code == 200:
                                    img = Image.open(BytesIO(img_response.content))
                                    img.save(cache_path, 'PNG')
                                    print(f"   ✅ Image downloaded: {cache_path}")
                                    return cache_path
                        
                        print(f"   ⚠️ No image in response from {model}")
                else:
                    error = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    print(f"   ⚠️ {model}: Error {response.status_code}")
                    
        except Exception as e:
            print(f"   ⚠️ {model} failed: {e}")
            continue
    
    # Fallback: Try Pollinations.ai (free, no API key)
    return await generate_with_pollinations(prompt, cache_path)


async def generate_with_pollinations(prompt: str, cache_path: str) -> Optional[str]:
    """Fallback to Pollinations.ai for image generation."""
    try:
        print(f"   🌸 Trying Pollinations.ai...")
        
        # Clean prompt for URL
        clean_prompt = prompt.replace('\n', ' ').strip()[:200]
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=768&height=512&nologo=true"
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(url, follow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'image' in content_type:
                    # Save temporarily to check
                    temp_path = cache_path + ".temp"
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Verify it's a valid image and NOT a rate limit image
                    try:
                        img = Image.open(temp_path)
                        img.verify()
                        
                        # Re-open to check size (verify closes file)
                        img = Image.open(temp_path)
                        width, height = img.size
                        
                        # Rate limit images are often small or have specific dimensions
                        # Also check file size - rate limit images are usually small
                        file_size = os.path.getsize(temp_path)
                        
                        if file_size < 5000:  # Less than 5KB is suspicious
                            print(f"   ⚠️ Pollinations returned small image ({file_size} bytes) - likely rate limit")
                            os.remove(temp_path)
                            return None
                        
                        # Move to final path
                        os.rename(temp_path, cache_path)
                        print(f"   ✅ Pollinations image saved: {cache_path}")
                        return cache_path
                    except Exception as e:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        print(f"   ⚠️ Invalid image from Pollinations: {e}")
                        return None
                else:
                    print(f"   ⚠️ Pollinations returned non-image: {content_type}")
                    
    except Exception as e:
        print(f"   ⚠️ Pollinations error: {e}")
    
    return None


def extract_base64_image(content: str) -> Optional[bytes]:
    """Extract base64 image data from content."""
    import re
    
    # Try to find base64 data
    patterns = [
        r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)',
        r'^([A-Za-z0-9+/=]{100,})$',  # Raw base64
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            try:
                return base64.b64decode(match.group(1))
            except:
                continue
    
    return None


def extract_url(content: str) -> Optional[str]:
    """Extract image URL from content."""
    import re
    
    pattern = r'https?://[^\s<>"]+\.(?:png|jpg|jpeg|webp)'
    match = re.search(pattern, content)
    if match:
        return match.group(0)
    return None


def generate_image(prompt: str, scene_type: str = "definition") -> Optional[str]:
    """Synchronous wrapper for image generation."""
    try:
        return asyncio.run(generate_image_async(prompt, scene_type))
    except RuntimeError:
        # Already in an async context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(generate_image_async(prompt, scene_type))
                )
                return future.result(timeout=90)
        return loop.run_until_complete(generate_image_async(prompt, scene_type))


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test image generation
    test_prompt = "A bright yellow sun with rays shining on green plants, photosynthesis concept, educational illustration, dark background"
    
    print("Testing image generation...")
    result = generate_image(test_prompt, "title")
    
    if result:
        print(f"✅ Success! Image at: {result}")
    else:
        print("❌ Failed to generate image")
