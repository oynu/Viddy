import re
from pathlib import Path
from typing import Dict, Any, Optional

def clean_title_from_filename(filename_or_title: str) -> str:
    """Cleans file extensions, underscores, dashes and numbers into a readable title."""
    stem = Path(filename_or_title).stem
    # Strip leading timestamps or hash prefixes like 839fae12_
    cleaned = re.sub(r"^[a-f0-9]{8}_", "", stem)
    cleaned = re.sub(r"[_\-\.]+", " ", cleaned).strip()
    # Capitalize words
    words = cleaned.split()
    return " ".join(w.capitalize() for w in words) if words else "Short Video"

def extract_topic_keywords(text: str) -> list[str]:
    """Extracts informative keywords ignoring common stop words."""
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "from", "up", "about", "into", "over", "after", "how", "what", "why", "when", "does", "did", "is", "are", "video", "short", "mp4"}
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return [w for w in words if w not in stop_words]

def generate_smart_metadata(
    raw_title: str,
    prompt: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates viral metadata for TikTok and YouTube Shorts based on the video title and optional prompt.
    """
    base_title = prompt.strip() if prompt and prompt.strip() else clean_title_from_filename(raw_title)
    keywords = extract_topic_keywords(base_title)

    # 1. Attention-grabbing Hook Title
    hook_patterns = [
        f"{base_title} 🤯 (Wait till the end!)",
        f"The Truth Behind: {base_title} 👀",
        f"Why Nobody Talks About: {base_title} ⚡",
        f"{base_title} Explained in 40 Seconds 🚀"
    ]
    # Deterministic choice based on length to maintain stability
    chosen_title = hook_patterns[len(base_title) % len(hook_patterns)]

    # 2. Targeted Hashtags
    core_reach_tags = ["#fyp", "#foryou", "#foryoupage", "#viral", "#trending", "#shorts", "#mustwatch"]
    topic_tags = [f"#{k}" for k in keywords[:6]]
    all_hashtags = " ".join(list(dict.fromkeys(core_reach_tags[:4] + topic_tags + core_reach_tags[4:])))

    # 3. TikTok Pinned Commentary (drives reply count & algorithm retention)
    commentary_options = [
        f"💬 QUESTION: Did you know this before watching, or did this completely blow your mind? Drop your thoughts below! 👇",
        f"💬 Be honest: Did you expect that ending? Let's debate in the comments! 👇",
        f"💬 What mind-bending topic should we break down next? Leave your ideas below! 👇"
    ]
    chosen_comment = commentary_options[len(keywords) % len(commentary_options)]

    # 4. TikTok Full Caption
    tiktok_caption = f"{chosen_title}\n\n{all_hashtags}"

    # 5. YouTube Description & Tags
    youtube_desc = f"{chosen_title}\n\nQuick breakdown of {base_title}.\n\n#Shorts {all_hashtags}"
    youtube_tags = list(dict.fromkeys(["shorts", "viral", "trending"] + keywords[:8]))

    return {
        "title": chosen_title,
        "clean_title": base_title,
        "tiktok_caption": tiktok_caption,
        "tiktok_hashtags": all_hashtags,
        "tiktok_commentary": chosen_comment,
        "youtube_description": youtube_desc,
        "youtube_tags": ",".join(youtube_tags)
    }
