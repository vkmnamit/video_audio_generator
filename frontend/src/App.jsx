import React, { useState, useEffect, useRef } from 'react';
import { Clock, Zap, Video, Sparkles, Download, Loader2, Upload, Palette, X, Check, ImagePlus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import AetherisPlayer from './AetherisPlayer';


const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Sidebar = ({ activeTab, setActiveTab }) => (
  <div className="sidebar glass">
    <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
      <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', borderRadius: '12px', display: 'grid', placeItems: 'center' }}>
        <Sparkles size={24} color="white" />
      </div>
      <h2 style={{ fontSize: '24px' }}>Aetheris</h2>
    </div>
    <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <NavItem icon={<Video size={20} />} label="Video Studio" active={activeTab === 'studio'} onClick={() => setActiveTab('studio')} />
      <NavItem icon={<ImagePlus size={20} />} label="Custom Images" active={activeTab === 'images'} onClick={() => setActiveTab('images')} />
      <NavItem icon={<Palette size={20} />} label="Themes" active={activeTab === 'themes'} onClick={() => setActiveTab('themes')} />
    </nav>
  </div>
);

const NavItem = ({ icon, label, active, onClick }) => (
  <div className={`nav-item ${active ? 'active' : ''}`} onClick={onClick}
    style={{
      display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', borderRadius: '12px', cursor: 'pointer',
      color: active ? 'white' : 'var(--text-muted)', background: active ? 'var(--bg-surface-elevated)' : 'transparent', transition: 'all 0.2s ease'
    }}>
    {icon}
    <span style={{ fontWeight: 500 }}>{label}</span>
  </div>
);

const ThemeSelector = ({ currentTheme, onSelectTheme }) => {
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/themes`).then(r => r.json()).then(d => { setThemes(d.themes); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const selectTheme = async (name) => {
    const res = await fetch(`${API_URL}/themes/select`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme_name: name }) });
    const data = await res.json();
    if (data.success) onSelectTheme(name);
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '40px' }}><Loader2 className="animate-spin" size={32} /></div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
      {themes.map((theme) => (
        <motion.div key={theme.name} whileHover={{ scale: 1.02 }} className="glass" onClick={() => selectTheme(theme.name)}
          style={{ padding: '24px', cursor: 'pointer', border: currentTheme === theme.name ? '2px solid var(--primary)' : '1px solid var(--border)', position: 'relative' }}>
          {currentTheme === theme.name && <div style={{ position: 'absolute', top: '12px', right: '12px', background: 'var(--primary)', borderRadius: '50%', padding: '4px' }}><Check size={14} color="white" /></div>}
          <h3 style={{ marginBottom: '8px' }}>{theme.display_name}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '16px' }}>{theme.description}</p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: `rgb(${theme.colors.bg.join(',')})`, border: '1px solid rgba(255,255,255,0.2)' }} />
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: `rgb(${theme.colors.primary.join(',')})` }} />
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: `rgb(${theme.colors.accent.join(',')})` }} />
          </div>
        </motion.div>
      ))}
    </div>
  );
};

const StatusStep = ({ icon, label, sublabel, active, completed }) => (
  <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', opacity: active || completed ? 1 : 0.4, transition: 'all 0.3s' }}>
    <div style={{
      width: '32px', height: '32px', borderRadius: '50%', background: completed ? '#10b981' : active ? 'var(--primary)' : 'var(--bg-surface-elevated)',
      display: 'grid', placeItems: 'center', flexShrink: 0, boxShadow: active ? '0 0 15px var(--primary-glow)' : 'none'
    }}>
      {completed ? <Check size={18} color="white" /> : React.cloneElement(icon, { size: 18, color: "white" })}
    </div>
    <div>
      <p style={{ fontWeight: 600, fontSize: '14px', color: active ? 'white' : 'var(--text-main)' }}>{label}</p>
      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{sublabel}</p>
    </div>
  </div>
);

const ImageUploader = ({ onSessionCreated }) => {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [session, setSession] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const processFiles = (incomingFiles) => {
    const sel = Array.from(incomingFiles);
    setFiles(p => [...p, ...sel]);
    sel.forEach(f => {
      const r = new FileReader();
      r.onload = ev => setPreviews(p => [...p, { file: f.name, url: ev.target.result }]);
      r.readAsDataURL(f);
    });
  };

  const handleInputChange = (e) => {
    if (e.target.files) processFiles(e.target.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const upload = async () => {
    if (files.length < 2) { alert('Need at least 2 images'); return; }
    setUploading(true);
    const fd = new FormData();
    files.forEach(f => fd.append('files', f));
    try {
      const res = await fetch(`${API_URL}/upload-images`, { method: 'POST', body: fd });
      const data = await res.json();
      setSession(data);
      onSessionCreated(data);
    } catch { alert('Upload failed'); }
    setUploading(false);
  };

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? 'var(--primary)' : 'var(--border)'}`,
          backgroundColor: isDragging ? 'rgba(var(--primary-rgb), 0.1)' : 'transparent',
          borderRadius: '16px',
          padding: '40px',
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: '24px',
          transition: 'all 0.2s ease'
        }}
      >
        <Upload size={48} style={{ color: isDragging ? 'var(--primary)' : 'var(--text-muted)', marginBottom: '16px' }} />
        <p style={{ fontSize: '18px', marginBottom: '8px' }}>{isDragging ? 'Drop images now' : 'Drop images or click to upload'}</p>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Upload 4-8 images for your topic</p>
        <input ref={inputRef} type="file" multiple accept="image/*" onChange={handleInputChange} style={{ display: 'none' }} />
      </div>
      {previews.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3>{previews.length} images</h3>
            <button onClick={() => { setFiles([]); setPreviews([]); setSession(null); }} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>Clear</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '12px' }}>
            {previews.map((p, i) => (
              <div key={i} style={{ position: 'relative' }}>
                <img src={p.url} style={{ width: '100%', height: '100px', objectFit: 'cover', borderRadius: '12px' }} />
                <button onClick={() => { setFiles(f => f.filter((_, j) => j !== i)); setPreviews(pr => pr.filter((_, j) => j !== i)); }}
                  style={{ position: 'absolute', top: '-8px', right: '-8px', background: 'var(--accent)', border: 'none', borderRadius: '50%', width: '24px', height: '24px', cursor: 'pointer' }}>
                  <X size={12} color="white" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      {previews.length >= 2 && !session && (
        <button onClick={upload} disabled={uploading} className="glow-btn" style={{ width: '100%', padding: '16px' }}>
          {uploading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
          {uploading ? ' Analyzing...' : ' Upload & Analyze'}
        </button>
      )}
      {session && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass" style={{ padding: '20px', marginTop: '20px', background: 'rgba(139, 92, 246, 0.1)' }}>
          <p><Check size={16} color="var(--primary)" /> <strong>Images analyzed!</strong> Go to Video Studio.</p>
        </motion.div>
      )}
    </div>
  );
};

function App() {
  const [tab, setTab] = useState('studio');
  const [prompt, setPrompt] = useState('');
  const [videoType, setVideoType] = useState('short');
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState(null);
  const [theme, setTheme] = useState('algorithm');
  const [imgSession, setImgSession] = useState(null);
  const [useImg, setUseImg] = useState(false);


  // Always use /generate-video-hq and send theme
  const [status, setStatus] = useState(null); // 'scholar', 'director', 'animator', 'editor'

  const generate = async () => {
    if (!prompt) return;
    setLoading(true); setVideoData(null); setStatus('scholar');
    try {
      // Stage 1 & 2: Get the Premium Script
      let endpoint = '/generate-script';
      let body = { prompt, video_type: videoType };

      const scriptRes = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const scriptData = await scriptRes.json();

      setStatus('animator');

      // Stage 3 & 4: Render Video (Parallel Workers + Music ducking)
      const videoRes = await fetch(`${API_URL}/generate-video-from-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script: scriptData, theme })
      });

      const finalData = await videoRes.json();
      setVideoData({ ...finalData, script: scriptData });
      setStatus('editor');
      setTimeout(() => setStatus(null), 3000);
    } catch (err) {
      console.error(err);
      alert('Generation failed. Check console for details.');
      setStatus(null);
    }
    setLoading(false);
  };



  return (
    <div className="app-layout">
      <Sidebar activeTab={tab} setActiveTab={setTab} />
      <main className="main-content">
        <header style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>{tab === 'studio' ? 'Aetheris Studio' : tab === 'images' ? 'Custom Images' : 'Themes'}</h1>
          <p style={{ color: 'var(--text-muted)' }}>{tab === 'studio' ? 'Generate videos instantly.' : tab === 'images' ? 'Upload your images.' : 'Choose a theme.'}</p>
        </header>

        {tab === 'studio' && (
          <>
            <section className="glass animate-fade-in" style={{ padding: '32px', marginBottom: '40px' }}>
              <h2 style={{ marginBottom: '24px' }}><Sparkles size={24} color="var(--primary)" /> Studio</h2>
              {imgSession && (
                <div onClick={() => setUseImg(!useImg)} className="glass" style={{ padding: '16px', marginBottom: '20px', cursor: 'pointer', border: useImg ? '2px solid var(--primary)' : '1px solid var(--border)', display: 'flex', gap: '12px' }}>
                  <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: useImg ? 'var(--primary)' : 'transparent', border: useImg ? 'none' : '2px solid var(--border)', display: 'grid', placeItems: 'center' }}>
                    {useImg && <Check size={14} color="white" />}
                  </div>
                  <div><p style={{ fontWeight: 600 }}>Use my images</p><p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{imgSession.images.length} images</p></div>
                </div>
              )}
              <textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder={useImg ? 'e.g. Bubble Sort with my images...' : 'e.g. Explain Python...'} style={{ width: '100%', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '16px', padding: '20px', color: 'white', fontSize: '16px', height: '100px', resize: 'none', marginBottom: '20px' }} />
              <div className="controls-container">
                <div className="glass toggle-group">
                  <button onClick={() => setVideoType('short')} style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', background: videoType === 'short' ? 'var(--primary)' : 'transparent', color: 'white', flex: 1 }}>Short</button>
                  <button onClick={() => setVideoType('long')} style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', background: videoType === 'long' ? 'var(--primary)' : 'transparent', color: 'white', flex: 1 }}>Long</button>
                </div>
                <button onClick={generate} disabled={loading} className="glow-btn generate-btn">
                  {loading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
                  {loading ? ' Preparing...' : ' Generate Video'}
                </button>
              </div>
            </section>
            <AnimatePresence>
              {(videoData?.video_url || videoData?.motion_canvas_url) && (
                <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass" style={{ padding: '40px', textAlign: 'center' }}>
                  <h3>{videoData?.title}</h3>
                  <p style={{ color: 'var(--text-muted)', marginBottom: '20px' }}><Clock size={16} /> {Math.floor(videoData?.duration || 0)}s</p>

                  {/* INSTANT PREVIEW PLAYER */}
                  {videoData?.script && (
                    <div style={{ marginBottom: '40px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', justifyContent: 'center' }}>
                        <Zap size={18} color="var(--primary)" />
                        <span style={{ fontWeight: 600, fontSize: '14px', letterSpacing: '1px', textTransform: 'uppercase' }}>Instant AI Preview</span>
                      </div>
                      <AetherisPlayer script={videoData.script} theme={theme} />
                    </div>
                  )}

                  {videoData?.motion_canvas_url ? (
                    <>
                      <iframe
                        src={videoData.motion_canvas_url}
                        style={{ width: '100%', height: '600px', border: '1px solid var(--border)', borderRadius: '16px', marginTop: '20px', background: '#0f141e' }}
                        title="Motion Canvas"
                      />
                      <p style={{ marginTop: 16, fontSize: 13, opacity: 0.7 }}>
                        Interactive Animation • <a href={videoData.motion_canvas_url} target="_blank" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Open Full Screen</a>
                        <br />
                        <span style={{ fontSize: 11 }}>Note: If video is blank, ensure backend server port is accessible.</span>
                      </p>

                      {videoData.video_url && (
                        <>
                          <video src={videoData.video_url} controls style={{ maxWidth: videoType === 'short' ? '300px' : '100%', marginTop: '20px' }} />
                          <br />
                          <a href={videoData.video_url} download className="glow-btn" style={{ marginTop: '20px', display: 'inline-flex', gap: '8px', textDecoration: 'none' }}>
                            <Download size={18} /> Download
                          </a>
                        </>
                      )}
                    </>
                  ) : (
                    <>
                      <video src={videoData.video_url} controls style={{ maxWidth: videoType === 'short' ? '300px' : '100%', marginTop: '20px' }} />
                      <br />
                      <a href={videoData.video_url} download className="glow-btn" style={{ marginTop: '20px', display: 'inline-flex', gap: '8px', textDecoration: 'none' }}>
                        <Download size={18} /> Download
                      </a>
                    </>
                  )}
                </motion.section>
              )}
            </AnimatePresence>
            {loading && (
              <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass" style={{ padding: '32px', textAlign: 'center' }}>
                <h3 style={{ marginBottom: '24px' }}>Deep Video Production in Progress</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '400px', margin: '0 auto', textAlign: 'left' }}>
                  <StatusStep
                    icon={<Sparkles />}
                    label="Stage 1 & 2: The Scholar & Director"
                    sublabel="Extracting facts & composing Manim script"
                    active={status === 'scholar'}
                    completed={['animator', 'editor'].includes(status)}
                  />
                  <StatusStep
                    icon={<Zap />}
                    label="Stage 3: Parallel Animators"
                    sublabel="Rendering scenes via distributed workers"
                    active={status === 'animator'}
                    completed={['editor'].includes(status)}
                  />
                  <StatusStep
                    icon={<Palette />}
                    label="Stage 4: Professional Editor"
                    sublabel="Music ducking & premium composition"
                    active={status === 'editor'}
                    completed={false}
                  />
                </div>
                <div style={{ marginTop: '32px' }}>
                  <Loader2 className="animate-spin" size={32} style={{ color: 'var(--primary)' }} />
                  <p style={{ color: 'var(--text-muted)', marginTop: '16px', fontSize: '14px' }}>
                    {status === 'scholar' ? 'Consulting facts...' : status === 'animator' ? 'Executing Manim renders...' : 'Mixing final audio track...'}
                  </p>
                </div>
              </motion.section>
            )}
          </>
        )}

        {tab === 'images' && (
          <section className="glass animate-fade-in" style={{ padding: '32px' }}>
            <h2 style={{ marginBottom: '8px' }}><ImagePlus size={24} color="var(--primary)" /> Upload Images</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>AI uses YOUR images in the video!</p>
            <ImageUploader onSessionCreated={s => { setImgSession(s); setUseImg(true); }} />
          </section>
        )}

        {tab === 'themes' && <ThemeSelector currentTheme={theme} onSelectTheme={setTheme} />}


      </main>
    </div>
  );
}

export default App;
