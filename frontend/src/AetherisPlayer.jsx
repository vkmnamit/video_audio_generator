import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Info, Box, GitBranch, List, Terminal, Activity, Calendar, Share2, Layers } from 'lucide-react';

const AetherisPlayer = ({ script, theme }) => {
    const [currentSceneIndex, setCurrentSceneIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const scenes = script?.scenes || [];

    useEffect(() => {
        if (isPlaying && currentSceneIndex < scenes.length) {
            const timer = setTimeout(() => {
                setCurrentSceneIndex(i => i + 1);
            }, (scenes[currentSceneIndex].duration || 5) * 1000);
            return () => clearTimeout(timer);
        } else if (currentSceneIndex >= scenes.length) {
            setIsPlaying(false);
        }
    }, [currentSceneIndex, isPlaying, scenes]);

    const restart = () => {
        setCurrentSceneIndex(0);
        setIsPlaying(true);
    };

    if (!scenes.length) return null;

    const currentScene = scenes[currentSceneIndex] || scenes[0];
    const { scene_type, headline, narration, animation_params } = currentScene;

    return (
        <div className="aetheris-player glass" style={{
            width: '100%',
            aspectRatio: '16/9',
            position: 'relative',
            overflow: 'hidden',
            background: '#0c111a',
            borderRadius: '24px',
            border: '1px solid rgba(255,255,255,0.1)'
        }}>
            {/* BACKGROUND DECOR */}
            <div style={{ position: 'absolute', top: '-10%', left: '-10%', width: '40%', height: '40%', background: 'var(--primary)', opacity: 0.1, filter: 'blur(100px)', borderRadius: '50%' }} />
            <div style={{ position: 'absolute', bottom: '-10%', right: '-10%', width: '40%', height: '40%', background: 'var(--secondary)', opacity: 0.1, filter: 'blur(100px)', borderRadius: '50%' }} />

            <AnimatePresence mode="wait">
                <motion.div
                    key={currentSceneIndex}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                    style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px' }}
                >
                    {/* HEADLINE */}
                    <motion.h2
                        initial={{ y: -20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        style={{ fontSize: '36px', fontWeight: 800, marginBottom: '40px', background: 'linear-gradient(to right, #fff, #888)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', textAlign: 'center' }}
                    >
                        {headline}
                    </motion.h2>

                    {/* VISUAL CENTER */}
                    <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <VisualContent sceneType={scene_type} params={animation_params} narration={narration} />
                    </div>

                    {/* NARRATION BOX */}
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        style={{
                            marginTop: '40px',
                            padding: '20px 30px',
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '16px',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            maxWidth: '80%',
                            textAlign: 'center'
                        }}
                    >
                        <p style={{ color: '#ccc', fontStyle: 'italic', fontSize: '18px', lineHeight: 1.6 }}>"{narration}"</p>
                    </motion.div>
                </motion.div>
            </AnimatePresence>

            {/* PLAYER CONTROLS */}
            <div style={{ position: 'absolute', bottom: '20px', left: '20px', display: 'flex', gap: '12px', zIndex: 10 }}>
                <button className="control-btn" onClick={() => setIsPlaying(!isPlaying)} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '8px 16px', borderRadius: '12px', cursor: 'pointer' }}>
                    {isPlaying ? 'Pause' : 'Play'}
                </button>
                <button className="control-btn" onClick={restart} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '8px 16px', borderRadius: '12px', cursor: 'pointer' }}>
                    Restart
                </button>
            </div>

            <div style={{ position: 'absolute', bottom: '20px', right: '20px', color: 'rgba(255,255,255,0.3)', fontSize: '12px' }}>
                Scene {currentSceneIndex + 1} / {scenes.length}
            </div>

            {/* PROGRESS BAR */}
            <div style={{ position: 'absolute', bottom: 0, left: 0, height: '4px', background: 'var(--primary)', width: `${(currentSceneIndex / (scenes.length - 1)) * 100}%`, transition: 'width 0.5s ease' }} />
        </div>
    );
};

const VisualContent = ({ sceneType, params, narration }) => {
    const containerVariants = {
        hidden: { opacity: 0, scale: 0.9 },
        visible: { opacity: 1, scale: 1, transition: { staggerChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: { y: 0, opacity: 1 }
    };

    switch (sceneType) {
        case 'array':
        case 'queue':
            const items = params?.key_numbers || [38, 27, 43, 3, 9];
            return (
                <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{ display: 'flex', gap: '10px' }}>
                    {items.map((it, i) => (
                        <motion.div key={i} variants={itemVariants} style={{
                            width: '70px', height: '70px', background: 'rgba(0, 255, 136, 0.1)', border: '2px solid var(--primary)', borderRadius: '12px',
                            display: 'grid', placeItems: 'center', fontSize: '24px', fontWeight: 700, position: 'relative'
                        }}>
                            {it}
                            {sceneType === 'queue' && i === 0 && <span style={{ position: 'absolute', top: '-25px', color: '#ff4444', fontSize: '12px' }}>FRONT</span>}
                            {sceneType === 'queue' && i === items.length - 1 && <span style={{ position: 'absolute', top: '-25px', color: '#4444ff', fontSize: '12px' }}>REAR</span>}
                        </motion.div>
                    ))}
                </motion.div>
            );

        case 'usage':
            const usages = params?.usages || ["Enterprise", "Web", "Mobile"];
            return (
                <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{ display: 'flex', gap: '20px' }}>
                    {usages.slice(0, 3).map((u, i) => (
                        <motion.div key={i} variants={itemVariants} className="glass" style={{
                            width: '180px', height: '140px', padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '10px'
                        }}>
                            <Activity size={32} color="var(--primary)" />
                            <span style={{ fontWeight: 600 }}>{u}</span>
                        </motion.div>
                    ))}
                </motion.div>
            );

        case 'complexity':
            return (
                <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass" style={{ padding: '40px', width: '300px', textAlign: 'center' }}>
                    <div style={{ color: 'var(--text-muted)', marginBottom: '10px' }}>Time Complexity</div>
                    <div style={{ fontSize: '48px', fontWeight: 900, color: 'var(--primary)', marginBottom: '20px' }}>{params?.time || 'O(n log n)'}</div>
                    <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', marginBottom: '20px' }} />
                    <div style={{ color: 'var(--text-muted)' }}>Space: <span style={{ color: 'white' }}>{params?.space || 'O(n)'}</span></div>
                </motion.div>
            );

        case 'summary':
        case 'process':
            const points = params?.points || params?.steps || ["Step 1", "Step 2", "Step 3"];
            return (
                <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{ display: 'flex', flexDirection: 'column', gap: '15px', alignItems: 'flex-start' }}>
                    {points.map((p, i) => (
                        <motion.div key={i} variants={itemVariants} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                            {sceneType === 'summary' ? (
                                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--primary)', display: 'grid', placeItems: 'center' }}><Check size={14} color="black" /></div>
                            ) : (
                                <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--primary)', display: 'grid', placeItems: 'center', fontSize: '12px', fontWeight: 800 }}>{i + 1}</div>
                            )}
                            <span style={{ fontSize: '20px' }}>{p}</span>
                        </motion.div>
                    ))}
                </motion.div>
            );

        case 'code':
            const code = params?.code || "function algorithm() {\n  // Logic here\n}";
            return (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} style={{
                    width: '90%', background: '#050a14', padding: '30px', borderRadius: '16px', border: '1px solid var(--primary)',
                    fontFamily: 'monospace', fontSize: '18px', color: '#00ff88', overflowX: 'auto', whiteSpace: 'pre'
                }}>
                    {code.split('\n').map((line, i) => (
                        <div key={i}><span style={{ opacity: 0.3, marginRight: '20px' }}>{i + 1}</span>{line}</div>
                    ))}
                </motion.div>
            );

        case 'formula':
            const formula = params?.formula || "E = mc^2";
            return (
                <motion.div initial={{ scale: 1.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} style={{
                    fontSize: '48px', fontWeight: 700, fontStyle: 'italic', letterSpacing: '2px', color: 'white',
                    padding: '20px 40px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px', borderLeft: '4px solid var(--primary)'
                }}>
                    {formula}
                </motion.div>
            );

        case 'timeline':
            const timelineItems = params?.items || ["1947: Event A", "1969: Event B"];
            return (
                <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div style={{ position: 'absolute', left: '20px', top: 0, bottom: 0, width: '4px', background: 'var(--primary)', opacity: 0.3 }} />
                    {timelineItems.map((item, i) => (
                        <motion.div key={i} variants={itemVariants} style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px', marginLeft: '10px' }}>
                            <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'var(--primary)', zIndex: 2 }} />
                            <div className="glass" style={{ padding: '10px 20px', minWidth: '200px' }}>
                                <Calendar size={14} color="var(--primary)" style={{ marginBottom: '5px' }} />
                                <div style={{ fontSize: '18px', fontWeight: 600 }}>{item}</div>
                            </div>
                        </motion.div>
                    ))}
                </motion.div>
            );

        case 'tree':
        case 'hierarchy':
            const root = params?.root || "Concept";
            const branches = params?.branches || ["Sub 1", "Sub 2"];
            return (
                <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '40px' }}>
                    <motion.div variants={itemVariants} className="glass" style={{ padding: '15px 30px', border: '2px solid var(--primary)', borderRadius: '12px', fontWeight: 700 }}>
                        <Share2 size={20} color="var(--primary)" style={{ marginBottom: '5px' }} /> {root}
                    </motion.div>
                    <div style={{ display: 'flex', gap: '20px' }}>
                        {branches.map((b, i) => (
                            <motion.div key={i} variants={itemVariants} className="glass" style={{ padding: '10px 20px', background: 'rgba(255,255,255,0.05)' }}>
                                <Layers size={16} color="var(--secondary)" /> {b}
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            );

        default:
            return (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: '600px', textAlign: 'center' }}>
                    <Info size={64} color="var(--primary)" style={{ marginBottom: '20px' }} />
                    <p style={{ fontSize: '18px', color: '#888' }}>{narration.slice(0, 100)}...</p>
                </motion.div>
            );
    }
};

export default AetherisPlayer;
