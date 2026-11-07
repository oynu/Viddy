import os
import sys
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from backend.agents.visual_director import SceneInstruction, VisualProductionPlan
from backend.config import settings

# Modular Python low-poly scene generator scripts executed inside Blender
BLENDER_BASE_TEMPLATE = """
import bpy
import math
import random

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Ensure a collection exists
    if not bpy.data.collections:
        col = bpy.data.collections.new("ViddyCollection")
        bpy.context.scene.collection.children.link(col)

def setup_render_engine(fps=30, total_frames=120, output_path="//render_scene.mp4"):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    
    # Set 9:16 vertical resolution
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.fps = 30
    
    scene.frame_start = 1
    scene.frame_end = total_frames
    
    # Configure MP4 H.264 video output
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.audio_codec = 'NONE'

def create_low_poly_material(name, color_rgba, roughness=0.8, metallic=0.1, emission=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color_rgba
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if emission > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = color_rgba
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission
    return mat

def setup_cinematic_lighting(theme="space_sunlight", accent_color=(0.0, 1.0, 0.8, 1.0)):
    # Key light
    key_light_data = bpy.data.lights.new(name="KeyLight", type='SUN' if theme == "space_sunlight" else 'AREA')
    key_light_data.energy = 5.0 if theme == "space_sunlight" else 500.0
    key_light_data.color = (1.0, 0.95, 0.9)
    key_light_obj = bpy.data.objects.new(name="KeyLight", object_data=key_light_data)
    bpy.context.scene.collection.objects.link(key_light_obj)
    key_light_obj.location = (5.0, -6.0, 7.0)
    key_light_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(35))
    
    # Colored Rim Light for premium low-poly look
    rim_light_data = bpy.data.lights.new(name="RimLight", type='POINT')
    rim_light_data.energy = 800.0
    rim_light_data.color = (accent_color[0], accent_color[1], accent_color[2])
    rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_light_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.location = (-4.0, 5.0, 3.0)
    
    # Soft fill ambient
    fill_light_data = bpy.data.lights.new(name="FillLight", type='POINT')
    fill_light_data.energy = 250.0
    fill_light_data.color = (0.3, 0.4, 0.6)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_light_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = (0.0, -5.0, -2.0)

def setup_camera(total_frames, motion="orbit"):
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 45  # Cinematic vertical focal length
    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    # Camera trajectory keyframes
    cam_obj.location = (0.0, -9.0, 2.5)
    cam_obj.rotation_euler = (math.radians(78), 0, 0)
    
    if motion == "orbit":
        # Smooth circular orbit around target
        for f in range(1, total_frames + 1):
            angle = (f / total_frames) * math.pi * 0.7 - 0.35
            radius = 8.5
            cam_obj.location.x = radius * math.sin(angle)
            cam_obj.location.y = -radius * math.cos(angle)
            cam_obj.location.z = 2.2 + 0.5 * math.sin(angle * 2)
            cam_obj.rotation_euler.z = angle
            cam_obj.keyframe_insert(data_path="location", frame=f)
            cam_obj.keyframe_insert(data_path="rotation_euler", frame=f)
    elif motion == "flythrough" or motion == "zoom_in":
        cam_obj.location = (0.0, -12.0, 3.5)
        cam_obj.keyframe_insert(data_path="location", frame=1)
        cam_obj.location = (0.0, -6.0, 1.8)
        cam_obj.keyframe_insert(data_path="location", frame=total_frames)
    else:
        # Subtle slow pan
        cam_obj.location = (-1.5, -9.0, 2.5)
        cam_obj.keyframe_insert(data_path="location", frame=1)
        cam_obj.location = (1.5, -9.0, 2.5)
        cam_obj.keyframe_insert(data_path="location", frame=total_frames)

"""

SCENE_GENERATOR_SPACE = """
def build_scene(total_frames):
    # Low-poly planet (Icosphere with subdivisions=2 for flat geometric look)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=2.2, location=(0, 0, 0))
    planet = bpy.context.active_object
    planet.name = "LowPolyPlanet"
    
    # Flat shading
    for poly in planet.data.polygons:
        poly.use_smooth = False
        
    mat_planet = create_low_poly_material("PlanetMat", (0.1, 0.45, 0.85, 1.0), roughness=0.7)
    planet.data.materials.append(mat_planet)
    
    # Keyframe planet slow rotation
    planet.rotation_euler = (0.1, 0.2, 0)
    planet.keyframe_insert(data_path="rotation_euler", frame=1)
    planet.rotation_euler = (0.1, 0.2, math.pi * 0.8)
    planet.keyframe_insert(data_path="rotation_euler", frame=total_frames)
    
    # Low-poly Moon
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.6, location=(4.2, 1.0, 0.8))
    moon = bpy.context.active_object
    moon.name = "LowPolyMoon"
    for poly in moon.data.polygons:
        poly.use_smooth = False
    mat_moon = create_low_poly_material("MoonMat", (0.8, 0.8, 0.85, 1.0), roughness=0.9)
    moon.data.materials.append(mat_moon)
    
    # Moon orbit trajectory
    for f in range(1, total_frames + 1):
        angle = (f / total_frames) * math.pi * 1.2
        moon.location.x = 4.2 * math.cos(angle)
        moon.location.y = 3.5 * math.sin(angle)
        moon.location.z = 0.8 + 0.4 * math.sin(angle)
        moon.keyframe_insert(data_path="location", frame=f)
        
    # Asteroid belt particles
    random.seed(42)
    for i in range(16):
        r = random.uniform(5.5, 7.5)
        theta = random.uniform(0, 2 * math.pi)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.1, 0.25), location=(r*math.cos(theta), r*math.sin(theta), random.uniform(-0.5, 0.5)))
        rock = bpy.context.active_object
        mat_rock = create_low_poly_material(f"RockMat_{i}", (0.5, 0.4, 0.35, 1.0), roughness=1.0)
        rock.data.materials.append(mat_rock)
"""

SCENE_GENERATOR_PHYSICS = """
def build_scene(total_frames):
    # Pedestal / Floor plate
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=4.0, depth=0.4, location=(0, 0, -1.5))
    floor = bpy.context.active_object
    mat_floor = create_low_poly_material("FloorMat", (0.15, 0.18, 0.25, 1.0), roughness=0.6)
    floor.data.materials.append(mat_floor)
    
    # Dynamic tumbling geometric primitives
    random.seed(99)
    for i in range(8):
        x = random.uniform(-2.0, 2.0)
        y = random.uniform(-1.5, 1.5)
        start_z = 3.0 + i * 0.8
        
        if i % 2 == 0:
            bpy.ops.mesh.primitive_cube_add(size=0.9, location=(x, y, start_z))
        else:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.55, location=(x, y, start_z))
            
        obj = bpy.context.active_object
        for poly in obj.data.polygons:
            poly.use_smooth = False
            
        color = (random.uniform(0.8, 1.0), random.uniform(0.2, 0.5), random.uniform(0.1, 0.3), 1.0)
        mat = create_low_poly_material(f"PhysMat_{i}", color, roughness=0.4, metallic=0.3)
        obj.data.materials.append(mat)
        
        # Falling animation
        obj.location = (x, y, start_z)
        obj.keyframe_insert(data_path="location", frame=1)
        land_frame = min(total_frames, int(15 + i * 10))
        obj.location = (x, y, -1.0 + (i * 0.25))
        obj.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
        obj.keyframe_insert(data_path="location", frame=land_frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=land_frame)
"""

SCENE_GENERATOR_MICRO = """
def build_scene(total_frames):
    # Biological / Neural Low-poly network
    random.seed(123)
    nodes = []
    for i in range(12):
        x = random.uniform(-2.5, 2.5)
        y = random.uniform(-2.0, 2.0)
        z = random.uniform(-1.5, 2.5)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.4, location=(x, y, z))
        node = bpy.context.active_object
        for p in node.data.polygons:
            p.use_smooth = False
        color = (0.0, 0.85, 0.95, 1.0) if i % 2 == 0 else (1.0, 0.2, 0.5, 1.0)
        mat = create_low_poly_material(f"NodeMat_{i}", color, emission=2.5)
        node.data.materials.append(mat)
        nodes.append((x, y, z))
        
        # Pulsing scale keyframe
        node.scale = (1.0, 1.0, 1.0)
        node.keyframe_insert(data_path="scale", frame=1)
        node.scale = (1.4, 1.4, 1.4)
        node.keyframe_insert(data_path="scale", frame=int(total_frames / 2))
        node.scale = (1.0, 1.0, 1.0)
        node.keyframe_insert(data_path="scale", frame=total_frames)

    # Interconnecting geometric axons (cylinders with 6 vertices)
    for i in range(len(nodes) - 1):
        p1 = nodes[i]
        p2 = nodes[i+1]
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.08, depth=2.0, location=mid)
        axon = bpy.context.active_object
        mat_axon = create_low_poly_material(f"Axon_{i}", (0.2, 0.4, 0.6, 1.0), roughness=0.5)
        axon.data.materials.append(mat_axon)
"""

SCENE_GENERATOR_TECH = """
def build_scene(total_frames):
    # Cybernetic geometric lattice / Supercomputer matrix
    for x in range(-2, 3):
        for y in range(-2, 3):
            height = 0.5 + 0.3 * (abs(x) + abs(y))
            bpy.ops.mesh.primitive_cube_add(size=0.8, location=(x * 1.1, y * 1.1, 0))
            block = bpy.context.active_object
            for p in block.data.polygons:
                p.use_smooth = False
            is_active = (x + y) % 2 == 0
            color = (0.0, 1.0, 0.6, 1.0) if is_active else (0.1, 0.15, 0.22, 1.0)
            mat = create_low_poly_material(f"MatrixMat_{x}_{y}", color, roughness=0.3, emission=1.5 if is_active else 0.0)
            block.data.materials.append(mat)
            
            # Oscillating vertical height keyframes
            block.location.z = 0
            block.keyframe_insert(data_path="location", frame=1)
            block.location.z = 0.8 if is_active else -0.3
            block.keyframe_insert(data_path="location", frame=int(total_frames/2))
            block.location.z = 0
            block.keyframe_insert(data_path="location", frame=total_frames)
"""

SCENE_GENERATOR_ATMOSPHERE = """
def build_scene(total_frames):
    # Low-poly mountain/volcano cone with 8 vertices
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=3.5, depth=4.0, location=(0, 0, 0))
    cone = bpy.context.active_object
    for p in cone.data.polygons:
        p.use_smooth = False
    mat_rock = create_low_poly_material("MountainMat", (0.3, 0.25, 0.22, 1.0), roughness=0.9)
    cone.data.materials.append(mat_rock)
    
    # Erupting geometric smoke/fire particles
    random.seed(55)
    for i in range(10):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=(0, 0, 2.1))
        smoke = bpy.context.active_object
        for p in smoke.data.polygons:
            p.use_smooth = False
        color = (1.0, 0.35, 0.0, 1.0) if i < 4 else (0.4, 0.4, 0.45, 1.0)
        mat = create_low_poly_material(f"SmokeMat_{i}", color, emission=2.0 if i < 4 else 0.0)
        smoke.data.materials.append(mat)
        
        start_f = int(i * (total_frames / 12))
        smoke.location = (0, 0, 2.1)
        smoke.scale = (0.2, 0.2, 0.2)
        smoke.keyframe_insert(data_path="location", frame=max(1, start_f))
        smoke.keyframe_insert(data_path="scale", frame=max(1, start_f))
        
        target_z = 5.0 + i * 0.4
        offset_x = random.uniform(-1.0, 1.0)
        smoke.location = (offset_x, random.uniform(-0.5, 0.5), target_z)
        smoke.scale = (1.2, 1.2, 1.2)
        smoke.keyframe_insert(data_path="location", frame=total_frames)
        smoke.keyframe_insert(data_path="scale", frame=total_frames)
"""

RUNNER_FOOTER = """
if __name__ == "__main__":
    import sys
    reset_scene()
    setup_render_engine(fps=30, total_frames={total_frames}, output_path=r"{output_video_path}")
    setup_cinematic_lighting(theme="{lighting_theme}")
    setup_camera(total_frames={total_frames}, motion="{camera_motion}")
    build_scene(total_frames={total_frames})
    
    print("[VIDDY_BLENDER] Starting render...")
    bpy.ops.render.render(animation=True)
    print("[VIDDY_BLENDER] Render finished successfully.")
"""

class BlenderRunner:
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self._find_blender()

    def _find_blender(self) -> str:
        """Finds blender in PATH or common Windows installation directories."""
        # 1. Environment or PATH
        cmd = shutil.which("blender")
        if cmd:
            return cmd
            
        # 2. Standard Windows Program Files locations
        common_paths = [
            Path(r"C:\Program Files\Blender Foundation"),
            Path(r"C:\Program Files (x86)\Blender Foundation"),
            Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs")),
        ]
        for base in common_paths:
            if base.exists():
                for sub in base.glob("**/blender.exe"):
                    if sub.is_file():
                        return str(sub)
        return "blender"

    def is_blender_available(self) -> bool:
        """Native generation active: Blender binary execution disabled per user mandate."""
        return False

    def generate_blender_script(
        self,
        scene: SceneInstruction,
        output_dir: str,
        output_video_name: str = "scene.mp4"
    ) -> str:
        """
        Generates self-contained standalone Python script for Blender headless rendering.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        script_file = out_dir / f"render_scene_{scene.scene_id}.py"
        video_out = str((out_dir / output_video_name).resolve())
        
        total_frames = max(30, int(scene.duration * 30))
        
        generators = {
            "space": SCENE_GENERATOR_SPACE,
            "physics": SCENE_GENERATOR_PHYSICS,
            "micro": SCENE_GENERATOR_MICRO,
            "tech": SCENE_GENERATOR_TECH,
            "atmosphere": SCENE_GENERATOR_ATMOSPHERE
        }
        gen_code = generators.get(scene.generator_type, SCENE_GENERATOR_SPACE)
        
        footer = RUNNER_FOOTER.format(
            total_frames=total_frames,
            output_video_path=video_out,
            lighting_theme=scene.lighting_theme,
            camera_motion=scene.camera_motion
        )
        
        full_script = BLENDER_BASE_TEMPLATE + "\n" + gen_code + "\n" + footer
        
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(full_script)
            
        return str(script_file)

    async def render_scene_async(
        self,
        scene: SceneInstruction,
        output_dir: str,
        output_video_name: str = "scene.mp4",
        timeout_seconds: float = 180.0
    ) -> str:
        """
        Executes Blender in headless background mode:
        blender -b -P <script.py>
        With timeout watchdog and automated fallback generator.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        video_out = str((out_dir / output_video_name).resolve())
        
        script_path = self.generate_blender_script(scene, output_dir, output_video_name)
        
        if self.is_blender_available():
            cmd = [self.blender_path, "-b", "-P", script_path]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
                if proc.returncode == 0 and os.path.exists(video_out) and os.path.getsize(video_out) > 1000:
                    return video_out
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
            except Exception:
                pass
                
        # High-Fidelity Procedural 3D Fallback:
        # Generates vertical 1080x1920 low-poly geometric video clip
        return await self._generate_procedural_fallback_video(scene, video_out, timeout_seconds=timeout_seconds)

    async def _generate_procedural_fallback_video(
        self,
        scene: SceneInstruction,
        video_out: str,
        timeout_seconds: float = 60.0
    ) -> str:
        """
        Generates real animated 1080x1920 30FPS low-poly 3D video using Procedural3DRenderer.
        Renders real 3D geometry with perspective projection, flat faceted shading, and starfield.
        """
        from backend.blender.renderer_3d import Procedural3DRenderer
        renderer = Procedural3DRenderer()
        fps = 30
        total_sec = max(2.0, scene.duration)
        total_frames = int(total_sec * fps)
        
        cmd = [
            settings.ffmpeg_path, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", "1080x1920",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            video_out
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            for i in range(total_frames):
                t_norm = i / max(1, total_frames)
                frame = renderer.render_frame(
                    scene_type=scene.generator_type,
                    t_normalized=t_norm,
                    accent_color_hex=scene.accent_color,
                    caption_tag=scene.generator_type.upper()
                )
                proc.stdin.write(frame.tobytes())
                if i % 15 == 0:
                    await proc.stdin.drain()
                    
            await proc.stdin.drain()
            proc.stdin.close()
            await asyncio.wait_for(proc.wait(), timeout=timeout_seconds)
        except Exception:
            pass
            
        return video_out

    async def generate_titled_video_async(
        self,
        category: str,
        title: str,
        duration: float,
        output_video_path: str,
        timeout_seconds: float = 240.0
    ) -> str:
        """
        Directly generates complete titled 1080x1920 30FPS 3D MP4 video using native Procedural3DVideoGenerator.
        """
        from backend.media.video_generator import Procedural3DVideoGenerator
        gen = Procedural3DVideoGenerator()
        return await gen.generate_titled_video_async(
            category=category,
            title=title,
            duration=duration,
            output_video_path=output_video_path,
            timeout_seconds=timeout_seconds
        )
