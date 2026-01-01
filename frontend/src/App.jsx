import React, { useState } from 'react';
import {
  Play,
  Clock,
  Zap,
  Video,
  Sparkles,
  Download,
  Loader2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Sidebar = () => (
  <div className="sidebar glass">
    <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
      <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', borderRadius: '12px', display: 'grid', placeItems: 'center' }}>
        <Sparkles size={24} color="white" />
      </div>
      <h2 style={{ fontSize: '24px' }}>Aetheris</h2>
    </div>
    <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <NavItem icon={<Video size={20} />} label="Video Studio" active />
    </nav>
  </div>
);

const NavItem = ({ icon, label, active }) => (
  <div className={`nav-item ${active ? 'active' : ''}`} style={{
    display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', borderRadius: '12px', cursor: 'pointer',
    color: active ? 'white' : 'var(--text-muted)', background: active ? 'var(--bg-surface-elevated)' : 'transparent',
  }}>
    {icon}
    <span style={{ fontWeight: 500 }}>{label}</span>
  </div>
);

function App() {
  const [prompt, setPrompt] = useState("");
  const [videoType, setVideoType] = useState("short");
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState(null);

  const generateVideo = async () => {
    if (!prompt) return;
    setLoading(true);
    setVideoData(null);
    try {
      const response = await fetch('http://localhost:8000/generate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, video_type: videoType })
      });
      const data = await response.json();
      setVideoData(data);
    } catch (err) {
      console.error(err);
      alert("Generation failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <header style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>Aetheris Studio</h1>
          <p style={{ color: 'var(--text-muted)' }}>Generate complete educational videos instantly.</p>
        </header>

        <section className="glass animate-fade-in" style={{ padding: '32px', marginBottom: '40px' }}>
          <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Sparkles size={24} color="var(--primary)" />
            Studio Controls
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Explain Python variables for beginners..."
              style={{
                width: '100%', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)',
                borderRadius: '16px', padding: '20px', color: 'white', fontSize: '16px', height: '100px', resize: 'none'
              }}
            />
            <div className="controls-container">
              <div className="glass toggle-group">
                <button
                  onClick={() => setVideoType("short")}
                  style={{
                    padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                    background: videoType === "short" ? 'var(--primary)' : 'transparent',
                    color: 'white', transition: '0.3s',
                    flex: 1
                  }}
                >
                  Short (45s)
                </button>
                <button
                  onClick={() => setVideoType("long")}
                  style={{
                    padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                    background: videoType === "long" ? 'var(--primary)' : 'transparent',
                    color: 'white', transition: '0.3s',
                    flex: 1
                  }}
                >
                  Long (3m)
                </button>
              </div>
              <button
                onClick={generateVideo}
                disabled={loading}
                className="glow-btn generate-btn"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
                {loading ? "Rendering..." : "Generate Video"}
              </button>
            </div>
          </div>
        </section>

        <AnimatePresence>
          {videoData && (
            <motion.section
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass"
              style={{ padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px' }}
            >
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontSize: '24px', marginBottom: '8px' }}>{videoData.title}</h3>
                <div style={{ color: 'var(--text-muted)', display: 'flex', justifyContent: 'center', gap: '16px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={16} /> {Math.floor(videoData.duration)}s</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Video size={16} /> 1080p</span>
                </div>
              </div>

              <div className="video-container" style={{
                width: '100%',
                maxWidth: videoType === "short" ? '360px' : '100%',
                aspectRatio: videoType === "short" ? '9/16' : '16/9',
              }}>
                <video src={videoData.video_url} controls style={{ width: '100%', height: '100%' }} />
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <a href={videoData.video_url} download className="glow-btn" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                  <Download size={18} />
                  Download MP4
                </a>
              </div>
            </motion.section>
          )}
        </AnimatePresence>

        {loading && (
          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <Loader2 className="animate-spin" size={48} style={{ marginBottom: '16px', color: 'var(--primary)' }} />
            <p style={{ color: 'var(--text-muted)' }}>AI is writing script, generating speech, and rendering visuals...</p>
            <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.3)', marginTop: '8px' }}>This may take 30-60 seconds</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
