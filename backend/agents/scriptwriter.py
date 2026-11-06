from typing import List, Optional
from pydantic import BaseModel, Field
from backend.agents.researcher import ResearchedConcept

class VideoScript(BaseModel):
    title: str
    hook: str
    narration_blocks: List[str] = Field(default_factory=list)
    full_narration: str = ""
    call_to_action: str = "Follow for daily mind-bending science!"
    estimated_duration: float = 35.0
    on_screen_texts: List[str] = Field(default_factory=list)
    tiktok_caption: str = ""
    tiktok_hashtags: str = ""
    tiktok_commentary: str = ""
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_tags: List[str] = Field(default_factory=list)

class ScriptwritingAgent:
    def __init__(self, target_wpm: int = 140):
        self.target_wpm = target_wpm

    def _generate_tiktok_hashtags(self, category: str, title: str) -> str:
        """
        Generates algorithm-optimized TikTok hashtag block combining:
        1. Universal high-traffic FYP tags
        2. STEM / Education authority tags
        3. Topic-specific category tags
        """
        # FYP + STEM authority staples
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

        # Deduplicate while preserving order
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
        clean_title = concept.title.replace('What if ', '').replace('How does ', '').rstrip('?')
        
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
        Synthesizes researched scientific facts into a viral, high-retention 30-45s script.
        """
        # 1. Attention-grabbing opening hook
        hook = f"What if {concept.title.replace('What if ', '').replace('How does ', '').rstrip('?')}?"
        if concept.hook_angle:
            hook = f"Imagine this: {concept.hook_angle}."
            
        # 2. Narration narrative blocks
        blocks = []
        # Opening shock
        blocks.append(hook)
        
        # Primary consequence from fact 1
        if len(concept.key_facts) > 0:
            blocks.append(f"Within seconds, {concept.key_facts[0].lower()}")
            
        # Scientific explanation from fact 2
        if len(concept.key_facts) > 1:
            blocks.append(f"Why? Because {concept.key_facts[1].lower()}")
            
        # Escalation / Twist from fact 3
        if len(concept.key_facts) > 2:
            blocks.append(f"Even crazier, {concept.key_facts[2].lower()}")
            
        cta = "Which cosmic mystery should we unravel next? Drop a comment and follow Viddy!"
        blocks.append(cta)
        
        full_text = " ".join(blocks)
        word_count = len(full_text.split())
        estimated_duration = round((word_count / self.target_wpm) * 60.0, 1)
        
        # Key on-screen text highlights
        on_screen_texts = [
            concept.title.upper(),
            "PHYSICS COLLAPSE",
            "WHAT HAPPENS NEXT?"
        ]
        
        # Algorithm-optimized hashtags and viral commentary
        cat = getattr(concept, "category", "science")
        tiktok_hashtags = self._generate_tiktok_hashtags(cat, concept.title)
        tiktok_commentary = self._generate_tiktok_commentary(concept)
        
        # Optimized TikTok caption with viral hook + tags
        tiktok_caption = f"{concept.title} 🤯 Science breakdown you didn't know!\n\n{tiktok_hashtags}"
        
        # YouTube Shorts metadata
        youtube_tags = ["#shorts", "#science", "#education", "#physics", "#whatif", "#viddy", "#learn"]
        youtube_title = f"{concept.title} #shorts"
        
        sources_str = ", ".join(concept.scientific_sources) if concept.scientific_sources else "Verified Academic Sources"
        youtube_description = (
            f"{concept.title}\n\n"
            f"{full_text}\n\n"
            f"Sources: {sources_str}\n"
            f"Produced autonomously by Viddy AI Video Studio.\n\n"
            f"{tiktok_hashtags}"
        )
        
        return VideoScript(
            title=concept.title,
            hook=hook,
            narration_blocks=blocks,
            full_narration=full_text,
            call_to_action=cta,
            estimated_duration=max(25.0, min(58.0, estimated_duration)),
            on_screen_texts=on_screen_texts,
            tiktok_caption=tiktok_caption,
            tiktok_hashtags=tiktok_hashtags,
            tiktok_commentary=tiktok_commentary,
            youtube_title=youtube_title,
            youtube_description=youtube_description,
            youtube_tags=youtube_tags
        )
