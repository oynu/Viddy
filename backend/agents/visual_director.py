from typing import List
from pydantic import BaseModel, Field
from backend.agents.researcher import ResearchedConcept
from backend.agents.scriptwriter import VideoScript

class SceneInstruction(BaseModel):
    scene_id: int
    generator_type: str  # space, physics, micro, tech, atmosphere
    duration: float
    camera_motion: str  # orbit, flythrough, zoom_in, pan, top_down
    lighting_theme: str = "cinematic_studio"  # cinematic_studio, space_sunlight, cyber_glow, dramatic_rim
    description: str = ""
    accent_color: str = "#FF5500"

class VisualProductionPlan(BaseModel):
    title: str
    scenes: List[SceneInstruction] = Field(default_factory=list)
    total_duration: float = 0.0
    palette: List[str] = Field(default_factory=lambda: ["#0B0E14", "#1E2638", "#00FFCC", "#FF3366", "#FFFFFF"])

class VisualDirectorAgent:
    def __init__(self):
        pass

    def create_production_plan(self, concept: ResearchedConcept, script: VideoScript) -> VisualProductionPlan:
        """
        Translates script blocks and scientific concepts into a scene-by-scene 3D production plan.
        """
        category_to_generator = {
            "astronomy": "space",
            "physics": "physics",
            "biology": "micro",
            "chemistry": "micro",
            "technology": "tech",
            "everyday_science": "physics",
            "mathematics": "tech",
            "psychology": "micro"
        }
        
        primary_gen = category_to_generator.get(concept.category, "space")
        num_blocks = len(script.narration_blocks)
        scene_duration = round(script.estimated_duration / max(1, num_blocks), 1)
        
        scenes = []
        camera_motions = ["orbit", "flythrough", "zoom_in", "pan", "top_down"]
        
        for idx, block in enumerate(script.narration_blocks):
            motion = camera_motions[idx % len(camera_motions)]
            # Alternate generator slightly for dynamic visual progression
            gen_type = primary_gen
            if idx == 0:
                gen_type = primary_gen
            elif idx == len(script.narration_blocks) - 1:
                gen_type = "space" if primary_gen != "space" else "tech"
                
            scenes.append(SceneInstruction(
                scene_id=idx + 1,
                generator_type=gen_type,
                duration=scene_duration,
                camera_motion=motion,
                lighting_theme="space_sunlight" if gen_type == "space" else "cyber_glow",
                description=f"Scene {idx+1}: {block[:60]}...",
                accent_color="#00FFCC" if idx % 2 == 0 else "#FF3366"
            ))
            
        total_dur = sum(s.duration for s in scenes)
        
        return VisualProductionPlan(
            title=script.title,
            scenes=scenes,
            total_duration=total_dur
        )
