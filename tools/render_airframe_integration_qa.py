"""Render repeatable QA views for the corrected airframe integrations."""

from __future__ import annotations

from pathlib import Path
import os

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
    "downward-vr-camera": ((-3.10, -1.18, -1.02), (-2.41, 0.0, -0.06), 96),
    "vr-propeller-clearance": ((-3.05, -6.20, 0.15), (-3.05, 0.0, 0.19), 68),
    "radiator-intercooler-chin-inlet": ((-5.20, 0.0, 0.15), (-3.46, 0.0, 0.15), 102),
    "cooling-inlet-side-blend": ((-3.95, -2.10, 0.28), (-3.43, 0.0, 0.15), 100),
    "gimbal-fuel-and-bay": ((-4.95, -6.40, -2.20), (-1.30, -0.40, -0.40), 72),
    "gimbal-forward-third": ((-4.45, -3.85, -1.55), (-1.82, 0.0, -0.52), 82),
    "flush-drone-bay-hatch": ((-1.10, -2.05, -1.15), (-0.25, 0.0, -0.19), 98),
    "port-navigation-light": ((-3.05, 10.65, 1.42), (-1.45, 9.05, 0.62), 108),
    "starboard-navigation-light": ((-3.05, -10.65, 1.42), (-1.45, -9.05, 0.62), 108),
    "winglet-75-percent-profile": ((-2.65, -10.65, 0.66), (-1.48, -8.92, 0.40), 92),
    "wing-flap-seam-flush": ((-2.50, -6.20, 0.78), (-1.16, -4.65, 0.08), 112),
    "vertical-tail-airfoil-leading-edge": ((1.90, -2.25, 0.35), (3.13, 0.0, 0.25), 98),
    "horizontal-tail-airfoil-leading-edge": ((2.05, -3.25, 1.35), (3.30, 0.0, 0.91), 98),
    "tail-root-fillet": ((2.35, -2.15, -0.10), (3.20, 0.0, -0.36), 100),
    "fuel-tank-pylon-blends": ((-2.65, -4.35, -0.50), (-1.40, -2.68, -0.23), 96),
    "aft-fuselage": ((4.90, -7.10, 1.15), (1.80, 0.0, 0.06), 70),
    "gimbal-barrel-cleanup": ((-3.55, -2.35, -1.05), (-2.42, 0.0, -0.42), 102),
    "gimbal-muzzle-open-bore": ((-3.50, -0.13, -0.26), (-2.75, -0.01, -0.35), 110),
    "propeller-smooth-profile": ((-5.35, -2.35, 0.32), (-3.95, 0.0, 0.0), 98),
    "rotax-reduction-gearbox-cutaway": ((-4.75, -2.15, 0.82), (-3.28, 0.0, 0.36), 108),
    "rotax-916isc-starboard-detail": ((-4.30, -1.90, 0.72), (-3.20, -0.02, 0.30), 112),
    "rotax-916isc-installed-three-quarter": ((-4.65, -2.80, 1.05), (-3.20, -0.02, 0.28), 98),
    "jetson-t5000-module-detail": ((-1.35, -2.05, 0.23), (-1.35, -0.36, 0.23), 76),
    "jetson-t5000-three-quarter": ((-2.25, -1.65, 0.70), (-1.35, -0.36, 0.23), 72),
    "sta10-closed-magazine": ((-1.10, -2.05, -1.15), (-0.25, 0.0, -0.19), 98),
    "sta10-closed-topside": ((-1.05, -2.45, 1.50), (-0.28, 0.0, 0.02), 88),
    "sta10-hatch-open": ((-1.28, -2.35, -1.32), (-0.28, 0.0, -0.30), 88),
    "sta10-twin-door-clearance": ((-0.28, -0.10, -3.10), (-0.28, 0.0, -0.20), 92),
    "sta10-populated-magazine": ((-0.35, -1.38, -1.18), (-0.30, 0.0, -0.07), 104),
    "sta10-first-release": ((-1.45, -2.75, -1.65), (-0.05, -0.10, -0.50), 76),
    "sta10-two-vehicle-release": ((0.15, -5.20, -3.20), (0.45, -0.10, -0.95), 58),
    "sta10-formation-flight": ((2.85, -5.80, -2.80), (2.49, -0.32, -1.67), 66),
    "sta10-featured-homing-drone": ((2.25, -3.35, 0.05), (2.955, -2.15, -1.508), 76),
    "sta10-gear-retracted": ((-4.50, 0.0, -4.20), (-1.42, 0.0, -0.42), 72),
}
animation_frames = {
    "sta10-closed-magazine": 1,
    "sta10-closed-topside": 1,
    "sta10-hatch-open": 96,
    "sta10-twin-door-clearance": 110,
    "sta10-populated-magazine": 96,
    "sta10-first-release": 145,
    "sta10-two-vehicle-release": 205,
    "sta10-formation-flight": 275,
    "sta10-featured-homing-drone": 330,
    "sta10-gear-retracted": 58,
}
requested_labels = {
    label.strip()
    for label in os.environ.get("SKYSHIELD_QA_ONLY", "").split(",")
    if label.strip()
}
if requested_labels:
    unknown_labels = requested_labels.difference(views)
    if unknown_labels:
        raise ValueError(f"Unknown QA view labels: {sorted(unknown_labels)}")
    views = {label: view for label, view in views.items() if label in requested_labels}
for label, (location, target, lens) in views.items():
    isolated_rotax = label.startswith("rotax-")
    isolated_jetson = label.startswith("jetson-")
    for scene_object in scene.objects:
        if scene_object.type == "MESH":
            scene_object.hide_render = (
                (isolated_rotax and "Rotax 916" not in scene_object.name)
                or (isolated_jetson and "NVIDIA Jetson T5000" not in scene_object.name)
            )
    scene.frame_set(animation_frames.get(label, 1))
    drone_bay_skin = bpy.data.materials.get("Drone bay deployment skin")
    if drone_bay_skin:
        reveal_bay = label.startswith("sta10-") and animation_frames.get(label, 1) > 30
        alpha = 0.0 if reveal_bay else 1.0
        drone_bay_skin.diffuse_color[3] = alpha
        drone_bay_bsdf = drone_bay_skin.node_tree.nodes.get("Principled BSDF")
        if drone_bay_bsdf:
            drone_bay_bsdf.inputs["Base Color"].default_value[3] = alpha
            if drone_bay_bsdf.inputs.get("Alpha"):
                drone_bay_bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(drone_bay_skin, "surface_render_method"):
            drone_bay_skin.surface_render_method = "DITHERED" if reveal_bay else "DITHERED"
        for door_material_name in (
            "STA 10 physical deployment door outer",
            "STA 10 physical deployment door inner",
        ):
            door_material = bpy.data.materials.get(door_material_name)
            if not door_material:
                continue
            # Doors are opaque in the production asset and remain naturally
            # hidden below the intact outer mold line while closed.
            door_alpha = 1.0
            door_material.diffuse_color[3] = door_alpha
            door_bsdf = door_material.node_tree.nodes.get("Principled BSDF")
            if door_bsdf:
                door_bsdf.inputs["Base Color"].default_value[3] = door_alpha
                if door_bsdf.inputs.get("Alpha"):
                    door_bsdf.inputs["Alpha"].default_value = door_alpha
            if hasattr(door_material, "surface_render_method"):
                door_material.surface_render_method = "DITHERED"
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUTPUT_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)

print(f"QA renders: {OUTPUT_DIR}")
