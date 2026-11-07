import re
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from backend.agents.researcher import ResearchedConcept

class VideoScript(BaseModel):
    title: str
    hook: str
    narration_blocks: List[str] = Field(default_factory=list)
    full_narration: str = ""
    call_to_action: str = "Follow for daily mind-bending science!"
    estimated_duration: float = 38.0
    on_screen_texts: List[str] = Field(default_factory=list)
    tiktok_caption: str = ""
    tiktok_hashtags: str = ""
    tiktok_commentary: str = ""
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_tags: List[str] = Field(default_factory=list)

class ScriptwritingAgent:
    """
    Transforms researched scientific discoveries into high-retention,
    cinematic educational scripts tailored for vertical short-form video.
    """
    def __init__(self, target_wpm: int = 145):
        self.target_wpm = target_wpm

    def _generate_tiktok_hashtags(self, category: str, title: str) -> str:
        """
        Generates algorithm-optimized TikTok hashtag block combining:
        1. Universal high-traffic FYP tags
        2. STEM / Education authority tags
        3. Topic-specific category tags
        """
        core_tags = ["#fyp", "#foryou", "#foryoupage", "#viral", "#trending", "#learnontiktok", "#stemtok", "#sciencetok", "#factsdaily", "#whatif"]
        
        category_tags_map = {
            "space": ["#space", "#universe", "#astronomy", "#nasa", "#blackhole", "#cosmos", "#galaxy", "#astrophysics"],
            "physics": ["#physics", "#quantum", "#quantumphysics", "#relativity", "#sciencefacts", "#einstein"],
            "biology": ["#biology", "#neuroscience", "#brain", "#dna", "#cells", "#humanbody", "#science"],
            "chemistry": ["#chemistry", "#atoms", "#molecules", "#elements", "#reactions", "#sciencetok"],
            "technology": ["#tech", "#technology", "#ai", "#artificialintelligence", "#futuretech", "#engineering"],
            "psychology": ["#psychology", "#brainfacts", "#humanbehavior", "#mindblowing", "#psychologyfacts"],
            "math": ["#math", "#mathematics", "#geometry", "#logic", "#mindblowing", "#education"],
            "everyday": ["#everydayphysics", "#sciencefacts", "#didyouknow", "#mindblown", "#curiosity"]
        }
        
        cat_lower = (category or "science").lower()
        selected_cat_tags = []
        for key, tags in category_tags_map.items():
            if key in cat_lower or key in title.lower():
                selected_cat_tags.extend(tags)
                
        if not selected_cat_tags:
            selected_cat_tags = ["#science", "#physics", "#mindblown", "#curiosity", "#education"]

        all_tags = []
        for tag in core_tags + selected_cat_tags:
            if tag not in all_tags:
                all_tags.append(tag)
                
        return " ".join(all_tags[:16])

    def _generate_tiktok_commentary(self, concept: ResearchedConcept) -> str:
        """
        Generates a viral first pinned comment designed to trigger debate,
        theories, and comments to maximize TikTok engagement signals.
        """
        clean_title = concept.title.replace('What if ', '').replace('How does ', '').replace(' happened tomorrow?', '').rstrip('?')
        
        if "what if" in concept.title.lower():
            return (
                f"💬 PINNED QUESTION: Be honest—if {clean_title.lower()} happened tomorrow, "
                f"what would be your very first move? Drop your wildest theory below! 👇"
            )
        elif "why" in concept.title.lower() or "how" in concept.title.lower():
            return (
                f"💬 PINNED QUESTION: Did you know this before watching, or did this surprise you? "
                f"What mind-bending question should Viddy explain next? Drop it below! 👇"
            )
        else:
            return (
                f"💬 PINNED QUESTION: What is the most mind-bending fact about {clean_title} you've ever heard? "
                f"Share your thoughts below! 👇"
            )

    def generate_script(self, concept: ResearchedConcept) -> VideoScript:
        """
        Synthesizes researched scientific facts into an elaborate, captivating, high-retention script.
        """
        title_clean = concept.title.replace(' happened tomorrow?', '').rstrip('?')
        topic_subject = title_clean.replace('What if ', '').replace('How does ', '').replace('Why does ', '')

        # 1. Cinematic Visceral Opening Hook (Punchy ~18 words)
        if concept.hook_angle:
            hook = f"Picture this: {concept.hook_angle}. If {topic_subject.lower()} happened right now, reality would shatter."
        elif "what if" in concept.title.lower():
            hook = f"What if {topic_subject.lower()} occurred right now? Before your brain could process it, physics would retaliate."
        else:
            hook = f"Have you ever wondered how {topic_subject.lower()} actually works? The reality is far more extreme than you think."

        blocks = [hook]

        # 2. Immediate Consequence / Science Fact (~22 words)
        if len(concept.key_facts) > 0:
            fact_1 = concept.key_facts[0].rstrip('.')
            blocks.append(f"Within seconds, {fact_1.lower()}. Every calculation scientists rely on collapses into chaos.")
        else:
            blocks.append("Within seconds, equilibrium vanishes as the fundamental forces of matter cascade out of control.")

        # 3. Scientific Deep-Dive Mechanism (~25 words)
        if len(concept.key_facts) > 1:
            fact_2 = concept.key_facts[1].rstrip('.')
            blocks.append(f"Here is why: {fact_2}. This isn't speculation—it is governed by absolute conservation laws.")
        else:
            blocks.append("Why? Because thermodynamic entropy instantly forces a violent reallocation of mass and energy.")

        # 4. Mind-Blowing Escalation / Hidden Truth (~20 words)
        if len(concept.key_facts) > 2:
            fact_3 = concept.key_facts[2].rstrip('.')
            blocks.append(f"Even crazier, {fact_3.lower()}. Our existence balances on an impossibly fragile cosmic edge.")

        # 5. Punchy Call-to-Action (~12 words)
        cta = "What mind-bending question should Viddy explain next? Drop it below and follow for daily science!"
        blocks.append(cta)

        full_text = " ".join(blocks)
        word_count = len(full_text.split())
        estimated_duration = round((word_count / self.target_wpm) * 60.0, 1)

        # On-screen text kinetic highlights
        on_screen_texts = [
            title_clean.upper(),
            "COSMIC INSTABILITY",
            "PHYSICS COLLAPSE",
            "THE HIDDEN TRUTH"
        ]

        cat = getattr(concept, "category", "science")
        tiktok_hashtags = self._generate_tiktok_hashtags(cat, concept.title)
        tiktok_commentary = self._generate_tiktok_commentary(concept)

        # High-CTR TikTok caption
        tiktok_caption = (
            f"{title_clean} 🤯 The science breakdown that changes everything!\n\n"
            f"{tiktok_hashtags}"
        )

        youtube_tags = ["#shorts", "#science", "#education", "#physics", "#whatif", "#viddy", "#learn"]
        youtube_title = f"{title_clean} #shorts"

        sources_str = ", ".join(concept.scientific_sources) if concept.scientific_sources else "Verified Academic Sources"
        youtube_description = (
            f"{title_clean}\n\n"
            f"{full_text}\n\n"
            f"Sources & Citations: {sources_str}\n"
            f"Produced autonomously by Viddy AI Video Studio.\n\n"
            f"{tiktok_hashtags}"
        )

        return VideoScript(
            title=title_clean,
            hook=hook,
            narration_blocks=blocks,
            full_narration=full_text,
            call_to_action=cta,
            estimated_duration=max(30.0, min(55.0, estimated_duration)),
            on_screen_texts=on_screen_texts,
            tiktok_caption=tiktok_caption,
            tiktok_hashtags=tiktok_hashtags,
            tiktok_commentary=tiktok_commentary,
            youtube_title=youtube_title,
            youtube_description=youtube_description,
            youtube_tags=youtube_tags
        )
