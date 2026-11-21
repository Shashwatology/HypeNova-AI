"""HypeNova AI - Gaming-Specific Event & Dialogue Intelligence"""
import re
from typing import Dict, List, Tuple

# Gaming Dialogue & Event Patterns (Hinglish + English)
CONFIDENT_CLAIMS = [
    r"\beasy\b", r"\baasan\b", r"\bbohot aasan\b", r"\bbaccha bhi kar lega\b",
    r"\bwatch this\b", r"\bdekho abhi\b", r"\bpro player\b", r"\bno damage\b",
    r"\bpiece of cake\b", r"\b100% win\b", r"\bkoi nahi bachega\b"
]

FAILURE_EVENTS = [
    r"\bwasted\b", r"\bmission failed\b", r"\bmar gaya\b", r"\bkhalaas\b",
    r"\byeh kya hua\b", r"\bwait what\b", r"\bch**iya kat gaya\b", r"\bsh*t\b",
    r"\boh no\b", r"\bdead\b", r"\bfail\b", r"\bcrash\b"
]

ROAST_AND_COMEDY = [
    r"\btera baap\b", r"\bkya gunda banega re tu\b", r"\bnoob\b", r"\blol\b",
    r"\bhahaha\b", r"\bepic\b", r"\bpagal hai kya\b", r"\barre yaar\b",
    r"\bsirf 12 views\b", r"\bchup kar\b"
]

NPC_AND_PHYSICS = [
    r"\bphysics\b", r"\bglitch\b", r"\bnpc\b", r"\bpolice\b", r"\bcar ud gayi\b",
    r"\bhelicopter\b", r"\bexplosion\b", r"\bblast\b"
]

def analyze_gaming_dialogue(transcript_lines: List[Dict]) -> List[Dict]:
    """Scans timestamped sentences for gaming comedy, roasts, and streamer-gameplay ironies."""
    candidates = []

    for i, line in enumerate(transcript_lines):
        text = line.get("text", "").lower()
        start = line.get("s", line.get("start", 0.0))
        end = line.get("e", line.get("end", 0.0))

        # Check for setup -> failure irony
        for claim_pat in CONFIDENT_CLAIMS:
            if re.search(claim_pat, text):
                # Look ahead for sudden failure within next 2-3 lines (~15-30s)
                for j in range(i + 1, min(len(transcript_lines), i + 4)):
                    next_text = transcript_lines[j].get("text", "").lower()
                    for fail_pat in FAILURE_EVENTS:
                        if re.search(fail_pat, next_text):
                            payoff_end = transcript_lines[j].get("e", transcript_lines[j].get("end", end))
                            candidates.append({
                                "start_time": max(0.0, start - 1.0),
                                "end_time": payoff_end + 1.5,
                                "type": "streamer_gameplay_contradiction",
                                "description": f"Confident boast '{text}' followed by sudden failure '{next_text}'",
                                "hook_text": text.title(),
                                "confidence_boost": 25.0
                            })
                            break

        # Check for high comedy roasts or banter
        for roast_pat in ROAST_AND_COMEDY:
            if re.search(roast_pat, text):
                candidates.append({
                    "start_time": max(0.0, start - 1.0),
                    "end_time": min(end + 15.0, start + 35.0),
                    "type": "gaming_banter_roast",
                    "description": f"Comedic remark or punchline: '{text}'",
                    "hook_text": text.capitalize(),
                    "confidence_boost": 18.0
                })

    return candidates
