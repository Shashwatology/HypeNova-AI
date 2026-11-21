"""HypeNova AI - Podcast & Interview Intelligence Engine"""
import re
from typing import Dict, List

CONTRARIAN_HOOKS = [
    r"\bmost people think\b", r"\bsabse badi galti\b", r"\bthe biggest mistake\b",
    r"\bsecret\b", r"\bnever do this\b", r"\bkisi ko nahi pata\b",
    r"\balmost all the advice is terrible\b", r"\byou are doing it wrong\b",
    r"\bthe truth about\b", r"\bnobody tells you\b"
]

LESSON_AND_WISDOM = [
    r"\blesson\b", r"\bcareer\b", r"\bmoney\b", r"\bpaisa\b",
    r"\bbusiness\b", r"\bstartup\b", r"\bdiscipline\b", r"\bsuccess\b",
    r"\bfailure\b", r"\bfirst crore\b", r"\bexperience\b"
]

def analyze_podcast_dialogue(transcript_lines: List[Dict]) -> List[Dict]:
    """Identifies self-contained high-value conversational moments, contrarian insights, and lessons."""
    candidates = []

    for i, line in enumerate(transcript_lines):
        text = line.get("text", "").lower()
        start = line.get("s", line.get("start", 0.0))
        end = line.get("e", line.get("end", 0.0))

        # Check for high-retention contrarian hook
        for hook_pat in CONTRARIAN_HOOKS:
            if re.search(hook_pat, text):
                # A good podcast clip is 30-60s to ensure complete narrative arc
                clip_end = min(start + 55.0, end + 35.0)
                # Find ending sentence closest to 35-50s
                for j in range(i + 1, min(len(transcript_lines), i + 10)):
                    line_end = transcript_lines[j].get("e", transcript_lines[j].get("end", end))
                    if 25.0 <= (line_end - start) <= 60.0:
                        clip_end = line_end

                candidates.append({
                    "start_time": max(0.0, start - 0.5),
                    "end_time": clip_end + 0.5,
                    "type": "contrarian_podcast_insight",
                    "description": f"Powerful hook statement: '{text}' with full explanation.",
                    "hook_text": text.capitalize(),
                    "confidence_boost": 22.0
                })

    return candidates
