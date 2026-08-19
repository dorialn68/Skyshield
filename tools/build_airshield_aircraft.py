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
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_GLB = ROOT / "airshield-ximango.glb"
OUTPUT_RENDER = ROOT / "airshield-xmango-hero.jpg"

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


IAF_GRAY = material("IAF matte light gray", (0.39, 0.405, 0.40, 1.0), 0.02, 0.48)
IAF_GRAY_DARK = material("Avionics fairing gray", (0.055, 0.085, 0.10, 1.0), 0.10, 0.24)
GRAPHITE = material("Graphite", (0.035, 0.045, 0.052, 1.0), 0.28, 0.28)
RUBBER = material("Tire rubber", (0.012, 0.014, 0.016, 1.0), 0.0, 0.72)
LENS = material("Sensor glass", (0.015, 0.055, 0.075, 1.0), 0.38, 0.08)
STEEL = material("Mechanism steel", (0.18, 0.20, 0.21, 1.0), 0.72, 0.24)
CONCRETE = material("Concrete", (0.24, 0.26, 0.27, 1.0), 0.0, 0.84)
HANGAR = material("Hangar", (0.075, 0.09, 0.10, 1.0), 0.15, 0.58)


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
    hub = cylinder_between(
        f"{name} hub",
        (x, y - width * 0.58, z),
        (x, y + width * 0.58, z),
        outer_radius * 0.34,
        STEEL,
        vertices=32,
    )
    hub.parent = parent
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
    assign(blade, GRAPHITE)
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
) -> bpy.types.Object:
    """Loft elliptical rings along X. Each section is x, radius_y, radius_z, z_offset."""
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    for x, ry, rz, z_offset in sections:
        for idx in range(ring_segments):
            angle = 2 * math.pi * idx / ring_segments
            vertices.append((x, math.cos(angle) * ry, z_offset + math.sin(angle) * rz))

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
    return airfoil_half(name, side, stations, IAF_GRAY, chord_points=38)


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
    ring_segments = 40
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
    root["landing_gear_layout"] = "two retractable main gears and coupled tail wheel"
    # A compact tail assembly creates the characteristic tail-down ground
    # attitude while keeping all three tires on the same apron plane.
    root["ground_attitude_deg"] = 4.7
    root.rotation_euler[1] = math.radians(4.7)
    mark_export(root)

    fuselage = create_loft(
        "Ximango-derived composite fuselage",
        [
            (-3.84, 0.20, 0.20, 0.00),
            (-3.52, 0.34, 0.34, 0.00),
            (-3.05, 0.42, 0.41, 0.03),
            (-2.45, 0.48, 0.47, 0.07),
            (-1.55, 0.51, 0.52, 0.10),
            (-0.55, 0.48, 0.47, 0.10),
            (0.30, 0.40, 0.39, 0.07),
            (1.25, 0.31, 0.30, 0.02),
            (2.35, 0.22, 0.21, -0.03),
            (3.25, 0.13, 0.14, -0.08),
            (3.90, 0.055, 0.065, -0.12),
        ],
        IAF_GRAY,
    )
    fuselage.parent = root

    # A tapered avionics fairing follows the actual Ximango canopy envelope.
    # The asymmetric fore/aft sections avoid the generic capsule shape.
    fairing = create_loft(
        "Ximango-profile avionics fairing",
        [
            (-2.80, 0.06, 0.05, 0.42),
            (-2.65, 0.20, 0.11, 0.45),
            (-2.40, 0.34, 0.22, 0.52),
            (-2.00, 0.42, 0.30, 0.58),
            (-1.55, 0.43, 0.32, 0.59),
            (-1.20, 0.39, 0.29, 0.56),
            (-0.90, 0.30, 0.22, 0.50),
            (-0.72, 0.19, 0.13, 0.45),
            (-0.58, 0.05, 0.04, 0.39),
        ],
        IAF_GRAY_DARK,
        ring_segments=36,
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
            chord_points=28,
        )
        stab.parent = root

    # Nose spinner and two-blade variable-pitch propeller.
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.035, radius2=0.205, depth=0.34, location=(-4.00, 0, 0))
    spinner = bpy.context.object
    spinner.name = "Propeller spinner"
    spinner.rotation_euler[1] = math.radians(90)
    assign(spinner, IAF_GRAY_DARK)
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
        mount_y = 1.18 * side
        wheel_y = 1.40 * side
        # Short, broad gear geometry follows the close-coupled Super Ximango
        # installation: the tire sits just below the under-wing fairing.
        wheel_location = (-1.87, wheel_y, -0.78)

        # Compact under-wing mounting blister, visible in the 360-degree view.
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=28,
            ring_count=14,
            location=(-1.87, mount_y, -0.33),
        )
        blister = bpy.context.object
        blister.name = f"{label} main gear wing-root fairing"
        blister.scale = (0.30, 0.21, 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(blister, IAF_GRAY_DARK)
        smooth(blister)
        mark_export(blister)
        blister.parent = root

        main_strut = cylinder_between(
            f"{label} main gear strut",
            (-1.87, mount_y, -0.35),
            wheel_location,
            0.020,
            STEEL,
        )
        main_strut.parent = root
        landing_gear_fairing(
            f"{label} retractable main gear fairing",
            (-1.87, mount_y, -0.37),
            (-1.87, wheel_y, wheel_location[2] + 0.12),
            root,
        )
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

    # EO/IR gimbal: approximately 0.34 m diameter, beneath the forward fuselage.
    gimbal_location = (-2.62, 0, -0.55)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.17, location=gimbal_location)
    gimbal = bpy.context.object
    gimbal.name = "EO IR stabilized gimbal"
    assign(gimbal, GRAPHITE)
    smooth(gimbal)
    mark_export(gimbal)
    gimbal.parent = root
    pylon = cylinder_between("EO IR gimbal pylon", (-2.62, 0, -0.33), (-2.62, 0, -0.48), 0.07, STEEL)
    pylon.parent = root
    for y, z, radius in ((-0.055, -0.53, 0.045), (0.055, -0.59, 0.033)):
        lens = cylinder_between(
            "EO IR sensor aperture",
            (-2.775, y, z),
            (-2.80, y, z),
            radius,
            LENS,
            vertices=32,
        )
        lens.parent = root

    # Compact .338-class stabilized remote weapon station.
    # The full visible system is under 1.25 m long and kept behind the EO/IR field of view.
    turret_y = -0.18
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.19, depth=0.10, location=(-0.92, turret_y, -0.49))
    yaw_base = bpy.context.object
    yaw_base.name = "Stabilized weapon yaw base"
    assign(yaw_base, GRAPHITE)
    smooth(yaw_base)
    mark_export(yaw_base)
    yaw_base.parent = root
    receiver = cube(
        "Compact cannon receiver",
        (-1.11, turret_y, -0.63),
        (0.28, 0.105, 0.11),
        GRAPHITE,
        0.035,
    )
    receiver.parent = root
    trunnion = cylinder_between(
        "Weapon elevation trunnion",
        (-1.00, turret_y - 0.16, -0.62),
        (-1.00, turret_y + 0.16, -0.62),
        0.07,
        STEEL,
    )
    trunnion.parent = root
    barrel = cylinder_between(
        "Cannon barrel",
        (-1.36, turret_y, -0.62),
        (-2.20, turret_y, -0.62),
        0.018,
        GRAPHITE,
        vertices=20,
    )
    barrel.parent = root
    muzzle = cylinder_between(
        "Cannon muzzle device",
        (-2.16, turret_y, -0.62),
        (-2.27, turret_y, -0.62),
        0.029,
        GRAPHITE,
        vertices=20,
    )
    muzzle.parent = root
    optic = cube(
        "Weapon boresight optic",
        (-1.16, turret_y - 0.14, -0.55),
        (0.09, 0.055, 0.055),
        GRAPHITE,
        0.018,
    )
    optic.parent = root
    optic_lens = cylinder_between(
        "Weapon optic aperture",
        (-1.255, turret_y - 0.14, -0.55),
        (-1.275, turret_y - 0.14, -0.55),
        0.028,
        LENS,
        vertices=24,
    )
    optic_lens.parent = root

    # A restrained swept dorsal data-link fairing.
    mast = fin_mesh(
        "Datalink fairing",
        [(1.34, 0.34), (1.76, 0.34), (1.66, 0.62), (1.47, 0.60)],
        0.055,
        IAF_GRAY_DARK,
    )
    mast.parent = root

    return root


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.render.filepath = str(OUTPUT_RENDER)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.use_file_extension = True

    world = scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.11, 0.13, 0.15, 1.0)
    bg.inputs["Strength"].default_value = 0.52

    # Concrete apron.
    bpy.ops.mesh.primitive_plane_add(size=70, location=(0, 0, -0.79))
    ground = bpy.context.object
    ground.name = "Concrete apron"
    assign(ground, CONCRETE)

    # Restrained hangar mass in the far background.
    hangar = cube("Background hangar", (9.0, 15.0, 2.9), (10.0, 5.0, 4.0), HANGAR, 0.10, export=False)
    door = cube("Hangar opening", (0.7, 9.92, 2.5), (3.4, 0.08, 3.0), GRAPHITE, 0.03, export=False)
    door.parent = hangar

    # Neutral key, fill and sunlight.
    bpy.ops.object.light_add(type="SUN", location=(-4, -8, 14))
    sun = bpy.context.object
    sun.name = "Late morning sun"
    sun.data.energy = 1.35
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
    )


def main() -> None:
    reset_scene()
    create_aircraft()
    setup_scene()
    export_glb()
    bpy.context.scene.render.filepath = str(OUTPUT_RENDER)
    bpy.ops.render.render(write_still=True)
    print(f"GLB: {OUTPUT_GLB}")
    print(f"Render: {OUTPUT_RENDER}")


if __name__ == "__main__":
    main()
