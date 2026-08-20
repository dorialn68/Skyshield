"""Render repeatable close-up QA views of the exported kinetic gimbal."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "airshield-ximango-integration-corrections-v26.glb"
OUTPUT_DIR = ROOT / "qa-gimbal-v26"


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(MODEL))

for obj in bpy.context.scene.objects:
    if obj.type == "MESH" and "gimbal" not in obj.name.lower():
        obj.hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 1000
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
background.inputs["Color"].default_value = (0.030, 0.040, 0.052, 1.0)
background.inputs["Strength"].default_value = 0.32

for location, energy, size, color in (
    ((-3.0, -3.0, 2.0), 850.0, 3.5, (0.88, 0.94, 1.0)),
    ((1.0, 2.5, 1.2), 620.0, 3.0, (0.62, 0.74, 1.0)),
    ((-0.5, 0.0, -2.5), 330.0, 2.5, (0.30, 0.48, 0.72)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    look_at(light, (-1.32, -0.12, -0.61))

bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.lens = 72
camera.data.sensor_width = 36
scene.camera = camera

OUTPUT_DIR.mkdir(exist_ok=True)
views = {
    "front-three-quarter": (-3.39, -1.78, -0.12),
    "front": (-3.69, -0.12, -0.25),
    "starboard": (-1.06, 2.65, -0.20),
}
for label, location in views.items():
    camera.location = location
    look_at(camera, (-1.36, -0.12, -0.61))
    scene.render.filepath = str(OUTPUT_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)

print(f"QA renders: {OUTPUT_DIR}")
