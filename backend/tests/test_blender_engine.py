import os
from backend.blender.runner import BlenderRunner
from backend.agents.visual_director import SceneInstruction

def test_blender_script_generation(tmp_path):
    runner = BlenderRunner()
    scene = SceneInstruction(
        scene_id=1,
        generator_type="space",
        duration=4.0,
        camera_motion="orbit",
        description="Low poly Earth with vanishing Moon in deep space",
        accent_color="#00FFCC"
    )
    script_path = runner.generate_blender_script(scene, output_dir=str(tmp_path))
    assert os.path.exists(script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
        assert "import bpy" in code
        assert "bpy.context.scene.render.resolution_x = 1080" in code
        assert "bpy.context.scene.render.resolution_y = 1920" in code
        assert "bpy.context.scene.render.fps = 30" in code
        assert "icosphere" in code.lower() or "planet" in code.lower() or "space" in code.lower()

def test_all_scene_types_generation(tmp_path):
    runner = BlenderRunner()
    scene_types = ["space", "physics", "micro", "tech", "atmosphere"]
    
    for stype in scene_types:
        scene = SceneInstruction(
            scene_id=1,
            generator_type=stype,
            duration=3.0,
            camera_motion="flythrough",
            description=f"Test {stype} scene"
        )
        script_path = runner.generate_blender_script(scene, output_dir=str(tmp_path))
        assert os.path.exists(script_path)
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
            assert "1080" in code
            assert "1920" in code
            assert "build_scene" in code
