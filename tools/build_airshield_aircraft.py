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
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_GLB = ROOT / "airshield-ximango.glb"
OUTPUT_RENDER = ROOT / "airshield-xmango-hero.jpg"
TEXTURE_DIR = ROOT / "textures"
SKIN_IMAGEGEN_SOURCE = TEXTURE_DIR / "airshield_skin_imagegen_source_v1.png"
GIMBAL_IMAGEGEN_SOURCE = TEXTURE_DIR / "airshield_gimbal_imagegen_source_v1.png"

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
HARDWARE_GRAY = material("Dark gray external hardware", (0.22, 0.235, 0.24, 1.0), 0.02, 0.34)
GRAPHITE = material("Graphite", (0.035, 0.045, 0.052, 1.0), 0.28, 0.28)
CARBON = material("Carbon fiber propeller", (0.025, 0.032, 0.036, 1.0), 0.16, 0.30)
RUBBER = material("Tire rubber", (0.012, 0.014, 0.016, 1.0), 0.0, 0.72)
LENS = material("Sensor glass", (0.015, 0.055, 0.075, 1.0), 0.38, 0.08)
STEEL = material("Mechanism steel", (0.18, 0.20, 0.21, 1.0), 0.72, 0.24)
ALLOY = material("Machined wheel alloy", (0.34, 0.355, 0.36, 1.0), 0.78, 0.20)
RAIL = material("Empty launch rail anodized alloy", (0.075, 0.083, 0.086, 1.0), 0.62, 0.30)
SEAM = material("Composite panel seam", (0.055, 0.062, 0.064, 1.0), 0.04, 0.58)
NAV_RED = material("Port navigation lens", (0.34, 0.008, 0.006, 1.0), 0.0, 0.16)
NAV_GREEN = material("Starboard navigation lens", (0.006, 0.28, 0.09, 1.0), 0.0, 0.16)
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
    skin_low = wrapped_low_pass(skin_luma, (1, 2, 4, 8, 16, 32))
    skin_micro = normalized_field(skin_luma - wrapped_low_pass(skin_luma, (1, 2, 4)))
    skin_macro = normalized_field(skin_low)
    skin_chroma = skin_source - skin_luma[..., None]
    skin_rgb = np.clip(
        np.array([0.495, 0.512, 0.525], dtype=np.float32)[None, None, :]
        + skin_macro[..., None] * 0.004
        + skin_micro[..., None] * 0.003
        + skin_chroma * 0.035,
        0.0,
        1.0,
    )
    skin_roughness = np.clip(0.47 + skin_macro * 0.008 + skin_micro * 0.018, 0.40, 0.56)
    skin_height = skin_macro * 0.002 + skin_micro * 0.018
    skin_occlusion = np.clip(0.992 - np.maximum(-skin_micro, 0.0) * 0.008, 0.96, 1.0)

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
    textured_principled_material(
        IAF_GRAY,
        skin_base,
        skin_rough,
        skin_normal,
        metallic=0.015,
        normal_strength=0.24,
        coat_weight=0.28,
        coat_roughness=0.27,
    )
    attach_gltf_occlusion(IAF_GRAY, skin_ao)

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
        normal_strength=0.26,
        coat_weight=0.18,
        coat_roughness=0.24,
    )
    attach_gltf_occlusion(GRAPHITE, gimbal_ao)

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
    """Tapered 0.85 m blade for the specified two-blade Hoffmann envelope."""
    radial_sections = [(0.11, 0.16), (0.48, 0.12), (0.85, 0.055)]
    radial_y, radial_z = math.sin(angle), math.cos(angle)
    chord_y, chord_z = math.cos(angle), -math.sin(angle)
    verts: list[tuple[float, float, float]] = []
    for radius, chord in radial_sections:
        center_y = radial_y * radius
        center_z = radial_z * radius
        for x_offset in (-0.018, 0.018):
            verts.extend(
                [
                    (-4.19 + x_offset, center_y - chord_y * chord * 0.5, center_z - chord_z * chord * 0.5),
                    (-4.19 + x_offset, center_y + chord_y * chord * 0.5, center_z + chord_z * chord * 0.5),
                ]
            )
    faces: list[tuple[int, ...]] = []
    for section in range(len(radial_sections) - 1):
        a = section * 4
        b = (section + 1) * 4
        faces.extend(
            [
                (a, b, b + 1, a + 1),
                (a + 2, a + 3, b + 3, b + 2),
                (a, a + 2, b + 2, b),
                (a + 1, b + 1, b + 3, a + 3),
            ]
        )
    faces.extend([(0, 1, 3, 2), (8, 10, 11, 9)])
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    blade = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(blade)
    assign(blade, CARBON)
    bevel(blade, 0.018, 3)
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


def wing_half(name: str, side: float) -> bpy.types.Object:
    """AMT-200S planform calibrated to 18.70 m² and 2.5° dihedral."""
    dihedral = math.tan(math.radians(2.5))
    root_z = -0.25
    stations = [
        # span, leading x, chord, z, NACA thickness ratio, incidence
        (0.00, -2.22, 1.48, root_z, 0.18, 2.0),
        (1.40, -2.18, 1.38, root_z + 1.40 * dihedral, 0.18, 1.7),
        (4.80, -1.98, 1.04, root_z + 4.80 * dihedral, 0.18, 0.8),
        (8.735, -1.73, 0.58, root_z + 8.735 * dihedral, 0.18, 0.0),
    ]
    return airfoil_half(name, side, stations, IAF_GRAY, chord_points=52)


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


def canted_winglet(name: str, side: float) -> bpy.types.Object:
    """Tapered winglet canted outboard as shown on late Super Ximangos."""
    base_y = 8.71 * side
    top_y = 8.96 * side
    half_thickness = 0.022
    profile = [
        (-1.73, base_y, 0.12),
        (-1.15, base_y, 0.12),
        (-1.29, top_y, 0.73),
        (-1.61, top_y, 0.83),
    ]
    verts = [(x, y - half_thickness, z) for x, y, z in profile] + [
        (x, y + half_thickness, z) for x, y, z in profile
    ]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7)]
    for idx in range(4):
        nxt = (idx + 1) % 4
        faces.append((idx, nxt, 4 + nxt, 4 + idx))
    mesh = bpy.data.meshes.new(f"{name} mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, IAF_GRAY)
    bevel(obj, 0.018, 3)
    smooth(obj)
    mark_export(obj)
    return obj


def add_airframe_surface_details(root: bpy.types.Object) -> None:
    """Add restrained scale cues found on a composite production airframe."""
    # Cowling, equipment-bay and avionics-cover joints.  These are deliberately
    # narrow: they should catch highlights without reading as decorative bands.
    elliptical_ring("Engine cowling joint", -3.62, 0.307, 0.205, 0.02, 0.0055, SEAM, root)
    elliptical_ring("Avionics cover joint", -1.62, 0.412, 0.148, 0.335, 0.0042, SEAM, root)
    elliptical_ring("Mission bay shell joint", 0.18, 0.307, 0.170, 0.035, 0.0045, SEAM, root)
    elliptical_ring("Aft shell joint", 2.18, 0.162, 0.118, -0.025, 0.0040, SEAM, root)

    # Fine cover-to-fuselage seals define the low, opaque avionics cover.  The
    # cover uses the exact same composite skin material as the fuselage.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        surface_detail_line(
            f"{label} canopy perimeter seal",
            [
                (-2.56, 0.17 * side, 0.300),
                (-2.30, 0.31 * side, 0.286),
                (-1.76, 0.41 * side, 0.272),
                (-1.22, 0.36 * side, 0.255),
                (-0.76, 0.16 * side, 0.238),
            ],
            0.0060,
            SEAM,
            root,
        )

    # Flap and aileron hinge lines sit just above the lifting-surface skin.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        surface_detail_line(
            f"{label} flap hinge",
            [
                (-1.09, 1.48 * side, -0.120),
                (-1.10, 3.18 * side, -0.055),
                (-1.13, 4.70 * side, 0.010),
            ],
            0.0055,
            SEAM,
            root,
        )
        surface_detail_line(
            f"{label} aileron hinge",
            [
                (-1.14, 4.84 * side, 0.018),
                (-1.20, 6.62 * side, 0.095),
                (-1.28, 8.46 * side, 0.170),
            ],
            0.0050,
            SEAM,
            root,
        )
        surface_detail_line(
            f"{label} elevator hinge",
            [
                (3.51, 0.12 * side, 1.312),
                (3.51, 1.74 * side, 1.325),
            ],
            0.0045,
            SEAM,
            root,
        )

        # Scale-appropriate navigation lenses and a short static wick.
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=24,
            ring_count=12,
            radius=0.035,
            location=(-1.43, 8.72 * side, 0.155),
        )
        navigation_light = bpy.context.object
        navigation_light.name = f"{label} navigation lens"
        navigation_light.scale = (1.25, 0.66, 0.62)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(navigation_light, NAV_RED if side > 0 else NAV_GREEN)
        smooth(navigation_light)
        mark_export(navigation_light)
        navigation_light.parent = root

        wick = cylinder_between(
            f"{label} static discharge wick",
            (-1.15, 8.68 * side, 0.145),
            (-0.96, 8.75 * side, 0.135),
            0.0038,
            GRAPHITE,
            vertices=10,
        )
        wick.parent = root


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
    root["landing_gear_layout"] = "two swept wing-mounted main gears and compact tail wheel; no nose wheel"
    root["external_store_visualization"] = "two symmetric nonfunctional external fuel-tank visualizations"
    root["mission_system_geometry"] = "illustrative external visualization only"
    # A compact tail assembly creates the characteristic tail-down ground
    # attitude while keeping all three tires on the same apron plane.
    root["ground_attitude_deg"] = 4.7
    root.rotation_euler[1] = math.radians(4.7)
    mark_export(root)

    fuselage = create_asymmetric_fuselage(
        "Ximango-derived composite fuselage",
        [
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
            (0.18, 0.285, 0.158, 0.172, 0.030, 0.62),
            (0.78, 0.232, 0.138, 0.142, 0.014, 0.68),
            (1.48, 0.188, 0.122, 0.120, -0.006, 0.72),
            (2.18, 0.148, 0.104, 0.100, -0.030, 0.76),
            (2.82, 0.110, 0.088, 0.080, -0.058, 0.80),
            (3.36, 0.082, 0.072, 0.062, -0.084, 0.84),
            (3.72, 0.058, 0.055, 0.049, -0.106, 0.88),
            (3.90, 0.042, 0.045, 0.042, -0.120, 0.92),
        ],
        IAF_GRAY,
    )
    fuselage.parent = root

    # The UAV avionics cover follows the Ximango canopy footprint but is much
    # lower than the crewed glazing.  It is an opaque continuation of the same
    # IAF composite skin — no glass material and no contrasting canopy color.
    fairing = create_loft(
        "Low Ximango-profile opaque avionics cover",
        [
            (-2.70, 0.045, 0.018, 0.272),
            (-2.56, 0.165, 0.052, 0.292),
            (-2.30, 0.305, 0.102, 0.330),
            (-1.98, 0.390, 0.142, 0.355),
            (-1.62, 0.412, 0.150, 0.362),
            (-1.30, 0.368, 0.128, 0.348),
            (-1.02, 0.282, 0.088, 0.315),
            (-0.78, 0.155, 0.043, 0.272),
            (-0.66, 0.040, 0.016, 0.238),
        ],
        IAF_GRAY,
        ring_segments=64,
    )
    fairing.parent = root

    # Long wing with a restrained 2.5 degree dihedral.
    wing_left = wing_half("Port wing", 1.0)
    wing_right = wing_half("Starboard wing", -1.0)
    wing_left.parent = root
    wing_right.parent = root
    port_fillet = wing_root_fillet("Port wing root blended fairing", 1.0)
    starboard_fillet = wing_root_fillet("Starboard wing root blended fairing", -1.0)
    port_fillet.parent = root
    starboard_fillet.parent = root

    # Compact upturned tips consistent with later Super Ximango examples.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        tip = canted_winglet(f"{label} winglet", side)
        tip.parent = root

    # Two presentation-only external fuel tanks. Their uninterrupted teardrop
    # shells, rounded ends and paired suspension points deliberately distinguish
    # them from missile geometry; no internal fuel-system detail is represented.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        station_y = 2.68 * side
        pylon = fin_mesh(
            f"{label} external fuel-tank pylon",
            [
                (-2.18, -0.19),
                (-0.72, -0.13),
                (-0.57, -0.27),
                (-0.72, -0.42),
                (-2.02, -0.42),
                (-2.23, -0.31),
            ],
            0.075,
            IAF_GRAY,
            y_offset=station_y,
        )
        pylon.parent = root

        tank = create_loft(
            f"{label} external fuel tank",
            [
                (-2.48, 0.020, 0.018, -0.565),
                (-2.39, 0.085, 0.078, -0.565),
                (-2.20, 0.158, 0.145, -0.565),
                (-1.92, 0.202, 0.184, -0.565),
                (-1.28, 0.212, 0.192, -0.565),
                (-0.82, 0.188, 0.170, -0.565),
                (-0.48, 0.116, 0.102, -0.565),
                (-0.28, 0.028, 0.024, -0.565),
            ],
            IAF_GRAY,
            ring_segments=56,
            y_offset=station_y,
        )
        tank.parent = root

        for x, suffix in ((-1.88, "forward"), (-0.94, "aft")):
            clevis = cylinder_between(
                f"{label} fuel-tank {suffix} suspension pin",
                (x, station_y - 0.092, -0.405),
                (x, station_y + 0.092, -0.405),
                0.024,
                STEEL,
                vertices=20,
            )
            clevis.parent = root
            lug = cube(
                f"{label} fuel-tank {suffix} mounting lug",
                (x, station_y, -0.455),
                (0.075, 0.105, 0.070),
                HARDWARE_GRAY,
                0.018,
            )
            lug.parent = root

        for x, radius_y, radius_z in (
            (-2.18, 0.164, 0.150),
            (-1.28, 0.212, 0.192),
            (-0.66, 0.154, 0.139),
        ):
            elliptical_ring(
                f"{label} fuel-tank shell joint",
                x,
                radius_y,
                radius_z,
                -0.565,
                0.0036,
                SEAM,
                root,
                segments=56,
                tube_segments=6,
                y_offset=station_y,
            )

    # Vertical fin and high-mounted stabilizer.
    vertical = fin_mesh(
        "Vertical stabilizer",
        [(2.48, -0.08), (3.88, -0.12), (3.70, 1.34), (3.03, 1.32)],
        0.075,
        IAF_GRAY,
    )
    vertical.parent = root

    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        stab = airfoil_half(
            f"{label} horizontal stabilizer",
            side,
            [
                (0.00, 2.82, 0.92, 1.29, 0.12, -1.0),
                (1.84, 3.02, 0.65, 1.31, 0.12, -1.0),
            ],
            IAF_GRAY,
            chord_points=40,
        )
        stab.parent = root

    # Nose spinner and two-blade variable-pitch propeller.
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.035, radius2=0.205, depth=0.34, location=(-4.00, 0, 0))
    spinner = bpy.context.object
    spinner.name = "Propeller spinner"
    spinner.rotation_euler[1] = math.radians(90)
    assign(spinner, HARDWARE_GRAY)
    smooth(spinner)
    mark_export(spinner)
    spinner.parent = root

    hub = cylinder_between("Propeller hub", (-4.13, 0, 0), (-4.24, 0, 0), 0.09, STEEL)
    hub.parent = root
    for angle, suffix in ((math.radians(14), "A"), (math.radians(194), "B")):
        propeller_blade(f"Propeller blade {suffix}", angle, root)

    # Ximango/glider-style tail-dragger gear. There is deliberately no nose
    # wheel: the two independent main wheels sit below the wing roots and the
    # small aft wheel supports the tail.
    for side, label in ((1.0, "Port"), (-1.0, "Starboard")):
        mount_x = -1.63
        mount_y = 1.18 * side
        wheel_y = 1.40 * side
        # The axle is forward and outboard of the upper attachment. This short
        # swept leaf is the characteristic Ximango stance visible in the hangar
        # reference, and avoids the toy-like vertical post of the earlier model.
        wheel_location = (-1.89, wheel_y, -0.78)

        # Compact under-wing mounting blister that visibly intersects the wing
        # skin and closes the assembly at its upper end.
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=36,
            ring_count=18,
            location=(mount_x, mount_y, -0.315),
        )
        blister = bpy.context.object
        blister.name = f"{label} main gear wing-root fairing"
        blister.scale = (0.30, 0.22, 0.095)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(blister, IAF_GRAY)
        smooth(blister)
        mark_export(blister)
        blister.parent = root

        attachment_pin = cylinder_between(
            f"{label} main gear upper attachment pin",
            (mount_x, mount_y - 0.16, -0.35),
            (mount_x, mount_y + 0.16, -0.35),
            0.036,
            STEEL,
            vertices=32,
        )
        attachment_pin.parent = root

        landing_gear_fairing(
            f"{label} swept composite main gear leg",
            (mount_x, mount_y, -0.34),
            (-1.83, wheel_y, wheel_location[2] + 0.115),
            root,
        )

        # Twin lower fork arms terminate at the spanwise axle. Their overlap
        # with both the faired leaf and hub makes the load path unambiguous.
        for fork_offset, suffix in ((-0.062, "inboard"), (0.062, "outboard")):
            fork = cylinder_between(
                f"{label} main gear {suffix} axle fork",
                (-1.82, wheel_y + fork_offset, -0.64),
                (wheel_location[0], wheel_y + fork_offset, wheel_location[2]),
                0.027,
                STEEL,
                vertices=28,
            )
            fork.parent = root
        axle = cylinder_between(
            f"{label} main wheel axle",
            (wheel_location[0], wheel_y - 0.105, wheel_location[2]),
            (wheel_location[0], wheel_y + 0.105, wheel_location[2]),
            0.028,
            STEEL,
            vertices=32,
        )
        axle.parent = root
        landing_wheel(label, wheel_location, 0.165, 0.13, root)

    tail_wheel_location = (3.48, 0.0, -0.40)
    for y in (-0.045, 0.045):
        tail_fork = cylinder_between(
            "Tail wheel spring fork",
            (3.31, y, -0.22),
            (tail_wheel_location[0], y, tail_wheel_location[2]),
            0.022,
            IAF_GRAY,
        )
        tail_fork.parent = root
    tail_fairing = cube(
        "Streamlined tail wheel fairing",
        (3.395, 0.0, -0.31),
        (0.14, 0.050, 0.035),
        IAF_GRAY,
        0.045,
    )
    tail_fairing.rotation_euler[1] = math.radians(46.6)
    tail_fairing.parent = root
    landing_wheel("Tail", tail_wheel_location, 0.105, 0.065, root)

    # EO/IR assembly aft of the turret. A blended belly pad, yaw ring and
    # two-sided yoke now form one continuous mechanical chain from airframe to
    # sensor ball; none of the visible pieces are suspended in space.
    gimbal_y = 0.15
    gimbal_x = -0.38
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=(gimbal_x, gimbal_y, -0.30))
    gimbal_pad = bpy.context.object
    gimbal_pad.name = "EO IR blended belly attachment fairing"
    gimbal_pad.scale = (0.30, 0.23, 0.095)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(gimbal_pad, IAF_GRAY)
    smooth(gimbal_pad)
    mark_export(gimbal_pad)
    gimbal_pad.parent = root

    gimbal_shaft = cylinder_between(
        "EO IR yaw shaft",
        (gimbal_x, gimbal_y, -0.30),
        (gimbal_x, gimbal_y, -0.45),
        0.092,
        STEEL,
        vertices=32,
    )
    gimbal_shaft.parent = root
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=0.17,
        depth=0.10,
        location=(gimbal_x, gimbal_y, -0.46),
    )
    gimbal_yaw_ring = bpy.context.object
    gimbal_yaw_ring.name = "EO IR azimuth bearing ring"
    assign(gimbal_yaw_ring, HARDWARE_GRAY)
    smooth(gimbal_yaw_ring)
    mark_export(gimbal_yaw_ring)
    gimbal_yaw_ring.parent = root

    yoke_bridge = cylinder_between(
        "EO IR yoke bridge",
        (gimbal_x, gimbal_y - 0.17, -0.49),
        (gimbal_x, gimbal_y + 0.17, -0.49),
        0.036,
        STEEL,
        vertices=28,
    )
    yoke_bridge.parent = root
    for y, suffix in ((gimbal_y - 0.15, "port"), (gimbal_y + 0.15, "starboard")):
        arm = cylinder_between(
            f"EO IR {suffix} yoke arm",
            (gimbal_x, y, -0.48),
            (gimbal_x, y, -0.62),
            0.030,
            STEEL,
            vertices=24,
        )
        arm.parent = root

    gimbal_location = (gimbal_x, gimbal_y, -0.635)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=28, radius=0.20, location=gimbal_location)
    gimbal = bpy.context.object
    gimbal.name = "EO IR stabilized gimbal"
    gimbal.scale = (0.95, 1.0, 0.98)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(gimbal, GRAPHITE)
    smooth(gimbal)
    mark_export(gimbal)
    gimbal.parent = root

    # Side trunnions terminate the yoke at the roll axis rather than letting
    # its arms disappear into a generic sphere.
    for y, suffix in ((gimbal_y - 0.205, "port"), (gimbal_y + 0.205, "starboard")):
        bracket = cube(
            f"EO IR {suffix} trunnion bracket",
            (gimbal_x, y, -0.565),
            (0.070, 0.032, 0.090),
            HARDWARE_GRAY,
            0.025,
        )
        bracket.parent = root
        trunnion_cap = cylinder_between(
            f"EO IR {suffix} roll-axis cap",
            (gimbal_x, y - 0.025, -0.635),
            (gimbal_x, y + 0.025, -0.635),
            0.050,
            ALLOY,
            vertices=36,
        )
        trunnion_cap.parent = root

    elliptical_ring(
        "EO IR roll-axis housing joint",
        gimbal_x,
        0.198,
        0.194,
        -0.635,
        0.006,
        SEAM,
        root,
        segments=56,
        tube_segments=6,
        y_offset=gimbal_y,
    )

    # A shallow machined face plate creates the flat optical datum used on a
    # professional multi-sensor turret. Each aperture includes a metal bezel,
    # recessed glass and visible fasteners instead of lenses pasted to a ball.
    face_plate = cube(
        "EO IR machined optical face plate",
        (gimbal_x - 0.160, gimbal_y, -0.635),
        (0.025, 0.120, 0.110),
        HARDWARE_GRAY,
        0.028,
    )
    face_plate.parent = root
    aperture_layout = (
        (gimbal_y - 0.045, -0.605, 0.058, "daylight EO"),
        (gimbal_y + 0.050, -0.675, 0.043, "cooled IR"),
        (gimbal_y + 0.060, -0.585, 0.022, "range channel"),
    )
    for y, z, radius, label in aperture_layout:
        bezel = cylinder_between(
            f"EO IR {label} aperture bezel",
            (gimbal_x - 0.170, y, z),
            (gimbal_x - 0.205, y, z),
            radius * 1.24,
            ALLOY,
            vertices=40,
        )
        bezel.parent = root
        lens = cylinder_between(
            f"EO IR {label} optical glass",
            (gimbal_x - 0.202, y, z),
            (gimbal_x - 0.222, y, z),
            radius,
            LENS,
            vertices=40,
        )
        lens.parent = root
    for y_offset, z_offset in ((-0.102, -0.090), (-0.102, 0.090), (0.102, -0.090), (0.102, 0.090)):
        fastener = cylinder_between(
            "EO IR face-plate captive fastener",
            (gimbal_x - 0.184, gimbal_y + y_offset, -0.635 + z_offset),
            (gimbal_x - 0.200, gimbal_y + y_offset, -0.635 + z_offset),
            0.008,
            STEEL,
            vertices=20,
        )
        fastener.parent = root

    # Enlarged stabilized turret visualization.  These are presentation-only
    # exterior proportions, intentionally omitting functional weapon detail.
    turret_y = -0.20
    turret_x = -1.00
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=(turret_x, turret_y, -0.31))
    turret_pad = bpy.context.object
    turret_pad.name = "Weapon station blended belly hardpoint"
    turret_pad.scale = (0.40, 0.31, 0.115)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(turret_pad, IAF_GRAY)
    smooth(turret_pad)
    mark_export(turret_pad)
    turret_pad.parent = root

    turret_shaft = cylinder_between(
        "Weapon station azimuth shaft",
        (turret_x, turret_y, -0.32),
        (turret_x, turret_y, -0.48),
        0.16,
        HARDWARE_GRAY,
        vertices=36,
    )
    turret_shaft.parent = root

    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.27, depth=0.14, location=(turret_x, turret_y, -0.51))
    yaw_base = bpy.context.object
    yaw_base.name = "Stabilized weapon yaw base"
    assign(yaw_base, GRAPHITE)
    smooth(yaw_base)
    mark_export(yaw_base)
    yaw_base.parent = root
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.248,
        minor_radius=0.008,
        major_segments=48,
        minor_segments=8,
        location=(turret_x, turret_y, -0.445),
    )
    yaw_joint = bpy.context.object
    yaw_joint.name = "Weapon station yaw-bearing joint"
    assign(yaw_joint, SEAM)
    smooth(yaw_joint)
    mark_export(yaw_joint)
    yaw_joint.parent = root
    for index in range(6):
        angle = 2.0 * math.pi * index / 6.0
        bolt_x = turret_x + math.cos(angle) * 0.19
        bolt_y = turret_y + math.sin(angle) * 0.19
        bolt = cylinder_between(
            "Weapon station captive mounting bolt",
            (bolt_x, bolt_y, -0.430),
            (bolt_x, bolt_y, -0.455),
            0.011,
            STEEL,
            vertices=20,
        )
        bolt.parent = root
    upper_yoke = cylinder_between(
        "Weapon upper yoke bridge",
        (turret_x, turret_y - 0.22, -0.55),
        (turret_x, turret_y + 0.22, -0.55),
        0.046,
        STEEL,
        vertices=32,
    )
    upper_yoke.parent = root
    receiver = cube(
        "Gimballed cannon receiver",
        (-1.19, turret_y, -0.67),
        (0.38, 0.15, 0.145),
        GRAPHITE,
        0.052,
    )
    receiver.parent = root
    trunnion = cylinder_between(
        "Weapon elevation trunnion",
        (-1.04, turret_y - 0.23, -0.65),
        (-1.04, turret_y + 0.23, -0.65),
        0.095,
        STEEL,
        vertices=32,
    )
    trunnion.parent = root
    for y, suffix in ((turret_y - 0.245, "port"), (turret_y + 0.245, "starboard")):
        trunnion_cap = cylinder_between(
            f"Weapon {suffix} trunnion end cap",
            (-1.04, y - 0.025, -0.65),
            (-1.04, y + 0.025, -0.65),
            0.104,
            ALLOY,
            vertices=40,
        )
        trunnion_cap.parent = root
    for y, suffix in ((turret_y - 0.19, "port"), (turret_y + 0.19, "starboard")):
        yoke = cylinder_between(
            f"Weapon mount {suffix} yoke",
            (-1.04, y, -0.52),
            (-1.04, y, -0.65),
            0.034,
            STEEL,
            vertices=24,
        )
        yoke.parent = root
    sleeve = cylinder_between(
        "Cannon barrel thermal sleeve",
        (-1.48, turret_y, -0.66),
        (-1.88, turret_y, -0.66),
        0.050,
        RAIL,
        vertices=28,
    )
    sleeve.parent = root
    barrel = cylinder_between(
        "Cannon barrel",
        (-1.48, turret_y, -0.66),
        (-2.58, turret_y, -0.66),
        0.026,
        GRAPHITE,
        vertices=24,
    )
    barrel.parent = root
    muzzle = cylinder_between(
        "Cannon muzzle device",
        (-2.52, turret_y, -0.66),
        (-2.72, turret_y, -0.66),
        0.043,
        GRAPHITE,
        vertices=24,
    )
    muzzle.parent = root
    optic = cube(
        "Weapon boresight optic",
        (-1.22, turret_y - 0.20, -0.55),
        (0.115, 0.068, 0.070),
        GRAPHITE,
        0.025,
    )
    optic.parent = root
    optic_lens = cylinder_between(
        "Weapon optic aperture",
        (-1.330, turret_y - 0.20, -0.55),
        (-1.360, turret_y - 0.20, -0.55),
        0.036,
        LENS,
        vertices=30,
    )
    optic_lens.parent = root

    # A restrained swept dorsal data-link fairing.
    mast = fin_mesh(
        "Datalink fairing",
        [(1.34, 0.34), (1.76, 0.34), (1.66, 0.62), (1.47, 0.60)],
        0.055,
        HARDWARE_GRAY,
    )
    mast.parent = root

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
    bpy.ops.mesh.primitive_plane_add(size=70, location=(0, 0, -0.79))
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
