# 🎬 Aetheris - AI Video Generator

> Transform any topic into engaging explainer videos with AI-powered visuals and narration

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ What is Aetheris?

Aetheris is an AI-powered video generation platform that creates **professional explainer videos** from just a text prompt. Simply type any topic, and the AI will:

1. 🧠 **Think like a teacher** - Break down complex topics into simple concepts
2. 🎨 **Generate smart visuals** - Automatically choose the best visualization (arrays, flowcharts, formulas, diagrams)
3. 🎙️ **Add human-like narration** - Natural voice using Microsoft Edge TTS
4. 🎬 **Render a complete video** - Ready to upload to YouTube Shorts or any platform

## 🎥 Demo

![Aetheris Demo](https://via.placeholder.com/800x400?text=Aetheris+Demo+Video)

## 🚀 Features

### Smart Visual Selection
The AI automatically picks the right visualization for each concept:

| Topic Type | Visualization |
|------------|---------------|
| Sorting Algorithms | 📊 Array with numbers moving |
| Math/Physics | 📐 Formula with explained parts |
| Processes | 🔀 Flowchart with connections |
| Comparisons | ⚖️ Side-by-side comparison |
| Data | 📋 Tables with headers |
| Cycles/Parts | 🔄 Diagrams |

### Video Formats
- **YouTube Shorts** (9:16) - 40-60 seconds
- **Long Form** (16:9) - 2-5 minutes

### Visual Themes
- 🌙 Dark minimalist style
- 🎨 Accent colors (green, red, teal, yellow, purple, orange)
- ✨ Clean geometric shapes
- 📝 Bold typography

## 🛠️ Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - High-performance API
- **MoviePy** - Video compositing
- **Edge TTS** - Natural voice synthesis (Microsoft voices)
- **OpenRouter API** - AI script generation (Gemini 2.0 Flash)
- **Pollinations.ai** - FREE AI image generation (Stable Diffusion/FLUX)
- **Google Gemini** - Backup image generation

### Frontend
- **React 18** - UI framework
- **Vite** - Fast build tool
- **CSS3** - Modern styling

### Image Generation (Priority Order)
1. **Pollinations.ai** - FREE, no API key needed, uses FLUX model
2. **Google Gemini** - Uses your Google API key
3. **OpenRouter** - Uses credits
4. **Pexels/Pixabay** - Free stock images as final fallback

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- FFmpeg (for video processing)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/aetheris-video-generator.git
cd aetheris-video-generator
```

### 2. Setup Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Setup Frontend
```bash
cd frontend
npm install
```

### 4. Configure API Keys
Create `backend/app_secrets.py`:
```python
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
```

Get your API key from [OpenRouter](https://openrouter.ai/)

## 🚀 Running the Application

### Start Backend (Terminal 1)
```bash
# Navigate to project root
Perfect — I’ll show you **exactly HOW the video is framed**, visually and structurally, so you can *see it in your head* and then implement it.

This is the **final framing blueprint** for your **Stable-Diffusion + Shorts-style explainer video**.

---

## 🎬 VIDEO CANVAS (FIXED FOREVER)

**Format**

* 📱 Vertical (YouTube Shorts)
* 📐 Size: **1080 × 1920**
* 🎨 Background: **Dark (near-black / dark gray)**

Every frame uses the **same canvas**.
Only **content inside changes**.

---

## 🧠 THE FRAME RULE (MOST IMPORTANT)

> **ONE frame = ONE idea**

No clutter.
No paragraphs.
No multiple concepts.

---

## 🧩 UNIVERSAL FRAME LAYOUT (BASE GRID)

```
┌──────────────────────────┐
│        HEADLINE          │  ← Big, bold (top 20%)
│──────────────────────────│
│                          │
│     VISUAL ZONE          │  ← Icons / shapes / arrows (middle 60%)
│                          │
│──────────────────────────│
│     SUPPORT TEXT         │  ← Small, optional (bottom 20%)
└──────────────────────────┘
```

This grid **never changes**.

---

## 🖼️ HOW EACH FRAME TYPE LOOKS (WITH PURPOSE)

![Image](https://piktochart.com/wp-content/uploads/2025/05/youtube-shorts-safe-zone.png)

![Image](https://st.depositphotos.com/24883724/53464/v/1600/depositphotos_534645398-stock-illustration-modern-infographic-process-flow-diagram.jpg)

![Image](https://png.pngtree.com/thumb_back/fh260/background/20220318/pngtree-visualization-of-fractal-grid-rendering-texture-algorithm-photo-image_3723387.jpg)

![Image](https://i.etsystatic.com/25502974/r/il/ba0918/2587313462/il_fullxfull.2587313462_s0qp.jpg)

---

## 1️⃣ TITLE FRAME (HOOK)

🎯 **Purpose**: Grab attention in 1 second

```
HEADLINE:
PHOTOSYNTHESIS

VISUAL:
• Single bold icon (leaf or sun)

SUPPORT TEXT:
(optional) "How plants make food"
```

**Design**

* Very big text
* Centered icon
* No arrows

---

## 2️⃣ INPUTS FRAME (WHAT GOES IN)

🎯 **Purpose**: Show ingredients / requirements

```
HEADLINE:
INPUTS

VISUAL:
☀️   💧   CO₂
(icons evenly spaced)

SUPPORT TEXT:
"Energy + materials"
```

**Design**

* 3 icons in a row
* Same size
* No motion yet (or subtle fade)

---

## 3️⃣ PROCESS FRAME (CORE EXPLANATION)

🎯 **Purpose**: Explain HOW it works

```
HEADLINE:
PROCESS

VISUAL:
[Sun Icon] → [Leaf Box]

SUPPORT TEXT:
"Leaf absorbs sunlight"
```

**Design**

* Rectangle = system
* Arrow = flow
* Icon enters box (slide animation)

👉 This is where **learning happens**

---

## 4️⃣ OUTPUT FRAME (RESULT)

🎯 **Purpose**: Show result clearly

```
HEADLINE:
OUTPUT

VISUAL:
[Leaf Box] →  Glucose   Oxygen

SUPPORT TEXT:
"Food + air"
```

**Design**

* Arrows moving outward
* Bright accent color
* Slight scale-up animation

---

## 5️⃣ SUMMARY FRAME (MEMORY LOCK)

🎯 **Purpose**: Make user remember

```
HEADLINE:
SUMMARY

VISUAL:
✔ Uses sunlight
✔ Makes food
✔ Releases oxygen

SUPPORT TEXT:
(none)
```

**Design**

* Checkmarks
* Calm motion
* Clean exit

---

## ⏱️ TIMING (VERY IMPORTANT)

| Frame Type | Duration |
| ---------- | -------- |
| Title      | 1.5 s    |
| Inputs     | 2 s      |
| Process    | 3 s      |
| Output     | 2 s      |
| Summary    | 1.5 s    |

Total ≈ **10 seconds** (perfect Shorts length)

---

## 🎨 COLOR & STYLE RULES (LOCK THESE)

* Background: `#0E0E0E`
* Text: `#FFFFFF`
* Accent: **ONE per frame** (green / yellow / teal)
* Shapes: Rounded corners
* Font: Bold, sans-serif

---

## 🧠 WHERE Stable Diffusion FITS (CLEARLY)

Stable Diffusion generates ONLY:

* ☀️ Sun icon
* 🍃 Leaf icon
* 💧 Water icon
* CO₂ symbol

It does **NOT**:

* Place arrows
* Align layout
* Add text

You place everything using code.

---

## 🎬 FINAL VIDEO FEEL

* Fast
* Clean
* Logical
* Visual
* Silent but understandable
* Shorts-ready

Exactly like the video you referenced.

---

## 🧠 ONE-LINE FINAL CLARITY

> **Your video is a sequence of vertically framed slides where each slide uses big text + simple shapes to explain one idea.**

---

## 🚀 WHAT TO DO NEXT (CLEAR OPTIONS)

If you want, next I can:

1️⃣ Draw **ASCII wireframes** for every frame
2️⃣ Give **Python code** that builds this exact layout
3️⃣ Create a **sample photosynthesis video spec**
4️⃣ Help you design **motion rules** (slide, fade, scale)

Just reply with the number 👉 **1, 2, 3, or 4**


# Activate virtual environment
source venv/bin/activate

# Go to backend and run server
cd backend
uvicorn main:app --reload --port 8000
```
Backend runs on: `http://localhost:8000`

**Alternative (simple):**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev -- --port 5175
```
Frontend runs on: `http://localhost:5175`

## 📖 Usage

1. Open `http://localhost:5173` in your browser
2. Enter any topic (e.g., "Explain Bubble Sort", "How does photosynthesis work?")
3. Select video type (Short or Long)
4. Optionally specify target audience
5. Click **Generate Video**
6. Wait for AI to create your video
7. Download and share!

### Example Prompts
- "Explain Bubble Sort algorithm"
- "How does WiFi work?"
- "What is photosynthesis?"
- "Explain Newton's Laws of Motion"
- "How does a CPU work?"
- "What is Machine Learning?"

## 📁 Project Structure

```
aetheris-video-generator/
├── backend/
│   ├── main.py              # FastAPI server & video generation
│   ├── app_secrets.py       # API keys (not in git)
│   ├── requirements.txt     # Python dependencies
│   ├── output/              # Generated videos
│   └── temp/                # Temporary files
│       ├── audio/           # TTS audio files
│       └── images/          # Frame images
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styles
│   │   └── main.jsx         # Entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
└── README.md
```

## 🎨 Frame Types

The AI can generate these visual frame types:

| Frame | Description |
|-------|-------------|
| `title` | Bold centered text with accent underline |
| `definition` | Term + meaning with icon |
| `explanation` | Concept with visual elements |
| `process` | Numbered steps list |
| `flowchart` | Nodes with arrows/connections |
| `formula` | Math equation with part explanations |
| `array` | Numbers in boxes (for sorting) |
| `table` | Data in rows and columns |
| `comparison` | Side-by-side comparison |
| `diagram` | Shapes showing relationships |
| `example` | Real-world example |
| `summary` | Key takeaways with checkmarks |

## 🔧 Configuration

### Video Settings (in `main.py`)
```python
# Video dimensions
SHORT_SIZE = (1080, 1920)  # 9:16 for Shorts
LONG_SIZE = (1920, 1080)   # 16:9 for YouTube

# Colors
BG_COLOR = (18, 18, 24)    # Dark background
ACCENT_COLORS = {
    "green": (0, 255, 136),
    "red": (255, 71, 87),
    "teal": (0, 255, 255),
    # ...
}
```

### TTS Voice
Default voice: `en-US-ChristopherNeural` (Microsoft Edge TTS)

## 🚀 Deployment

### Deploy Frontend to Vercel

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) and import your repo
3. Set the **Root Directory** to `frontend`
4. Add environment variable:
   - `VITE_API_URL` = `https://your-backend.railway.app`
5. Deploy!

### Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) and create new project
2. Select "Deploy from GitHub repo"
3. Choose your repo and set **Root Directory** to `backend`
4. Add environment variable:
   - `OPENROUTER_API_KEY` = your API key from [OpenRouter](https://openrouter.ai/)
5. Railway will auto-detect the Dockerfile and deploy!

### Environment Variables

| Variable | Where | Description |
|----------|-------|-------------|
| `OPENROUTER_API_KEY` | Backend (Railway) | Your OpenRouter API key |
| `VITE_API_URL` | Frontend (Vercel) | Your Railway backend URL |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MoviePy](https://zulko.github.io/moviepy/) - Video editing
- [Edge TTS](https://github.com/rany2/edge-tts) - Text-to-speech
- [OpenRouter](https://openrouter.ai/) - AI API
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework

## 📧 Contact

Your Name - [@vkmnamit](https://twitter.com/vkmnamit)

Project Link: [https://github.com/vkmnamit/aetheris-video-generator](https://github.com/vkmnamit/aetheris-video-generator)

---

<p align="center">Made with ❤️ by Namit</p>



cd /Users/namitraj/Documents/coding_folder/yt_idea/backend && /Users/namitraj/Documents/coding_folder/yt_idea/venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000