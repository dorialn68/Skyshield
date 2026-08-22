"""Build the AirShield AI.onSuper concept aircraft as a reusable GLB and hero render.

The geometry is intentionally parametric and based on the overall proportions of
the AMT-200 Super Ximango reference airframe:
  span 17.47 m, length 8.08 m, 18.70 m² NACA 64(3)-618 wing, T-tail,
  2.80 m main-gear track and 5.35 m main-to-tail-wheel axis spacing.

It is a visualization model, not manufacturing or airworthiness geometry.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_GLB = ROOT / "airshield-ximango-direct-tanks-v30.glb"
OUTPUT_RENDER = ROOT / "airshield-xmango-hero-v30.jpg"
TEXTURE_DIR = ROOT / "textures"
SKIN_IMAGEGEN_SOURCE = TEXTURE_DIR / "airshield_skin_imagegen_source_v2.png"
GIMBAL_IMAGEGEN_SOURCE = TEXTURE_DIR / "airshield_gimbal_imagegen_source_v2.png"
ROTAX_IMAGEGEN_SOURCE = TEXTURE_DIR / "airshield_rotax_cast_aluminum_source_v1.png"

EXPORT_OBJECTS: list[bpy.types.Object] = []


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        pass


def material(
    name: str,
    color: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.45,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


IAF_GRAY = material("IAF ghost-gray composite skin", (0.37, 0.39, 0.405, 1.0), 0.02, 0.48)
ENGINE_COWLING = material("Engine cutaway cowling", (0.37, 0.39, 0.405, 1.0), 0.02, 0.48)
MISSION_COMPUTER_SKIN = material("Mission computer cutaway skin", (0.37, 0.39, 0.405, 1.0), 0.02, 0.48)
DRONE_BAY_SKIN = material("Drone bay deployment skin", (0.37, 0.39, 0.405, 1.0), 0.02, 0.48)
STA10_DOOR_OUTER = material("STA 10 physical deployment door outer", (0.37, 0.39, 0.405, 1.0), 0.02, 0.48)
STA10_DOOR_INNER = material("STA 10 physical deployment door inner", (0.004, 0.007, 0.009, 1.0), 0.04, 0.84)
# The two physical doors are exported opaque.  Their closed geometry is seated
# below the intact fuselage outer mold line, which hides them naturally without
# making their visibility dependent on a browser-side material animation.
HARDWARE_GRAY = material("Dark gray external hardware", (0.22, 0.235, 0.24, 1.0), 0.02, 0.34)
GRAPHITE = material("Graphite", (0.035, 0.045, 0.052, 1.0), 0.28, 0.28)
GIMBAL_ALLOY = material("Bead-blasted kinetic gimbal alloy", (0.31, 0.33, 0.34, 1.0), 0.68, 0.32)
CARBON = material("Carbon fiber propeller", (0.025, 0.032, 0.036, 1.0), 0.16, 0.30)
PROP_WHITE = material("White propeller polyurethane", (0.72, 0.74, 0.75, 1.0), 0.02, 0.34)
RUBBER = material("Tire rubber", (0.012, 0.014, 0.016, 1.0), 0.0, 0.72)
LENS = material("Sensor glass", (0.015, 0.055, 0.075, 1.0), 0.38, 0.08)
LENS_DARK = material("Low-light sensor glass", (0.004, 0.009, 0.012, 1.0), 0.16, 0.07)
LENS_IR = material("IR germanium sensor glass", (0.004, 0.026, 0.020, 1.0), 0.22, 0.09)
OPTICAL_VOID = material("Recessed optical and vent void", (0.0015, 0.0020, 0.0025, 1.0), 0.0, 0.82)
BORE_VOID = material("Non-reflective barrel bore", (0.00005, 0.00005, 0.00005, 1.0), 0.0, 1.0)
_bore_bsdf = BORE_VOID.node_tree.nodes.get("Principled BSDF")
if _bore_bsdf and _bore_bsdf.inputs.get("Specular IOR Level"):
    _bore_bsdf.inputs["Specular IOR Level"].default_value = 0.0
STEEL = material("Mechanism steel", (0.18, 0.20, 0.21, 1.0), 0.72, 0.24)
ALLOY = material("Machined wheel alloy", (0.34, 0.355, 0.36, 1.0), 0.78, 0.20)
RAIL = material("Empty launch rail anodized alloy", (0.075, 0.083, 0.086, 1.0), 0.62, 0.30)
SEAM = material("Composite panel seam", (0.055, 0.062, 0.064, 1.0), 0.04, 0.58)
ROTAX_ALLOY = material("Rotax 916 engine alloy", (0.235, 0.255, 0.265, 1.0), 0.72, 0.25)
ROTAX_DARK = material("Rotax 916 engine dark hardware", (0.035, 0.045, 0.050, 1.0), 0.38, 0.30)
ROTAX_HEAD = material("Rotax 916 cylinder-head finish", (0.105, 0.115, 0.118, 1.0), 0.60, 0.24)
ROTAX_TURBO = material("Rotax 916 turbocharger", (0.30, 0.235, 0.165, 1.0), 0.76, 0.26)
ROTAX_STEEL = material("Rotax 916 brushed stainless hardware", (0.28, 0.30, 0.31, 1.0), 0.90, 0.20)
ROTAX_RUBBER = material("Rotax 916 reinforced hose rubber", (0.012, 0.016, 0.018, 1.0), 0.0, 0.70)
ROTAX_ACCENT = material("Rotax 916 service accent", (0.42, 0.065, 0.025, 1.0), 0.12, 0.36)
ROTAX_COVER = material("Rotax 916 pearl-gray branded covers", (0.63, 0.66, 0.67, 1.0), 0.44, 0.22)
ROTAX_LABEL = material("Rotax 916 recessed cover lettering", (0.095, 0.105, 0.108, 1.0), 0.32, 0.30)
ROTAX_HEAT_WRAP = material("Rotax 916 exhaust heat wrap", (0.30, 0.285, 0.255, 1.0), 0.08, 0.84)
JETSON_PCB = material("NVIDIA Jetson T5000 matte black PCB", (0.012, 0.018, 0.019, 1.0), 0.16, 0.42)
JETSON_PACKAGE = material("NVIDIA Jetson T5000 Blackwell package", (0.035, 0.040, 0.042, 1.0), 0.42, 0.24)
JETSON_DIE = material("NVIDIA Jetson T5000 exposed Blackwell die", (0.075, 0.34, 0.15, 1.0), 0.30, 0.12)
JETSON_MEMORY = material("NVIDIA Jetson T5000 LPDDR5X packages", (0.022, 0.025, 0.027, 1.0), 0.18, 0.34)
JETSON_CONTACT = material("NVIDIA Jetson T5000 gold contacts", (0.55, 0.31, 0.055, 1.0), 0.88, 0.18)
JETSON_HEATSINK = material("NVIDIA Jetson T5000 black finned heatsink", (0.018, 0.022, 0.024, 1.0), 0.66, 0.27)
JETSON_CARRIER = material("NVIDIA Jetson T5000 aerospace carrier", (0.105, 0.118, 0.122, 1.0), 0.58, 0.30)
JETSON_CONNECTOR = material("NVIDIA Jetson T5000 carrier connectors", (0.018, 0.022, 0.024, 1.0), 0.08, 0.44)
JETSON_LABEL = material("NVIDIA Jetson T5000 white identification", (0.78, 0.82, 0.83, 1.0), 0.12, 0.28)
JETSON_GREEN = material("NVIDIA Jetson T5000 green identification", (0.16, 0.58, 0.045, 1.0), 0.05, 0.24)
DRONE_BAY_VOID = material("STA 10 drone bay non-reflective interior", (0.004, 0.007, 0.009, 1.0), 0.04, 0.84)
DRONE_RACK = material("STA 10 drone magazine anodized rack", (0.075, 0.085, 0.090, 1.0), 0.64, 0.29)
DRONE_BAY_LIGHT = material("STA 10 magazine low-level guide light", (0.015, 0.16, 0.19, 1.0), 0.0, 0.22)
POINT_BLANK_BODY = material("STA 10 Point Blank warm composite body", (0.68, 0.63, 0.50, 1.0), 0.02, 0.44)
POINT_BLANK_DARK = material("STA 10 Point Blank dark motor mechanisms", (0.012, 0.017, 0.020, 1.0), 0.30, 0.28)
POINT_BLANK_BLADE = material("STA 10 Point Blank propeller blades", (0.11, 0.13, 0.14, 1.0), 0.14, 0.34)
POINT_BLANK_RED = material("STA 10 Point Blank red safety marking", (0.56, 0.025, 0.012, 1.0), 0.06, 0.30)
POINT_BLANK_PAYLOAD = material("STA 10 Point Blank external mission payload shell", (0.52, 0.48, 0.37, 1.0), 0.08, 0.38)
POINT_BLANK_MOTOR_BAND = material("STA 10 Point Blank motor identification bands", (0.34, 0.36, 0.36, 1.0), 0.72, 0.22)
_drone_bay_light_bsdf = DRONE_BAY_LIGHT.node_tree.nodes.get("Principled BSDF")
if _drone_bay_light_bsdf:
    _drone_bay_light_emission = _drone_bay_light_bsdf.inputs.get("Emission Color") or _drone_bay_light_bsdf.inputs.get("Emission")
    _drone_bay_light_strength = _drone_bay_light_bsdf.inputs.get("Emission Strength")
    if _drone_bay_light_emission:
        _drone_bay_light_emission.default_value = (0.025, 0.54, 0.66, 1.0)
    if _drone_bay_light_strength:
        _drone_bay_light_strength.default_value = 1.35
NAV_RED = material("Port navigation lens", (0.46, 0.004, 0.003, 1.0), 0.0, 0.14)
NAV_GREEN = material("Starboard navigation lens", (0.003, 0.42, 0.045, 1.0), 0.0, 0.14)
NAV_WHITE = material("Aft navigation lens", (0.72, 0.76, 0.78, 1.0), 0.0, 0.12)
for navigation_material, emission_color in (
    (NAV_RED, (1.0, 0.002, 0.001, 1.0)),
    (NAV_GREEN, (0.002, 1.0, 0.028, 1.0)),
    (NAV_WHITE, (1.0, 1.0, 1.0, 1.0)),
):
    navigation_bsdf = navigation_material.node_tree.nodes.get("Principled BSDF")
    if navigation_bsdf:
        emission_socket = navigation_bsdf.inputs.get("Emission Color") or navigation_bsdf.inputs.get("Emission")
        strength_socket = navigation_bsdf.inputs.get("Emission Strength")
        if emission_socket:
            emission_socket.default_value = emission_color
        if strength_socket:
            strength_socket.default_value = 4.0
CONCRETE = material("Concrete", (0.24, 0.26, 0.27, 1.0), 0.0, 0.84)
HANGAR = material("Hangar", (0.075, 0.09, 0.10, 1.0), 0.15, 0.58)


def set_bsdf_input(bsdf: bpy.types.Node, name: str, value: float | tuple[float, ...]) -> None:
    socket = bsdf.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def write_texture(name: str, pixels: np.ndarray, colorspace: str) -> bpy.types.Image:
    """Persist a generated texture so Blender and the exported GLB share it."""
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    height, width = pixels.shape[:2]
    image = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=False)
    image.colorspace_settings.name = colorspace
    image.filepath_raw = str(TEXTURE_DIR / f"{name}.png")
    image.file_format = "PNG"
    image.pixels.foreach_set(np.ascontiguousarray(pixels, dtype=np.float32).ravel())
    image.save()
    return image


def rgba_from_rgb(rgb: np.ndarray) -> np.ndarray:
    alpha = np.ones((*rgb.shape[:2], 1), dtype=np.float32)
    return np.concatenate((rgb.astype(np.float32), alpha), axis=2)


def rgba_from_gray(gray: np.ndarray) -> np.ndarray:
    rgb = np.repeat(gray[..., None], 3, axis=2)
    return rgba_from_rgb(rgb)


def normal_map_from_height(height: np.ndarray, strength: float) -> np.ndarray:
    gradient_y, gradient_x = np.gradient(height)
    normal = np.dstack((-gradient_x * strength, -gradient_y * strength, np.ones_like(height)))
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    encoded = normal * 0.5 + 0.5
    return rgba_from_rgb(encoded)


def seamless_imagegen_source(path: Path, size: int) -> np.ndarray:
    """Load an image-generated material scan and make its repeat mathematically exact.

    Image generation supplies the natural micro-variation. A mirrored 2x2
    construction guarantees identical opposite edges without blurring away the
    useful paint grain, so WebGL repeat sampling cannot expose a UV seam.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing image-generated material source: {path}")
    half = size // 2
    source = bpy.data.images.load(str(path), check_existing=True)
    source.colorspace_settings.name = "sRGB"
    source.scale(half, half)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape((half, half, 4))[..., :3]
    top = np.concatenate((pixels, np.flip(pixels, axis=1)), axis=1)
    return np.concatenate((top, np.flip(top, axis=0)), axis=0)


def wrapped_low_pass(field: np.ndarray, steps: tuple[int, ...]) -> np.ndarray:
    """Small periodic blur used to separate material grain from broad tone."""
    result = field.astype(np.float32, copy=True)
    for step in steps:
        result = (
            result
            + np.roll(result, step, axis=0)
            + np.roll(result, -step, axis=0)
            + np.roll(result, step, axis=1)
            + np.roll(result, -step, axis=1)
        ) / 5.0
    return result


def normalized_field(field: np.ndarray, limit: float = 3.0) -> np.ndarray:
    centered = field - float(field.mean())
    return np.clip(centered / max(float(centered.std()), 1e-6), -limit, limit)


def textured_principled_material(
    mat: bpy.types.Material,
    base_image: bpy.types.Image,
    roughness_image: bpy.types.Image,
    normal_image: bpy.types.Image,
    *,
    metallic: float,
    normal_strength: float,
    coat_weight: float,
    coat_roughness: float,
) -> None:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    set_bsdf_input(bsdf, "Metallic", metallic)
    set_bsdf_input(bsdf, "Coat Weight", coat_weight)
    set_bsdf_input(bsdf, "Coat Roughness", coat_roughness)
    set_bsdf_input(bsdf, "IOR", 1.46)
    set_bsdf_input(bsdf, "Specular IOR Level", 0.34)

    base = nodes.new("ShaderNodeTexImage")
    base.name = f"{mat.name} base color"
    base.image = base_image
    base.interpolation = "Linear"
    base.extension = "REPEAT"
    links.new(base.outputs["Color"], bsdf.inputs["Base Color"])

    roughness = nodes.new("ShaderNodeTexImage")
    roughness.name = f"{mat.name} roughness"
    roughness.image = roughness_image
    roughness.interpolation = "Linear"
    roughness.extension = "REPEAT"
    links.new(roughness.outputs["Color"], bsdf.inputs["Roughness"])

    normal_texture = nodes.new("ShaderNodeTexImage")
    normal_texture.name = f"{mat.name} normal"
    normal_texture.image = normal_image
    normal_texture.interpolation = "Linear"
    normal_texture.extension = "REPEAT"
    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = f"{mat.name} normal conversion"
    normal.inputs["Strength"].default_value = normal_strength
    links.new(normal_texture.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])


def attach_gltf_occlusion(mat: bpy.types.Material, image: bpy.types.Image) -> None:
    """Expose a micro-cavity map to glTF real-time viewers as ambient occlusion."""
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        group.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        group.nodes.new("NodeGroupInput")

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    occlusion = nodes.new("ShaderNodeTexImage")
    occlusion.name = f"{mat.name} micro-cavity occlusion"
    occlusion.image = image
    occlusion.interpolation = "Linear"
    occlusion.extension = "REPEAT"
    output = nodes.new("ShaderNodeGroup")
    output.name = "glTF Material Output"
    output.node_tree = group
    links.new(occlusion.outputs["Color"], output.inputs["Occlusion"])


def build_pbr_materials() -> None:
    """Build portable PBR maps from image-generated, lighting-neutral sources."""

    # A 2K authored surface holds up during investor-presentation close-ups.
    # The HDR environments remain 1K because model-viewer clamps lighting
    # environments internally; geometric and material detail belong here.
    size = 2048
    skin_source = seamless_imagegen_source(SKIN_IMAGEGEN_SOURCE, size)
    skin_luma = (
        skin_source[..., 0] * 0.2126
        + skin_source[..., 1] * 0.7152
        + skin_source[..., 2] * 0.0722
    )
    # Remove broad image-generation tone before deriving maps. Only the
    # coating-scale high-frequency grain is allowed onto the aircraft; broad
    # clouds or streaks become implausible bands once repeated along a fuselage.
    skin_blur = wrapped_low_pass(skin_luma, (1, 1, 2, 2, 4, 4, 8, 8, 16, 32))
    skin_micro = normalized_field(skin_luma - skin_blur, limit=2.5)
    skin_rgb = np.clip(
        np.array([0.335, 0.355, 0.370], dtype=np.float32)[None, None, :]
        + skin_micro[..., None] * 0.0025,
        0.0,
        1.0,
    )
    skin_roughness = np.clip(0.53 + skin_micro * 0.018, 0.47, 0.59)
    skin_height = skin_micro * 0.016
    skin_occlusion = np.clip(0.996 - np.maximum(-skin_micro, 0.0) * 0.004, 0.98, 1.0)

    skin_base = write_texture("airshield_skin_basecolor", rgba_from_rgb(skin_rgb), "sRGB")
    skin_rough = write_texture("airshield_skin_roughness", rgba_from_gray(skin_roughness), "Non-Color")
    skin_normal = write_texture(
        "airshield_skin_normal",
        normal_map_from_height(skin_height, 2.8),
        "Non-Color",
    )
    skin_ao = write_texture(
        "airshield_skin_occlusion",
        rgba_from_gray(skin_occlusion),
        "Non-Color",
    )
    for skin_material in (IAF_GRAY, ENGINE_COWLING, MISSION_COMPUTER_SKIN, DRONE_BAY_SKIN, STA10_DOOR_OUTER):
        textured_principled_material(
            skin_material,
            skin_base,
            skin_rough,
            skin_normal,
            metallic=0.015,
            normal_strength=0.28,
            coat_weight=0.12,
            coat_roughness=0.40,
        )
        attach_gltf_occlusion(skin_material, skin_ao)

    # The EO/IR ball, stabilized weapon housing and axle caps share a dark,
    # fine-grain aerospace coating derived from a second image-generated scan.
    gimbal_size = 1024
    gimbal_source = seamless_imagegen_source(GIMBAL_IMAGEGEN_SOURCE, gimbal_size)
    gimbal_luma = (
        gimbal_source[..., 0] * 0.2126
        + gimbal_source[..., 1] * 0.7152
        + gimbal_source[..., 2] * 0.0722
    )
    gimbal_low = wrapped_low_pass(gimbal_luma, (1, 2, 4, 8, 16))
    gimbal_micro = normalized_field(gimbal_luma - wrapped_low_pass(gimbal_luma, (1, 2)))
    gimbal_macro = normalized_field(gimbal_low)
    gimbal_chroma = gimbal_source - gimbal_luma[..., None]
    gimbal_rgb = np.clip(
        np.array([0.032, 0.038, 0.042], dtype=np.float32)[None, None, :]
        + gimbal_macro[..., None] * 0.008
        + gimbal_micro[..., None] * 0.004
        + gimbal_chroma * 0.040,
        0.0,
        1.0,
    )
    gimbal_roughness = np.clip(0.31 + gimbal_macro * 0.018 + gimbal_micro * 0.035, 0.22, 0.45)
    gimbal_height = gimbal_macro * 0.006 + gimbal_micro * 0.026
    gimbal_occlusion = np.clip(0.985 - np.maximum(-gimbal_micro, 0.0) * 0.016, 0.93, 1.0)
    gimbal_base = write_texture("airshield_gimbal_basecolor", rgba_from_rgb(gimbal_rgb), "sRGB")
    gimbal_rough = write_texture(
        "airshield_gimbal_roughness",
        rgba_from_gray(gimbal_roughness),
        "Non-Color",
    )
    gimbal_normal = write_texture(
        "airshield_gimbal_normal",
        normal_map_from_height(gimbal_height, 3.8),
        "Non-Color",
    )
    gimbal_ao = write_texture(
        "airshield_gimbal_occlusion",
        rgba_from_gray(gimbal_occlusion),
        "Non-Color",
    )
    textured_principled_material(
        GRAPHITE,
        gimbal_base,
        gimbal_rough,
        gimbal_normal,
        metallic=0.30,
        normal_strength=0.18,
        coat_weight=0.18,
        coat_roughness=0.24,
    )
    attach_gltf_occlusion(GRAPHITE, gimbal_ao)

    # A separate calibrated alloy response uses the same authored microfinish
    # while preserving the lighter bead-blasted receiver and yoke seen in the
    # kinetic-gimbal reference. This avoids a flat single-material assembly.
    gimbal_alloy_rgb = np.clip(
        np.array([0.385, 0.400, 0.410], dtype=np.float32)[None, None, :]
        + gimbal_macro[..., None] * 0.014
        + gimbal_micro[..., None] * 0.0025
        + gimbal_chroma * 0.025,
        0.0,
        1.0,
    )
    gimbal_alloy_roughness = np.clip(0.34 + gimbal_macro * 0.022 + gimbal_micro * 0.028, 0.26, 0.44)
    gimbal_alloy_base = write_texture(
        "airshield_gimbal_alloy_basecolor",
        rgba_from_rgb(gimbal_alloy_rgb),
        "sRGB",
    )
    gimbal_alloy_rough = write_texture(
        "airshield_gimbal_alloy_roughness",
        rgba_from_gray(gimbal_alloy_roughness),
        "Non-Color",
    )
    textured_principled_material(
        GIMBAL_ALLOY,
        gimbal_alloy_base,
        gimbal_alloy_rough,
        gimbal_normal,
        metallic=0.48,
        normal_strength=0.15,
        coat_weight=0.10,
        coat_roughness=0.30,
    )
    attach_gltf_occlusion(GIMBAL_ALLOY, gimbal_ao)

    # A dedicated 1K cast-aluminum scan gives the exposed Rotax installation
    # its own micro-scale response. The same measured-looking grain is tinted
    # and calibrated per engine material, so the crankcase, black heads and
    # turbo read as separate manufactured finishes instead of uniform blocks.
    rotax_size = 1024
    rotax_source = seamless_imagegen_source(ROTAX_IMAGEGEN_SOURCE, rotax_size)
    rotax_luma = (
        rotax_source[..., 0] * 0.2126
        + rotax_source[..., 1] * 0.7152
        + rotax_source[..., 2] * 0.0722
    )
    rotax_low = wrapped_low_pass(rotax_luma, (1, 2, 4, 8, 16, 32))
    rotax_micro = normalized_field(rotax_luma - wrapped_low_pass(rotax_luma, (1, 2, 4)), limit=2.4)
    rotax_macro = normalized_field(rotax_low, limit=2.0)
    rotax_height = rotax_macro * 0.004 + rotax_micro * 0.022
    rotax_occlusion = np.clip(0.982 - np.maximum(-rotax_micro, 0.0) * 0.020, 0.90, 1.0)
    rotax_normal = write_texture(
        "airshield_rotax_cast_normal",
        normal_map_from_height(rotax_height, 4.2),
        "Non-Color",
    )
    rotax_ao = write_texture(
        "airshield_rotax_cast_occlusion",
        rgba_from_gray(rotax_occlusion),
        "Non-Color",
    )

    rotax_material_profiles = (
        (
            ROTAX_ALLOY,
            "alloy",
            np.array([0.34, 0.36, 0.37], dtype=np.float32),
            0.47,
            0.72,
            0.28,
            0.08,
        ),
        (
            ROTAX_HEAD,
            "head",
            np.array([0.095, 0.105, 0.108], dtype=np.float32),
            0.41,
            0.58,
            0.23,
            0.12,
        ),
        (
            ROTAX_DARK,
            "dark_hardware",
            np.array([0.030, 0.038, 0.042], dtype=np.float32),
            0.34,
            0.38,
            0.18,
            0.16,
        ),
        (
            ROTAX_TURBO,
            "turbo",
            np.array([0.255, 0.190, 0.125], dtype=np.float32),
            0.39,
            0.78,
            0.22,
            0.05,
        ),
    )
    for engine_material, suffix, color, roughness_center, metallic, normal_strength, coat_weight in rotax_material_profiles:
        engine_rgb = np.clip(
            color[None, None, :]
            + rotax_macro[..., None] * 0.012
            + rotax_micro[..., None] * 0.008,
            0.0,
            1.0,
        )
        engine_roughness = np.clip(
            roughness_center + rotax_macro * 0.018 + rotax_micro * 0.028,
            0.18,
            0.72,
        )
        engine_base = write_texture(
            f"airshield_rotax_{suffix}_basecolor",
            rgba_from_rgb(engine_rgb),
            "sRGB",
        )
        engine_rough = write_texture(
            f"airshield_rotax_{suffix}_roughness",
            rgba_from_gray(engine_roughness),
            "Non-Color",
        )
        textured_principled_material(
            engine_material,
            engine_base,
            engine_rough,
            rotax_normal,
            metallic=metallic,
            normal_strength=normal_strength,
            coat_weight=coat_weight,
            coat_roughness=0.30,
        )
        attach_gltf_occlusion(engine_material, rotax_ao)

    rotax_steel_bsdf = ROTAX_STEEL.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(rotax_steel_bsdf, "Metallic", 0.82)
    set_bsdf_input(rotax_steel_bsdf, "Roughness", 0.28)
    set_bsdf_input(rotax_steel_bsdf, "Anisotropic", 0.24)
    set_bsdf_input(rotax_steel_bsdf, "Coat Weight", 0.06)

    rotax_rubber_bsdf = ROTAX_RUBBER.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(rotax_rubber_bsdf, "Roughness", 0.78)
    set_bsdf_input(rotax_rubber_bsdf, "Specular IOR Level", 0.20)

    rotax_accent_bsdf = ROTAX_ACCENT.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(rotax_accent_bsdf, "Coat Weight", 0.28)
    set_bsdf_input(rotax_accent_bsdf, "Coat Roughness", 0.24)

    carbon_size = 1024
    cy, cx = np.mgrid[0:carbon_size, 0:carbon_size].astype(np.float32) / float(carbon_size)
    warp = np.sin(2.0 * math.pi * (cx + cy) * 52.0)
    weft = np.sin(2.0 * math.pi * (cx - cy) * 52.0)
    weave = 0.5 + 0.5 * warp * weft
    carbon_rgb = np.repeat((0.040 + weave * 0.045)[..., None], 3, axis=2)
    carbon_rgb[..., 2] *= 1.08
    carbon_roughness = np.clip(0.24 + (1.0 - weave) * 0.12, 0.20, 0.40)
    carbon_height = (warp * weft) * 0.06
    carbon_occlusion = np.clip(0.90 + weave * 0.10, 0.88, 1.0)
    carbon_base = write_texture("airshield_carbon_basecolor", rgba_from_rgb(carbon_rgb), "sRGB")
    carbon_rough = write_texture("airshield_carbon_roughness", rgba_from_gray(carbon_roughness), "Non-Color")
    carbon_normal = write_texture(
        "airshield_carbon_normal",
        normal_map_from_height(carbon_height, 4.5),
        "Non-Color",
    )
    carbon_ao = write_texture(
        "airshield_carbon_occlusion",
        rgba_from_gray(carbon_occlusion),
        "Non-Color",
    )
    textured_principled_material(
        CARBON,
        carbon_base,
        carbon_rough,
        carbon_normal,
        metallic=0.16,
        normal_strength=0.32,
        coat_weight=0.46,
        coat_roughness=0.18,
    )
    attach_gltf_occlusion(CARBON, carbon_ao)

    hardware_bsdf = HARDWARE_GRAY.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(hardware_bsdf, "Metallic", 0.02)
    set_bsdf_input(hardware_bsdf, "Transmission Weight", 0.0)
    set_bsdf_input(hardware_bsdf, "Coat Weight", 0.20)
    set_bsdf_input(hardware_bsdf, "Coat Roughness", 0.28)
    set_bsdf_input(hardware_bsdf, "Specular IOR Level", 0.32)
    set_bsdf_input(hardware_bsdf, "IOR", 1.47)

    steel_bsdf = STEEL.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(steel_bsdf, "Metallic", 0.88)
    set_bsdf_input(steel_bsdf, "Roughness", 0.20)
    set_bsdf_input(steel_bsdf, "Anisotropic", 0.22)

    rail_bsdf = RAIL.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(rail_bsdf, "Metallic", 0.70)
    set_bsdf_input(rail_bsdf, "Roughness", 0.28)
    set_bsdf_input(rail_bsdf, "Anisotropic", 0.18)
    set_bsdf_input(rail_bsdf, "Coat Weight", 0.12)

    rubber_bsdf = RUBBER.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(rubber_bsdf, "Roughness", 0.76)
    set_bsdf_input(rubber_bsdf, "Specular IOR Level", 0.22)

    lens_bsdf = LENS.node_tree.nodes.get("Principled BSDF")
    set_bsdf_input(lens_bsdf, "Metallic", 0.06)
    set_bsdf_input(lens_bsdf, "Roughness", 0.055)
    set_bsdf_input(lens_bsdf, "Transmission Weight", 0.28)
    set_bsdf_input(lens_bsdf, "Coat Weight", 1.0)
    set_bsdf_input(lens_bsdf, "Coat Roughness", 0.04)
    set_bsdf_input(lens_bsdf, "IOR", 1.48)

    for nav_material, color in (
        (NAV_RED, (0.62, 0.01, 0.006, 1.0)),
        (NAV_GREEN, (0.006, 0.55, 0.08, 1.0)),
        (NAV_WHITE, (0.82, 0.88, 0.90, 1.0)),
    ):
        nav_bsdf = nav_material.node_tree.nodes.get("Principled BSDF")
        set_bsdf_input(nav_bsdf, "Coat Weight", 1.0)
        set_bsdf_input(nav_bsdf, "Coat Roughness", 0.035)
        set_bsdf_input(nav_bsdf, "Emission Color", color)
        set_bsdf_input(nav_bsdf, "Emission Strength", 1.8)

    # Render-only concrete variation gives the aircraft a believable scale and
    # prevents the apron from reading as an infinite studio cyclorama.
    concrete_nodes = CONCRETE.node_tree.nodes
    concrete_links = CONCRETE.node_tree.links
    concrete_bsdf = concrete_nodes.get("Principled BSDF")
    noise = concrete_nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 7.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = concrete_nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (0.16, 0.18, 0.19, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.34, 0.36, 0.36, 1.0)
    bump = concrete_nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.055
    concrete_links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    concrete_links.new(ramp.outputs["Color"], concrete_bsdf.inputs["Base Color"])
    concrete_links.new(noise.outputs["Fac"], bump.inputs["Height"])
    concrete_links.new(bump.outputs["Normal"], concrete_bsdf.inputs["Normal"])


def assign(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    if hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    return obj


def mark_export(obj: bpy.types.Object) -> bpy.types.Object:
    EXPORT_OBJECTS.append(obj)
    return obj


def union_into_airframe(
    target: bpy.types.Object,
    addition: bpy.types.Object,
    modifier_name: str,
) -> bpy.types.Object:
    """Fuse an intersecting aerodynamic mount into its parent airframe mesh."""
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    union = target.modifiers.new(modifier_name, "BOOLEAN")
    union.operation = "UNION"
    union.solver = "EXACT"
    union.object = addition

    # Keep any finishing bevel after the structural union in the stack so the
    # resulting junction remains a radiused production surface.
    while target.modifiers.find(union.name) > 0:
        bpy.ops.object.modifier_move_up(modifier=union.name)
    bpy.ops.object.modifier_apply(modifier=union.name)

    if addition in EXPORT_OBJECTS:
        EXPORT_OBJECTS.remove(addition)
    bpy.data.objects.remove(addition, do_unlink=True)
    return target


def cut_from_hard_surface(
    target: bpy.types.Object,
    cutter: bpy.types.Object,
    modifier_name: str,
    before_finish: bool = False,
) -> bpy.types.Object:
    """Apply a deterministic exterior recess and discard its cutter mesh."""
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    cut = target.modifiers.new(modifier_name, "BOOLEAN")
    cut.operation = "DIFFERENCE"
    cut.solver = "EXACT"
    cut.object = cutter
    if before_finish:
        # Cut the raw shell first and leave its existing manufacturing bevel
        # after the Boolean. This rounds the new opening inward instead of
        # creating an applied external lip or evaluating the cut after finish.
        while target.modifiers.find(cut.name) > 0:
            bpy.ops.object.modifier_move_up(modifier=cut.name)
    bpy.ops.object.modifier_apply(modifier=cut.name)
    if cutter in EXPORT_OBJECTS:
        EXPORT_OBJECTS.remove(cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def bevel(obj: bpy.types.Object, width: float, segments: int = 3) -> bpy.types.Object:
    modifier = obj.modifiers.new("Manufacturing edge radius", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    return obj


def smooth(obj: bpy.types.Object) -> bpy.types.Object:
    if hasattr(obj.data, "polygons"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def cube(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    edge: float = 0.0,
    export: bool = True,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if edge:
        bevel(obj, edge)
    if export:
        mark_export(obj)
    return obj


def cylinder_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    vertices: int = 24,
    export: bool = True,
) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    delta = b - a
    midpoint = (a + b) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, mat)
    smooth(obj)
    if export:
        mark_export(obj)
    return obj


def curved_tube(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    mat: bpy.types.Material,
    resolution: int = 4,
) -> bpy.types.Object:
    """Create a smooth presentation tube through a small set of control points."""
    curve_data = bpy.data.curves.new(f"{name} path", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = resolution
    curve_data.fill_mode = "FULL"
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bezier_point, coordinate in zip(spline.bezier_points, points):
        bezier_point.co = coordinate
        bezier_point.handle_left_type = "AUTO"
        bezier_point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    smooth(obj)
    mark_export(obj)
    return obj


def chamfered_xz_cover(
    name: str,
    center: tuple[float, float, float],
    half_size: tuple[float, float, float],
    mat: bpy.types.Material,
    edge: float = 0.010,
) -> bpy.types.Object:
    """Build an eight-corner cover plate extruded along Y."""
    center_x, center_y, center_z = center
    half_x, half_y, half_z = half_size
    outline = (
        (-0.64 * half_x, -half_z),
        (0.64 * half_x, -half_z),
        (half_x, -0.68 * half_z),
        (half_x, 0.64 * half_z),
        (0.66 * half_x, half_z),
        (-0.66 * half_x, half_z),
        (-half_x, 0.64 * half_z),
        (-half_x, -0.68 * half_z),
    )
    vertices: list[tuple[float, float, float]] = []
    for y_offset in (-half_y, half_y):
        vertices.extend((center_x + x, center_y + y_offset, center_z + z) for x, z in outline)
    faces: list[tuple[int, ...]] = [tuple(reversed(range(8))), tuple(range(8, 16))]
    for index in range(8):
        following = (index + 1) % 8
        faces.append((index, following, following + 8, index + 8))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    if edge:
        bevel(obj, edge, segments=3)
    mark_export(obj)
    return obj


def raised_cover_text(
    name: str,
    body: str,
    location: tuple[float, float, float],
    side: float,
    size: float,
    mat: bpy.types.Material = ROTAX_LABEL,
) -> bpy.types.Object:
    """Convert compact cover lettering to mesh so it survives GLB export."""
    bpy.ops.object.text_add(location=location, rotation=(math.radians(-90.0 * side), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.0012
    obj.data.bevel_depth = 0.0004
    obj.data.bevel_resolution = 2
    assign(obj, mat)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    mark_export(obj)
    return obj


def open_tube_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    vertices: int = 32,
) -> bpy.types.Object:
    """Create an uncapped inward-facing tube with its axis baked into the mesh.

    Baking the orientation avoids a glTF transform edge case that reset the
    bore liner to Blender's default Z axis and produced a detached vertical
    black rod beside the weapon.
    """
    a, b = Vector(start), Vector(end)
    delta = b - a
    midpoint = (a + b) * 0.5
    axis = delta.normalized()
    reference = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.92 else Vector((0.0, 1.0, 0.0))
    radial_u = axis.cross(reference).normalized()
    radial_v = axis.cross(radial_u).normalized()
    mesh_vertices: list[tuple[float, float, float]] = []
    # Keep geometry local to the tube's midpoint. The complete gimbal is later
    # reparented into a shared scale/translation node, so storing absolute
    # coordinates here would apply that installation transform twice.
    for endpoint in (a - midpoint, b - midpoint):
        for index in range(vertices):
            angle = index * math.tau / vertices
            radial = radial_u * (math.cos(angle) * radius) + radial_v * (math.sin(angle) * radius)
            mesh_vertices.append(tuple(endpoint + radial))
    faces: list[tuple[int, int, int, int]] = []
    for index in range(vertices):
        next_index = (index + 1) % vertices
        faces.append((index, next_index, vertices + next_index, vertices + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(mesh_vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = midpoint
    for polygon in mesh.polygons:
        polygon.flip()
        polygon.use_smooth = True
    assign(obj, mat)
    mark_export(obj)
    return obj


def hollow_cylinder_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    outer_radius: float,
    inner_radius: float,
    mat: bpy.types.Material,
    vertices: int = 32,
) -> bpy.types.Object:
    """Create a capped annular cylinder with a guaranteed open axial bore."""
    a, b = Vector(start), Vector(end)
    delta = b - a
    half_length = delta.length * 0.5
    mesh_vertices: list[tuple[float, float, float]] = []
    for z_pos, radius in (
        (-half_length, outer_radius),
        (half_length, outer_radius),
        (-half_length, inner_radius),
        (half_length, inner_radius),
    ):
        for index in range(vertices):
            angle = index * math.tau / vertices
            mesh_vertices.append((radius * math.cos(angle), radius * math.sin(angle), z_pos))

    outer_start = 0
    outer_end = vertices
    inner_start = vertices * 2
    inner_end = vertices * 3
    faces: list[tuple[int, int, int, int]] = []
    for index in range(vertices):
        next_index = (index + 1) % vertices
        faces.extend(
            (
                (
                    outer_start + index,
                    outer_start + next_index,
                    outer_end + next_index,
                    outer_end + index,
                ),
                (
                    inner_start + next_index,
                    inner_start + index,
                    inner_end + index,
                    inner_end + next_index,
                ),
                (
                    outer_start + next_index,
                    outer_start + index,
                    inner_start + index,
                    inner_start + next_index,
                ),
                (
                    outer_end + index,
                    outer_end + next_index,
                    inner_end + next_index,
                    inner_end + index,
                ),
            )
        )

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(mesh_vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (a + b) * 0.5
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    for polygon in mesh.polygons:
        polygon.use_smooth = polygon.index % 4 < 2
    assign(obj, mat)
    mark_export(obj)
    return obj


def beam_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    depth: float,
    mat: bpy.types.Material,
    edge: float = 0.0,
) -> bpy.types.Object:
    """Create a radiused rectangular structural member between two points."""
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = cube(
        name,
        tuple((a + b) * 0.5),
        (width * 0.5, depth * 0.5, delta.length * 0.5),
        mat,
        edge,
    )
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def extruded_plate_y(
    name: str,
    outline_xz: list[tuple[float, float]],
    center_y: float,
    thickness: float,
    mat: bpy.types.Material,
    edge: float = 0.0,
) -> bpy.types.Object:
    """Extrude a closed hard-surface profile along the aircraft lateral axis."""
    half = thickness * 0.5
    count = len(outline_xz)
    vertices = [(x, center_y - half, z) for x, z in outline_xz]
    vertices.extend((x, center_y + half, z) for x, z in outline_xz)
    faces: list[tuple[int, ...]] = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    if edge:
        bevel(obj, edge, 4)
    mark_export(obj)
    return obj


def contoured_side_plate(
    name: str,
    outer_vertices: list[tuple[float, float, float]],
    side: float,
    thickness: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    """Create a thin inset plate whose lateral position follows a curved shell."""
    count = len(outer_vertices)
    inner_vertices = [
        (x, y - thickness * side, z)
        for x, y, z in outer_vertices
    ]
    vertices = inner_vertices + outer_vertices
    faces: list[tuple[int, ...]] = [
        tuple(reversed(range(count))),
        tuple(range(count, count * 2)),
    ]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    mark_export(obj)
    return obj


def extruded_plate_x(
    name: str,
    outline_yz: list[tuple[float, float]],
    center_x: float,
    thickness: float,
    mat: bpy.types.Material,
    edge: float = 0.0,
) -> bpy.types.Object:
    """Extrude a closed front-facing hard-surface profile along aircraft X."""
    half = thickness * 0.5
    count = len(outline_yz)
    vertices = [(center_x - half, y, z) for y, z in outline_yz]
    vertices.extend((center_x + half, y, z) for y, z in outline_yz)
    faces: list[tuple[int, ...]] = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following, count + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    if edge:
        bevel(obj, edge, 4)
    mark_export(obj)
    return obj


def elliptical_ring(
    name: str,
    x: float,
    radius_y: float,
    radius_z: float,
    center_z: float,
    tube_radius: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
    segments: int = 72,
    tube_segments: int = 8,
    y_offset: float = 0.0,
) -> bpy.types.Object:
    """A fine manufacturing joint wrapped around an elliptical shell section."""
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    for ring in range(segments):
        angle = 2.0 * math.pi * ring / segments
        cosine, sine = math.cos(angle), math.sin(angle)
        for tube in range(tube_segments):
            tube_angle = 2.0 * math.pi * tube / tube_segments
            radial = tube_radius * math.sin(tube_angle)
            vertices.append(
                (
                    x + tube_radius * math.cos(tube_angle),
                    y_offset + (radius_y + radial) * cosine,
                    center_z + (radius_z + radial) * sine,
                )
            )
    for ring in range(segments):
        next_ring = (ring + 1) % segments
        for tube in range(tube_segments):
            next_tube = (tube + 1) % tube_segments
            a = ring * tube_segments + tube
            b = next_ring * tube_segments + tube
            c = next_ring * tube_segments + next_tube
            d = ring * tube_segments + next_tube
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    obj.parent = parent
    return obj


def surface_detail_line(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
) -> None:
    """Build a subtle raised hinge or panel line from connected round segments."""
    for index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        detail = cylinder_between(
            f"{name} {index:02d}",
            start,
            end,
            radius,
            mat,
            vertices=10,
        )
        detail.parent = parent


def wing_upper_surface_z(x: float, span: float) -> float:
    """Evaluate the main-wing upper skin at one chord/span coordinate."""
    dihedral = math.tan(math.radians(2.5))
    root_z = -0.25
    sections = (
        (0.00, -2.22, 1.48, root_z, 0.16, 2.0),
        (1.40, -2.18, 1.38, root_z + 1.40 * dihedral, 0.16, 1.7),
        (4.80, -1.98, 1.04, root_z + 4.80 * dihedral, 0.15, 0.8),
        (8.735, -1.73, 0.58, root_z + 8.735 * dihedral, 0.13, 0.0),
    )
    absolute_span = max(0.0, min(abs(span), sections[-1][0]))
    lower = sections[0]
    upper = sections[-1]
    for first, second in zip(sections, sections[1:]):
        if first[0] <= absolute_span <= second[0]:
            lower, upper = first, second
            break
    blend = (absolute_span - lower[0]) / max(upper[0] - lower[0], 1e-6)
    lead, chord, z_base, thickness_ratio, incidence_deg = (
        lower[index] + (upper[index] - lower[index]) * blend
        for index in range(1, 6)
    )
    u = max(0.0, min(1.0, (x - lead) / max(chord, 1e-6)))
    thickness = 5.0 * thickness_ratio * chord * (
        0.2969 * math.sqrt(max(u, 0.0))
        - 0.1260 * u
        - 0.3516 * u**2
        + 0.2843 * u**3
        - 0.1036 * u**4
    )
    camber = 0.012 * chord * math.sin(math.pi * u)
    incidence = math.radians(incidence_deg)
    quarter_chord = lead + chord * 0.25
    profile_x = lead + chord * u - quarter_chord
    return z_base - profile_x * math.sin(incidence) + (camber + thickness) * math.cos(incidence)


def wing_surface_seam(
    name: str,
    control_points: list[tuple[float, float, float]],
    width: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
    samples_per_segment: int = 14,
) -> bpy.types.Object:
    """Lay a flat hinge-line ribbon directly on the wing upper skin.

    The previous round cylinders were visually acceptable at overview scale
    but revealed an air gap in close-up.  This zero-thickness ribbon samples
    the analytic airfoil and sits only 0.35 mm above it to avoid z-fighting.
    """
    sampled: list[Vector] = []
    for start, end in zip(control_points, control_points[1:]):
        for sample in range(samples_per_segment):
            blend = sample / samples_per_segment
            sampled.append(
                Vector(
                    (
                        start[0] + (end[0] - start[0]) * blend,
                        start[1] + (end[1] - start[1]) * blend,
                        0.0,
                    )
                )
            )
    sampled.append(Vector((control_points[-1][0], control_points[-1][1], 0.0)))

    vertices: list[tuple[float, float, float]] = []
    for index, center in enumerate(sampled):
        previous = sampled[max(index - 1, 0)]
        following = sampled[min(index + 1, len(sampled) - 1)]
        tangent = Vector((following.x - previous.x, following.y - previous.y, 0.0))
        if tangent.length < 1e-8:
            tangent = Vector((0.0, 1.0, 0.0))
        tangent.normalize()
        lateral = Vector((-tangent.y, tangent.x, 0.0)) * (width * 0.5)
        for point in (center + lateral, center - lateral):
            vertices.append(
                (
                    point.x,
                    point.y,
                    wing_upper_surface_z(point.x, point.y) + 0.00035,
                )
            )

    faces = [
        (index * 2, index * 2 + 1, index * 2 + 3, index * 2 + 2)
        for index in range(len(sampled) - 1)
    ]
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    seam = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(seam)
    assign(seam, mat)
    mark_export(seam)
    seam.parent = parent
    return seam


def landing_wheel(
    name: str,
    location: tuple[float, float, float],
    outer_radius: float,
    width: float,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    """Create a correctly dimensioned wheel with its axle running spanwise."""
    tire_tube_radius = min(width * 0.5, outer_radius * 0.39)
    tire_center_radius = outer_radius - tire_tube_radius
    bpy.ops.mesh.primitive_torus_add(
        major_radius=tire_center_radius,
        minor_radius=tire_tube_radius,
        major_segments=40,
        minor_segments=14,
        location=location,
        rotation=(math.radians(90), 0, 0),
    )
    wheel = bpy.context.object
    wheel.name = f"{name} tire"
    assign(wheel, RUBBER)
    smooth(wheel)
    mark_export(wheel)
    wheel.parent = parent

    x, y, z = location
    # The real sailplane wheel reads as a small aircraft wheel, not a black
    # bead. Layered rim faces, a recessed brake disc and axle caps keep that
    # mechanical construction legible in close model-viewer inspection.
    hub = cylinder_between(
        f"{name} wheel rim",
        (x, y - width * 0.48, z),
        (x, y + width * 0.48, z),
        outer_radius * 0.40,
        ALLOY,
        vertices=40,
    )
    hub.parent = parent

    brake = cylinder_between(
        f"{name} recessed brake disc",
        (x, y - width * 0.51, z),
        (x, y - width * 0.40, z),
        outer_radius * 0.29,
        HARDWARE_GRAY,
        vertices=36,
    )
    brake.parent = parent

    for side, suffix in ((-1.0, "inboard"), (1.0, "outboard")):
        axle_cap = cylinder_between(
            f"{name} {suffix} axle cap",
            (x, y + side * width * 0.50, z),
            (x, y + side * width * 0.66, z),
            outer_radius * 0.17,
            GRAPHITE,
            vertices=28,
        )
        axle_cap.parent = parent
    return wheel


def landing_gear_fairing(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    parent: bpy.types.Object,
) -> bpy.types.Object:
    """Broad tapered composite gear leg matching the AMT-200 ground profile."""
    sx, sy, sz = start
    ex, ey, ez = end
    top_x, top_y = 0.13, 0.055
    bottom_x, bottom_y = 0.075, 0.045
    verts = [
        (sx - top_x, sy - top_y, sz),
        (sx + top_x, sy - top_y, sz),
        (sx + top_x, sy + top_y, sz),
        (sx - top_x, sy + top_y, sz),
        (ex - bottom_x, ey - bottom_y, ez),
        (ex + bottom_x, ey - bottom_y, ez),
        (ex + bottom_x, ey + bottom_y, ez),
        (ex - bottom_x, ey + bottom_y, ez),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, IAF_GRAY)
    bevel(obj, 0.025, 3)
    smooth(obj)
    mark_export(obj)
    obj.parent = parent
    return obj


def propeller_blade(
    name: str,
    angle: float,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    """Smooth tapered and twisted 0.87 m blade at the spinner's aft plane."""
    # More radial stations and elliptical section loops prevent the propeller
    # from collapsing into a long faceted bar when viewed edge-on.  The root is
    # buried inside the spinner, the broad working section transitions gently,
    # and the rounded tip closes without a bevel-induced spike.
    # radius, chord, geometric pitch, section thickness
    radial_sections = [
        (0.10, 0.130, 34.0, 0.030),
        (0.18, 0.158, 32.0, 0.032),
        (0.30, 0.164, 29.0, 0.031),
        (0.43, 0.148, 26.0, 0.028),
        (0.57, 0.124, 23.0, 0.025),
        (0.69, 0.098, 20.0, 0.021),
        (0.79, 0.070, 17.0, 0.017),
        (0.855, 0.038, 15.0, 0.012),
        (0.875, 0.010, 14.0, 0.006),
    ]
    blade_plane_x = -3.925
    radial_y, radial_z = math.sin(angle), math.cos(angle)
    chord_y, chord_z = math.cos(angle), -math.sin(angle)
    verts: list[tuple[float, float, float]] = []
    section_segments = 12
    for radius, chord, pitch_deg, thickness in radial_sections:
        center_y = radial_y * radius
        center_z = radial_z * radius
        pitch = math.radians(pitch_deg)
        chord_axis = Vector((math.sin(pitch), chord_y * math.cos(pitch), chord_z * math.cos(pitch)))
        thickness_axis = Vector((math.cos(pitch), -chord_y * math.sin(pitch), -chord_z * math.sin(pitch)))
        center = Vector((blade_plane_x, center_y, center_z))
        for segment in range(section_segments):
            section_angle = 2.0 * math.pi * segment / section_segments
            # A slightly fuller leading half and restrained trailing half read
            # as an aerodynamic blade section without adding costly geometry.
            chord_factor = math.cos(section_angle)
            thickness_factor = math.sin(section_angle)
            if chord_factor < 0.0:
                chord_factor *= 0.90
            vertex = (
                center
                + chord_axis * chord_factor * chord * 0.5
                + thickness_axis * thickness_factor * thickness * 0.5
            )
            verts.append(tuple(vertex))
    faces: list[tuple[int, ...]] = []
    for section in range(len(radial_sections) - 1):
        first = section * section_segments
        following = (section + 1) * section_segments
        for segment in range(section_segments):
            nxt = (segment + 1) % section_segments
            faces.append((first + segment, following + segment, following + nxt, first + nxt))
    faces.append(tuple(range(section_segments - 1, -1, -1)))
    last = (len(radial_sections) - 1) * section_segments
    faces.append(tuple(last + segment for segment in range(section_segments)))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    blade = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(blade)
    assign(blade, PROP_WHITE)
    bevel(blade, 0.004, 2)
    smooth(blade)
    mark_export(blade)
    blade.parent = parent
    return blade


def create_loft(
    name: str,
    sections: list[tuple[float, float, float, float]],
    mat: bpy.types.Material,
    ring_segments: int = 32,
    y_offset: float = 0.0,
) -> bpy.types.Object:
    """Loft elliptical rings along X. Each section is x, radius_y, radius_z, z_offset."""
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    for x, ry, rz, z_offset in sections:
        for idx in range(ring_segments):
            angle = 2 * math.pi * idx / ring_segments
            vertices.append((x, y_offset + math.cos(angle) * ry, z_offset + math.sin(angle) * rz))

    for ring in range(len(sections) - 1):
        for idx in range(ring_segments):
            nxt = (idx + 1) % ring_segments
            a = ring * ring_segments + idx
            b = ring * ring_segments + nxt
            c = (ring + 1) * ring_segments + nxt
            d = (ring + 1) * ring_segments + idx
            faces.append((a, b, c, d))

    faces.append(tuple(range(ring_segments - 1, -1, -1)))
    last = (len(sections) - 1) * ring_segments
    faces.append(tuple(last + i for i in range(ring_segments)))

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bevel(obj, 0.018, 2)
    smooth(obj)
    mark_export(obj)
    return obj


def create_asymmetric_fuselage(
    name: str,
    sections: list[tuple[float, float, float, float, float, float]],
    mat: bpy.types.Material,
    ring_segments: int = 64,
) -> bpy.types.Object:
    """Loft a non-cylindrical fuselage with independent crown and belly.

    Each section is x, half-width, crown height, belly depth, center z and
    superellipse exponent.  The changing section shape follows the Ximango's
    engine cowling, broad cockpit shoulders, lower wing saddle and slender
    structural tail boom instead of scaling one tube along its length.
    """
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for x, half_width, crown, belly, center_z, exponent in sections:
        for index in range(ring_segments):
            angle = 2.0 * math.pi * index / ring_segments
            cosine = math.cos(angle)
            sine = math.sin(angle)
            y = math.copysign(abs(cosine) ** exponent, cosine) * half_width
            vertical_radius = crown if sine >= 0.0 else belly
            z = center_z + math.copysign(abs(sine) ** exponent, sine) * vertical_radius
            vertices.append((x, y, z))

    for ring in range(len(sections) - 1):
        for index in range(ring_segments):
            nxt = (index + 1) % ring_segments
            current = ring * ring_segments + index
            following = (ring + 1) * ring_segments + index
            faces.append((current, following, (ring + 1) * ring_segments + nxt, ring * ring_segments + nxt))

    faces.append(tuple(range(ring_segments - 1, -1, -1)))
    last = (len(sections) - 1) * ring_segments
    faces.append(tuple(last + index for index in range(ring_segments)))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    # Preserve the four longitudinal shoulder/chine breaks that define the
    # composite Ximango fuselage section. Without these split normals, fully
    # smooth shading makes even a superelliptic body read as a round tube.
    chine_indices = {
        round(ring_segments * fraction) % ring_segments
        for fraction in (0.125, 0.375, 0.625, 0.875)
    }
    for edge in mesh.edges:
        first, second = edge.vertices
        first_index = first % ring_segments
        second_index = second % ring_segments
        if first_index == second_index and first_index in chine_indices:
            edge.use_edge_sharp = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bevel(obj, 0.015, 2)
    smooth(obj)
    mark_export(obj)
    return obj


def interpolate_fuselage_section(
    x: float,
    sections: list[tuple[float, float, float, float, float, float]],
) -> tuple[float, float, float, float, float]:
    """Interpolate the local superellipse parameters at one fuselage station."""
    if x <= sections[0][0]:
        return sections[0][1:]
    if x >= sections[-1][0]:
        return sections[-1][1:]
    for left, right in zip(sections, sections[1:]):
        if left[0] <= x <= right[0]:
            blend = (x - left[0]) / (right[0] - left[0])
            return tuple(
                left[index] + (right[index] - left[index]) * blend
                for index in range(1, 6)
            )
    return sections[-1][1:]


def fuselage_lower_surface_point(
    x: float,
    y: float,
    sections: list[tuple[float, float, float, float, float, float]],
    outward_offset: float = 0.0,
) -> tuple[float, float, float]:
    """Return a point that follows the analytic lower fuselage outer mold line."""
    half_width, _crown, belly, center_z, exponent = interpolate_fuselage_section(x, sections)
    normalized_y = min(abs(y) / max(half_width, 1e-6), 0.999999)
    cosine = normalized_y ** (1.0 / exponent)
    sine = math.sqrt(max(0.0, 1.0 - cosine * cosine))
    z = center_z - (sine ** exponent) * belly
    if outward_offset:
        normal = Vector((0.0, y / max(half_width, 1e-6), (z - center_z) / max(belly, 1e-6))).normalized()
        x += normal.x * outward_offset
        y += normal.y * outward_offset
        z += normal.z * outward_offset
    return (x, y, z)


def surface_conforming_seam(
    name: str,
    control_loop: list[tuple[float, float]],
    sections: list[tuple[float, float, float, float, float, float]],
    width: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
    samples_per_edge: int = 8,
) -> bpy.types.Object:
    """Create a flat ribbon whose vertices are evaluated on the fuselage skin."""
    centerline: list[Vector] = []
    for start, end in zip(control_loop, control_loop[1:] + control_loop[:1]):
        for sample in range(samples_per_edge):
            blend = sample / samples_per_edge
            centerline.append(
                Vector(
                    (
                        start[0] + (end[0] - start[0]) * blend,
                        start[1] + (end[1] - start[1]) * blend,
                    )
                )
            )

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    half_width = width * 0.5
    point_count = len(centerline)
    for index, center in enumerate(centerline):
        previous = centerline[(index - 1) % point_count]
        following = centerline[(index + 1) % point_count]
        tangent = following - previous
        if tangent.length < 1e-8:
            tangent = Vector((1.0, 0.0))
        tangent.normalize()
        lateral = Vector((-tangent.y, tangent.x)) * half_width
        for point_2d in (center + lateral, center - lateral):
            vertices.append(
                fuselage_lower_surface_point(
                    point_2d.x,
                    point_2d.y,
                    sections,
                    outward_offset=0.00018,
                )
            )

    for index in range(point_count):
        following = (index + 1) % point_count
        faces.append((index * 2, following * 2, following * 2 + 1, index * 2 + 1))

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    mark_export(obj)
    obj.parent = parent
    obj["surface_treatment"] = "flush seam ribbon evaluated on fuselage outer mold line"
    return obj


def create_open_loft(
    name: str,
    sections: list[tuple[float, float, float, float]],
    mat: bpy.types.Material,
    ring_segments: int = 48,
    y_offset: float = 0.0,
) -> bpy.types.Object:
    """Loft an uncapped aerodynamic duct shell along the aircraft X axis."""
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    for x, radius_y, radius_z, center_z in sections:
        for index in range(ring_segments):
            angle = math.tau * index / ring_segments
            vertices.append(
                (
                    x,
                    y_offset + math.cos(angle) * radius_y,
                    center_z + math.sin(angle) * radius_z,
                )
            )
    for ring in range(len(sections) - 1):
        for index in range(ring_segments):
            following = (index + 1) % ring_segments
            current = ring * ring_segments + index
            next_ring = (ring + 1) * ring_segments + index
            faces.append(
                (
                    current,
                    next_ring,
                    (ring + 1) * ring_segments + following,
                    ring * ring_segments + following,
                )
            )
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    return obj


def assign_forward_material(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    maximum_centroid_x: float,
) -> None:
    """Give the forward cowling its own runtime-fadeable material slot."""
    material_index = len(obj.data.materials)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        centroid_x = sum(obj.data.vertices[index].co.x for index in polygon.vertices) / len(polygon.vertices)
        if centroid_x <= maximum_centroid_x:
            polygon.material_index = material_index


def assign_mission_computer_cutaway_material(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
) -> None:
    """Create a flush, runtime-fadeable avionics window in the starboard skin.

    The material uses the same PBR maps as the surrounding composite, so the
    closed aircraft remains visually continuous. STA 03 only fades this local
    polygon band, revealing the correctly scaled T5000 module without making
    the complete fuselage transparent.
    """
    material_index = len(obj.data.materials)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        coordinates = [obj.data.vertices[index].co for index in polygon.vertices]
        centroid_x = sum(vertex.x for vertex in coordinates) / len(coordinates)
        centroid_y = sum(vertex.y for vertex in coordinates) / len(coordinates)
        centroid_z = sum(vertex.z for vertex in coordinates) / len(coordinates)
        if (
            -1.74 <= centroid_x <= -1.08
            and centroid_y <= -0.24
            and -0.10 <= centroid_z <= 0.245
        ):
            polygon.material_index = material_index


def assign_drone_bay_cutaway_material(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
) -> None:
    """Give the flush STA 10 belly hatch a dedicated runtime-fadeable skin.

    The same coating maps remain visible in the closed condition. During the
    deployment demonstration, the local polygon patch fades while the physical
    hatch rotates away, revealing the magazine without making the complete
    fuselage transparent.
    """
    material_index = len(obj.data.materials)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        coordinates = [obj.data.vertices[index].co for index in polygon.vertices]
        centroid_x = sum(vertex.x for vertex in coordinates) / len(coordinates)
        centroid_y = sum(vertex.y for vertex in coordinates) / len(coordinates)
        centroid_z = sum(vertex.z for vertex in coordinates) / len(coordinates)
        # Match the complete physical-door footprint, including the tapered
        # forward and aft rows.  The earlier, smaller material window left a
        # strip of opaque fuselage above the rotating doors, so the doors moved
        # but the opening still looked sealed in model-viewer.
        if (
            -0.81 <= centroid_x <= 0.25
            and abs(centroid_y) <= 0.215
            and centroid_z <= -0.105
        ):
            polygon.material_index = material_index


def create_rotax_916_engine(parent: bpy.types.Object) -> None:
    """Build a high-detail presentation cutaway of a Rotax 916 installation.

    The assembly remains visualization geometry rather than a manufacturing
    replica, but close-up presentation now carries a complete material and
    mechanical hierarchy: textured cast cases, machined gearbox stages,
    opposed finned cylinders, fasteners, ignition hardware, coolant and charge
    plumbing, exhaust collectors, turbocharger, intercooler and engine mount.
    It remains inside the closed cowling until STA 02 fades that shell at run
    time in model-viewer.
    """

    engine_scale = 0.82
    engine_pivot = Vector((-3.235, 0.0, 0.0))
    engine_group = bpy.data.objects.new("Rotax 916 fitted installation transform", None)
    bpy.context.collection.objects.link(engine_group)
    engine_group.parent = parent
    engine_group["system_station"] = "STA 02"
    engine_group["installation_scale"] = engine_scale
    mark_export(engine_group)

    def parent_engine(obj: bpy.types.Object) -> bpy.types.Object:
        obj.parent = engine_group
        if getattr(obj, "data", None) is not None:
            obj.data.name = obj.name
        obj["system_station"] = "STA 02"
        obj["visualization_detail"] = "high-detail textured Rotax 916 iS/iSc cutaway"
        return obj

    parent_engine(
        cube(
            "Rotax 916 central crankcase",
            (-3.235, 0.0, -0.005),
            (0.285, 0.135, 0.125),
            ROTAX_ALLOY,
            edge=0.045,
        )
    )
    parent_engine(
        cube(
            "Rotax 916 lower oil-sump case",
            (-3.215, 0.0, -0.145),
            (0.215, 0.115, 0.055),
            ROTAX_DARK,
            edge=0.026,
        )
    )

    # Cast-case ribs, side inspection covers and captive fasteners break up the
    # large crankcase volumes at close range and provide realistic scale cues.
    for rib_x in (-3.455, -3.355, -3.255, -3.155, -3.055):
        parent_engine(
            cube(
                f"Rotax 916 crankcase reinforcement rib {rib_x:+.3f}",
                (rib_x, 0.0, 0.0),
                (0.010, 0.143, 0.112),
                ROTAX_HEAD,
                edge=0.005,
            )
        )
    for side, side_name in ((1.0, "port"), (-1.0, "starboard")):
        parent_engine(
            cylinder_between(
                f"Rotax 916 {side_name} crankcase inspection cover",
                (-3.235, side * 0.135, 0.0),
                (-3.235, side * 0.151, 0.0),
                0.098,
                ROTAX_ALLOY,
                vertices=48,
            )
        )
        for angle_index in range(8):
            angle = angle_index * math.tau / 8.0
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} crankcase cover fastener {angle_index + 1:02d}",
                    (-3.235 + math.cos(angle) * 0.078, side * 0.150, math.sin(angle) * 0.078),
                    (-3.235 + math.cos(angle) * 0.078, side * 0.161, math.sin(angle) * 0.078),
                    0.0065,
                    ROTAX_STEEL,
                    vertices=20,
                )
            )

    parent_engine(
        cylinder_between(
            "Rotax 916 oil filter",
            (-3.000, -0.135, -0.135),
            (-3.000, -0.135, -0.270),
            0.044,
            ROTAX_DARK,
            vertices=40,
        )
    )
    parent_engine(
        cylinder_between(
            "Rotax 916 service oil cap",
            (-3.075, 0.052, 0.118),
            (-3.075, 0.052, 0.180),
            0.032,
            ROTAX_ACCENT,
            vertices=32,
        )
    )

    # The 916 drives the propeller through its integrated propeller-speed
    # reduction gearbox. The modeled output train includes the 2.5454:1 stage,
    # output flange and overload clutch instead of implying a direct drive.
    for name, start_x, end_x, radius, mat in (
        ("Rotax 916 propeller drive shaft", -3.865, -3.690, 0.038, ROTAX_DARK),
        ("Rotax 916 reduction gearbox forward stage", -3.710, -3.590, 0.155, ROTAX_ALLOY),
        ("Rotax 916 reduction gearbox aft stage", -3.610, -3.490, 0.185, ROTAX_HEAD),
        ("Rotax 916 gearbox collar", -3.505, -3.455, 0.128, ROTAX_DARK),
    ):
        parent_engine(cylinder_between(name, (start_x, 0.0, 0.0), (end_x, 0.0, 0.0), radius, mat, vertices=48))

    parent_engine(
        cylinder_between(
            "Rotax 916 propeller output flange",
            (-3.905, 0.0, 0.0),
            (-3.850, 0.0, 0.0),
            0.076,
            ROTAX_STEEL,
            vertices=48,
        )
    )
    parent_engine(
        cylinder_between(
            "Rotax 916 overload clutch pack",
            (-3.735, 0.0, 0.0),
            (-3.685, 0.0, 0.0),
            0.092,
            ROTAX_DARK,
            vertices=48,
        )
    )
    for plate_index, plate_x in enumerate((-3.724, -3.711, -3.698), start=1):
        parent_engine(
            cylinder_between(
                f"Rotax 916 overload clutch friction plate {plate_index:02d}",
                (plate_x, 0.0, 0.0),
                (plate_x + 0.006, 0.0, 0.0),
                0.099,
                ROTAX_STEEL,
                vertices=48,
            )
        )
    for bolt_index in range(8):
        angle = bolt_index * math.tau / 8.0
        bolt_y = math.cos(angle) * 0.120
        bolt_z = math.sin(angle) * 0.120
        parent_engine(
            cylinder_between(
                f"Rotax 916 reduction gearbox perimeter fastener {bolt_index + 1:02d}",
                (-3.716, bolt_y, bolt_z),
                (-3.700, bolt_y, bolt_z),
                0.0065,
                ROTAX_STEEL,
                vertices=20,
            )
        )

    # Two opposed cylinder pairs. Alternating fore/aft offsets keep the compact
    # flat-four readable from either side instead of collapsing into one block.
    for pair_index, cylinder_x in enumerate((-3.385, -3.105), start=1):
        for side, side_name in ((1.0, "port"), (-1.0, "starboard")):
            parent_engine(
                cylinder_between(
                    f"Rotax 916 cylinder {pair_index} {side_name}",
                    (cylinder_x, side * 0.105, 0.025),
                    (cylinder_x, side * 0.270, 0.025),
                    0.080,
                    ROTAX_HEAD,
                    vertices=40,
                )
            )
            parent_engine(
                chamfered_xz_cover(
                    f"Rotax 916 pearl-gray cylinder-head cover {pair_index} {side_name}",
                    (cylinder_x, side * 0.305, 0.025),
                    (0.105, 0.045, 0.090),
                    ROTAX_COVER,
                    edge=0.012,
                )
            )
            parent_engine(
                raised_cover_text(
                    f"Rotax 916 ROTAX head-cover lettering {pair_index} {side_name}",
                    "ROTAX",
                    (cylinder_x, side * 0.353, 0.062),
                    side,
                    0.021,
                )
            )
            for fin_offset in (-0.068, -0.051, -0.034, -0.017, 0.0, 0.017, 0.034, 0.051, 0.068):
                parent_engine(
                    cube(
                        f"Rotax 916 cooling fin {pair_index} {side_name} {fin_offset:+.3f}",
                        (cylinder_x + fin_offset, side * 0.190, 0.025),
                        (0.004, 0.074, 0.094),
                        ROTAX_DARK,
                        edge=0.002,
                    )
                )

    # Machined cover bolts, plug boots and fuel rails remain readable when the
    # STA 02 camera pushes inside the translucent cowling.
    for cylinder_x in (-3.385, -3.105):
        for side, side_name in ((1.0, "port"), (-1.0, "starboard")):
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} central head-cover fastener",
                    (cylinder_x, side * 0.348, 0.006),
                    (cylinder_x, side * 0.363, 0.006),
                    0.0080,
                    ROTAX_STEEL,
                    vertices=24,
                )
            )
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} spark-plug insulator",
                    (cylinder_x, side * 0.312, 0.060),
                    (cylinder_x, side * 0.312, 0.132),
                    0.013,
                    ROTAX_ACCENT,
                    vertices=24,
                )
            )
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} spark-plug boot",
                    (cylinder_x, side * 0.312, 0.120),
                    (cylinder_x + 0.045, side * 0.285, 0.165),
                    0.016,
                    ROTAX_RUBBER,
                    vertices=24,
                )
            )

    # The raised 916 iS induction covers and pearl-gray rocker covers are the
    # most immediate visual identifiers in Rotax's official product imagery.
    for side, side_name in ((1.0, "port"), (-1.0, "starboard")):
        parent_engine(
            chamfered_xz_cover(
                f"Rotax 916 branded upper induction cover {side_name}",
                (-3.165, side * 0.275, 0.174),
                (0.140, 0.034, 0.052),
                ROTAX_COVER,
                edge=0.012,
            )
        )
        parent_engine(
            raised_cover_text(
                f"Rotax 916 916 iS cover lettering {side_name}",
                "916 iS",
                (-3.165, side * 0.312, 0.184),
                side,
                0.031,
            )
        )

    for side, side_name in ((1.0, "port"), (-1.0, "starboard")):
        parent_engine(
            cylinder_between(
                f"Rotax 916 {side_name} fuel rail",
                (-3.475, side * 0.334, 0.150),
                (-3.015, side * 0.334, 0.150),
                0.011,
                ROTAX_STEEL,
                vertices=28,
            )
        )
        for cylinder_x in (-3.385, -3.105):
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} injector feed",
                    (cylinder_x, side * 0.332, 0.150),
                    (cylinder_x, side * 0.270, 0.108),
                    0.008,
                    ROTAX_RUBBER,
                    vertices=20,
                )
            )

            # Stainless exhaust primaries sweep inward to compact collectors.
            parent_engine(
                cylinder_between(
                    f"Rotax 916 {side_name} exhaust primary",
                    (cylinder_x, side * 0.305, -0.040),
                    (cylinder_x + 0.075, side * 0.190, -0.175),
                    0.021,
                    ROTAX_HEAT_WRAP,
                    vertices=28,
                )
            )
        parent_engine(
            cylinder_between(
                f"Rotax 916 {side_name} exhaust collector",
                (-3.420, side * 0.190, -0.175),
                (-2.875, side * 0.190, -0.175),
                0.027,
                ROTAX_HEAT_WRAP,
                vertices=32,
            )
        )

        # Two-piece coolant hoses imply a molded elbow while keeping the GLB
        # lightweight and stable in model-viewer.
        coolant_midpoint = (-3.220, side * 0.245, 0.205)
        parent_engine(
            cylinder_between(
                f"Rotax 916 {side_name} coolant hose aft",
                (-3.385, side * 0.305, 0.090),
                coolant_midpoint,
                0.018,
                ROTAX_RUBBER,
                vertices=28,
            )
        )
        parent_engine(
            cylinder_between(
                f"Rotax 916 {side_name} coolant hose forward",
                coolant_midpoint,
                (-2.815, side * 0.185, 0.165),
                0.018,
                ROTAX_RUBBER,
                vertices=28,
            )
        )

    parent_engine(
        cube(
            "Rotax 916 lower induction plenum",
            (-3.210, 0.0, 0.145),
            (0.235, 0.105, 0.040),
            ROTAX_DARK,
            edge=0.026,
        )
    )
    for cylinder_x in (-3.385, -3.105):
        for side in (-1.0, 1.0):
            parent_engine(
                cylinder_between(
                    "Rotax 916 intake runner",
                    (cylinder_x, side * 0.080, 0.155),
                    (cylinder_x, side * 0.245, 0.095),
                    0.018,
                    ROTAX_RUBBER,
                    vertices=24,
                )
            )

    # The official 916 installation carries a broad molded charge tube across
    # the top of the engine. A smooth multi-point elbow is visually much closer
    # to that assembly than the former rectangular plenum.
    parent_engine(
        curved_tube(
            "Rotax 916 broad upper charge-air tube",
            [
                (-2.720, -0.085, 0.105),
                (-2.780, -0.095, 0.205),
                (-2.965, -0.070, 0.255),
                (-3.245, -0.015, 0.255),
                (-3.490, 0.035, 0.205),
            ],
            0.047,
            ROTAX_RUBBER,
            resolution=5,
        )
    )
    for clamp_x, clamp_z in ((-2.780, 0.195), (-3.450, 0.213)):
        parent_engine(
            cylinder_between(
                "Rotax 916 upper charge-tube stainless clamp",
                (clamp_x - 0.010, -0.072, clamp_z),
                (clamp_x + 0.010, -0.072, clamp_z),
                0.052,
                ROTAX_STEEL,
                vertices=40,
            )
        )

    # The turbo is low and outboard, matching the official front three-quarter
    # imagery. It is placed on the station's default visible side so the
    # compressor eye reads immediately when the cowling fades.
    bpy.ops.mesh.primitive_torus_add(
        major_segments=48,
        minor_segments=18,
        location=(-2.870, -0.205, -0.070),
        major_radius=0.092,
        minor_radius=0.032,
        rotation=(math.radians(90), 0.0, 0.0),
    )
    turbo_scroll = bpy.context.object
    turbo_scroll.name = "Rotax 916 turbocharger compressor scroll"
    assign(turbo_scroll, ROTAX_TURBO)
    smooth(turbo_scroll)
    mark_export(turbo_scroll)
    parent_engine(turbo_scroll)
    parent_engine(
        cylinder_between(
            "Rotax 916 turbocharger core",
            (-2.870, -0.160, -0.070),
            (-2.870, -0.275, -0.070),
            0.050,
            ROTAX_DARK,
            vertices=40,
        )
    )
    parent_engine(
        cylinder_between(
            "Rotax 916 turbocharger machined inlet",
            (-2.870, -0.270, -0.070),
            (-2.870, -0.338, -0.070),
            0.067,
            ROTAX_ALLOY,
            vertices=48,
        )
    )
    parent_engine(
        cylinder_between(
            "Rotax 916 turbocharger compressor eye",
            (-2.870, -0.337, -0.070),
            (-2.870, -0.348, -0.070),
            0.039,
            ROTAX_DARK,
            vertices=48,
        )
    )
    parent_engine(
        cylinder_between(
            "Rotax 916 turbocharger exhaust transition",
            (-2.875, -0.190, -0.175),
            (-2.870, -0.200, -0.112),
            0.030,
            ROTAX_HEAT_WRAP,
            vertices=32,
        )
    )
    parent_engine(
        curved_tube(
            "Rotax 916 turbo-to-intercooler charge pipe",
            [
                (-2.870, -0.205, 0.015),
                (-2.805, -0.185, 0.070),
                (-2.720, -0.145, 0.115),
                (-2.690, -0.090, 0.145),
            ],
            0.027,
            ROTAX_ALLOY,
            resolution=4,
        )
    )
    parent_engine(
        curved_tube(
            "Rotax 916 heat-wrapped turbo exhaust outlet",
            [
                (-2.875, -0.175, -0.135),
                (-2.815, -0.155, -0.205),
                (-2.700, -0.115, -0.245),
                (-2.575, -0.075, -0.245),
            ],
            0.029,
            ROTAX_HEAT_WRAP,
            resolution=4,
        )
    )

    # Compact dual electronic modules and their harnesses add the dense,
    # installation-ready character visible around the official upper covers.
    for module_x in (-3.290, -3.080):
        parent_engine(
            cube(
                "Rotax 916 engine-control electronics module",
                (module_x, 0.010, 0.288),
                (0.072, 0.060, 0.027),
                ROTAX_DARK,
                edge=0.010,
            )
        )
        parent_engine(
            curved_tube(
                "Rotax 916 engine-control wiring harness",
                [
                    (module_x, -0.020, 0.270),
                    (module_x + 0.030, -0.090, 0.235),
                    (module_x + 0.055, -0.180, 0.165),
                ],
                0.008,
                ROTAX_RUBBER,
                resolution=3,
            )
        )

    # A dark fin matrix with machined side tanks recreates the prominent
    # rectangular intercooler shown behind the upper charge duct.
    parent_engine(
        cube(
            "Rotax 916 intercooler dark fin core",
            (-2.735, 0.0, 0.080),
            (0.060, 0.235, 0.137),
            ROTAX_DARK,
            edge=0.012,
        )
    )
    for side in (-1.0, 1.0):
        parent_engine(
            cube(
                "Rotax 916 intercooler machined side tank",
                (-2.730, side * 0.244, 0.080),
                (0.071, 0.018, 0.148),
                ROTAX_ALLOY,
                edge=0.014,
            )
        )
    for z in (-0.030, -0.010, 0.010, 0.030, 0.050, 0.070, 0.090, 0.110, 0.130, 0.150, 0.170, 0.190):
        parent_engine(
            cube(
                f"Rotax 916 intercooler fin {z:+.3f}",
                (-2.671, 0.0, z),
                (0.006, 0.225, 0.005),
                ROTAX_ALLOY,
                edge=0.002,
            )
        )
    for y in (-0.200, -0.150, -0.100, -0.050, 0.0, 0.050, 0.100, 0.150, 0.200):
        parent_engine(
            cube(
                f"Rotax 916 intercooler vertical fin {y:+.3f}",
                (-2.669, y, 0.080),
                (0.005, 0.003, 0.130),
                ROTAX_ALLOY,
                edge=0.0015,
            )
        )

    # A restrained four-point truss locates the powerplant inside the airframe.
    for side in (-1.0, 1.0):
        for z in (-0.135, 0.145):
            parent_engine(
                cylinder_between(
                    "Rotax 916 tubular engine mount",
                    (-3.300, side * 0.145, z * 0.72),
                    (-2.585, side * 0.255, z),
                    0.012,
                    ROTAX_STEEL,
                    vertices=20,
                )
            )

    parent["engine_model"] = "Rotax 916 iS/C, turbo"
    parent["engine_takeoff_power_hp"] = 160
    parent["engine_continuous_power_hp"] = 137
    parent["engine_propeller_reduction_ratio"] = "2.5454:1"
    parent["engine_gearbox_protection"] = "integrated overload clutch"
    parent["engine_visualization"] = "official-reference high-detail cutaway, illustrative and not manufacturing geometry"
    engine_group.matrix_local = (
        Matrix.Translation(engine_pivot)
        @ Matrix.Scale(engine_scale, 4)
        @ Matrix.Translation(-engine_pivot)
    )


def create_jetson_thor_mission_computer(parent: bpy.types.Object) -> None:
    """Build the STA 03 NVIDIA Jetson T5000 airborne-compute cutaway.

    NVIDIA's T5000 system-on-module is represented at its published 100 x 87 mm
    envelope. The surrounding cold plate, carrier, shock mounts and aircraft
    harness are integration geometry rather than a claim that the desktop
    developer-kit enclosure flies in the aircraft. The visible hierarchy follows
    NVIDIA's official exploded reference: T5000 PCB and Blackwell package,
    heatsink/fan, carrier I/O and structural outer frame.
    """
    mission_group = bpy.data.objects.new("NVIDIA Jetson T5000 mission computer assembly", None)
    bpy.context.collection.objects.link(mission_group)
    mission_group.parent = parent
    mark_export(mission_group)

    def mission_component(obj: bpy.types.Object) -> bpy.types.Object:
        obj.parent = mission_group
        obj["station"] = "STA 03"
        obj["visualization_detail"] = "official-reference NVIDIA Jetson T5000 mission-compute cutaway"
        return obj

    carrier_x = -1.40
    carrier_y = -0.325
    carrier_z = 0.065

    # Rugged aircraft carrier and shock-isolated mounting tray. This is the
    # integration structure around the published module, not a copy of the
    # desk-oriented developer-kit enclosure.
    mission_component(
        cube(
            "NVIDIA Jetson T5000 aerospace carrier backplane",
            (carrier_x, carrier_y, carrier_z),
            (0.285, 0.012, 0.145),
            JETSON_CARRIER,
            edge=0.012,
        )
    )
    for z_offset, label in ((0.132, "upper"), (-0.132, "lower")):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 {label} structural frame rail",
                (carrier_x, carrier_y - 0.030, carrier_z + z_offset),
                (0.285, 0.022, 0.012),
                ROTAX_STEEL,
                edge=0.006,
            )
        )
    for x_offset, label in ((-0.272, "forward"), (0.272, "aft")):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 {label} structural frame rail",
                (carrier_x + x_offset, carrier_y - 0.030, carrier_z),
                (0.012, 0.022, 0.122),
                ROTAX_STEEL,
                edge=0.006,
            )
        )
    for x_offset in (-0.245, 0.245):
        for z_offset in (-0.105, 0.105):
            mission_component(
                cylinder_between(
                    "NVIDIA Jetson T5000 vibration isolator",
                    (carrier_x + x_offset, carrier_y + 0.018, carrier_z + z_offset),
                    (carrier_x + x_offset, carrier_y - 0.060, carrier_z + z_offset),
                    0.016,
                    ROTAX_RUBBER,
                    vertices=28,
                )
            )
            mission_component(
                cylinder_between(
                    "NVIDIA Jetson T5000 captive mount fastener",
                    (carrier_x + x_offset, carrier_y - 0.062, carrier_z + z_offset),
                    (carrier_x + x_offset, carrier_y - 0.068, carrier_z + z_offset),
                    0.0065,
                    JETSON_CONTACT,
                    vertices=20,
                )
            )

    # The T5000 board itself stays at the official 100 x 87 mm module envelope.
    # It is displayed slightly proud of the cold plate so the package, memory,
    # power stages and edge contacts remain legible through the side cutaway.
    module_x = -1.305
    module_y = -0.407
    module_z = 0.028
    module_board = mission_component(
        cube(
            "NVIDIA Jetson T5000 100x87mm system-on-module PCB",
            (module_x, module_y, module_z),
            (0.050, 0.0032, 0.0435),
            JETSON_PCB,
            edge=0.0025,
        )
    )
    module_board["module_width_mm"] = 100
    module_board["module_height_mm"] = 87
    module_board["module_memory_gb"] = 128
    module_board["memory_bandwidth_gbps"] = 273

    package_y = module_y - 0.0055
    mission_component(
        cube(
            "NVIDIA Jetson T5000 Blackwell multi-chip package",
            (module_x - 0.006, package_y, module_z - 0.004),
            (0.0155, 0.0030, 0.0155),
            JETSON_PACKAGE,
            edge=0.0018,
        )
    )
    mission_component(
        cube(
            "NVIDIA Jetson T5000 exposed Blackwell GPU die",
            (module_x - 0.006, package_y - 0.0033, module_z - 0.004),
            (0.0088, 0.0012, 0.0088),
            JETSON_DIE,
            edge=0.0008,
        )
    )

    memory_positions = (
        (-0.032, -0.024), (-0.032, 0.018),
        (0.021, -0.024), (0.021, 0.018),
        (-0.006, -0.032), (-0.006, 0.026),
        (-0.040, -0.003), (0.030, -0.003),
    )
    for memory_index, (x_offset, z_offset) in enumerate(memory_positions, start=1):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 LPDDR5X package {memory_index:02d}",
                (module_x + x_offset, package_y - 0.0015, module_z + z_offset),
                (0.0070, 0.0018, 0.0048),
                JETSON_MEMORY,
                edge=0.0009,
            )
        )

    for stage_index, x_offset in enumerate((-0.039, -0.026, -0.013, 0.0, 0.013, 0.026, 0.039), start=1):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 power stage {stage_index:02d}",
                (module_x + x_offset, package_y - 0.0012, module_z + 0.036),
                (0.0044, 0.0016, 0.0035),
                JETSON_PACKAGE,
                edge=0.0007,
            )
        )

    # Gold landing pads and high-density board-to-board connector blocks hint at
    # the real 699-pin interface without drawing hundreds of web-heavy objects.
    for pad_index, x_offset in enumerate(
        (-0.044, -0.036, -0.028, -0.020, -0.012, -0.004, 0.004, 0.012, 0.020, 0.028, 0.036, 0.044),
        start=1,
    ):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 representative gold contact {pad_index:02d}",
                (module_x + x_offset, module_y - 0.0043, module_z - 0.039),
                (0.0021, 0.0007, 0.0012),
                JETSON_CONTACT,
                edge=0.0003,
            )
        )
    for z_offset, label in ((-0.018, "lower"), (0.018, "upper")):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 {label} 699-pin interface block",
                (module_x + 0.057, module_y + 0.003, module_z + z_offset),
                (0.007, 0.006, 0.012),
                JETSON_CONNECTOR,
                edge=0.0015,
            )
        )

    # The official architecture pairs the module with a black finned thermal
    # assembly. A compact cold plate and fan sit beside the exposed board in the
    # presentation cutaway so both identifiers remain visible at once.
    heatsink_x = -1.515
    heatsink_z = 0.105
    mission_component(
        cube(
            "NVIDIA Jetson T5000 heatsink cold plate",
            (heatsink_x, -0.372, heatsink_z),
            (0.078, 0.020, 0.066),
            JETSON_HEATSINK,
            edge=0.006,
        )
    )
    for fin_index, x_offset in enumerate(
        (-0.070, -0.060, -0.050, -0.040, -0.030, -0.020, -0.010, 0.0, 0.010, 0.020, 0.030, 0.040, 0.050, 0.060, 0.070),
        start=1,
    ):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 heatsink fin {fin_index:02d}",
                (heatsink_x + x_offset, -0.403, heatsink_z),
                (0.0024, 0.012, 0.062),
                JETSON_HEATSINK,
                edge=0.0008,
            )
        )
    mission_component(
        cylinder_between(
            "NVIDIA Jetson T5000 cooling fan hub",
            (heatsink_x, -0.414, heatsink_z),
            (heatsink_x, -0.427, heatsink_z),
            0.025,
            JETSON_CONNECTOR,
            vertices=40,
        )
    )
    for blade_index in range(7):
        angle = blade_index * math.tau / 7.0
        blade = mission_component(
            cube(
                f"NVIDIA Jetson T5000 cooling fan blade {blade_index + 1:02d}",
                (
                    heatsink_x + math.cos(angle) * 0.038,
                    -0.422,
                    heatsink_z + math.sin(angle) * 0.038,
                ),
                (0.021, 0.003, 0.006),
                JETSON_HEATSINK,
                edge=0.002,
            )
        )
        blade.rotation_euler[1] = -angle
    mission_component(
        cylinder_between(
            "NVIDIA Jetson T5000 fan NVIDIA green badge",
            (heatsink_x, -0.428, heatsink_z),
            (heatsink_x, -0.431, heatsink_z),
            0.011,
            JETSON_GREEN,
            vertices=36,
        )
    )

    # Carrier I/O is reduced to the interfaces relevant to an airborne mission
    # computer: high-speed sensor ingest, Ethernet, CAN and protected power.
    for connector_index, (z_offset, width, label) in enumerate(
        ((0.074, 0.030, "sensor QSFP"), (0.018, 0.026, "5GbE"), (-0.038, 0.022, "CAN"), (-0.088, 0.020, "protected power")),
        start=1,
    ):
        mission_component(
            cube(
                f"NVIDIA Jetson T5000 carrier {label} connector",
                (-1.145, -0.392, carrier_z + z_offset),
                (0.020, 0.025, width * 0.5),
                JETSON_CONNECTOR,
                edge=0.003,
            )
        )
        for contact_index in range(3):
            mission_component(
                cube(
                    f"NVIDIA Jetson T5000 carrier connector contact {connector_index:02d}-{contact_index + 1:02d}",
                    (-1.166 + contact_index * 0.012, -0.418, carrier_z + z_offset),
                    (0.003, 0.0015, width * 0.26),
                    JETSON_CONTACT,
                    edge=0.0007,
                )
            )

    for harness_index, (z_offset, material_value) in enumerate(
        ((0.074, JETSON_CONNECTOR), (0.018, JETSON_CONNECTOR), (-0.088, ROTAX_ACCENT)),
        start=1,
    ):
        harness = curved_tube(
            f"NVIDIA Jetson T5000 aircraft harness {harness_index:02d}",
            [
                (-1.120, -0.365, carrier_z + z_offset),
                (-1.050, -0.300, carrier_z + z_offset * 0.80),
                (-0.965, -0.245, carrier_z + z_offset * 0.60),
            ],
            0.006 if harness_index < 3 else 0.008,
            material_value,
            resolution=3,
        )
        mission_component(harness)

    mission_component(
        raised_cover_text(
            "NVIDIA Jetson T5000 NVIDIA identification",
            "NVIDIA",
            (-1.535, -0.430, -0.030),
            -1.0,
            0.026,
            JETSON_GREEN,
        )
    )
    mission_component(
        raised_cover_text(
            "NVIDIA Jetson T5000 model identification",
            "JETSON T5000",
            (-1.360, -0.430, -0.030),
            -1.0,
            0.018,
            JETSON_LABEL,
        )
    )

    mission_group["official_reference"] = "NVIDIA Jetson Thor T5000 module"
    mission_group["module_dimensions_mm"] = [100, 87]
    mission_group["ai_performance"] = "up to 2070 FP4 TFLOPS sparse at 130 W"
    mission_group["gpu"] = "NVIDIA Blackwell, 2560 CUDA cores, 96 fifth-generation Tensor cores"
    mission_group["cpu"] = "14-core Arm Neoverse V3AE"
    mission_group["memory"] = "128 GB LPDDR5X, 273 GB/s"
    mission_group["installed_architecture"] = "T5000 SoM on illustrative rugged aerospace carrier, cold plate and shock mounts"
    parent["mission_computer_model"] = "NVIDIA Jetson Thor T5000"
    parent["flight_control_separation"] = "mission AI compute is distinct from the safety-critical flight-control layer"


def create_surface_hatch_panel(
    name: str,
    control_loop: list[tuple[float, float]],
    sections: list[tuple[float, float, float, float, float, float]],
    mat: bpy.types.Material,
    thickness: float = 0.012,
    inner_mat: bpy.types.Material | None = None,
    lateral_fraction_range: tuple[float, float] = (1.0, -1.0),
) -> bpy.types.Object:
    """Create a tessellated hatch that follows the curved fuselage belly.

    A single non-planar n-gon can be triangulated differently by Blender and
    the browser renderer, leaving parts of the physical hatch inside the skin.
    This ruled surface samples every longitudinal row across the belly so the
    closed panel remains continuous and flush in both renderers.
    """
    width_by_x: dict[float, float] = {}
    for x, y in control_loop:
        width_by_x[x] = max(width_by_x.get(x, 0.0), abs(y))
    control_rows = sorted(width_by_x.items())
    longitudinal_rows: list[tuple[float, float]] = []
    subdivisions_per_span = 4
    for row_index in range(len(control_rows) - 1):
        start_x, start_width = control_rows[row_index]
        end_x, end_width = control_rows[row_index + 1]
        for subdivision in range(subdivisions_per_span):
            blend = subdivision / subdivisions_per_span
            longitudinal_rows.append(
                (
                    start_x + (end_x - start_x) * blend,
                    start_width + (end_width - start_width) * blend,
                )
            )
    longitudinal_rows.append(control_rows[-1])
    lateral_samples = 13
    outer: list[Vector] = []
    lateral_start, lateral_end = lateral_fraction_range
    for x, half_width in longitudinal_rows:
        for sample in range(lateral_samples):
            fraction = sample / (lateral_samples - 1)
            lateral_fraction = lateral_start + (lateral_end - lateral_start) * fraction
            y = half_width * lateral_fraction
            outer.append(
                # The fuselage skin remains intact in the closed/default state.
                # Seat the physical door just below that outer mold line so its
                # dark inner wall can never peek through as a tapered belly gap.
                Vector(fuselage_lower_surface_point(x, y, sections, outward_offset=-0.0400))
            )
    inner = [Vector((point.x, point.y, point.z + thickness)) for point in outer]
    vertices = [tuple(point) for point in outer + inner]
    surface_count = len(outer)
    faces: list[tuple[int, ...]] = []
    inner_face_indices: list[int] = []
    row_count = len(longitudinal_rows)
    for row in range(row_count - 1):
        for sample in range(lateral_samples - 1):
            a = row * lateral_samples + sample
            b = a + 1
            d = (row + 1) * lateral_samples + sample
            c = d + 1
            faces.append((a, d, c, b))
            faces.append((surface_count + a, surface_count + b, surface_count + c, surface_count + d))
            inner_face_indices.append(len(faces) - 1)

    perimeter: list[int] = []
    perimeter.extend(range(lateral_samples))
    perimeter.extend(row * lateral_samples + lateral_samples - 1 for row in range(1, row_count))
    perimeter.extend(
        range((row_count - 1) * lateral_samples + lateral_samples - 2, (row_count - 1) * lateral_samples - 1, -1)
    )
    perimeter.extend(row * lateral_samples for row in range(row_count - 2, 0, -1))
    side_face_start = len(faces)
    for index, vertex_index in enumerate(perimeter):
        following = perimeter[(index + 1) % len(perimeter)]
        faces.append(
            (vertex_index, following, surface_count + following, surface_count + vertex_index)
        )
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    panel = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(panel)
    assign(panel, mat)
    if inner_mat:
        panel.data.materials.append(inner_mat)
        dark_face_indices = set(inner_face_indices)
        dark_face_indices.update(range(side_face_start, len(faces)))
        for polygon_index in dark_face_indices:
            panel.data.polygons[polygon_index].material_index = 1
    # Keep the aerodynamic outer and inner skins smooth, while the thin edge
    # remains flat. A perimeter bevel used here previously rolled the door skin
    # away from the fuselage and exposed the dark inner material when closed.
    for polygon_index, polygon in enumerate(panel.data.polygons):
        polygon.use_smooth = polygon_index < side_face_start
    mark_export(panel)
    panel["outer_mold_line"] = "sub-skin seated and visually flush when closed"
    panel["closed_surface_offset_m"] = -0.0400
    return panel


def create_point_blank_vtol(
    name: str,
    center: tuple[float, float, float],
    parent: bpy.types.Object,
    featured_payload: bool = False,
    visual_scale: float = 1.0,
    stowed_wing_scale: float = 1.0,
) -> tuple[
    bpy.types.Object,
    list[tuple[str, tuple[float, float, float], list[bpy.types.Object], str]],
    list[tuple[str, tuple[float, float, float], tuple[float, float, float], list[bpy.types.Object]]],
]:
    """Create a public-reference Point Blank external presentation model.

    The proportions follow IAI's public product imagery and published approximate
    one-metre length. Four cruciform wings terminate in compact motor nacelles.
    Only public external features are represented; internal, energetic and
    manufacturing details are intentionally omitted.
    """
    center_x, center_y, center_z = center
    group = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(group)
    group.parent = parent
    group["station"] = "STA 10"
    group["reference"] = "IAI Point Blank public product page and supplied external reference image"
    group["visualization_only"] = True
    group["featured_terminal_guidance_presentation"] = featured_payload
    group["approximate_public_length_m"] = 1.0
    group["approximate_public_weight_kg"] = 10.0
    group["propulsion_layout"] = "four wingtip motor-propeller units on a cruciform X-wing"
    group["presentation_scale"] = visual_scale
    group["magazine_wing_scale"] = stowed_wing_scale
    mark_export(group)

    def drone_component(obj: bpy.types.Object) -> bpy.types.Object:
        obj.parent = group
        obj["station"] = "STA 10"
        return obj

    drone_component(create_loft(
        f"{name} one metre composite fuselage",
        [
            (center_x - 0.500, 0.010, 0.010, center_z),
            (center_x - 0.470, 0.027, 0.025, center_z),
            (center_x - 0.405, 0.035, 0.033, center_z),
            (center_x - 0.285, 0.039, 0.036, center_z),
            (center_x + 0.300, 0.038, 0.035, center_z),
            (center_x + 0.420, 0.032, 0.030, center_z),
            (center_x + 0.485, 0.024, 0.022, center_z),
            (center_x + 0.500, 0.014, 0.013, center_z),
        ],
        POINT_BLANK_BODY,
        ring_segments=40,
        y_offset=center_y,
    ))
    drone_component(
        cylinder_between(
            f"{name} recessed EO day-night aperture",
            (center_x - 0.487, center_y, center_z),
            (center_x - 0.500, center_y, center_z),
            0.013,
            LENS_DARK,
            vertices=32,
        )
    )
    drone_component(cylinder_between(
        f"{name} aft red safety cap",
        (center_x + 0.470, center_y, center_z),
        (center_x + 0.500, center_y, center_z),
        0.011,
        POINT_BLANK_RED,
        vertices=32,
    ))
    if featured_payload:
        drone_component(
            create_loft(
                f"{name} external mission payload fairing",
                [
                    (center_x - 0.405, 0.031, 0.029, center_z),
                    (center_x - 0.380, 0.036, 0.034, center_z),
                    (center_x - 0.245, 0.036, 0.034, center_z),
                    (center_x - 0.220, 0.033, 0.031, center_z),
                ],
                POINT_BLANK_PAYLOAD,
                ring_segments=36,
                y_offset=center_y,
            )
        )
        for payload_edge_x, payload_edge_label in (
            (center_x - 0.380, "forward"),
            (center_x - 0.245, "aft"),
        ):
            drone_component(
                elliptical_ring(
                    f"{name} {payload_edge_label} mission payload interface ring",
                    payload_edge_x,
                    0.0365,
                    0.0345,
                    center_z,
                    0.0014,
                    POINT_BLANK_DARK,
                    group,
                    segments=32,
                    tube_segments=6,
                    y_offset=center_y,
                )
            )
    for ring_x, ring_label in ((center_x - 0.175, "forward"), (center_x + 0.315, "aft")):
        drone_component(
            elliptical_ring(
                f"{name} {ring_label} safety band",
                ring_x,
                0.0355,
                0.0335,
                center_z,
                0.0013,
                POINT_BLANK_DARK,
                group,
                segments=32,
                tube_segments=6,
                y_offset=center_y,
            )
        )

    rotor_blade_sets: list[tuple[str, tuple[float, float, float], list[bpy.types.Object], str]] = []
    wing_bone_sets: list[
        tuple[str, tuple[float, float, float], tuple[float, float, float], list[bpy.types.Object]]
    ] = []

    def create_x_wing_panel(wing_name: str, angle: float) -> bpy.types.Object:
        radial_y, radial_z = math.sin(angle), math.cos(angle)
        tangent_y, tangent_z = math.cos(angle), -math.sin(angle)
        profile = [
            # The root deliberately overlaps the slim fuselage envelope.  It
            # remains a single fixed X configuration in the magazine, during
            # release and in flight; no panel grows out of the body.
            (center_x - 0.100, 0.018),
            (center_x - 0.058, 0.230),
            (center_x + 0.068, 0.230),
            (center_x + 0.105, 0.018),
        ]
        half_thickness = 0.0035
        vertices: list[tuple[float, float, float]] = []
        for tangent in (-half_thickness, half_thickness):
            for x, radius in profile:
                vertices.append((
                    x,
                    center_y + radial_y * radius + tangent_y * tangent,
                    center_z + radial_z * radius + tangent_z * tangent,
                ))
        count = len(profile)
        faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
        for index in range(count):
            following = (index + 1) % count
            faces.append((index, following, count + following, count + index))
        mesh = bpy.data.meshes.new(f"{wing_name} mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        wing = bpy.data.objects.new(wing_name, mesh)
        bpy.context.collection.objects.link(wing)
        assign(wing, POINT_BLANK_BODY)
        bevel(wing, 0.003, 2)
        smooth(wing)
        mark_export(wing)
        return wing

    for wing_index, wing_angle_degrees in enumerate((45.0, 135.0, 225.0, 315.0), start=1):
        wing_angle = math.radians(wing_angle_degrees)
        radial_y, radial_z = math.sin(wing_angle), math.cos(wing_angle)
        wing_label = f"X-wing {wing_index:02d}"
        wing_components: list[bpy.types.Object] = []
        wing = drone_component(create_x_wing_panel(f"{name} {wing_label} aerodynamic panel", wing_angle))
        wing_components.append(wing)

        tip_y = center_y + radial_y * 0.230
        tip_z = center_z + radial_z * 0.230
        motor_center_x = center_x + 0.035
        motor = drone_component(cylinder_between(
            f"{name} {wing_label} wingtip motor nacelle",
            (motor_center_x - 0.055, tip_y, tip_z),
            (motor_center_x + 0.055, tip_y, tip_z),
            0.030,
            POINT_BLANK_DARK,
            vertices=32,
        ))
        wing_components.append(motor)
        motor_band = drone_component(cylinder_between(
            f"{name} {wing_label} motor identification band",
            (motor_center_x - 0.012, tip_y, tip_z),
            (motor_center_x + 0.004, tip_y, tip_z),
            0.0315,
            POINT_BLANK_MOTOR_BAND,
            vertices=32,
        ))
        wing_components.append(motor_band)

        rotor_hub = (motor_center_x - 0.063, tip_y, tip_z)
        rotor_cap = drone_component(cylinder_between(
            f"{name} {wing_label} propeller hub",
            (rotor_hub[0] - 0.010, tip_y, tip_z),
            (rotor_hub[0] + 0.010, tip_y, tip_z),
            0.010,
            POINT_BLANK_DARK,
            vertices=28,
        ))
        wing_components.append(rotor_cap)
        rotor_blades: list[bpy.types.Object] = []
        for blade_index in range(4):
            blade_angle = blade_index * math.tau / 4.0
            blade_radius = 0.052
            blade = drone_component(cube(
                f"{name} {wing_label} propeller blade {blade_index + 1:02d}",
                (
                    rotor_hub[0] - 0.012,
                    tip_y + math.cos(blade_angle) * blade_radius * 0.52,
                    tip_z + math.sin(blade_angle) * blade_radius * 0.52,
                ),
                (0.0025, blade_radius * 0.54, 0.0035),
                POINT_BLANK_BLADE,
                edge=0.002,
            ))
            blade.rotation_euler[0] = blade_angle
            rotor_blades.append(blade)

        hinge_head = (
            center_x + 0.010,
            center_y + radial_y * 0.030,
            center_z + radial_z * 0.030,
        )
        hinge_tail = (
            center_x + 0.010,
            center_y + radial_y * 0.230,
            center_z + radial_z * 0.230,
        )
        wing_bone_sets.append((wing_label, hinge_head, hinge_tail, wing_components))
        rotor_blade_sets.append((wing_label, rotor_hub, rotor_blades, wing_label))

    # Scale the complete public-reference silhouette uniformly.  The four fixed
    # X-wing assemblies remain attached at their true relative span in both the
    # magazine and flight poses.  ``stowed_wing_scale`` is retained only as a
    # compatibility hook for earlier files and is 1.0 in the production scene;
    # no wing grows out of the body during release.
    center_point = Vector(center)
    vehicle_scale_matrix = (
        Matrix.Translation(center_point)
        @ Matrix.Scale(visual_scale, 4)
        @ Matrix.Translation(-center_point)
    )
    for component in tuple(group.children):
        component.matrix_world = vehicle_scale_matrix @ component.matrix_world

    scaled_rotor_sets: list[
        tuple[str, tuple[float, float, float], list[bpy.types.Object], str]
    ] = []
    scaled_wing_sets: list[
        tuple[str, tuple[float, float, float], tuple[float, float, float], list[bpy.types.Object]]
    ] = []
    for wing_set, rotor_set in zip(wing_bone_sets, rotor_blade_sets):
        wing_label, hinge_head, hinge_tail, wing_components = wing_set
        rotor_label, rotor_hub, rotor_blades, rotor_wing_label = rotor_set
        scaled_hinge_head = center_point + (Vector(hinge_head) - center_point) * visual_scale
        scaled_hinge_tail = center_point + (Vector(hinge_tail) - center_point) * visual_scale
        scaled_rotor_hub = center_point + (Vector(rotor_hub) - center_point) * visual_scale
        compact_matrix = (
            Matrix.Translation(scaled_hinge_head)
            @ Matrix.Scale(stowed_wing_scale, 4)
            @ Matrix.Translation(-scaled_hinge_head)
        )
        for component in (*wing_components, *rotor_blades):
            component.matrix_world = compact_matrix @ component.matrix_world
        compact_hinge_tail = scaled_hinge_head + (
            scaled_hinge_tail - scaled_hinge_head
        ) * stowed_wing_scale
        compact_rotor_hub = scaled_hinge_head + (
            scaled_rotor_hub - scaled_hinge_head
        ) * stowed_wing_scale
        scaled_wing_sets.append(
            (
                wing_label,
                tuple(scaled_hinge_head),
                tuple(compact_hinge_tail),
                wing_components,
            )
        )
        scaled_rotor_sets.append(
            (
                rotor_label,
                tuple(compact_rotor_hub),
                rotor_blades,
                rotor_wing_label,
            )
        )

    return group, scaled_rotor_sets, scaled_wing_sets


def create_sta10_deployment_system(
    root: bpy.types.Object,
    fuselage_sections: list[tuple[float, float, float, float, float, float]],
    hatch_control_loop: list[tuple[float, float]],
    gear_assemblies: list[tuple[str, float, tuple[float, float, float], list[bpy.types.Object]]],
) -> None:
    """Build and animate the complete STA 10 airborne release presentation."""
    # Open-bottom bay volume and an orderly two-cell magazine. The cavity sits
    # behind the runtime-fadeable fuselage patch and is invisible in overview.
    bay_center_x = -0.28
    bay_half_length = 0.55
    bay_half_width = 0.205
    bay_cell_y = 0.070
    bay_parts = [
        cube("STA 10 magazine ceiling", (bay_center_x, 0.0, 0.145), (bay_half_length, bay_half_width, 0.010), DRONE_BAY_VOID, 0.008),
        cube("STA 10 port magazine wall", (bay_center_x, bay_half_width, 0.000), (bay_half_length, 0.010, 0.135), DRONE_BAY_VOID, 0.006),
        cube("STA 10 starboard magazine wall", (bay_center_x, -bay_half_width, 0.000), (bay_half_length, 0.010, 0.135), DRONE_BAY_VOID, 0.006),
        cube("STA 10 forward magazine bulkhead", (bay_center_x - bay_half_length, 0.0, 0.000), (0.010, bay_half_width, 0.135), DRONE_BAY_VOID, 0.006),
        cube("STA 10 aft magazine bulkhead", (bay_center_x + bay_half_length, 0.0, 0.000), (0.010, bay_half_width, 0.135), DRONE_BAY_VOID, 0.006),
        cube("STA 10 port deployment rail", (bay_center_x, bay_cell_y, -0.070), (0.515, 0.010, 0.008), DRONE_RACK, 0.004),
        cube("STA 10 starboard deployment rail", (bay_center_x, -bay_cell_y, -0.070), (0.515, 0.010, 0.008), DRONE_RACK, 0.004),
        cube("STA 10 port recessed aperture frame", (bay_center_x, 0.187, -0.137), (0.520, 0.006, 0.007), DRONE_RACK, 0.003),
        cube("STA 10 starboard recessed aperture frame", (bay_center_x, -0.187, -0.137), (0.520, 0.006, 0.007), DRONE_RACK, 0.003),
        cube("STA 10 forward recessed aperture frame", (bay_center_x - 0.520, 0.0, -0.137), (0.008, 0.180, 0.007), DRONE_RACK, 0.003),
        cube("STA 10 aft recessed aperture frame", (bay_center_x + 0.520, 0.0, -0.137), (0.008, 0.145, 0.007), DRONE_RACK, 0.003),
        cube("STA 10 port low-level magazine guide light", (bay_center_x, 0.193, -0.080), (0.470, 0.003, 0.003), DRONE_BAY_LIGHT, 0.002),
        cube("STA 10 starboard low-level magazine guide light", (bay_center_x, -0.193, -0.080), (0.470, 0.003, 0.003), DRONE_BAY_LIGHT, 0.002),
    ]
    for bay_part in bay_parts:
        bay_part.parent = root
        bay_part["station"] = "STA 10"

    for cradle_y, cradle_label in ((bay_cell_y, "port"), (-bay_cell_y, "starboard")):
        cradle = cube(
            f"STA 10 {cradle_label} shock-isolated launch cradle",
            (bay_center_x, cradle_y, -0.062),
            (0.505, 0.032, 0.008),
            DRONE_RACK,
            edge=0.006,
        )
        cradle.parent = root
        for x_offset, side_name in ((-0.405, "forward"), (0.405, "aft")):
            restraint = cube(
                f"STA 10 {cradle_label} {side_name} restraint shoe",
                (bay_center_x + x_offset, cradle_y, -0.035),
                (0.030, 0.032, 0.026),
                DRONE_RACK,
                edge=0.006,
            )
            restraint.parent = root

    hatch_panels: list[tuple[str, float, bpy.types.Object]] = []
    for side_label, side, lateral_range in (
        ("port", 1.0, (1.0, 0.0)),
        ("starboard", -1.0, (0.0, -1.0)),
    ):
        hatch_panel = create_surface_hatch_panel(
            f"STA 10 flush animated {side_label} deployment door",
            hatch_control_loop,
            fuselage_sections,
            STA10_DOOR_OUTER,
            thickness=0.010,
            inner_mat=STA10_DOOR_INNER,
            lateral_fraction_range=lateral_range,
        )
        hatch_panel.parent = root
        hatch_panel["station"] = "STA 10"
        hatch_panel["door_layout"] = "paired conformal outward-opening longitudinal doors"
        hatch_panels.append((side_label, side, hatch_panel))

    # Two faithful, uniformly reduced vehicles sit laterally side-by-side on
    # separate rails.  A small longitudinal stagger prevents the fixed X-wing
    # assemblies from intersecting while preserving the public silhouette.
    # Nothing changes scale or grows after release.
    stowed_drone_scale = 0.65
    stowed_wing_scale = 1.0
    drone_origins = [
        (bay_center_x - 0.140, bay_cell_y, -0.010),
        (bay_center_x + 0.140, -bay_cell_y, -0.010),
    ]
    created_drones = [
        create_point_blank_vtol(
            "STA 10 Point Blank vehicle 01",
            drone_origins[0],
            root,
            featured_payload=True,
            visual_scale=stowed_drone_scale,
            stowed_wing_scale=stowed_wing_scale,
        ),
        create_point_blank_vtol(
            "STA 10 Point Blank vehicle 02",
            drone_origins[1],
            root,
            visual_scale=stowed_drone_scale,
            stowed_wing_scale=stowed_wing_scale,
        ),
    ]
    released_drones = [created_drone[0] for created_drone in created_drones]
    rotor_sets_by_drone = [created_drone[1] for created_drone in created_drones]
    wing_sets_by_drone = [created_drone[2] for created_drone in created_drones]

    armature_data = bpy.data.armatures.new("STA 10 deployment animation rig data")
    armature = bpy.data.objects.new("STA 10 deployment animation rig", armature_data)
    bpy.context.collection.objects.link(armature)
    armature.parent = root
    armature["animation"] = "airborne gear retraction, hatch opening and sequential VTOL release"
    mark_export(armature)

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    bone_specs: list[tuple[str, tuple[float, float, float], tuple[float, float, float]]] = []
    for label, _side, pivot, _parts in gear_assemblies:
        bone_specs.append((f"{label} main gear retract", pivot, (pivot[0] + 0.24, pivot[1], pivot[2])))
    for side_label, side, _hatch_panel in hatch_panels:
        door_head = (bay_center_x - 0.520, side * 0.190, -0.150)
        door_tail = (bay_center_x + 0.520, side * 0.190, -0.150)
        bone_specs.append((f"STA 10 {side_label} hatch hinge", door_head, door_tail))
    for drone_index, origin in enumerate(drone_origins, start=1):
        bone_specs.append(
            (
                f"STA 10 vehicle {drone_index:02d} release",
                origin,
                (origin[0], origin[1], origin[2] + 0.12),
            )
        )
    edit_bones_by_name: dict[str, bpy.types.EditBone] = {}
    for bone_name, head, tail in bone_specs:
        edit_bone = armature.data.edit_bones.new(bone_name)
        edit_bone.head = head
        edit_bone.tail = tail
        edit_bone.use_deform = False
        edit_bones_by_name[bone_name] = edit_bone

    wing_bone_bindings: list[tuple[str, list[bpy.types.Object], int]] = []
    rotor_bone_bindings: list[tuple[str, list[bpy.types.Object], float]] = []
    for drone_index, wing_sets in enumerate(wing_sets_by_drone, start=1):
        release_bone_name = f"STA 10 vehicle {drone_index:02d} release"
        for wing_label, hinge_head, hinge_tail, wing_components in wing_sets:
            wing_bone_name = f"STA 10 vehicle {drone_index:02d} {wing_label} deploy"
            wing_bone = armature.data.edit_bones.new(wing_bone_name)
            wing_bone.head = hinge_head
            wing_bone.tail = hinge_tail
            wing_bone.parent = edit_bones_by_name[release_bone_name]
            wing_bone.use_deform = False
            wing_bone_bindings.append((wing_bone_name, wing_components, drone_index))
    for drone_index, rotor_sets in enumerate(rotor_sets_by_drone, start=1):
        for rotor_index, (rotor_label, hub, rotor_blades, wing_label) in enumerate(rotor_sets, start=1):
            rotor_bone_name = f"STA 10 vehicle {drone_index:02d} {rotor_label} rotor spin"
            rotor_bone = armature.data.edit_bones.new(rotor_bone_name)
            rotor_bone.head = (hub[0] - 0.030, hub[1], hub[2])
            rotor_bone.tail = (hub[0] + 0.030, hub[1], hub[2])
            rotor_bone.parent = armature.data.edit_bones[f"STA 10 vehicle {drone_index:02d} {wing_label} deploy"]
            rotor_bone.use_deform = False
            spin_direction = 1.0 if rotor_index % 2 else -1.0
            rotor_bone_bindings.append((rotor_bone_name, rotor_blades, spin_direction))
    bpy.ops.object.mode_set(mode="POSE")

    def parent_to_bone_keep_world(obj: bpy.types.Object, bone_name: str) -> None:
        world_matrix = obj.matrix_world.copy()
        obj.parent = armature
        obj.parent_type = "BONE"
        obj.parent_bone = bone_name
        obj.matrix_world = world_matrix

    for label, _side, _pivot, parts in gear_assemblies:
        for part in parts:
            parent_to_bone_keep_world(part, f"{label} main gear retract")
    for side_label, _side, hatch_panel in hatch_panels:
        parent_to_bone_keep_world(hatch_panel, f"STA 10 {side_label} hatch hinge")
    for drone_index, drone in enumerate(released_drones, start=1):
        parent_to_bone_keep_world(drone, f"STA 10 vehicle {drone_index:02d} release")
    for wing_bone_name, wing_components, _drone_index in wing_bone_bindings:
        for wing_component in wing_components:
            parent_to_bone_keep_world(wing_component, wing_bone_name)
    for rotor_bone_name, rotor_blades, _spin_direction in rotor_bone_bindings:
        for rotor_blade in rotor_blades:
            parent_to_bone_keep_world(rotor_blade, rotor_bone_name)

    action = bpy.data.actions.new("STA10_DEPLOYMENT_DEMO")
    armature.animation_data_create()
    armature.animation_data.action = action

    def keyframe_pose_rotation(pose_bone: bpy.types.PoseBone, frame: int, y_rotation: float) -> None:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, y_rotation, 0.0)
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=pose_bone.name)

    def keyframe_rotor_spin(pose_bone: bpy.types.PoseBone, frame: int, rotor_rotation: float) -> None:
        pose_bone.rotation_mode = "XYZ"
        # Blender bones use local Y along head-to-tail. Point Blank rotor bones
        # run along the nacelle/vehicle X axis, matching the public X-wing view.
        pose_bone.rotation_euler = (0.0, rotor_rotation, 0.0)
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=pose_bone.name)

    def keyframe_wing_extension(pose_bone: bpy.types.PoseBone, frame: int, extension: float) -> None:
        # The compact magazine state draws the four radial assemblies toward the
        # fuselage. After the vehicle clears the bay they extend to the public
        # cruciform silhouette. This is a visual stow/deploy treatment only.
        pose_bone.scale = (extension, extension, extension)
        pose_bone.keyframe_insert(data_path="scale", frame=frame, group=pose_bone.name)

    def keyframe_pose_translation(
        pose_bone: bpy.types.PoseBone,
        frame: int,
        aircraft_delta: tuple[float, float, float],
    ) -> None:
        rest_rotation = pose_bone.bone.matrix_local.to_3x3()
        pose_bone.location = rest_rotation.inverted() @ Vector(aircraft_delta)
        pose_bone.keyframe_insert(data_path="location", frame=frame, group=pose_bone.name)

    def keyframe_drone_attitude(
        pose_bone: bpy.types.PoseBone,
        frame: int,
        aircraft_rotation_degrees: tuple[float, float, float],
    ) -> None:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = tuple(
            math.radians(value) for value in aircraft_rotation_degrees
        )
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=pose_bone.name)

    # Both main gears fold inboard by a true 90 degrees before the hatch opens.
    for label, side, _pivot, _parts in gear_assemblies:
        pose_bone = armature.pose.bones[f"{label} main gear retract"]
        for frame in (1, 10):
            keyframe_pose_rotation(pose_bone, frame, 0.0)
        for frame in (58, 330):
            keyframe_pose_rotation(pose_bone, frame, math.radians(-90.0 * side))

    for side_label, side, _hatch_panel in hatch_panels:
        hatch_bone = armature.pose.bones[f"STA 10 {side_label} hatch hinge"]
        for frame in (1, 56):
            keyframe_pose_rotation(hatch_bone, frame, 0.0)
        for frame in (96, 330):
            keyframe_pose_rotation(hatch_bone, frame, math.radians(128.0 * side))

    # The release paths include a positive clearance hold after both doors have
    # reached their fully open stops at frame 96.  Each vehicle first translates
    # vertically through the unobstructed centre corridor before beginning its
    # lateral flight path, so no part of the X-wing or rotor envelope intersects
    # either door.
    release_paths = (
        (
            (1, (0.0, 0.0, 0.0)),
            (120, (0.0, 0.0, 0.0)),
            (150, (0.0, 0.0, -0.44)),
            (185, (1.25, -0.82, -1.24)),
            (220, (2.15, -1.40, -2.10)),
            (275, (3.25, -2.10, -1.55)),
            (330, (3.60, -2.15, -1.05)),
        ),
        (
            (1, (0.0, 0.0, 0.0)),
            (165, (0.0, 0.0, 0.0)),
            (195, (0.0, 0.0, -0.42)),
            (220, (1.28, 0.96, -1.52)),
            (275, (2.10, 1.50, -1.10)),
            (330, (3.05, 1.90, -0.70)),
        ),
    )
    flight_attitudes = (
        (
            (1, (0.0, 0.0, 0.0)),
            (150, (0.0, 0.0, 0.0)),
            (185, (-6.0, 4.0, -10.0)),
            (220, (-14.0, 8.0, -16.0)),
            (275, (10.0, -5.0, -8.0)),
            (330, (0.0, 0.0, 0.0)),
        ),
        (
            (1, (0.0, 0.0, 0.0)),
            (195, (0.0, 0.0, 0.0)),
            (220, (12.0, -7.0, 14.0)),
            (275, (-9.0, 5.0, 7.0)),
            (330, (0.0, 0.0, 0.0)),
        ),
    )
    for drone_index, path in enumerate(release_paths, start=1):
        pose_bone = armature.pose.bones[f"STA 10 vehicle {drone_index:02d} release"]
        for frame, delta in path:
            keyframe_pose_translation(pose_bone, frame, delta)
        for frame, rotation in flight_attitudes[drone_index - 1]:
            keyframe_drone_attitude(pose_bone, frame, rotation)

    deployed_wing_extension = 1.0
    for wing_bone_name, _wing_components, drone_index in wing_bone_bindings:
        pose_bone = armature.pose.bones[wing_bone_name]
        if drone_index == 1:
            keyframe_wing_extension(pose_bone, 1, 1.0)
            keyframe_wing_extension(pose_bone, 126, deployed_wing_extension)
            keyframe_wing_extension(pose_bone, 154, deployed_wing_extension)
            keyframe_wing_extension(pose_bone, 330, deployed_wing_extension)
        else:
            keyframe_wing_extension(pose_bone, 1, 1.0)
            keyframe_wing_extension(pose_bone, 162, deployed_wing_extension)
            keyframe_wing_extension(pose_bone, 190, deployed_wing_extension)
            keyframe_wing_extension(pose_bone, 330, deployed_wing_extension)

    # Counter-rotating blades start slowly and accelerate smoothly.  Dense
    # per-frame keys keep every angular step below pi, preventing glTF quaternion
    # interpolation from appearing to reverse, hesitate or rotate off-axis.
    for rotor_bone_name, _rotor_blades, spin_direction in rotor_bone_bindings:
        pose_bone = armature.pose.bones[rotor_bone_name]
        keyframe_rotor_spin(pose_bone, 1, 0.0)
        keyframe_rotor_spin(pose_bone, 86, 0.0)
        spool_frames = 42.0
        maximum_radians_per_frame = math.tau * 4.5 / 24.0
        for frame in range(87, 331):
            elapsed = float(frame - 86)
            if elapsed <= spool_frames:
                rotor_rotation = (
                    maximum_radians_per_frame
                    * elapsed**3
                    / (3.0 * spool_frames**2)
                )
            else:
                spool_rotation = maximum_radians_per_frame * spool_frames / 3.0
                rotor_rotation = spool_rotation + maximum_radians_per_frame * (
                    elapsed - spool_frames
                )
            keyframe_rotor_spin(pose_bone, frame, spin_direction * rotor_rotation)

    bpy.ops.object.mode_set(mode="OBJECT")
    root["sta10_payload_reference"] = "IAI Point Blank public product page and supplied external imagery"
    root["sta10_loaded_vehicle_count"] = 2
    root["sta10_magazine_layout"] = "two laterally adjacent fixed X-wing vehicles on staggered independent rails"
    root["sta10_vehicle_presentation_scale"] = stowed_drone_scale
    root["sta10_vehicle_public_length_m"] = 1.0
    root["sta10_vehicle_public_weight_kg"] = 10.0
    root["sta10_vehicle_public_max_speed_mps"] = 80.0
    root["sta10_demo_animation"] = "STA10_DEPLOYMENT_DEMO"
    root["sta10_release_interlock"] = "both doors fully open at frame 96; first release held to frame 120; second release held to frame 165"
    root["sta10_clearance_corridor"] = "vertical centreline extraction before lateral departure"
    root["sta10_flight_segment"] = "formation flight followed by featured vehicle close-up"
    root["sta10_demo_scope"] = "visual concept only, not production or release-system geometry"


def radial_store_fin(
    name: str,
    center_y: float,
    center_z: float,
    angle: float,
    profile: list[tuple[float, float]],
    thickness: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    """Create a presentation-only aerodynamic fin around an X-axis store."""
    radial_y, radial_z = math.sin(angle), math.cos(angle)
    tangent_y, tangent_z = math.cos(angle), -math.sin(angle)
    vertices: list[tuple[float, float, float]] = []
    for tangent in (-thickness, thickness):
        for x, radius in profile:
            vertices.append(
                (
                    x,
                    center_y + radial_y * radius + tangent_y * tangent,
                    center_z + radial_z * radius + tangent_z * tangent,
                )
            )
    count = len(profile)
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bevel(obj, 0.010, 2)
    smooth(obj)
    mark_export(obj)
    obj.parent = parent
    return obj


def airfoil_half(
    name: str,
    side: float,
    stations: list[tuple[float, float, float, float, float, float]],
    mat: bpy.types.Material,
    chord_points: int = 32,
) -> bpy.types.Object:
    """Create a smooth, closed lifting surface from real airfoil sections.

    Each station is: span, leading-edge X, chord, Z, thickness ratio,
    incidence in degrees. Cosine spacing produces a properly rounded leading
    edge rather than the rectangular slab used in the early visualization.
    """
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    perimeter_size = chord_points * 2
    for span, lead, chord, z_base, thickness_ratio, incidence_deg in stations:
        perimeter: list[tuple[float, float, float]] = []
        incidence = math.radians(incidence_deg)
        quarter_chord = lead + chord * 0.25

        for reverse, upper in ((False, True), (True, False)):
            indices = range(chord_points - 1, -1, -1) if reverse else range(chord_points)
            for idx in indices:
                u = 0.5 * (1.0 - math.cos(math.pi * idx / (chord_points - 1)))
                thickness = 5.0 * thickness_ratio * chord * (
                    0.2969 * math.sqrt(max(u, 0.0))
                    - 0.1260 * u
                    - 0.3516 * u**2
                    + 0.2843 * u**3
                    - 0.1036 * u**4
                )
                camber = 0.012 * chord * math.sin(math.pi * u)
                local_z = camber + (thickness if upper else -thickness)
                local_x = lead + chord * u - quarter_chord
                x = quarter_chord + local_x * math.cos(incidence) + local_z * math.sin(incidence)
                z = z_base - local_x * math.sin(incidence) + local_z * math.cos(incidence)
                perimeter.append((x, span * side, z))
        verts.extend(perimeter)

    for station in range(len(stations) - 1):
        current = station * perimeter_size
        following = (station + 1) * perimeter_size
        for idx in range(perimeter_size):
            nxt = (idx + 1) % perimeter_size
            faces.append((current + idx, following + idx, following + nxt, current + nxt))

    faces.append(tuple(range(perimeter_size - 1, -1, -1)))
    last = (len(stations) - 1) * perimeter_size
    faces.append(tuple(last + idx for idx in range(perimeter_size)))

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    return obj


def bent_airfoil_half(
    name: str,
    side: float,
    stations: list[tuple[float, float, float, float, float, float, float]],
    mat: bpy.types.Material,
    chord_points: int = 52,
) -> bpy.types.Object:
    """Create one continuous lifting surface through a bent wingtip.

    Each station is ``(span, z, leading_x, chord, thickness_ratio,
    incidence_deg, section_roll_deg)``.  Rotating the airfoil section from
    horizontal to vertical within one loft removes the overlapping end caps
    that previously produced a step and a lower-surface bulge at the winglet
    transition.
    """
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    perimeter_size = chord_points * 2

    for span, z_base, lead, chord, thickness_ratio, incidence_deg, roll_deg in stations:
        incidence = math.radians(incidence_deg)
        roll = math.radians(roll_deg)
        quarter_chord = lead + chord * 0.25
        perimeter: list[tuple[float, float, float]] = []
        for reverse, upper in ((False, True), (True, False)):
            indices = range(chord_points - 1, -1, -1) if reverse else range(chord_points)
            for index in indices:
                u = 0.5 * (1.0 - math.cos(math.pi * index / (chord_points - 1)))
                thickness = 5.0 * thickness_ratio * chord * (
                    0.2969 * math.sqrt(max(u, 0.0))
                    - 0.1260 * u
                    - 0.3516 * u**2
                    + 0.2843 * u**3
                    - 0.1036 * u**4
                )
                camber = 0.012 * chord * math.sin(math.pi * u)
                profile_z = camber + (thickness if upper else -thickness)
                profile_x = lead + chord * u - quarter_chord
                x = quarter_chord + profile_x * math.cos(incidence) + profile_z * math.sin(incidence)
                section_z = -profile_x * math.sin(incidence) + profile_z * math.cos(incidence)
                y = span * side - section_z * math.sin(roll) * side
                z = z_base + section_z * math.cos(roll)
                perimeter.append((x, y, z))
        vertices.extend(perimeter)

    for station in range(len(stations) - 1):
        current = station * perimeter_size
        following = (station + 1) * perimeter_size
        for index in range(perimeter_size):
            next_index = (index + 1) % perimeter_size
            faces.append(
                (
                    current + index,
                    following + index,
                    following + next_index,
                    current + next_index,
                )
            )
    faces.append(tuple(range(perimeter_size - 1, -1, -1)))
    last = (len(stations) - 1) * perimeter_size
    faces.append(tuple(last + index for index in range(perimeter_size)))

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    return obj


def wing_half(name: str, side: float) -> bpy.types.Object:
    """AMT-200S planform with a single continuous 25-degree winglet loft."""
    dihedral = math.tan(math.radians(2.5))
    root_z = -0.25
    wing_tip_z = root_z + 8.735 * dihedral
    stations = [
        # span, z, leading x, chord, NACA thickness ratio, incidence, section roll
        (0.00, root_z, -2.22, 1.48, 0.16, 2.0, 0.0),
        (1.40, root_z + 1.40 * dihedral, -2.18, 1.38, 0.16, 1.7, 0.0),
        (4.80, root_z + 4.80 * dihedral, -1.98, 1.04, 0.15, 0.8, 0.0),
        (8.735, wing_tip_z, -1.730, 0.580, 0.130, 0.0, 0.0),
        # The first three tip stations follow one clean 25-degree trapezoidal
        # plane.  The next two roll the section through a compact fillet into
        # the vertical winglet without adding a second capped mesh.
        (8.840, wing_tip_z + 0.048, -1.710, 0.540, 0.128, 0.0, 8.0),
        (8.960, wing_tip_z + 0.104, -1.670, 0.490, 0.125, 0.0, 18.0),
        (9.055, wing_tip_z + 0.148, -1.645, 0.455, 0.130, 0.0, 35.0),
        (9.085, wing_tip_z + 0.205, -1.625, 0.430, 0.125, 0.0, 68.0),
        (9.090, wing_tip_z + 0.255, -1.610, 0.405, 0.120, 0.0, 90.0),
        (9.090, wing_tip_z + 0.605, -1.485, 0.285, 0.110, 0.0, 90.0),
    ]
    wing = bent_airfoil_half(name, side, stations, IAF_GRAY, chord_points=52)
    wing["tip_transition_angle_deg"] = 25.0
    wing["winglet_height_scale"] = 0.75
    wing["construction"] = "single continuous bent airfoil loft; no overlap, boolean, or internal cap"
    return wing


def wing_root_fillet(name: str, side: float) -> bpy.types.Object:
    """Create the broad saddle fairing that blends each wing into the fuselage."""
    # y, center x, x radius, z radius, center z
    sections = [
        (0.30, -1.48, 1.02, 0.25, -0.20),
        (0.52, -1.48, 0.94, 0.22, -0.20),
        (0.82, -1.47, 0.84, 0.18, -0.195),
        (1.12, -1.47, 0.75, 0.145, -0.19),
        (1.40, -1.49, 0.69, 0.125, -0.19),
    ]
    ring_segments = 56
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for y, center_x, radius_x, radius_z, center_z in sections:
        for idx in range(ring_segments):
            angle = 2.0 * math.pi * idx / ring_segments
            verts.append(
                (
                    center_x + math.cos(angle) * radius_x,
                    y * side,
                    center_z + math.sin(angle) * radius_z,
                )
            )
    for ring in range(len(sections) - 1):
        for idx in range(ring_segments):
            nxt = (idx + 1) % ring_segments
            a = ring * ring_segments + idx
            b = ring * ring_segments + nxt
            c = (ring + 1) * ring_segments + nxt
            d = (ring + 1) * ring_segments + idx
            faces.append((a, b, c, d))
    faces.append(tuple(range(ring_segments - 1, -1, -1)))
    last = (len(sections) - 1) * ring_segments
    faces.append(tuple(last + idx for idx in range(ring_segments)))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, IAF_GRAY)
    smooth(obj)
    mark_export(obj)
    return obj


def fin_mesh(
    name: str,
    points: list[tuple[float, float]],
    thickness: float,
    mat: bpy.types.Material,
    y_offset: float = 0.0,
) -> bpy.types.Object:
    verts = [(x, y_offset - thickness, z) for x, z in points] + [
        (x, y_offset + thickness, z) for x, z in points
    ]
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bevel(obj, 0.018, 2)
    smooth(obj)
    mark_export(obj)
    return obj


def vertical_airfoil_fin(
    name: str,
    stations: list[tuple[float, float, float, float]],
    mat: bpy.types.Material,
    chord_points: int = 44,
) -> bpy.types.Object:
    """Create a tapered symmetric vertical-tail airfoil instead of a flat plate.

    Each station is ``(z, leading_x, chord, thickness_ratio)``.  The rounded
    leading edge, thickness distribution and closed trailing edge are carried
    through the complete fin height, then tapered with the planform.
    """
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    perimeter_size = chord_points * 2
    for z, leading_x, chord, thickness_ratio in stations:
        perimeter: list[tuple[float, float, float]] = []
        for lateral_sign, indices in (
            (1.0, range(chord_points)),
            (-1.0, range(chord_points - 1, -1, -1)),
        ):
            for index in indices:
                u = 0.5 * (1.0 - math.cos(math.pi * index / (chord_points - 1)))
                half_thickness = 5.0 * thickness_ratio * chord * (
                    0.2969 * math.sqrt(max(u, 0.0))
                    - 0.1260 * u
                    - 0.3516 * u**2
                    + 0.2843 * u**3
                    - 0.1036 * u**4
                )
                perimeter.append(
                    (leading_x + chord * u, lateral_sign * half_thickness, z)
                )
        vertices.extend(perimeter)

    for station in range(len(stations) - 1):
        current = station * perimeter_size
        following = (station + 1) * perimeter_size
        for index in range(perimeter_size):
            next_index = (index + 1) % perimeter_size
            faces.append(
                (
                    current + index,
                    following + index,
                    following + next_index,
                    current + next_index,
                )
            )
    faces.append(tuple(range(perimeter_size - 1, -1, -1)))
    last = (len(stations) - 1) * perimeter_size
    faces.append(tuple(last + index for index in range(perimeter_size)))

    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    return obj


def canted_fin_mesh(
    name: str,
    points: list[tuple[float, float, float]],
    thickness: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    """Extrude an already canted side profile across its local spanwise depth."""
    verts = [(x, y - thickness, z) for x, y, z in points] + [
        (x, y + thickness, z) for x, y, z in points
    ]
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for index in range(n):
        following = (index + 1) % n
        faces.append((index, following, n + following, n + index))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    bevel(obj, 0.014, 3)
    smooth(obj)
    mark_export(obj)
    return obj


def vertical_pylon_airfoil(
    name: str,
    y_offset: float,
    stations: list[tuple[float, float, float, float]],
    mat: bpy.types.Material,
    chord_points: int = 36,
) -> bpy.types.Object:
    """Create a short tapered NACA-like pylon with rounded leading edges.

    Each station is ``(z, leading_x, chord, thickness_ratio)``.  This avoids
    the slab-sided external-store bracket that previously met the wing and
    tank with abrupt corners.
    """
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    perimeter_size = chord_points * 2
    for z, leading_x, chord, thickness_ratio in stations:
        perimeter: list[tuple[float, float, float]] = []
        for lateral_sign, indices in (
            (1.0, range(chord_points)),
            (-1.0, range(chord_points - 1, -1, -1)),
        ):
            for index in indices:
                u = 0.5 * (1.0 - math.cos(math.pi * index / (chord_points - 1)))
                half_thickness = 5.0 * thickness_ratio * chord * (
                    0.2969 * math.sqrt(max(u, 0.0))
                    - 0.1260 * u
                    - 0.3516 * u**2
                    + 0.2843 * u**3
                    - 0.1036 * u**4
                )
                perimeter.append(
                    (leading_x + chord * u, y_offset + lateral_sign * half_thickness, z)
                )
        vertices.extend(perimeter)

    for station in range(len(stations) - 1):
        current = station * perimeter_size
        following = (station + 1) * perimeter_size
        for index in range(perimeter_size):
            next_index = (index + 1) % perimeter_size
            faces.append(
                (
                    current + index,
                    following + index,
                    following + next_index,
                    current + next_index,
                )
            )
    faces.append(tuple(range(perimeter_size - 1, -1, -1)))
    last = (len(stations) - 1) * perimeter_size
    faces.append(tuple(last + index for index in range(perimeter_size)))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    mark_export(obj)
    return obj


def add_airframe_surface_details(root: bpy.types.Object) -> None:
    """Add restrained scale cues found on a composite production airframe."""
    # Flap and aileron hinge lines are surface-conforming, zero-thickness ribbons.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        wing_surface_seam(
            f"{label} flap hinge",
            [
                (-1.09, 1.48 * side, -0.120),
                (-1.10, 3.18 * side, -0.055),
                (-1.13, 4.70 * side, 0.010),
            ],
            0.0080,
            SEAM,
            root,
        )
        wing_surface_seam(
            f"{label} aileron hinge",
            [
                (-1.14, 4.84 * side, 0.018),
                (-1.20, 6.62 * side, 0.095),
                (-1.28, 8.46 * side, 0.170),
            ],
            0.0070,
            SEAM,
            root,
        )
        surface_detail_line(
            f"{label} elevator hinge",
            [
                (3.50, 0.12 * side, 1.322),
                (3.50, 1.74 * side, 1.328),
            ],
            0.0050,
            SEAM,
            root,
        )

        # The rudder hinge is repeated on both exposed faces of the vertical
        # fin so the control-surface break remains legible from either side.
        surface_detail_line(
            f"{label} rudder hinge",
            [
                (3.585, 0.046 * side, 0.035),
                (3.555, 0.032 * side, 0.66),
                (3.535, 0.022 * side, 1.275),
            ],
            0.0050,
            SEAM,
            root,
        )

        # Position lights sit at the outer forward corners of the winglets.
        # Port/left is red and starboard/right is green. Placing the lenses at
        # the maximum lateral extent keeps their arcs legible from ahead and
        # from the side instead of floating above the middle of each winglet.
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=48,
            ring_count=24,
            radius=0.012,
            location=(-1.455, 9.090 * side, 0.690),
        )
        navigation_light = bpy.context.object
        navigation_light.name = f"{label} navigation lens"
        navigation_light.scale = (1.55, 0.42, 0.72)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(navigation_light, NAV_RED if side > 0 else NAV_GREEN)
        smooth(navigation_light)
        mark_export(navigation_light)
        navigation_light.parent = root

    # A white aft-facing position light completes the three-color navigation
    # set without adding a protruding beacon or unrelated external hardware.
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=40,
        ring_count=20,
        radius=0.024,
        location=(3.925, 0.0, -0.105),
    )
    aft_navigation_light = bpy.context.object
    aft_navigation_light.name = "Aft navigation lens"
    aft_navigation_light.scale = (1.18, 0.72, 0.72)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(aft_navigation_light, NAV_WHITE)
    smooth(aft_navigation_light)
    mark_export(aft_navigation_light)
    aft_navigation_light.parent = root

def create_aircraft() -> bpy.types.Object:
    root = bpy.data.objects.new("AI.onSuper visualization model", None)
    bpy.context.collection.objects.link(root)
    root["visualization_only"] = True
    root["reference_span_m"] = 17.47
    root["reference_length_m"] = 8.08
    root["reference_wing_area_m2"] = 18.70
    root["reference_airfoil"] = "NACA 64(3)-618"
    root["reference_main_gear_track_m"] = 2.80
    root["reference_gear_axis_spacing_m"] = 5.35
    root["landing_gear_layout"] = "two wing-mounted main gears with extended aft-and-outboard-canted legs, asymmetric right-angle wedge covers and exposed tire contact sections, plus compact tail wheel; no nose wheel"
    root["external_store_visualization"] = "two symmetric nonfunctional external fuel-tank visualizations carried below the wing skins on short streamlined pylons"
    root["external_fuel_tank_scale"] = 0.80
    root["winglet_height_scale"] = 0.75
    root["kinetic_gimbal_scale"] = 0.75
    root["kinetic_gimbal_mount_x_m"] = -1.82
    root["vr_camera_mount_x_m"] = -2.38
    root["vr_camera_view"] = "downward wide-angle stereo, clear of propeller disk"
    root["cooling_inlet"] = "single shallow chin ram-air inlet for radiator and intercooler"
    root["mission_system_geometry"] = "illustrative external visualization only"
    # A compact tail assembly creates the characteristic tail-down ground
    # attitude while keeping all three tires on the same apron plane.
    root["ground_attitude_deg"] = 6.9
    root.rotation_euler[1] = math.radians(6.9)
    mark_export(root)

    fuselage_sections = [
            # x, half-width, crown, belly, center z, section exponent
            # The forward spinner transition remains locally rounded.  From
            # the cowling rearward, lower exponents create flatter shoulders,
            # defined side walls and a shallower belly instead of a long tube.
            (-3.84, 0.195, 0.165, 0.150, 0.000, 0.82),
            (-3.62, 0.305, 0.235, 0.205, 0.005, 0.62),
            (-3.30, 0.390, 0.285, 0.270, 0.010, 0.50),
            (-2.92, 0.445, 0.305, 0.310, 0.016, 0.44),
            (-2.50, 0.475, 0.300, 0.350, 0.024, 0.42),
            (-2.08, 0.495, 0.290, 0.370, 0.032, 0.42),
            (-1.62, 0.500, 0.280, 0.380, 0.038, 0.42),
            (-1.18, 0.465, 0.250, 0.330, 0.042, 0.46),
            (-0.76, 0.405, 0.218, 0.270, 0.044, 0.50),
            (-0.34, 0.340, 0.188, 0.215, 0.040, 0.56),
            (0.18, 0.310, 0.170, 0.185, 0.030, 0.60),
            (0.78, 0.275, 0.155, 0.160, 0.014, 0.64),
            (1.48, 0.250, 0.150, 0.145, -0.006, 0.68),
            (2.18, 0.215, 0.140, 0.130, -0.030, 0.72),
            (2.82, 0.180, 0.120, 0.110, -0.058, 0.76),
            (3.36, 0.135, 0.105, 0.095, -0.084, 0.82),
            (3.72, 0.090, 0.075, 0.070, -0.106, 0.87),
            (3.90, 0.055, 0.055, 0.050, -0.120, 0.92),
    ]
    fuselage = create_asymmetric_fuselage(
        "Ximango-derived composite fuselage",
        fuselage_sections,
        IAF_GRAY,
    )
    assign_forward_material(fuselage, ENGINE_COWLING, -2.46)
    assign_mission_computer_cutaway_material(fuselage, MISSION_COMPUTER_SKIN)
    assign_drone_bay_cutaway_material(fuselage, DRONE_BAY_SKIN)
    fuselage.parent = root

    # STA 02 now resolves to a real internal powerplant. It is hidden by the
    # opaque cowling in overview and revealed by a dedicated material fade in
    # the web experience, leaving the external aerodynamic model unchanged.
    create_rotax_916_engine(root)

    # STA 03 reveals the published-size NVIDIA T5000 module and its illustrative
    # airborne carrier through a local material fade in the starboard fuselage.
    # Mission AI compute remains explicitly separate from the critical FCC.
    create_jetson_thor_mission_computer(root)

    # There is no cockpit, canopy or separate dorsal avionics cover. The
    # original fuselage loft is the uninterrupted closed upper surface.

    # Long wing with a restrained 2.5 degree dihedral.
    wing_left = wing_half("Port wing", 1.0)
    wing_right = wing_half("Starboard wing", -1.0)
    wing_left.parent = root
    wing_right.parent = root
    # The airfoil halves already penetrate the lower fuselage. Avoiding an
    # additional saddle removes the false thickened center-wing hump.

    # Each wing, its 25-degree transition and the vertical winglet now share
    # one continuous loft.  No overlapping cap or separate tip mesh remains.

    # Two presentation-only external fuel tanks sit clearly below the wing skin
    # on short, streamlined pylons. Their envelopes are reduced uniformly to
    # 80 percent while their top contact remains captured by the pylons.
    external_tank_scale = 0.80
    external_tank_origin_x = -1.38
    external_tank_sections = (
        (-2.48, 0.020, 0.018),
        (-2.39, 0.085, 0.078),
        (-2.20, 0.158, 0.145),
        (-1.92, 0.202, 0.184),
        (-1.28, 0.212, 0.192),
        (-0.82, 0.188, 0.170),
        (-0.48, 0.116, 0.102),
        (-0.28, 0.028, 0.024),
    )
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        station_y = 2.68 * side
        tank_center_z = -0.440
        # One closed hard-surface pylon carries its own widened end stations.
        # It overlaps the wing and tank skins slightly but never modifies either
        # source mesh, so their tessellation and aerodynamic surfaces stay clean.
        tank_pylon = vertical_pylon_airfoil(
            f"{label} external fuel-tank streamlined pylon",
            station_y,
            [
                (-0.122, -1.610, 0.380, 0.140),
                (-0.145, -1.590, 0.340, 0.110),
                (-0.215, -1.560, 0.300, 0.100),
                (-0.284, -1.540, 0.310, 0.110),
                (-0.307, -1.550, 0.350, 0.140),
            ],
            IAF_GRAY,
            chord_points=40,
        )
        tank_pylon.parent = root
        tank = create_loft(
            f"{label} external fuel tank",
            [
                (
                    external_tank_origin_x + (x - external_tank_origin_x) * external_tank_scale,
                    radius_y * external_tank_scale,
                    radius_z * external_tank_scale,
                    tank_center_z,
                )
                for x, radius_y, radius_z in external_tank_sections
            ],
            IAF_GRAY,
            ring_segments=56,
            y_offset=station_y,
        )
        tank.parent = root

        for x, radius_y, radius_z in (
            (-2.18, 0.164, 0.150),
            (-1.28, 0.212, 0.192),
            (-0.66, 0.154, 0.139),
        ):
            elliptical_ring(
                f"{label} fuel-tank shell joint",
                external_tank_origin_x + (x - external_tank_origin_x) * external_tank_scale,
                radius_y * external_tank_scale,
                radius_z * external_tank_scale,
                tank_center_z,
                0.0032,
                SEAM,
                root,
                segments=56,
                tube_segments=6,
                y_offset=station_y,
            )

    # Both tail stabilizers are true symmetric airfoil bodies.  The rounded
    # leading edges replace the former flat-plate visual while the trailing
    # edges remain crisp enough to preserve the rudder and elevator breaks.
    vertical = vertical_airfoil_fin(
        "Vertical stabilizer",
        [
            (-0.08, 2.48, 1.40, 0.105),
            (0.62, 2.72, 1.06, 0.100),
            (1.34, 3.03, 0.67, 0.090),
        ],
        IAF_GRAY,
        chord_points=52,
    )
    vertical.parent = root

    vertical_root_blend = create_loft(
        "Vertical stabilizer fuselage root aerodynamic fillet",
        [
            (2.42, 0.018, 0.010, -0.020),
            (2.56, 0.105, 0.055, -0.015),
            (3.26, 0.115, 0.060, -0.020),
            (3.82, 0.088, 0.040, -0.050),
            (3.94, 0.015, 0.008, -0.080),
        ],
        IAF_GRAY,
        ring_segments=40,
    )
    vertical_root_blend.parent = root

    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        stab = airfoil_half(
            f"{label} horizontal stabilizer",
            side,
            [
                (0.00, 2.82, 0.92, 1.29, 0.12, -1.0),
                (0.72, 2.90, 0.82, 1.30, 0.125, -1.0),
                (1.84, 3.02, 0.65, 1.31, 0.11, -1.0),
            ],
            IAF_GRAY,
            chord_points=52,
        )
        stab.parent = root

    # One closed white ogive replaces the exposed dark hub and simple cone.
    # Its aft ring penetrates the first cowling section so the engine area reads
    # as a continuous Ximango-style aerodynamic transition from every angle.
    spinner = create_asymmetric_fuselage(
        "White Ximango-style propeller spinner",
        [
            (-4.27, 0.010, 0.010, 0.010, 0.000, 0.88),
            (-4.23, 0.040, 0.040, 0.038, 0.000, 0.82),
            (-4.15, 0.090, 0.086, 0.082, 0.000, 0.76),
            (-4.05, 0.145, 0.134, 0.126, 0.000, 0.72),
            (-3.94, 0.184, 0.158, 0.145, 0.000, 0.72),
            (-3.82, 0.202, 0.168, 0.153, 0.000, 0.78),
        ],
        PROP_WHITE,
        ring_segments=56,
    )
    spinner.parent = root

    # The compact shaft and blade plane sit at the aft spinner station beside
    # the cowling, matching the reference installation instead of floating near
    # the spinner tip.
    hub = cylinder_between("Internal propeller shaft", (-3.86, 0, 0), (-3.98, 0, 0), 0.035, STEEL)
    hub.parent = root
    for angle, suffix in ((math.radians(14), "A"), (math.radians(194), "B")):
        propeller_blade(f"Propeller blade {suffix}", angle, root)

    # Each cowling side carries one restrained NACA-like recess. The narrow
    # forward tip grows gradually into a softly rounded, slightly asymmetric
    # aft mouth. A contoured internal floor follows the changing cowling width
    # and increases depth progressively, avoiding a flat plate or projecting
    # arrow at the nose. No auxiliary circular opening is retained.
    cowling_sections = [
        (-3.84, 0.195, 0.165, 0.150, 0.000, 0.82),
        (-3.62, 0.305, 0.235, 0.205, 0.005, 0.62),
        (-3.30, 0.390, 0.285, 0.270, 0.010, 0.50),
        (-2.92, 0.445, 0.305, 0.310, 0.016, 0.44),
    ]

    def cowling_surface_y(x: float, z: float) -> float:
        first = cowling_sections[0]
        last = cowling_sections[-1]
        if x <= first[0]:
            values = first[1:]
        elif x >= last[0]:
            values = last[1:]
        else:
            values = first[1:]
            for left, right in zip(cowling_sections, cowling_sections[1:]):
                if left[0] <= x <= right[0]:
                    blend = (x - left[0]) / (right[0] - left[0])
                    values = tuple(
                        left[index] + (right[index] - left[index]) * blend
                        for index in range(1, 6)
                    )
                    break
        half_width, crown, belly, center_z, exponent = values
        vertical_radius = crown if z >= center_z else belly
        normalized_z = min(abs(z - center_z) / max(vertical_radius, 1e-5), 0.999)
        sine = normalized_z ** (1.0 / exponent)
        cosine = math.sqrt(max(0.0, 1.0 - sine * sine))
        return (cosine ** exponent) * half_width

    tip_x = -3.570
    mouth_x = -3.075
    samples = 22

    def naca_edge(u: float, upper: bool) -> tuple[float, float]:
        x = tip_x + (mouth_x - tip_x) * u
        center_z = -0.143 + 0.010 * u
        half_height = 0.041 * (math.sin(u * math.pi * 0.5) ** 1.55)
        z = center_z + half_height * (0.76 if upper else -1.18)
        return (x, z)

    upper_edge = [naca_edge(index / samples, True) for index in range(samples + 1)]
    lower_edge = [naca_edge(index / samples, False) for index in range(samples, -1, -1)]
    diagonal_outline = upper_edge + [
        (-3.052, -0.108),
        (-3.042, -0.133),
        (-3.048, -0.159),
        (-3.060, -0.177),
    ] + lower_edge

    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        diagonal_cutter = extruded_plate_y(
            f"{label} diagonal intake subtraction cutter",
            diagonal_outline,
            0.355 * side,
            0.245,
            OPTICAL_VOID,
            0.008,
        )
        diagonal_cutter.parent = root
        cut_from_hard_surface(
            fuselage,
            diagonal_cutter,
            f"{label} inward-beveled diagonal intake recess",
            before_finish=True,
        )

        # The visible floor starts aft of the leading tip and remains only a few
        # millimetres below the skin there. It becomes gradually deeper toward
        # the rounded mouth, creating a delicate staged entry rather than a
        # hard-edged constant-depth void.
        floor_tip_x = -3.515
        floor_mouth_x = -3.090
        floor_samples = 20

        def floor_edge(u: float, upper: bool) -> tuple[float, float]:
            x = floor_tip_x + (floor_mouth_x - floor_tip_x) * u
            center_z = -0.143 + 0.009 * u
            half_height = 0.029 * (math.sin(u * math.pi * 0.5) ** 1.60)
            z = center_z + half_height * (0.72 if upper else -1.12)
            return (x, z)

        floor_outline_xz = [
            floor_edge(index / floor_samples, True)
            for index in range(floor_samples + 1)
        ] + [
            (-3.076, -0.118),
            (-3.070, -0.139),
            (-3.077, -0.158),
        ] + [
            floor_edge(index / floor_samples, False)
            for index in range(floor_samples, -1, -1)
        ]
        floor_vertices = []
        for x, z in floor_outline_xz:
            progression = min(max((x - floor_tip_x) / (floor_mouth_x - floor_tip_x), 0.0), 1.0)
            depth = 0.004 + 0.024 * progression**1.65
            surface_y = cowling_surface_y(x, z)
            floor_vertices.append((x, (surface_y - depth) * side, z))

        diagonal_duct = contoured_side_plate(
            f"{label} diagonal intake internal duct floor",
            floor_vertices,
            side,
            0.006,
            OPTICAL_VOID,
        )
        diagonal_duct.parent = root

    # A single shallow chin inlet supplies the radiator and turbo intercooler.
    # Its rounded capture lip sits just below the spinner wake, then grows into
    # a gentle internal diffuser before disappearing into the lower cowling.
    # The open shell and recessed dark pressure face read as a real duct rather
    # than an applied box or a solid blister.
    cooling_inlet_sections = [
        (-3.555, 0.142, 0.052, -0.265),
        (-3.425, 0.170, 0.064, -0.274),
        (-3.205, 0.198, 0.076, -0.278),
        (-3.020, 0.152, 0.056, -0.264),
        (-2.900, 0.030, 0.014, -0.246),
    ]
    cooling_inlet = create_open_loft(
        "Forward radiator and intercooler ram-air inlet",
        cooling_inlet_sections,
        IAF_GRAY,
        ring_segments=56,
    )
    cooling_inlet["system_role"] = "radiator and turbo intercooler cooling-air inlet"
    cooling_inlet["visualization_only"] = True
    cooling_inlet.parent = root
    elliptical_ring(
        "Forward cooling-air inlet rounded capture lip",
        -3.555,
        0.142,
        0.052,
        -0.265,
        0.010,
        IAF_GRAY,
        root,
        segments=64,
        tube_segments=10,
    )
    cooling_pressure_face_outline = [
        (
            math.cos(math.tau * index / 48) * 0.165,
            -0.276 + math.sin(math.tau * index / 48) * 0.060,
        )
        for index in range(48)
    ]
    cooling_pressure_face = extruded_plate_x(
        "Radiator and intercooler recessed diffuser pressure face",
        cooling_pressure_face_outline,
        -3.285,
        0.010,
        OPTICAL_VOID,
        0.004,
    )
    cooling_pressure_face.parent = root

    # Retractable tail-dragger gear.  The Ximango three-view and ground photos
    # show a nearly perpendicular deployment from the low wing, with a subtle
    # aft rake in profile and outboard cant in front view.  The distinctive
    # outboard door is an asymmetric right-angle wedge rather than a rectangular
    # spat: its upper aft corner is approximately square, its forward edge flows
    # diagonally into the leg, and only the tire contact patch remains visible.
    sta10_gear_assemblies: list[
        tuple[str, float, tuple[float, float, float], list[bpy.types.Object]]
    ] = []
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        mount_x = -1.62
        # Keep the wheel-centre track at the referenced 2.80 m.  The trunnion
        # sits inboard of the axle so the 110 mm spanwise change produces the
        # photographed cant without artificially widening the undercarriage.
        mount_y = 1.29 * side
        wheel_x = mount_x + 0.11
        wheel_y = mount_y + 0.11 * side
        wheel_location = (wheel_x, wheel_y, -0.94)
        moving_gear_parts: list[bpy.types.Object] = []

        # The wheel-well throat and trunnion housing deliberately penetrate the
        # wing skin.  This overlap is the load-bearing visual interface: no
        # landing-gear component may read as a separate object floating below
        # the wing.
        wheel_well = cube(
            f"{label} main gear recessed wheel-well throat",
            (mount_x, mount_y, -0.282),
            (0.185, 0.135, 0.025),
            SEAM,
            0.035,
        )
        wheel_well.parent = root

        # Do not Boolean a separate blister into either wing. Mirrored airfoil
        # topology can otherwise resolve the union differently on each side and
        # create a false underside bump. The socket and recessed throat already
        # overlap the pristine wing mesh and provide a continuous connection.

        trunnion_socket = cylinder_between(
            f"{label} main gear structural trunnion socket",
            (mount_x, mount_y, -0.265),
            (mount_x, mount_y, -0.415),
            0.068,
            HARDWARE_GRAY,
            vertices=36,
        )
        trunnion_socket.parent = root

        attachment_pin = cylinder_between(
            f"{label} main gear upper attachment pin",
            (mount_x, mount_y - 0.13, -0.345),
            (mount_x, mount_y + 0.13, -0.345),
            0.030,
            STEEL,
            vertices=32,
        )
        attachment_pin.parent = root

        vertical_strut = cylinder_between(
            f"{label} subtly canted main gear oleo",
            (mount_x, mount_y, -0.335),
            (wheel_x, wheel_y, wheel_location[2] + 0.11),
            0.034,
            STEEL,
            vertices=28,
        )
        vertical_strut.parent = root
        moving_gear_parts.append(vertical_strut)
        leg_cover = landing_gear_fairing(
            f"{label} full-depth aerodynamic main-gear leg fairing",
            (mount_x, mount_y, -0.315),
            (wheel_x - 0.025, wheel_y, -0.825),
            root,
        )
        leg_cover.parent = root
        moving_gear_parts.append(leg_cover)

        # Twin lower fork arms terminate at the spanwise axle.
        for fork_offset, suffix in ((-0.062, "inboard"), (0.062, "outboard")):
            fork = cylinder_between(
                f"{label} main gear {suffix} axle fork",
                (wheel_x - 0.025, wheel_y + fork_offset, -0.785),
                (wheel_x, wheel_y + fork_offset, wheel_location[2]),
                0.024,
                STEEL,
                vertices=28,
            )
            fork.parent = root
            moving_gear_parts.append(fork)
        axle = cylinder_between(
            f"{label} main wheel axle",
            (wheel_location[0], wheel_y - 0.105, wheel_location[2]),
            (wheel_location[0], wheel_y + 0.105, wheel_location[2]),
            0.028,
            STEEL,
            vertices=32,
        )
        axle.parent = root
        moving_gear_parts.append(axle)
        wheel_object_names_before = set(bpy.data.objects.keys())
        landing_wheel(label, wheel_location, 0.165, 0.13, root)
        moving_gear_parts.extend(
            obj
            for obj in bpy.data.objects
            if obj.name not in wheel_object_names_before
        )

        # One-sided outboard door, canted outboard from top to bottom. Its chord
        # is extended slightly at both ends while the diagonal lower cut reaches
        # close to the tire bottom. The longer boot profile conceals most of the
        # circular wheel but deliberately leaves a narrow tire crescent visible.
        # Mirror the chordwise profile about its own centre so the square heel is
        # aft (+X) and the streamlined diagonal toe faces the nose (-X).
        cover_top_y = mount_y + side * 0.085
        # Stand the cover just outside the tire shoulder. This maintains the
        # one-sided shield construction without surface intersections.
        cover_bottom_y = wheel_y + side * 0.140
        cover_profile_center_x = (
            (mount_x - 0.195) + (wheel_x + 0.225)
        ) * 0.5

        def fairing_x_aft(x: float) -> float:
            return 2.0 * cover_profile_center_x - x

        wheel_cover = canted_fin_mesh(
            f"{label} asymmetric right-angle main-wheel aerodynamic cover",
            [
                (fairing_x_aft(mount_x - 0.185), cover_top_y, -0.300),
                (fairing_x_aft(mount_x + 0.055), cover_top_y + side * 0.010, -0.300),
                (fairing_x_aft(wheel_x + 0.225), cover_bottom_y, -1.070),
                (fairing_x_aft(wheel_x - 0.225), cover_bottom_y, -1.025),
                (fairing_x_aft(mount_x - 0.195), cover_top_y + side * 0.035, -0.505),
            ],
            0.028,
            IAF_GRAY,
        )
        wheel_cover.parent = root
        moving_gear_parts.append(wheel_cover)
        seam_y = mount_y + side * 0.165
        cover_seam = cylinder_between(
                f"{label} wheel-cover upper maintenance seam",
                (fairing_x_aft(mount_x - 0.125), seam_y, -0.555),
                (fairing_x_aft(mount_x + 0.145), seam_y + side * 0.012, -0.555),
                0.0035,
                SEAM,
                vertices=10,
            )
        cover_seam.parent = root
        moving_gear_parts.append(cover_seam)
        sta10_gear_assemblies.append(
            (label, side, (mount_x, mount_y, -0.345), moving_gear_parts)
        )

    tail_wheel_location = (3.43, 0.0, -0.335)

    # A closed composite shoe grows directly out of the tapered aft belly and
    # encloses the upper tail-wheel pivot.  The first section is buried in the
    # fuselage loft, eliminating the former visible air gap.
    tail_mount = create_loft(
        "Fuselage-integrated tail wheel mounting shoe",
        [
            (3.04, 0.050, 0.028, -0.150),
            (3.18, 0.075, 0.050, -0.172),
            (3.31, 0.085, 0.072, -0.202),
            (3.40, 0.072, 0.060, -0.248),
        ],
        IAF_GRAY,
        ring_segments=36,
    )
    tail_mount.parent = root

    tail_pivot = cylinder_between(
        "Tail wheel mounting pivot",
        (3.34, -0.082, -0.205),
        (3.34, 0.082, -0.205),
        0.024,
        STEEL,
        vertices=28,
    )
    tail_pivot.parent = root

    for y in (-0.045, 0.045):
        tail_fork = cylinder_between(
            "Tail wheel spring fork",
            (3.34, y, -0.202),
            (tail_wheel_location[0], y, tail_wheel_location[2]),
            0.020,
            STEEL,
            vertices=24,
        )
        tail_fork.parent = root

    tail_fairing = landing_gear_fairing(
        "Streamlined tail wheel spring fairing",
        (3.27, 0.0, -0.175),
        (3.405, 0.0, -0.285),
        root,
    )
    union_into_airframe(fuselage, tail_mount, "Integral tail wheel mounting shoe")
    union_into_airframe(fuselage, tail_fairing, "Integral tail wheel spring fairing")
    landing_wheel("Tail", tail_wheel_location, 0.095, 0.060, root)

    # The physical doors retain a broad conformal footprint for the animation,
    # but the closed aircraft shows only one clean longitudinal service seam.
    # This avoids an irregular perimeter outline across the belly mesh.
    hatch_control_loop = [
        (-0.80, 0.180),
        (-0.69, 0.205),
        (0.12, 0.195),
        (0.24, 0.145),
        (0.24, -0.145),
        (0.12, -0.195),
        (-0.69, -0.205),
        (-0.80, -0.180),
    ]
    hatch_center_seam_loop = [
        (-0.72, 0.0014),
        (0.16, 0.0014),
        (0.16, -0.0014),
        (-0.72, -0.0014),
    ]
    hatch_seam = surface_conforming_seam(
        "Flush drone deployment hatch longitudinal center seam",
        hatch_center_seam_loop,
        fuselage_sections,
        0.0008,
        SEAM,
        root,
        samples_per_edge=12,
    )
    hatch_seam["outer_mold_line"] = "flush"
    create_sta10_deployment_system(
        root,
        fuselage_sections,
        hatch_control_loop,
        sta10_gear_assemblies,
    )

    # The compact VR/visual-navigation camera is positioned well aft of the
    # propeller disk and its immediate wake.  Its recessed stereo apertures face
    # downward for wide terrain coverage while the shallow teardrop fairing
    # remains clear of the main gear and the aft kinetic gimbal.
    camera_x = -2.38
    camera_y = 0.0
    camera_z = -0.350
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=(camera_x, camera_y, camera_z))
    camera_fairing = bpy.context.object
    camera_fairing.name = "Forward VR camera aerodynamic fairing"
    camera_fairing.scale = (0.155, 0.135, 0.064)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(camera_fairing, IAF_GRAY)
    smooth(camera_fairing)
    mark_export(camera_fairing)
    camera_fairing.parent = root
    camera_face = cube(
        "Downward VR camera recessed wide-angle face plate",
        (camera_x, camera_y, camera_z - 0.058),
        (0.092, 0.090, 0.010),
        HARDWARE_GRAY,
        0.020,
    )
    camera_face.parent = root
    for offset, label in ((-0.035, "port"), (0.035, "starboard")):
        camera_lens = cylinder_between(
            f"Downward VR camera {label} wide-angle aperture",
            (camera_x, camera_y + offset, camera_z - 0.064),
            (camera_x + 0.010, camera_y + offset, camera_z - 0.088),
            0.021,
            LENS,
            vertices=32,
        )
        camera_lens["optical_axis"] = "downward with 22 degree forward cant"
        camera_lens.parent = root

    # Exterior-only reconstruction of the supplied integrated EO/IR kinetic
    # gimbal. The hierarchy follows the visible reference: wide aircraft plate,
    # suspended stabilization stack, articulated service carrier, twin yoke,
    # tall rounded sensor/receiver body, dominant side drive and low vented
    # barrel package. No internal or manufacturing geometry is represented.
    turret_x = -0.82
    turret_y = 0.0
    body_x = -0.88
    body_z = -0.650

    # The mount is mechanically continuous with the aircraft belly. The broad
    # plate and captive isolators overlap the conformal fairing, eliminating the
    # floating-interface failure seen in earlier presentation versions.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=28, location=(turret_x, turret_y, -0.304))
    interface_fairing = bpy.context.object
    interface_fairing.name = "Integrated gimbal conformal aircraft interface"
    interface_fairing.scale = (0.40, 0.34, 0.064)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(interface_fairing, IAF_GRAY)
    smooth(interface_fairing)
    mark_export(interface_fairing)
    interface_fairing.parent = root

    mounting_plate = cube(
        "Integrated gimbal wide machined mounting plate",
        (turret_x, turret_y, -0.350),
        (0.36, 0.31, 0.022),
        GIMBAL_ALLOY,
        0.026,
    )
    mounting_plate.parent = root
    lower_mount_rail = cube(
        "Integrated gimbal suspended lower mount rail",
        (turret_x, turret_y, -0.452),
        (0.28, 0.235, 0.018),
        GIMBAL_ALLOY,
        0.016,
    )
    lower_mount_rail.parent = root

    # A closed aerodynamic interface shroud conceals the captive aircraft-side
    # fasteners. The isolators remain represented inside the assembly, but no
    # washer or bolt head is exposed on the exterior mounting surface.
    mount_shroud = create_loft(
        "Integrated gimbal closed aircraft-interface shroud",
        [
            (turret_x - 0.42, 0.025, 0.014, -0.350),
            (turret_x - 0.34, 0.310, 0.050, -0.365),
            (turret_x + 0.34, 0.310, 0.050, -0.365),
            (turret_x + 0.42, 0.025, 0.014, -0.350),
        ],
        IAF_GRAY,
        ring_segments=48,
    )
    mount_shroud.parent = root

    for x_offset in (-0.265, 0.265):
        for y_offset in (-0.220, 0.220):
            isolator = cylinder_between(
                "Integrated gimbal captive vibration isolator",
                (turret_x + x_offset, turret_y + y_offset, -0.325),
                (turret_x + x_offset, turret_y + y_offset, -0.374),
                0.032,
                GRAPHITE,
                vertices=32,
            )
            isolator.parent = root
            washer = cylinder_between(
                "Integrated gimbal isolator washer",
                (turret_x + x_offset, turret_y + y_offset, -0.365),
                (turret_x + x_offset, turret_y + y_offset, -0.380),
                0.042,
                STEEL,
                vertices=32,
            )
            washer.parent = root

    # Four inward-canted A-frame members reproduce the tall suspended support
    # visible beneath the mounting plate instead of collapsing the mechanism
    # into a single short cylinder.
    for x_offset in (-0.235, 0.235):
        for side, label in ((-1.0, "port"), (1.0, "starboard")):
            upper_y = turret_y + side * 0.245
            lower_y = turret_y + side * 0.180
            bracket = beam_between(
                f"Integrated gimbal {label} canted suspension bracket",
                (turret_x + x_offset, upper_y, -0.366),
                (turret_x + x_offset * 0.66, lower_y, -0.448),
                0.046,
                0.032,
                GIMBAL_ALLOY,
                0.009,
            )
            bracket.parent = root
    for side, label in ((-1.0, "port"), (1.0, "starboard")):
        if side > 0:
            support_outline = [
                (turret_y + 0.300, -0.367),
                (turret_y + 0.120, -0.367),
                (turret_y + 0.145, -0.447),
                (turret_y + 0.235, -0.447),
            ]
            support_inset = [
                (turret_y + 0.256, -0.384),
                (turret_y + 0.154, -0.384),
                (turret_y + 0.168, -0.426),
                (turret_y + 0.218, -0.426),
            ]
        else:
            support_outline = [
                (turret_y - 0.300, -0.367),
                (turret_y - 0.235, -0.447),
                (turret_y - 0.145, -0.447),
                (turret_y - 0.120, -0.367),
            ]
            support_inset = [
                (turret_y - 0.256, -0.384),
                (turret_y - 0.218, -0.426),
                (turret_y - 0.168, -0.426),
                (turret_y - 0.154, -0.384),
            ]
        suspension_web = extruded_plate_x(
            f"Integrated gimbal {label} front suspension web",
            support_outline,
            turret_x - 0.175,
            0.042,
            GIMBAL_ALLOY,
            0.010,
        )
        suspension_web.parent = root
        web_cutout = extruded_plate_x(
            f"Integrated gimbal {label} suspension-web recessed cutout",
            support_inset,
            turret_x - 0.198,
            0.008,
            OPTICAL_VOID,
            0.005,
        )
        web_cutout.parent = root

    # Layered azimuth/yaw stabilization stack with a domed upper actuator,
    # split bearing races and a service-readable fastener ring.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(turret_x, turret_y, -0.397))
    yaw_dome = bpy.context.object
    yaw_dome.name = "Integrated gimbal domed upper azimuth actuator"
    yaw_dome.scale = (0.126, 0.126, 0.062)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(yaw_dome, GRAPHITE)
    smooth(yaw_dome)
    mark_export(yaw_dome)
    yaw_dome.parent = root
    for start_z, end_z, radius, mat, label in (
        (-0.400, -0.428, 0.114, GRAPHITE, "upper actuator collar"),
        (-0.425, -0.468, 0.162, GIMBAL_ALLOY, "primary azimuth bearing"),
        (-0.463, -0.493, 0.176, HARDWARE_GRAY, "split bearing race"),
        (-0.488, -0.522, 0.154, GIMBAL_ALLOY, "lower yaw rotor"),
    ):
        stack = cylinder_between(
            f"Integrated gimbal {label}",
            (turret_x, turret_y, start_z),
            (turret_x, turret_y, end_z),
            radius,
            mat,
            vertices=56,
        )
        stack.parent = root
    for z, radius, label in ((-0.427, 0.116, "upper"), (-0.468, 0.164, "middle"), (-0.493, 0.154, "lower")):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=radius,
            minor_radius=0.005,
            major_segments=56,
            minor_segments=10,
            location=(turret_x, turret_y, z),
        )
        race = bpy.context.object
        race.name = f"Integrated gimbal {label} azimuth race seam"
        assign(race, SEAM)
        smooth(race)
        mark_export(race)
        race.parent = root
    for index in range(12):
        angle = 2.0 * math.pi * index / 12.0
        bolt_x = turret_x + math.cos(angle) * 0.142
        bolt_y = turret_y + math.sin(angle) * 0.142
        bolt = cylinder_between(
            "Integrated gimbal azimuth race captive fastener",
            (bolt_x, bolt_y, -0.484),
            (bolt_x, bolt_y, -0.500),
            0.006,
            STEEL,
            vertices=14,
        )
        bolt.parent = root

    # A visible articulated energy chain runs from the aircraft plate to the
    # moving body. Each link is a closed four-piece carrier rather than a loose
    # row of cubes, which reads correctly in frontal and three-quarter views.
    link_count = 13
    for index in range(link_count):
        fraction = index / (link_count - 1)
        link_x = turret_x - 0.305 - 0.030 * math.sin(fraction * math.pi)
        link_y = turret_y - 0.005 + 0.012 * math.sin(fraction * math.pi)
        link_z = -0.388 - 0.0105 * index
        for side in (-1.0, 1.0):
            rail = cube(
                "Integrated gimbal energy-chain side link",
                (link_x, link_y + side * 0.028, link_z),
                (0.014, 0.006, 0.008),
                GRAPHITE,
                0.003,
            )
            rail.parent = root
        for z_side in (-1.0, 1.0):
            crossbar = cube(
                "Integrated gimbal energy-chain crossbar",
                (link_x, link_y, link_z + z_side * 0.008),
                (0.014, 0.028, 0.003),
                GRAPHITE,
                0.002,
            )
            crossbar.parent = root

    # Twin lateral yoke cheeks tie the yaw stack to the elevation trunnion. The
    # dark inset profiles visually describe the machined triangular cut-outs
    # seen in the supplied reference without exposing hidden internal geometry.
    yoke_outline = [
        (-1.075, -0.493),
        (-0.620, -0.493),
        (-0.585, -0.535),
        (-0.655, -0.676),
        (-1.020, -0.676),
        (-1.095, -0.545),
    ]
    yoke_inset = [
        (-1.015, -0.520),
        (-0.680, -0.520),
        (-0.650, -0.544),
        (-0.704, -0.625),
        (-0.968, -0.625),
        (-1.030, -0.548),
    ]
    for side, label in ((-1.0, "port"), (1.0, "starboard")):
        outer_y = turret_y + side * 0.248
        yoke = extruded_plate_y(
            f"Integrated gimbal {label} machined elevation yoke",
            yoke_outline,
            outer_y,
            0.050,
            GIMBAL_ALLOY,
            0.014,
        )
        yoke.parent = root
        inset = extruded_plate_y(
            f"Integrated gimbal {label} recessed yoke web",
            yoke_inset,
            outer_y + side * 0.028,
            0.008,
            HARDWARE_GRAY,
            0.008,
        )
        inset.parent = root

    # Tall rounded sensor/receiver body. This is intentionally not a horizontal
    # tube: the frontal EO/IR panel, lower barrel saddle and side drive establish
    # the vertically balanced silhouette of the reference assembly.
    body = cube(
        "Integrated gimbal rounded sensor and receiver body",
        (body_x, turret_y, body_z),
        (0.225, 0.218, 0.215),
        GIMBAL_ALLOY,
        0.0,
    )
    bevel(body, 0.082, 8)
    body.parent = root
    body_top = cube(
        "Integrated gimbal upper body structural shoulder",
        (body_x + 0.005, turret_y, -0.470),
        (0.178, 0.190, 0.034),
        HARDWARE_GRAY,
        0.026,
    )
    body_top.parent = root
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(body_x + 0.025, turret_y, -0.835))
    lower_fairing = bpy.context.object
    lower_fairing.name = "Integrated gimbal rounded lower mission-system fairing"
    lower_fairing.scale = (0.205, 0.205, 0.085)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(lower_fairing, GIMBAL_ALLOY)
    smooth(lower_fairing)
    mark_export(lower_fairing)
    lower_fairing.parent = root

    # Full-span elevation spindle and the reference-dominant starboard drive.
    trunnion = cylinder_between(
        "Integrated gimbal full-span elevation spindle",
        (body_x + 0.055, turret_y - 0.285, body_z),
        (body_x + 0.055, turret_y + 0.285, body_z),
        0.080,
        STEEL,
        vertices=48,
    )
    trunnion.parent = root
    drive_outline = [
        (-1.015, -0.500),
        (-0.690, -0.500),
        (-0.620, -0.548),
        (-0.602, -0.730),
        (-0.668, -0.865),
        (-0.910, -0.875),
        (-1.020, -0.755),
    ]
    drive_lobe = extruded_plate_y(
        "Integrated gimbal reference-side elevation drive lobe",
        drive_outline,
        turret_y - 0.252,
        0.090,
        GIMBAL_ALLOY,
        0.032,
    )
    drive_lobe.parent = root
    pitch_drive = cylinder_between(
        "Integrated gimbal reference-side elevation drive housing",
        (body_x + 0.050, turret_y - 0.260, body_z),
        (body_x + 0.050, turret_y - 0.326, body_z),
        0.195,
        GIMBAL_ALLOY,
        vertices=64,
    )
    pitch_drive.parent = root
    pitch_cover = cylinder_between(
        "Integrated gimbal concentric elevation-drive access cover",
        (body_x + 0.050, turret_y - 0.323, body_z),
        (body_x + 0.050, turret_y - 0.344, body_z),
        0.158,
        HARDWARE_GRAY,
        vertices=64,
    )
    pitch_cover.parent = root
    for index in range(10):
        angle = 2.0 * math.pi * index / 10.0
        fastener_x = body_x + 0.050 + math.cos(angle) * 0.125
        fastener_z = body_z + math.sin(angle) * 0.125
        fastener = cylinder_between(
            "Integrated gimbal drive-cover captive fastener",
            (fastener_x, turret_y - 0.340, fastener_z),
            (fastener_x, turret_y - 0.352, fastener_z),
            0.0055,
            STEEL,
            vertices=14,
        )
        fastener.parent = root
    port_bearing = cylinder_between(
        "Integrated gimbal opposite-side elevation bearing cap",
        (body_x + 0.050, turret_y + 0.258, body_z),
        (body_x + 0.050, turret_y + 0.305, body_z),
        0.135,
        GIMBAL_ALLOY,
        vertices=56,
    )
    port_bearing.parent = root

    # Integrated forward EO/IR face. Four optically distinct apertures and their
    # nested bezels match the reference layout and remain attached to the main
    # housing instead of floating as a separate aft camera.
    sensor_face = cube(
        "Integrated gimbal EO IR forward sensor face",
        (-1.107, turret_y, -0.645),
        (0.018, 0.162, 0.175),
        GIMBAL_ALLOY,
        0.0,
    )
    bevel(sensor_face, 0.040, 7)
    sensor_face.parent = root
    sensors = (
        (turret_y + 0.072, -0.570, 0.049, LENS, "large EO aperture"),
        (turret_y - 0.078, -0.565, 0.026, LENS_IR, "auxiliary tracking aperture"),
        (turret_y + 0.074, -0.666, 0.033, LENS_DARK, "low-light aperture"),
        (turret_y - 0.075, -0.667, 0.045, LENS_IR, "large IR aperture"),
    )
    for lens_y, lens_z, radius, lens_mat, label in sensors:
        bezel = cylinder_between(
            f"Integrated gimbal {label} nested bezel",
            (-1.112, lens_y, lens_z),
            (-1.137, lens_y, lens_z),
            radius + 0.012,
            GRAPHITE,
            vertices=48,
        )
        bezel.parent = root
        optic = cylinder_between(
            f"Integrated gimbal {label} optical element",
            (-1.135, lens_y, lens_z),
            (-1.151, lens_y, lens_z),
            radius,
            lens_mat,
            vertices=48,
        )
        optic.parent = root
        if lens_mat == LENS:
            glint = cylinder_between(
                f"Integrated gimbal {label} inner coating",
                (-1.150, lens_y, lens_z),
                (-1.156, lens_y, lens_z),
                radius * 0.58,
                LENS,
                vertices=40,
            )
            glint.parent = root
    for y_offset in (-0.142, 0.142):
        for z_offset in (-0.145, 0.145):
            face_fastener = cylinder_between(
                "Integrated gimbal sensor-face flush fastener",
                (-1.125, turret_y + y_offset, -0.645 + z_offset),
                (-1.139, turret_y + y_offset, -0.645 + z_offset),
                0.005,
                STEEL,
                vertices=14,
            )
            face_fastener.parent = root

    # Low barrel saddle and perforated cooling shroud. Flush dark circular insets
    # sit at the shroud surface to read as recessed vent openings while the
    # restrained stepped barrel terminates in a recessed muzzle bore.
    gun_y = turret_y - 0.015
    gun_z = -0.785
    breech_block = cube(
        "Integrated gimbal lower barrel saddle",
        (-1.145, gun_y, gun_z),
        (0.060, 0.070, 0.056),
        GRAPHITE,
        0.018,
    )
    breech_block.parent = root
    breech_collar = cylinder_between(
        "Integrated gimbal barrel breech collar",
        (-1.175, gun_y, gun_z),
        (-1.320, gun_y, gun_z),
        0.063,
        HARDWARE_GRAY,
        vertices=48,
    )
    breech_collar.parent = root
    shroud = cylinder_between(
        "Integrated gimbal perforated barrel cooling shroud",
        (-1.285, gun_y, gun_z),
        (-1.685, gun_y, gun_z),
        0.052,
        STEEL,
        vertices=48,
    )
    shroud.parent = root
    shroud_liner = hollow_cylinder_between(
        "Integrated gimbal dark inner barrel liner",
        (-1.292, gun_y, gun_z),
        (-1.678, gun_y, gun_z),
        0.041,
        0.0185,
        GRAPHITE,
        vertices=48,
    )
    shroud_liner.parent = root
    vent_insets: list[bpy.types.Object] = []
    for ring_index, x_pos in enumerate((-1.335, -1.410, -1.485, -1.560, -1.635)):
        angle_offset = (ring_index % 2) * math.pi / 8.0
        for aperture_index in range(8):
            angle = angle_offset + aperture_index * math.pi / 4.0
            radial_y = math.cos(angle)
            radial_z = math.sin(angle)
            vent_inset = cylinder_between(
                "Integrated gimbal shroud recessed vent aperture",
                (x_pos, gun_y + radial_y * 0.048, gun_z + radial_z * 0.048),
                (x_pos, gun_y + radial_y * 0.0524, gun_z + radial_z * 0.0524),
                0.0085,
                BORE_VOID,
                vertices=16,
            )
            vent_inset.parent = root
            vent_insets.append(vent_inset)

    barrel = hollow_cylinder_between(
        "Integrated gimbal exposed precision barrel",
        (-1.635, gun_y, gun_z),
        (-1.930, gun_y, gun_z),
        0.023,
        0.0185,
        GRAPHITE,
        vertices=36,
    )
    barrel.parent = root
    for x_pos, radius, label in (
        (-1.675, 0.034, "shroud exit"),
        (-1.760, 0.028, "first barrel step"),
        (-1.865, 0.031, "muzzle support"),
        (-1.925, 0.037, "muzzle ring"),
    ):
        collar = hollow_cylinder_between(
            f"Integrated gimbal {label}",
            (x_pos - 0.016, gun_y, gun_z),
            (x_pos + 0.016, gun_y, gun_z),
            radius,
            0.0185,
            STEEL,
            vertices=40,
        )
        collar.parent = root
    muzzle = hollow_cylinder_between(
        "Integrated gimbal compact muzzle body",
        (-1.895, gun_y, gun_z),
        (-1.982, gun_y, gun_z),
        0.036,
        0.0185,
        GRAPHITE,
        vertices=40,
    )
    muzzle.parent = root
    muzzle_face = hollow_cylinder_between(
        "Integrated gimbal recessed muzzle face",
        (-1.977, gun_y, gun_z),
        (-1.997, gun_y, gun_z),
        0.031,
        0.0195,
        STEEL,
        vertices=40,
    )
    muzzle_face.parent = root
    bore_liner = open_tube_between(
        "Integrated gimbal continuous non-reflective barrel bore",
        (-1.999, gun_y, gun_z),
        (-1.305, gun_y, gun_z),
        0.0183,
        BORE_VOID,
        vertices=40,
    )
    bore_liner.parent = root
    bore_liner["bore_treatment"] = "continuous open axial passage with recessed non-reflective wall"
    # Every concentric component, including the cooling-shroud liner, is an
    # annulus. The dark inward-facing tube runs deep into the breech so the
    # muzzle reads as a genuine open bore from frontal and oblique views.

    # Export the perforation pattern as one mesh. Keep this operator-based join
    # after all concentric barrel parts have been created: Blender otherwise
    # leaves the joined vent array active and the following custom meshes can
    # lose their individual placement when export_apply flattens the hierarchy.
    # Joining here preserves both the recess pattern and the complete barrel
    # axis through the final GLB transform.
    primary_vent = vent_insets[0]
    for vent_inset in vent_insets[1:]:
        EXPORT_OBJECTS.remove(vent_inset)
    bpy.ops.object.select_all(action="DESELECT")
    for vent_inset in vent_insets:
        vent_inset.select_set(True)
    bpy.context.view_layer.objects.active = primary_vent
    bpy.ops.object.join()
    primary_vent.name = "Integrated gimbal shroud recessed vent array"

    # Scale the complete kinetic gimbal to 75 percent and move its mounting
    # axis into the forward third of the root chord. A shared transform keeps
    # the barrel, optics, yoke, shroud and aircraft interface mechanically
    # continuous instead of shifting individual pieces independently.
    gimbal_scale = 0.75
    gimbal_source_pivot = Vector((turret_x, turret_y, -0.350))
    gimbal_target_pivot = Vector((-1.82, turret_y, -0.350))
    gimbal_group = bpy.data.objects.new("Kinetic gimbal 0.75 forward-third transform", None)
    bpy.context.collection.objects.link(gimbal_group)
    gimbal_group.parent = root
    mark_export(gimbal_group)
    for component in tuple(EXPORT_OBJECTS):
        if not component.name.startswith("Integrated gimbal"):
            continue
        component_local = component.matrix_local.copy()
        component.parent = gimbal_group
        component.matrix_parent_inverse = Matrix.Identity(4)
        component.matrix_basis = component_local
    gimbal_group.matrix_local = (
        Matrix.Translation(gimbal_target_pivot)
        @ Matrix.Scale(gimbal_scale, 4)
        @ Matrix.Translation(-gimbal_source_pivot)
    )

    # Replace the dorsal hump with a flush conformal communications panel.
    datalink_panel = cube(
        "Conformal datalink antenna panel",
        (1.52, 0.0, 0.120),
        (0.23, 0.095, 0.008),
        HARDWARE_GRAY,
        0.028,
    )
    datalink_panel.parent = root

    add_airframe_surface_details(root)

    return root


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def generate_uv_maps() -> None:
    """Create repeatable real-scale UVs so authored maps survive GLB export."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in EXPORT_OBJECTS:
        if obj.type != "MESH" or len(obj.data.polygons) == 0:
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        # Airfoil and loft closures intentionally meet at coincident vertices.
        # Merge only exact duplicates before UV projection so the exporter does
        # not create zero-length tangent vectors at those closures.
        bpy.ops.mesh.remove_doubles(threshold=0.000001)
        materials = {slot.material for slot in obj.material_slots if slot.material is not None}
        # Seamless cube projection keeps texel scale consistent across the long
        # wing, changing fuselage sections and small stabilized housings. The
        # source maps repeat outside 0-1, so every projection seam is neutral.
        if IAF_GRAY in materials:
            bpy.ops.uv.cube_project(
                cube_size=1.8,
                correct_aspect=True,
                clip_to_bounds=False,
                scale_to_bounds=False,
            )
        elif GRAPHITE in materials:
            bpy.ops.uv.cube_project(
                cube_size=0.55,
                correct_aspect=True,
                clip_to_bounds=False,
                scale_to_bounds=False,
            )
        elif CARBON in materials:
            bpy.ops.uv.cube_project(
                cube_size=0.45,
                correct_aspect=True,
                clip_to_bounds=False,
                scale_to_bounds=False,
            )
        else:
            bpy.ops.uv.smart_project(
                angle_limit=math.radians(66.0),
                island_margin=0.025,
                area_weight=0.15,
                correct_aspect=True,
                scale_to_bounds=False,
            )
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.select_set(False)
        triangulate = obj.modifiers.new("Portable tangent-space triangulation", "TRIANGULATE")
        triangulate.quad_method = "BEAUTY"
        triangulate.ngon_method = "BEAUTY"


def setup_scene() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 95
    scene.render.filepath = str(OUTPUT_RENDER)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.use_file_extension = True
    scene.eevee.taa_render_samples = 256
    scene.eevee.use_shadows = True
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "SCREEN"
    scene.eevee.shadow_ray_count = 8
    scene.eevee.shadow_pool_size = "1024"
    scene.eevee.shadow_resolution_scale = 1.5

    world = scene.world
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_links = world.node_tree.links
    bg = world_nodes.get("Background")
    environment = world_nodes.new("ShaderNodeTexEnvironment")
    environment.name = "CC0 neutral studio environment"
    environment.image = bpy.data.images.load(str(ROOT / "environments" / "studio-softbox-1k.hdr"), check_existing=True)
    environment.interpolation = "Linear"
    world_links.new(environment.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.62

    # Concrete apron.
    bpy.ops.mesh.primitive_plane_add(size=70, location=(0, 0, -0.92))
    ground = bpy.context.object
    ground.name = "Concrete apron"
    assign(ground, CONCRETE)

    # Neutral key, fill and sunlight complement the HDR environment while
    # preserving contact shadows under the three-point landing gear.
    bpy.ops.object.light_add(type="SUN", location=(-4, -8, 14))
    sun = bpy.context.object
    sun.name = "Late morning sun"
    sun.data.energy = 1.35
    sun.data.angle = math.radians(3.5)
    sun.rotation_euler = (math.radians(24), math.radians(-18), math.radians(-28))

    bpy.ops.object.light_add(type="AREA", location=(-5, -8, 8))
    key = bpy.context.object
    key.name = "Soft sky fill"
    key.data.energy = 1050
    key.data.shape = "DISK"
    key.data.size = 10
    look_at(key, (0, 0, 0))

    bpy.ops.object.light_add(type="AREA", location=(8, 5, 5))
    rim = bpy.context.object
    rim.name = "Hangar rim light"
    rim.data.energy = 460
    rim.data.size = 7
    look_at(rim, (0, 0, 0))

    bpy.ops.object.light_add(type="AREA", location=(2.5, -7.5, 3.4))
    fill = bpy.context.object
    fill.name = "Low forward fill"
    fill.data.energy = 280
    fill.data.shape = "RECTANGLE"
    fill.data.size = 5.0
    fill.data.size_y = 2.5
    look_at(fill, (-1.0, 0.0, -0.15))

    bpy.ops.object.camera_add(location=(-14.2, -21.0, 3.15))
    camera = bpy.context.object
    camera.name = "Hero camera"
    camera.data.lens = 58
    camera.data.sensor_width = 36
    look_at(camera, (-0.05, 0, -0.08))
    scene.camera = camera


def export_glb() -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in EXPORT_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = EXPORT_OBJECTS[0]
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        # Tangent frames are derived by the real-time viewer from the exported
        # UVs. Blender can emit zero-length tangents at closed loft caps, which
        # violates glTF validation even though the surface renders correctly.
        export_tangents=False,
    )


def main() -> None:
    reset_scene()
    build_pbr_materials()
    create_aircraft()
    generate_uv_maps()
    setup_scene()
    export_glb()
    bpy.context.scene.render.filepath = str(OUTPUT_RENDER)
    bpy.ops.render.render(write_still=True)
    print(f"GLB: {OUTPUT_GLB}")
    print(f"Render: {OUTPUT_RENDER}")


if __name__ == "__main__":
    main()
