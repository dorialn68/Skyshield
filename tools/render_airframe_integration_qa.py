"""Render repeatable QA views for the corrected airframe integrations."""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "airshield-ximango-direct-tanks-v30.glb"
OUTPUT_DIR = ROOT / "qa-airframe-v30"


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(MODEL))

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"
scene.eevee.taa_render_samples = 192
scene.eevee.use_shadows = True
scene.eevee.use_raytracing = True

world = scene.world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.028, 0.036, 0.046, 1.0)
background.inputs["Strength"].default_value = 0.40

for location, energy, size, color in (
    ((-5.0, -6.0, 7.0), 1150.0, 5.0, (0.92, 0.96, 1.0)),
    ((3.5, 5.0, 3.0), 900.0, 4.0, (0.62, 0.76, 1.0)),
    ((0.0, -2.0, -4.5), 520.0, 3.0, (0.34, 0.50, 0.72)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    look_at(light, (0.0, 0.0, -0.1))

bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.sensor_width = 36
scene.camera = camera

OUTPUT_DIR.mkdir(exist_ok=True)
views = {
    # location, target, lens
    "complete-side": ((0.0, -15.5, 2.0), (0.0, 0.0, 0.0), 58),
    "underside-integration": ((-5.4, -7.6, -3.8), (-0.45, -0.15, -0.30), 64),
    "port-main-gear": ((-3.15, -4.25, -0.82), (-1.54, -1.38, -0.76), 76),
    "main-gear-external-silhouette": ((-1.50, 4.30, -0.82), (-1.52, 1.40, -0.78), 92),
    "main-gear-inboard-wheel": ((-2.95, 0.05, -0.84), (-1.51, 1.40, -0.82), 88),
    "main-gear-front-cant": ((-4.35, -0.10, -0.72), (-1.55, 0.0, -0.72), 82),
    "ground-stance-side": ((0.0, -16.5, 0.65), (0.0, 0.0, -0.15), 62),
    "symmetric-wing-undersides": ((-4.50, 0.0, -4.20), (-1.45, 0.0, -0.25), 76),
    "port-direct-tank-contact": ((-3.40, -4.90, -1.45), (-1.35, -2.68, -0.27), 88),
    "starboard-direct-tank-contact": ((-3.40, 4.90, -1.45), (-1.35, 2.68, -0.27), 88),
    "port-clean-gear-root": ((-2.65, -3.20, -1.30), (-1.62, -1.29, -0.30), 94),
    "starboard-clean-gear-root": ((-2.65, 3.20, -1.30), (-1.62, 1.29, -0.30), 94),
    "forward-vr-camera": ((-3.72, -0.82, -0.42), (-2.60, 0.0, -0.15), 94),
    "gimbal-fuel-and-bay": ((-4.95, -6.40, -2.20), (-1.30, -0.40, -0.40), 72),
    "gimbal-forward-third": ((-4.45, -3.85, -1.55), (-1.82, 0.0, -0.52), 82),
    "drone-bay-hatch-seam": ((-1.20, -2.20, -1.25), (-0.28, 0.0, -0.23), 94),
    "port-navigation-light": ((-3.30, 10.70, 1.70), (-1.46, 8.98, 0.75), 105),
    "starboard-navigation-light": ((-3.30, -10.70, 1.70), (-1.46, -8.98, 0.75), 105),
    "aft-fuselage": ((4.90, -7.10, 1.15), (1.80, 0.0, 0.06), 70),
    "gimbal-barrel-cleanup": ((-3.55, -2.35, -1.05), (-2.42, 0.0, -0.42), 102),
    "propeller-smooth-profile": ((-5.35, -2.35, 0.32), (-3.95, 0.0, 0.0), 98),
}
for label, (location, target, lens) in views.items():
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUTPUT_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)

print(f"QA renders: {OUTPUT_DIR}")
