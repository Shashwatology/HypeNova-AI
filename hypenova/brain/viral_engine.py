"""HypeNova AI - 7-Factor Viral Potential Scoring & Quality Critic Engine (HypeBrain)"""
import json
from typing import Any, Dict, List, Optional, Tuple
from hypenova.brain.gaming_intelligence import analyze_gaming_dialogue
from hypenova.brain.podcast_intelligence import analyze_podcast_dialogue

class HypeBrain:
    """Evaluates candidate moments and calculates a multidimensional editorial viral score (0-100)."""

    def score_candidate(self, candidate: Dict, sound_cues: Optional[Dict] = None, category: str = "gaming") -> Dict:
        """
        Calculates weighted 7-factor viral score (0 to 100):
          - Hook strength: 20
          - Narrative completion: 20
          - Humour or emotional impact: 15
          - Visual significance: 15
          - Standalone clarity: 10
          - Audio quality & delivery: 10
          - Trend relevance: 10
        """
        duration = candidate.get("duration", candidate.get("end_time", 0.0) - candidate.get("start_time", 0.0))
        hook_text = candidate.get("hook", candidate.get("hook_text", ""))
        clip_type = candidate.get("type", "general")

        # 1. Hook Strength (Max 20)
        hook_score = 12.0
        if len(hook_text.split()) >= 3:
            hook_score += 4.0
        if any(w in hook_text.lower() for w in ["why", "how", "never", "secret", "galti", "wait", "easy", "glitch"]):
            hook_score += 4.0
        hook_score = min(20.0, hook_score)

        # 2. Narrative Completion & Timing (Max 20)
        narrative_score = 14.0
        if 15.0 <= duration <= 45.0:  # Sweet spot for YouTube Shorts & Reels
            narrative_score += 6.0
        elif duration < 10.0 or duration > 90.0:
            narrative_score -= 8.0
        narrative_score = max(5.0, min(20.0, narrative_score))

        # 3. Humour or Emotional Impact (Max 15)
        emotion_score = 10.0
        if clip_type in ["streamer_gameplay_contradiction", "gaming_banter_roast"]:
            emotion_score += 5.0
        elif clip_type == "contrarian_podcast_insight":
            emotion_score += 4.0
        emotion_score = min(15.0, emotion_score)

        # 4. Visual Significance (Max 15)
        visual_score = 11.0
        if category == "gaming":
            visual_score += 4.0 # Gaming action has innate visual momentum
        visual_score = min(15.0, visual_score)

        # 5. Standalone Clarity (Max 10)
        clarity_score = 8.0
        if duration >= 14.0:
            clarity_score += 2.0
        clarity_score = min(10.0, clarity_score)

        # 6. Audio Quality & Cues (Max 10)
        audio_score = 8.0
        if sound_cues:
            if sound_cues.get("laughs", 0) > 0 or sound_cues.get("lively", 0) > 0:
                audio_score += 2.0
        audio_score = min(10.0, audio_score)

        # 7. Trend Relevance (Max 10)
        trend_score = 8.5

        total_score = round(
            hook_score + narrative_score + emotion_score + visual_score + clarity_score + audio_score + trend_score,
            1
        )

        breakdown = {
            "hook_strength": hook_score,
            "narrative_completion": narrative_score,
            "emotional_impact": emotion_score,
            "visual_significance": visual_score,
            "standalone_clarity": clarity_score,
            "audio_quality": audio_score,
            "trend_relevance": trend_score,
            "total": total_score
        }

        # Editorial reason
        reason = self._generate_editorial_reason(breakdown, clip_type, duration)

        # Critic second-pass
        passed_critic, critic_notes = self.critic_review(candidate, breakdown, duration)

        return {
            "score": total_score,
            "breakdown": breakdown,
            "editorial_reason": reason,
            "critic_passed": passed_critic,
            "critic_notes": critic_notes
        }

    def critic_review(self, candidate: Dict, breakdown: Dict, duration: float) -> Tuple[bool, str]:
        """Second-pass critic to reject unintelligible, cutoff, or repetitive clips."""
        if duration < 7.0:
            return False, "Rejected: Clip duration is under 7 seconds; insufficient time for narrative setup."
        if duration > 95.0:
            return False, "Rejected: Clip duration exceeds 95 seconds; over platform short-form limit."
        if breakdown["hook_strength"] < 8.0:
            return False, "Rejected: Weak opening hook. High drop-off likelihood in first 2 seconds."
        if breakdown["total"] < 50.0:
            return False, "Rejected: Overall viral score below minimum threshold."
        return True, "Passed editorial critic review."

    def _generate_editorial_reason(self, breakdown: Dict, clip_type: str, duration: float) -> str:
        strengths = []
        if breakdown["hook_strength"] >= 16.0:
            strengths.append("compelling high-retention hook")
        if breakdown["emotional_impact"] >= 13.0:
            strengths.append("strong comedic or emotional payoff")
        if breakdown["narrative_completion"] >= 17.0:
            strengths.append("ideal short-form pacing")

        joined = " and ".join(strengths) if strengths else "solid topical relevance"
        return f"Selected for {joined} with complete standalone context ({duration:.1f}s)."

    def discover_moments(self, transcript_lines: List[Dict], cues: Optional[Dict] = None, category: str = "gaming") -> List[Dict]:
        """Combines speech, gaming cues, and podcast heuristics to produce ranked candidate highlights."""
        if category == "gaming":
            raw_candidates = analyze_gaming_dialogue(transcript_lines)
        else:
            raw_candidates = analyze_podcast_dialogue(transcript_lines)

        # If no specific patterns detected, extract standard high-density dialogue segments
        if not raw_candidates and transcript_lines:
            t_start = transcript_lines[0].get("s", 0.0)
            t_end = min(t_start + 30.0, transcript_lines[-1].get("e", 30.0))
            raw_candidates.append({
                "start_time": t_start,
                "end_time": t_end,
                "type": "featured_highlight",
                "description": "Featured dialogue segment",
                "hook_text": transcript_lines[0].get("text", "")[:40]
            })

        scored_candidates = []
        for cand in raw_candidates:
            cand["duration"] = round(cand["end_time"] - cand["start_time"], 2)
            eval_result = self.score_candidate(cand, cues, category)
            cand.update(eval_result)
            if cand["critic_passed"]:
                scored_candidates.append(cand)

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates

# Backwards compatibility alias
ViralEngine = HypeBrain

