import re
from pathlib import Path
from typing import Dict, Any, Optional

def clean_title_from_filename(filename_or_title: str) -> str:
    """Cleans file extensions, underscores, dashes and numbers into a readable title."""
    stem = Path(filename_or_title).stem
    cleaned = re.sub(r"^[a-f0-9]{8}_", "", stem)
    cleaned = re.sub(r"[_\-\.]+", " ", cleaned).strip()
    words = cleaned.split()
    return " ".join(w.capitalize() for w in words) if words else "Short Video"

def extract_topic_keywords(text: str) -> list[str]:
    """Extracts informative keywords ignoring common stop words."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "with", "by", "of", "from", "up", "about", "into", "over", "after",
        "how", "what", "why", "when", "does", "did", "is", "are", "video",
        "short", "mp4", "this", "that", "these", "those", "you", "your", "they",
        "just", "have", "been", "would", "could", "should", "there", "then"
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return [w for w in words if w not in stop_words]

def generate_smart_metadata(
    raw_title: str,
    prompt: Optional[str] = None,
    script: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes the video script (or filename/prompt) to generate an ultra-viral
    caption, algorithm reach hashtags, and pinned discussion comment.
    """
    clean_stem = clean_title_from_filename(raw_title)
    base_title = prompt.strip() if prompt and prompt.strip() else clean_stem

    # If script is available, extract rich keywords from spoken content
    text_corpus = f"{base_title} {script or ''}"
    keywords = extract_topic_keywords(text_corpus)

    # 1. Attention-Grabbing Viral Hook Title
    if script and len(script.strip()) > 15:
        # Extract first punchy sentence or hook from script
        sentences = [s.strip() for s in re.split(r"[.!?]+", script) if len(s.strip()) > 8]
        first_sentence = sentences[0] if sentences else base_title
        if len(first_sentence) > 65:
            first_sentence = first_sentence[:62] + "..."
        hook_title = f"{first_sentence} 🤯"
    else:
        hook_patterns = [
            f"{base_title} 🤯 (Wait till the end!)",
            f"The Truth Behind: {base_title} 👀",
            f"Why Nobody Talks About: {base_title} ⚡",
            f"{base_title} Explained in 40 Seconds 🚀"
        ]
        hook_title = hook_patterns[len(base_title) % len(hook_patterns)]

    # 2. Targeted Reach & Viral Hashtags
    core_reach_tags = ["#fyp", "#foryou", "#foryoupage", "#viral", "#trending", "#shorts", "#learnontiktok"]
    topic_tags = [f"#{k}" for k in keywords[:6]]
    all_hashtags = " ".join(list(dict.fromkeys(core_reach_tags[:3] + topic_tags + core_reach_tags[3:])))

    # 3. Viral TikTok Pinned Commentary
    if keywords:
        top_keyword = keywords[0].capitalize()
        commentary_options = [
            f"💬 DISCUSSION: Did you know this about {top_keyword} before watching, or did this blow your mind? Drop your thoughts below! 👇",
            f"💬 Be honest: Did you expect that ending? What should we break down next? 👇",
            f"💬 What's your take on this? Let's debate in the comments! 👇"
        ]
    else:
        commentary_options = [
            f"💬 QUESTION: Did you know this before watching, or did this completely surprise you? Drop your thoughts below! 👇"
        ]
    chosen_comment = commentary_options[len(keywords) % len(commentary_options)]

    # 4. TikTok Full Caption (Hook + Brief Context + Hashtags)
    if script and len(script.strip()) > 20:
        brief_summary = script.strip()[:140] + ("..." if len(script.strip()) > 140 else "")
        tiktok_caption = f"{hook_title}\n\n{brief_summary}\n\n{all_hashtags}"
    else:
        tiktok_caption = f"{hook_title}\n\n{all_hashtags}"

    # 5. YouTube Description & Tags
    youtube_desc = f"{hook_title}\n\n{script or base_title}\n\n#Shorts {all_hashtags}"
    youtube_tags = list(dict.fromkeys(["shorts", "viral", "trending"] + keywords[:8]))

    return {
        "title": hook_title,
        "clean_title": base_title,
        "script": script or base_title,
        "tiktok_caption": tiktok_caption,
        "tiktok_hashtags": all_hashtags,
        "tiktok_commentary": chosen_comment,
        "youtube_description": youtube_desc,
        "youtube_tags": ",".join(youtube_tags)
    }
