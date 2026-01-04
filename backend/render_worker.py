import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import uuid
import tempfile
from manim import config, Scene
import manim_engine

def render_scene_from_json(scene_data_json, theme_name, output_file):
    scene_data = json.loads(scene_data_json)
    scene_type = scene_data.get('scene_type', 'definition').lower()
    headline = scene_data.get('headline', '')
    narration = scene_data.get('narration', '')
    # Duration Logic: Prioritize AI-calculated duration which now includes technical buffers
    target_duration = scene_data.get('duration', scene_data.get('target_duration', 5.0))
    animation_params = scene_data.get('animation_params', {})
    
    # Configure Manim
    config.pixel_width = 1080
    config.pixel_height = 1920
    config.frame_rate = 30
    config.output_file = output_file
    config.write_to_movie = True
    config.disable_caching = True
    config.verbosity = "ERROR" # Keep it clean
    
    theme = manim_engine.THEMES.get(theme_name, manim_engine.DEFAULT_THEME)
    
    # Map scene types to classes
    # (Simplified mapping for the worker)
    SCENE_MAP = {
        'title': manim_engine.TitleScene,
        'definition': manim_engine.DefinitionScene,
        'array': manim_engine.ArrayScene,
        'code': manim_engine.CodeScene,
        'linked_list': manim_engine.LinkedListScene,
        'process': manim_engine.ProcessFlowScene,
        'flowchart': manim_engine.ProcessFlowScene,
        'summary': manim_engine.SummaryScene,
        'table': manim_engine.TableScene,
        'formula': manim_engine.FormulaScene,
        'diagram': manim_engine.DiagramScene,
        'example': manim_engine.ExampleScene,
        'comparison': manim_engine.ComparisonScene,
        'tree': manim_engine.TreeScene,
        'divide_merge_scene': manim_engine.DivideMergeScene,
        'merge_process_scene': manim_engine.MergeProcessScene,
    }
    
    scene_class = SCENE_MAP.get(scene_type, manim_engine.DefinitionScene)
    
    # Prepare kwargs for the scene
    kwargs = {
        'theme': theme,
        'target_duration': target_duration,
        'animation_params': animation_params,
        'headline': headline,
        'captions': scene_data.get('captions', []),
        'visual_manifest': scene_data.get('visual_manifest', {}),
    }
    
    # Ensure DefinitionScene always has term and definition even as fallback
    if scene_class == manim_engine.DefinitionScene:
        kwargs['term'] = headline or "Concept"
        kwargs['definition'] = narration or "Technical explanation."

    if scene_type == 'title':
        kwargs['subtitle'] = narration[:80]
    elif scene_type == 'definition':
        kwargs['term'] = headline
        kwargs['definition'] = narration
    elif scene_type in ['array', 'linked_list', 'divide_merge_scene', 'merge_process_scene']:
        kwargs['items'] = scene_data.get('items', [])
        if scene_type == 'linked_list': kwargs['nodes'] = kwargs.pop('items')
    elif scene_type in ['process', 'flowchart', 'summary', 'tree']:
        kwargs['steps'] = scene_data.get('steps', [])
        if scene_type == 'summary': kwargs['points'] = kwargs.pop('steps')
        if scene_type == 'tree': 
            kwargs['branches'] = kwargs.pop('steps')
            kwargs['root_text'] = scene_data.get('root_text', headline)
    elif scene_type == 'table':
        kwargs['table'] = scene_data.get('table', [])
    elif scene_type == 'formula':
        kwargs['formula'] = scene_data.get('formula', narration)
    elif scene_type == 'code':
        # Priority: manifest primary_object > scene_data.get('code') > narration
        manifest = scene_data.get('visual_manifest', {})
        code = str(manifest.get('primary_object', ''))
        if len(code) < 5:
            code = scene_data.get('code', narration)
        kwargs['code'] = code
    elif scene_type == 'comparison':
        kwargs['left'] = scene_data.get('left', '')
        kwargs['right'] = scene_data.get('right', '')
    
    # Render
    scene = scene_class(**kwargs)
    scene.render()
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python render_worker.py <scene_json> <theme_name> <output_file>")
        sys.exit(1)
        
    scene_json = sys.argv[1]
    theme_name = sys.argv[2]
    output_file = sys.argv[3]
    
    render_scene_from_json(scene_json, theme_name, output_file)
