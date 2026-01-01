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
- **Edge TTS** - Natural voice synthesis
- **OpenRouter API** - AI script generation (Gemini 2.0 Flash)

### Frontend
- **React 18** - UI framework
- **Vite** - Fast build tool
- **CSS3** - Modern styling

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
cd backend
source ../venv/bin/activate
python main.py
```
Backend runs on: `http://localhost:8000`

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Frontend runs on: `http://localhost:5173`

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

Your Name - [@yourtwitter](https://twitter.com/yourtwitter)

Project Link: [https://github.com/yourusername/aetheris-video-generator](https://github.com/yourusername/aetheris-video-generator)

---

<p align="center">Made with ❤️ by Aetheris Team</p>
