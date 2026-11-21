"""HypeNova AI - Premium Visual Editing Presets (HypeCut)"""
from typing import Dict

EDITING_PRESETS: Dict[str, Dict] = {
    "GTA Chaos": {
        "name": "GTA Chaos",
        "description": "High-octane gaming highlights, energetic camera zooms on action beats, impact sound effects, dynamic karaoke captions.",
        "caption_look": "karaoke",
        "zoom": True,
        "sfx": "hype",
        "jump_cuts": True,
        "hook_title": True,
        "accent_color": "#FF0055",
        "target_niche": "gaming"
    },
    "Indian Gaming Comedy": {
        "name": "Indian Gaming Comedy",
        "description": "Optimized for Hinglish creator banter, punchlines, sudden laughter zooms, starred abusive terms for monetization safety.",
        "caption_look": "classic",
        "zoom": True,
        "sfx": "funny",
        "jump_cuts": True,
        "hook_title": False,
        "accent_color": "#FFD60A",
        "target_niche": "gaming"
    },
    "Clean Podcast": {
        "name": "Clean Podcast",
        "description": "Restrained, premium visual presentation for founder and tech interviews. Minimal clean subtitles, subtle speaker reframing.",
        "caption_look": "minimal",
        "zoom": False,
        "sfx": "none",
        "jump_cuts": True,
        "hook_title": False,
        "accent_color": "#00E5FF",
        "target_niche": "podcast"
    },
    "Cinematic Gaming": {
        "name": "Cinematic Gaming",
        "description": "Dramatic pacing, suspenseful visual cuts, subtle lower-third captions, atmospheric sound design.",
        "caption_look": "bold",
        "zoom": True,
        "sfx": "dramatic",
        "jump_cuts": False,
        "hook_title": True,
        "accent_color": "#8B5CF6",
        "target_niche": "gaming"
    },
    "Quick News": {
        "name": "Quick News",
        "description": "Informational layout with bold top hook banner, rapid jump cuts, source attribution ticker, and high mobile readability.",
        "caption_look": "box",
        "zoom": False,
        "sfx": "none",
        "jump_cuts": True,
        "hook_title": True,
        "accent_color": "#10B981",
        "target_niche": "news"
    },
    "Minimal Viral": {
        "name": "Minimal Viral",
        "description": "High-contrast legible captions without distracting visual clutter. Let the creator's personality and voice lead.",
        "caption_look": "classic",
        "zoom": True,
        "sfx": "subtle",
        "jump_cuts": True,
        "hook_title": False,
        "accent_color": "#FFFFFF",
        "target_niche": "general"
    }
}
