import os
import math
import asyncio
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from backend.config import settings

class Procedural3DVideoGenerator:
    """
    Native Python + FFmpeg 3D Video Production Engine.
    Generates high-definition (1080x1920 @ 30 FPS) vertical science videos
    with genuine 3D perspective geometry, cinematic camera motions,
    dynamic particle starfields, and futuristic HUD graphics without Blender.
    """
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.fov = 920.0
        self.center_x = width / 2.0
        self.center_y = height / 2.0
        
        # Pre-seed persistent 3D starfield (x, y, z, speed, brightness)
        np.random.seed(1337)
        self.num_stars = 320
        self.stars = np.random.uniform(-1400, 1400, (self.num_stars, 3))
        self.stars[:, 2] = np.random.uniform(150, 1900, self.num_stars)
        self.star_speeds = np.random.uniform(220, 480, self.num_stars)

    # -------------------------------------------------------------
    # 3D Geometric Mesh Builders
    # -------------------------------------------------------------
    def _create_icosphere(self, radius: float = 230.0, subdivisions: int = 1) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates low-poly icosphere vertices and triangular facets."""
        t = (1.0 + math.sqrt(5.0)) / 2.0
        verts = np.array([
            [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
            [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
            [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
        ], dtype=float)
        
        verts = verts / np.linalg.norm(verts, axis=1)[:, np.newaxis] * radius
        
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
        ]
        
        if subdivisions > 0:
            midpoints = {}
            def get_midpoint(i1, i2):
                nonlocal verts
                key = tuple(sorted((i1, i2)))
                if key in midpoints:
                    return midpoints[key]
                v = (verts[i1] + verts[i2]) / 2.0
                v = v / np.linalg.norm(v) * radius
                idx = len(verts)
                verts = np.vstack([verts, v])
                midpoints[key] = idx
                return idx
                
            new_faces = []
            for v1, v2, v3 in faces:
                a = get_midpoint(v1, v2)
                b = get_midpoint(v2, v3)
                c = get_midpoint(v3, v1)
                new_faces.extend([(v1, a, c), (v2, b, a), (v3, c, b), (a, b, c)])
            faces = new_faces

        return verts, faces

    def _create_ring(self, inner_r: float = 330.0, outer_r: float = 540.0, segments: int = 28) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates low-poly planetary rings or accretion disk."""
        verts = []
        faces = []
        for i in range(segments):
            angle = (2 * math.pi * i) / segments
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            verts.append([inner_r * cos_a, 0, inner_r * sin_a])
            verts.append([outer_r * cos_a, 0, outer_r * sin_a])
            
        for i in range(segments):
            next_i = (i + 1) % segments
            i1 = i * 2
            o1 = i * 2 + 1
            i2 = next_i * 2
            o2 = next_i * 2 + 1
            faces.append((i1, o1, i2))
            faces.append((o1, o2, i2))
            
        return np.array(verts, dtype=float), faces

    def _create_dna_helix(self, height: float = 900.0, radius: float = 190.0, turns: float = 2.4, steps: int = 36) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates 3D double helix ribbon with horizontal rungs."""
        verts = []
        faces = []
        for i in range(steps):
            t = i / steps
            y = (t - 0.5) * height
            angle = t * turns * 2 * math.pi
            x1 = math.cos(angle) * radius
            z1 = math.sin(angle) * radius
            x2 = math.cos(angle + math.pi) * radius
            z2 = math.sin(angle + math.pi) * radius
            verts.extend([[x1, y, z1], [x2, y, z2]])
            
        verts = np.array(verts, dtype=float)
        for i in range(steps - 1):
            s1_a, s2_a = i * 2, i * 2 + 1
            s1_b, s2_b = (i + 1) * 2, (i + 1) * 2 + 1
            faces.append((s1_a, s1_b, s2_a))
            faces.append((s2_a, s1_b, s2_b))
            
        return verts, faces

    def _create_tesseract(self, size: float = 220.0) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates 3D projection of hypercube / tesseract."""
        inner_scale = 0.5
        verts = []
        for z in [-1, 1]:
            for y in [-1, 1]:
                for x in [-1, 1]:
                    verts.append([x * size, y * size, z * size])
        for z in [-1, 1]:
            for y in [-1, 1]:
                for x in [-1, 1]:
                    verts.append([x * size * inner_scale, y * size * inner_scale, z * size * inner_scale])
                    
        faces = [
            # Outer cube faces
            (0, 1, 3), (0, 3, 2), (4, 5, 7), (4, 7, 6),
            (0, 1, 5), (0, 5, 4), (2, 3, 7), (2, 7, 6),
            # Connecting trapezoids
            (0, 2, 10), (0, 10, 8), (1, 3, 11), (1, 11, 9),
            (4, 6, 14), (4, 14, 12), (5, 7, 15), (5, 15, 13)
        ]
        return np.array(verts, dtype=float), faces

    # -------------------------------------------------------------
    # Frame Rendering
    # -------------------------------------------------------------
    def render_frame(
        self,
        category: str,
        t_normalized: float,
        current_time_sec: float,
        title_text: str = "",
        hook_text: str = ""
    ) -> Image.Image:
        """
        Renders a single 1080x1920 3D frame at high aesthetic quality.
        """
        img = Image.new("RGB", (self.width, self.height), (8, 11, 18))
        draw = ImageDraw.Draw(img)

        # 1. Atmospheric Deep Background Gradient
        cat = category.lower()
        if "astro" in cat or "space" in cat:
            top_color = (4, 7, 14)
            mid_color = (12, 18, 34)
            bot_color = (20, 10, 30)
            accent_hex = "#00F0FF"
            cat_badge = "ASTROPHYSICS // DEEP SPACE"
        elif "physic" in cat or "quantum" in cat:
            top_color = (6, 10, 20)
            mid_color = (18, 14, 38)
            bot_color = (8, 22, 36)
            accent_hex = "#FF007F"
            cat_badge = "QUANTUM MECHANICS // PHYSICS"
        elif "bio" in cat or "chem" in cat or "neuro" in cat:
            top_color = (4, 14, 14)
            mid_color = (10, 28, 26)
            bot_color = (16, 20, 34)
            accent_hex = "#00FFAA"
            cat_badge = "BIOLOGY // MOLECULAR SCIENCE"
        else:
            top_color = (10, 12, 18)
            mid_color = (20, 24, 35)
            bot_color = (14, 18, 28)
            accent_hex = "#FFCC00"
            cat_badge = "SCIENCE // TECHNOLOGY"

        # Background gradient bands
        band_size = 6
        for y in range(0, self.height, band_size):
            r1 = y / self.height
            if r1 < 0.5:
                sub_r = r1 * 2.0
                cr = int(top_color[0] + (mid_color[0] - top_color[0]) * sub_r)
                cg = int(top_color[1] + (mid_color[1] - top_color[1]) * sub_r)
                cb = int(top_color[2] + (mid_color[2] - top_color[2]) * sub_r)
            else:
                sub_r = (r1 - 0.5) * 2.0
                cr = int(mid_color[0] + (bot_color[0] - mid_color[0]) * sub_r)
                cg = int(mid_color[1] + (bot_color[1] - mid_color[1]) * sub_r)
                cb = int(mid_color[2] + (bot_color[2] - mid_color[2]) * sub_r)
            draw.rectangle([(0, y), (self.width, y + band_size)], fill=(cr, cg, cb))

        # 2. 3D Drifting Starfield Particles
        star_z = (self.stars[:, 2] - current_time_sec * self.star_speeds) % 1800 + 100
        for i in range(self.num_stars):
            sz = star_z[i]
            if sz > 60:
                sx = self.stars[i, 0]
                sy = self.stars[i, 1]
                px = (sx / sz) * self.fov + self.center_x
                py = (sy / sz) * self.fov + self.center_y
                if 0 <= px < self.width and 0 <= py < self.height:
                    depth_ratio = max(0.0, min(1.0, 1.0 - (sz / 1900)))
                    size = max(1, int(depth_ratio * 4.5))
                    b = int(depth_ratio * 220) + 35
                    draw.ellipse([(px - size, py - size), (px + size, py + size)], fill=(b, b, min(255, b + 20)))

        # 3. Category Specific 3D Geometry
        if "bio" in cat or "chem" in cat or "neuro" in cat:
            verts, faces = self._create_dna_helix(height=980.0, radius=210.0, turns=2.4)
            rot_y = current_time_sec * 0.9
            rot_x = math.radians(22)
            rot_z = math.radians(12) + math.sin(current_time_sec * 0.8) * 0.05
            cam_dist = 860.0
        elif "physic" in cat or "quantum" in cat:
            verts, faces = self._create_icosphere(radius=180.0, subdivisions=1)
            # Add orbital electron rings
            r_verts, r_faces = self._create_ring(inner_r=260.0, outer_r=380.0, segments=24)
            offset = len(verts)
            verts = np.vstack([verts, r_verts])
            for f in r_faces:
                faces.append((f[0] + offset, f[1] + offset, f[2] + offset))
            rot_y = current_time_sec * 1.4
            rot_x = current_time_sec * 0.7
            rot_z = current_time_sec * 0.4
            cam_dist = 780.0
        elif "tech" in cat or "math" in cat:
            verts, faces = self._create_tesseract(size=230.0)
            rot_y = current_time_sec * 0.7
            rot_x = current_time_sec * 0.5
            rot_z = current_time_sec * 0.3
            cam_dist = 850.0
        else: # Astronomy / Space / Default
            verts, faces = self._create_icosphere(radius=240.0, subdivisions=1)
            r_verts, r_faces = self._create_ring(inner_r=320.0, outer_r=550.0, segments=28)
            offset = len(verts)
            verts = np.vstack([verts, r_verts])
            for f in r_faces:
                faces.append((f[0] + offset, f[1] + offset, f[2] + offset))
            rot_y = current_time_sec * 0.5
            rot_x = math.radians(26) + math.sin(current_time_sec * 0.3) * 0.04
            rot_z = math.radians(-16)
            cam_dist = 840.0

        # Dynamic Camera Zoom (Slow cinematic breathing push-in)
        zoom_mod = math.sin(current_time_sec * 0.4) * 60.0
        cam_dist = max(600.0, cam_dist - zoom_mod)

        # 3D Rotation Matrices
        cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
        cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)
        cos_z, sin_z = math.cos(rot_z), math.sin(rot_z)
        R_y = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
        R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
        R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])
        rot_matrix = R_z @ R_x @ R_y

        transformed_verts = verts @ rot_matrix.T
        transformed_verts[:, 2] += cam_dist

        # 3D Perspective Projection
        z_vals = transformed_verts[:, 2]
        proj_x = (transformed_verts[:, 0] / z_vals) * self.fov + self.center_x
        # Push 3D model slightly upwards to leave clear lower space for subtitles
        proj_y = (transformed_verts[:, 1] / z_vals) * self.fov + (self.center_y - 80.0)

        # Lighting Vectors: Key Light + Specular Rim
        light_dir = np.array([0.5, -0.7, -0.5])
        light_dir = light_dir / np.linalg.norm(light_dir)

        # Parse Accent Color
        hex_clean = accent_hex.lstrip("#")
        base_r = int(hex_clean[0:2], 16)
        base_g = int(hex_clean[2:4], 16)
        base_b = int(hex_clean[4:6], 16)

        # Sort Faces by Depth (Painter's Algorithm)
        face_depths = []
        for i, face in enumerate(faces):
            avg_z = (z_vals[face[0]] + z_vals[face[1]] + z_vals[face[2]]) / 3.0
            face_depths.append((avg_z, i))
        face_depths.sort(key=lambda x: x[0], reverse=True)

        for _, face_idx in face_depths:
            v0_idx, v1_idx, v2_idx = faces[face_idx]
            p0 = (proj_x[v0_idx], proj_y[v0_idx])
            p1 = (proj_x[v1_idx], proj_y[v1_idx])
            p2 = (proj_x[v2_idx], proj_y[v2_idx])

            # Normal Vector Calculation
            v0 = transformed_verts[v0_idx]
            v1 = transformed_verts[v1_idx]
            v2 = transformed_verts[v2_idx]
            normal = np.cross(v1 - v0, v2 - v0)
            norm_len = np.linalg.norm(normal)
            if norm_len < 1e-6:
                continue
            normal = normal / norm_len

            # Backface culling
            if normal[2] > 0.18:
                continue

            # Shading: Diffuse + Specular Rim
            diffuse = max(0.08, float(np.dot(normal, -light_dir)))
            rim = pow(max(0.0, 1.0 + float(normal[2])), 2.2) * 0.45

            poly_r = min(255, int(base_r * diffuse + 255 * rim))
            poly_g = min(255, int(base_g * diffuse + 255 * rim))
            poly_b = min(255, int(base_b * diffuse + 255 * rim))

            edge_r = int(poly_r * 0.4)
            edge_g = int(poly_g * 0.4)
            edge_b = int(poly_b * 0.4)

            draw.polygon([p0, p1, p2], fill=(poly_r, poly_g, poly_b), outline=(edge_r, edge_g, edge_b))

        # 4. Cinematic Sci-Fi HUD Overlays
        # Telemetry Corner Crop Brackets
        margin = 55
        b_len = 40
        b_col = (180, 200, 230)
        draw.line([(margin, margin), (margin + b_len, margin)], fill=b_col, width=2)
        draw.line([(margin, margin), (margin, margin + b_len)], fill=b_col, width=2)
        draw.line([(self.width - margin, margin), (self.width - margin - b_len, margin)], fill=b_col, width=2)
        draw.line([(self.width - margin, margin), (self.width - margin, margin + b_len)], fill=b_col, width=2)
        draw.line([(margin, self.height - margin), (margin + b_len, self.height - margin)], fill=b_col, width=2)
        draw.line([(margin, self.height - margin), (margin, self.height - margin - b_len)], fill=b_col, width=2)
        draw.line([(self.width - margin, self.height - margin), (self.width - margin - b_len, self.height - margin)], fill=b_col, width=2)
        draw.line([(self.width - margin, self.height - margin), (self.width - margin, self.height - margin - b_len)], fill=b_col, width=2)

        # Top Category Badge Box
        top_badge_y = 100
        draw.rounded_rectangle([(self.center_x - 240, top_badge_y), (self.center_x + 240, top_badge_y + 44)], radius=6, fill=(10, 16, 26), outline=(base_r, base_g, base_b), width=2)
        draw.text((self.center_x, top_badge_y + 22), cat_badge, fill=(240, 245, 255), anchor="mm")

        # Top Progress Timeline Indicator
        prog_w = int(self.width * t_normalized)
        draw.rectangle([(0, 0), (self.width, 5)], fill=(30, 40, 55))
        draw.rectangle([(0, 0), (prog_w, 5)], fill=(base_r, base_g, base_b))

        # 5. Hook / Title Banner Card during initial 3.5 seconds
        if current_time_sec < 3.8 and title_text:
            opacity = 1.0
            if current_time_sec > 2.8:
                opacity = max(0.0, 1.0 - (current_time_sec - 2.8) / 1.0)
            
            if opacity > 0.05:
                # Banner card in upper third
                card_y = 220
                card_h = 160
                card_w = self.width - 120
                card_x1 = 60
                card_x2 = self.width - 60
                
                # Dark backing
                draw.rounded_rectangle(
                    [(card_x1, card_y), (card_x2, card_y + card_h)],
                    radius=12,
                    fill=(12, 16, 24),
                    outline=(int(base_r * opacity), int(base_g * opacity), int(base_b * opacity)),
                    width=2
                )
                
                # Title Text wrapped
                display_title = title_text.upper()
                if len(display_title) > 60:
                    display_title = display_title[:57] + "..."
                draw.text(
                    (self.center_x, card_y + card_h // 2),
                    display_title,
                    fill=(int(255 * opacity), int(255 * opacity), int(255 * opacity)),
                    anchor="mm"
                )

        return img

    async def generate_titled_video_async(
        self,
        category: str,
        title: str,
        duration: float,
        output_video_path: str,
        timeout_seconds: float = 240.0
    ) -> str:
        """
        Renders complete continuous 1080x1920 30FPS MP4 video directly via FFmpeg stdin stream.
        No Blender binary required.
        """
        out_path = Path(output_video_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        total_frames = max(30, int(duration * self.fps))

        cmd = [
            settings.ffmpeg_path, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            str(out_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        try:
            for f_idx in range(total_frames):
                cur_time = f_idx / self.fps
                t_norm = f_idx / max(1, total_frames)
                frame = self.render_frame(
                    category=category,
                    t_normalized=t_norm,
                    current_time_sec=cur_time,
                    title_text=title
                )
                proc.stdin.write(frame.tobytes())
                if f_idx % 20 == 0:
                    await proc.stdin.drain()

            await proc.stdin.drain()
            proc.stdin.close()
            await asyncio.wait_for(proc.wait(), timeout=timeout_seconds)
        except Exception as e:
            try:
                proc.kill()
            except Exception:
                pass
            raise e

        return str(out_path)
