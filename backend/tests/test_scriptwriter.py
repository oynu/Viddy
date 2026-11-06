import pytest
from backend.agents.idea_discovery import IdeaProposal
from backend.agents.researcher import ResearchedConcept
from backend.agents.scriptwriter import ScriptwritingAgent, VideoScript
from backend.agents.visual_director import VisualDirectorAgent, VisualProductionPlan, SceneInstruction

def test_script_generation():
    concept = ResearchedConcept(
        title="What if the Moon Disappeared?",
        category="astronomy",
        hook_angle="Tides collapse by 70 percent",
        key_facts=[
            "Ocean tides would shrink by roughly 70 percent.",
            "Earth axis would begin chaotic wobbling over millennia.",
            "Nights would become pitch black altering ecosystems."
        ],
        scientific_sources=["NASA Solar System Exploration"],
        target_duration=40.0
    )
    
    scriptwriter = ScriptwritingAgent()
    script = scriptwriter.generate_script(concept)
    assert isinstance(script, VideoScript)
    assert len(script.hook) > 10
    assert len(script.narration_blocks) >= 3
    assert 20.0 <= script.estimated_duration <= 60.0
    assert len(script.call_to_action) > 0
    assert script.tiktok_caption is not None
    assert "#shorts" in script.youtube_tags

def test_visual_director_plan():
    director = VisualDirectorAgent()
    concept = ResearchedConcept(
        title="What if the Moon Disappeared?",
        category="astronomy",
        hook_angle="Tides collapse",
        key_facts=["Tides shrink", "Earth wobbles"],
        scientific_sources=["NASA"],
        target_duration=40.0
    )
    script = VideoScript(
        title="What if the Moon Disappeared?",
        hook="What if tonight, you looked up... and the Moon was just GONE?",
        narration_blocks=[
            "First, ocean tides would collapse by over 70 percent worldwide.",
            "Next, Earth's stable 23.4-degree tilt would destabilize into erratic wobble.",
            "Without lunar gravity, our seasons would fluctuate wildly from ice ages to scorching heat."
        ],
        estimated_duration=35.0,
        call_to_action="Subscribe to Viddy for daily science mysteries!"
    )
    plan = director.create_production_plan(concept, script)
    assert isinstance(plan, VisualProductionPlan)
    assert len(plan.scenes) >= 2
    assert plan.scenes[0].generator_type in ["space", "physics", "micro", "tech", "atmosphere"]
    assert plan.scenes[0].camera_motion in ["orbit", "flythrough", "zoom_in", "pan", "top_down"]
    assert plan.total_duration > 0
