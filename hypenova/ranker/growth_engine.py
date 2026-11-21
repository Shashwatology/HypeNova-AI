"""HypeNova AI - Packaging, SEO, and Audience Growth Engine (HypeRank)"""
import re
from typing import Dict, List

class HypeRank:
    """Generates multi-platform titles, descriptions, hooks, and hashtags for short-form content."""

    def package_clip(self, title: str, hook: str, transcript_excerpt: str, category: str = "gaming", language: str = "hinglish") -> Dict:
        """Produces 5 title options, 3 hooks, platform captions, tags, and posting schedule advice."""
        clean_title = re.sub(r"[^\w\s-]", "", title).strip()

        # 5 Title Styles
        titles = [
            f"{clean_title} 🤯",
            f"The Biggest Mistake in {clean_title}?",
            f"Nobody Expected This To Happen... ({clean_title})",
            f"Bro Really Thought He Could Win 😂",
            f"Wait For The Ending: {clean_title}"
        ]

        # 3 Opening Hooks
        hooks = [
            f"Wait... Did that actually just happen?",
            f"If you think this was easy, watch until the end.",
            f"This is the one thing nobody tells you about {clean_title.lower()}."
        ]

        # Platform Hashtags
        if category == "gaming":
            yt_tags = ["#Shorts", "#Gaming", "#GTAV", "#GamingClips", "#FunnyMoments", "#Gameplay"]
            ig_tags = ["#gamingreels", "#gtamodes", "#gamerlife", "#funnygameplay", "#streamerclips", "#indianstreamers"]
        else:
            yt_tags = ["#Shorts", "#Podcast", "#Interview", "#LifeLessons", "#Success", "#Mindset"]
            ig_tags = ["#podcastreels", "#growthmindset", "#interviewclips", "#successtips", "#deepconversation"]

        yt_desc = f"{hook}\n\nWhat would you do in this situation? Let us know in the comments below!\n\n" + " ".join(yt_tags[:4])
        ig_caption = f"{hook} 👇 Drops your thoughts in the comments!\n.\n.\n" + " ".join(ig_tags[:6])

        # Suggested Publishing Time Window (Indian & Global Prime Time)
        suggested_time = "18:00 - 21:00 IST (High audience activity window)"

        # Monetization & Platform Risk Advisory
        risk_warnings = []
        abusive_words = ["f***", "c***", "gaali", "bkl", "mc"]
        for bad in abusive_words:
            if bad in transcript_excerpt.lower():
                risk_warnings.append(f"Contains flagged language '{bad}'. Ensure star-censor is active to preserve YouTube monetization.")

        return {
            "titles": titles,
            "hooks": hooks,
            "youtube": {
                "title": titles[0][:95],
                "description": yt_desc,
                "tags": [t.replace("#", "") for t in yt_tags]
            },
            "instagram": {
                "caption": ig_caption,
                "tags": ig_tags
            },
            "facebook": {
                "caption": f"{clean_title} - Highlights from today's session."
            },
            "suggested_publishing_window": suggested_time,
            "advertiser_friendliness_warnings": risk_warnings,
            "monetization_eligible": len(risk_warnings) == 0
        }

    def generate_complete_package(self, transcript_text: str = "", format_type: str = "Indian Gaming Comedy", category: str = "gaming", title: str = "Viral Highlight") -> Dict:
        """Helper method compatible with autonomous pipeline worker."""
        return self.package_clip(
            title=title,
            hook=transcript_text[:60] if transcript_text else "Wait until you see this",
            transcript_excerpt=transcript_text,
            category=category
        )

# Backwards compatibility alias
GrowthPackagingEngine = HypeRank
