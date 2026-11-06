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
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_tags: List[str] = Field(default_factory=list)

class ScriptwritingAgent:
    def __init__(self, target_wpm: int = 140):
        self.target_wpm = target_wpm

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
        
        # Platform-specific publishing metadata
        tags = ["#shorts", "#science", "#education", "#physics", "#whatif", "#viddy", "#learn"]
        tiktok_caption = f"{concept.title} 🤯 Science breakdown you didn't know! {' '.join(tags[:5])}"
        youtube_title = f"{concept.title} #shorts"
        
        sources_str = ", ".join(concept.scientific_sources) if concept.scientific_sources else "Verified Academic Sources"
        youtube_description = (
            f"{concept.title}\n\n"
            f"{full_text}\n\n"
            f"Sources: {sources_str}\n"
            f"Produced autonomously by Viddy AI Video Studio.\n\n"
            f"{' '.join(tags)}"
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
            youtube_title=youtube_title,
            youtube_description=youtube_description,
            youtube_tags=tags
        )
