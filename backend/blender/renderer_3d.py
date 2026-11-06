import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import List, Tuple, Dict, Any

class Procedural3DRenderer:
    """
    High-performance 3D software rasterizer for cinematic low-poly animations.
    Renders real 3D geometry with perspective projection, flat-faceted shading,
    and dynamic camera choreography at 1080x1920 (9:16 vertical).
    """
    def __init__(self, width: int = 1080, height: int = 1920, fov: float = 900.0):
        self.width = width
        self.height = height
        self.fov = fov
        self.center_x = width / 2.0
        self.center_y = height / 2.0
        
        # Initialize starfield particles (x, y, z)
        np.random.seed(42)
        n_stars = 250
        self.stars = np.random.uniform(-1200, 1200, (n_stars, 3))
        self.stars[:, 2] = np.random.uniform(200, 1800, n_stars)

    def _create_icosphere(self, radius: float = 220.0, subdivisions: int = 1) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates real low-poly icosphere vertices and triangular faces."""
        t = (1.0 + math.sqrt(5.0)) / 2.0
        verts = np.array([
            [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
            [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
            [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
        ], dtype=float)
        
        # Normalize to radius
        verts = verts / np.linalg.norm(verts, axis=1)[:, np.newaxis] * radius
        
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
        ]
        
        if subdivisions > 0:
            # Subdivide once for crisp low-poly facets
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

    def _create_ring(self, inner_r: float = 300.0, outer_r: float = 460.0, segments: int = 24) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates low-poly planetary ring geometry."""
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

    def _create_dna_helix(self, height: float = 800.0, radius: float = 180.0, turns: float = 2.5, steps: int = 40) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates 3D low-poly rotating DNA double helix."""
        verts = []
        faces = []
        
        for i in range(steps):
            t = (i / steps)
            y = (t - 0.5) * height
            angle = t * turns * 2 * math.pi
            
            x1 = math.cos(angle) * radius
            z1 = math.sin(angle) * radius
            x2 = math.cos(angle + math.pi) * radius
            z2 = math.sin(angle + math.pi) * radius
            
            # Strand 1, Strand 2, and rung
            verts.extend([[x1, y, z1], [x2, y, z2]])
            
        verts = np.array(verts, dtype=float)
        for i in range(steps - 1):
            s1_a, s2_a = i * 2, i * 2 + 1
            s1_b, s2_b = (i + 1) * 2, (i + 1) * 2 + 1
            # Connect strands with low-poly ribbon
            faces.append((s1_a, s1_b, s2_a))
            faces.append((s2_a, s1_b, s2_b))
            
        return verts, faces

    def _create_quantum_nucleus(self, radius: float = 160.0) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        """Generates multifaceted atomic nucleus with orbiting rings."""
        verts, faces = self._create_icosphere(radius=radius, subdivisions=1)
        return verts, faces

    def render_frame(
        self,
        scene_type: str,
        t_normalized: float,
        accent_color_hex: str = "#00FFCC",
        caption_tag: str = "3D VISUALIZATION"
    ) -> Image.Image:
        """
        Renders a single high-definition vertical 3D frame.
        """
        # Create base background gradient
        img = Image.new("RGB", (self.width, self.height), (8, 12, 20))
        draw = ImageDraw.Draw(img)
        
        # Deep cinematic radial vignette
        top_color = (6, 9, 15)
        bot_color = (15, 20, 32)
        for y in range(0, self.height, 4):
            ratio = y / self.height
            r = int(top_color[0] + (bot_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bot_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bot_color[2] - top_color[2]) * ratio)
            draw.rectangle([(0, y), (self.width, y + 4)], fill=(r, g, b))

        # 1. Dynamic 3D starfield particles with camera flythrough
        star_z_speed = 350.0
        cur_stars = self.stars.copy()
        cur_stars[:, 2] = (cur_stars[:, 2] - t_normalized * star_z_speed) % 1600 + 100
        
        for sx, sy, sz in cur_stars:
            if sz > 50:
                px = (sx / sz) * self.fov + self.center_x
                py = (sy / sz) * self.fov + self.center_y
                if 0 <= px < self.width and 0 <= py < self.height:
                    size = max(1, int((1.0 - sz / 1700) * 4))
                    brightness = int((1.0 - sz / 1700) * 200) + 55
                    draw.ellipse([(px - size, py - size), (px + size, py + size)], fill=(brightness, brightness, brightness))

        # 2. Geometry selection based on scene type
        st = scene_type.lower()
        if "micro" in st or "bio" in st:
            verts, faces = self._create_dna_helix(height=950.0, radius=220.0, turns=2.2)
            rot_y = t_normalized * math.pi * 2.5
            rot_x = math.radians(25)
            rot_z = math.radians(15) + math.sin(t_normalized * 4) * 0.1
            cam_dist = 850.0
        elif "physics" in st or "quantum" in st:
            verts, faces = self._create_quantum_nucleus(radius=200.0)
            rot_y = t_normalized * math.pi * 3
            rot_x = math.sin(t_normalized * 3) * 0.4
            rot_z = t_normalized * 1.5
            cam_dist = 700.0
        else: # space / default
            verts, faces = self._create_icosphere(radius=240.0, subdivisions=1)
            # Add planetary rings
            r_verts, r_faces = self._create_ring(inner_r=320.0, outer_r=520.0, segments=24)
            offset = len(verts)
            verts = np.vstack([verts, r_verts])
            for f in r_faces:
                faces.append((f[0] + offset, f[1] + offset, f[2] + offset))
            rot_y = t_normalized * math.pi * 1.8
            rot_x = math.radians(28) + math.sin(t_normalized * 2) * 0.08
            rot_z = math.radians(-15)
            cam_dist = 850.0

        # Parse accent color
        hex_clean = accent_color_hex.lstrip("#")
        base_r = int(hex_clean[0:2], 16) if len(hex_clean) >= 6 else 0
        base_g = int(hex_clean[2:4], 16) if len(hex_clean) >= 6 else 255
        base_b = int(hex_clean[4:6], 16) if len(hex_clean) >= 6 else 200

        # Apply 3D rotation matrices
        cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
        cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)
        cos_z, sin_z = math.cos(rot_z), math.sin(rot_z)
        
        R_y = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
        R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
        R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])
        
        rot_matrix = R_z @ R_x @ R_y
        transformed_verts = verts @ rot_matrix.T
        
        # Camera translation along Z
        transformed_verts[:, 2] += cam_dist
        
        # Perspective projection
        z_vals = transformed_verts[:, 2]
        proj_x = (transformed_verts[:, 0] / z_vals) * self.fov + self.center_x
        proj_y = (transformed_verts[:, 1] / z_vals) * self.fov + self.center_y
        
        # Directional light source
        light_dir = np.array([0.6, -0.7, -0.4])
        light_dir = light_dir / np.linalg.norm(light_dir)
        
        # Sort faces by average depth (Painter's algorithm)
        face_depths = []
        for i, face in enumerate(faces):
            avg_z = (z_vals[face[0]] + z_vals[face[1]] + z_vals[face[2]]) / 3.0
            face_depths.append((avg_z, i))
            
        face_depths.sort(key=lambda x: x[0], reverse=True)
        
        # Render shaded 3D facets
        for _, face_idx in face_depths:
            v0_idx, v1_idx, v2_idx = faces[face_idx]
            p0 = (proj_x[v0_idx], proj_y[v0_idx])
            p1 = (proj_x[v1_idx], proj_y[v1_idx])
            p2 = (proj_x[v2_idx], proj_y[v2_idx])
            
            # 3D Normal vector
            v0 = transformed_verts[v0_idx]
            v1 = transformed_verts[v1_idx]
            v2 = transformed_verts[v2_idx]
            normal = np.cross(v1 - v0, v2 - v0)
            norm_len = np.linalg.norm(normal)
            if norm_len < 1e-6:
                continue
            normal = normal / norm_len
            
            # Backface culling
            if normal[2] > 0.15:
                continue
                
            # Diffuse lighting calculation
            diffuse = max(0.08, float(np.dot(normal, -light_dir)))
            
            # Specular rim light
            rim = pow(max(0.0, 1.0 + float(normal[2])), 2.5) * 0.4
            
            col_r = min(255, int(base_r * diffuse + 255 * rim))
            col_g = min(255, int(base_g * diffuse + 255 * rim))
            col_b = min(255, int(base_b * diffuse + 255 * rim))
            
            # Draw shaded 3D polygon
            draw.polygon([p0, p1, p2], fill=(col_r, col_g, col_b), outline=(int(col_r * 0.4), int(col_g * 0.4), int(col_b * 0.4)))

        # 3. Clean cinematic HUD telemetry brackets
        b_color = (255, 255, 255)
        margin = 60
        b_len = 35
        # Top-left
        draw.line([(margin, margin), (margin + b_len, margin)], fill=b_color, width=2)
        draw.line([(margin, margin), (margin, margin + b_len)], fill=b_color, width=2)
        # Top-right
        draw.line([(self.width - margin, margin), (self.width - margin - b_len, margin)], fill=b_color, width=2)
        draw.line([(self.width - margin, margin), (self.width - margin, margin + b_len)], fill=b_color, width=2)
        # Bottom-left
        draw.line([(margin, self.height - margin), (margin + b_len, self.height - margin)], fill=b_color, width=2)
        draw.line([(margin, self.height - margin), (margin, self.height - margin - b_len)], fill=b_color, width=2)
        # Bottom-right
        draw.line([(self.width - margin, self.height - margin), (self.width - margin - b_len, self.height - margin)], fill=b_color, width=2)
        draw.line([(self.width - margin, self.height - margin), (self.width - margin, self.height - margin - b_len)], fill=b_color, width=2)

        return img
