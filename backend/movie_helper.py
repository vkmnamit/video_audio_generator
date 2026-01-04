
import os
import uuid
import subprocess
from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    CompositeVideoClip, 
    concatenate_videoclips,
    CompositeAudioClip,
    afx
)
from typing import List

def compose_final_video(clip_paths: List[str], output_path: str, background_music_path: str = None):
    """
    Stage 4: Professional Composition.
    Stitches clips, adds background music (ducked), and encodes with libx264.
    """
    print(f"🎬 Composing final video with {len(clip_paths)} clips...")
    
    clips = []
    for path in clip_paths:
        if os.path.exists(path):
            clips.append(VideoFileClip(path))
        else:
            print(f"⚠️ Warning: Clip not found at {path}")
            
    if not clips:
        raise Exception("No valid clips found for composition.")
        
    # Stitch clips with a smooth 0.5s cross-dissolve transition
    # We use padding=-0.5 and method="compose" for overlapping crossfades
    print(f"🔗 Linking frames with smooth cross-transitions...")
    final_video = concatenate_videoclips(clips, method="compose", padding=-0.3)
    
    # Add Background Music
    if background_music_path and os.path.exists(background_music_path):
        print(f"🎶 Adding background music: {background_music_path}")
        bg_music = AudioFileClip(background_music_path)
        
        # Loop music to fit video length
        if bg_music.duration < final_video.duration:
            bg_music = bg_music.loop(duration=final_video.duration)
        else:
            bg_music = bg_music.with_duration(final_video.duration)
            
        # Ducking: Background music at 10% volume
        bg_music = bg_music.multiply_volume(0.10)
        
        # Combine with existing narration audio
        if final_video.audio:
            new_audio = CompositeAudioClip([final_video.audio, bg_music])
            final_video = final_video.with_audio(new_audio)
        else:
            final_video = final_video.with_audio(bg_music)
    
    # Professional Encoding
    print(f"📦 Encoding final video to {output_path}...")
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="slow",
        threads=4
    )
    
    # Close clips to free memory
    for clip in clips:
        clip.close()
    final_video.close()
    
    return output_path

if __name__ == "__main__":
    # Test stub
    pass
