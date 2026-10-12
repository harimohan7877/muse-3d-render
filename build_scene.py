"""v3: full-3D Blender demo - fluffy Muse creature + orb + desk environment.
Reads scenes.json + envelope.json. Renders PNG sequence headless (Cycles CPU)."""
import bpy, json, math, os

BASE = os.path.dirname(os.path.abspath(__file__))  # script's own dir (works local + CI)
print("BASE:", BASE, flush=True)
SC = json.load(open(f"{BASE}/scenes.json"))
SCENES, TOTAL, FPS = SC["scenes"], SC["total"], SC["fps"]
ENV = json.load(open(f"{BASE}/envelope.json"))
NFRAMES = int(TOTAL * FPS)
FRAMES_DIR = f"{BASE}/frames3d"
os.makedirs(FRAMES_DIR, exist_ok=True)

# ---------- clean ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

def mat(name, color, rough=0.6, emission=None, e_strength=0.0, subsurface=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    if subsurface:
        try:
            b.inputs["Subsurface Weight"].default_value = subsurface
        except KeyError:
            pass
        try:
            b.inputs["Subsurface Color"].default_value = (*color, 1.0)
        except KeyError:
            pass
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = e_strength
    return m

CREAM = mat("Cream", (0.92, 0.86, 0.76), 0.9)
DARK = mat("Dark", (0.05, 0.06, 0.08), 0.15)
WHITE = mat("White", (1, 1, 1), 0.3)
PINK = mat("Pink", (1.0, 0.62, 0.62), 0.7)
ORB_MAT = mat("Orb", (0.4, 0.3, 1.0), 0.2, emission=(0.55, 0.35, 1.0), e_strength=1.6)
WOOD = mat("Wood", (0.35, 0.22, 0.12), 0.8)
WALL_MAT = mat("Wall", (0.06, 0.09, 0.18), 0.95)
HOODIE = mat("Hoodie", (0.12, 0.15, 0.24), 0.9)
SKIN = mat("Skin", (0.85, 0.62, 0.45), 0.7)
HAIR_MAT = mat("Hair", (0.1, 0.09, 0.12), 0.85)
SCREEN_MAT = mat("Screen", (0.05, 0.1, 0.2), 0.4, emission=(0.2, 0.5, 0.9), e_strength=1.2)
NIGHT_MAT = mat("Night", (0.03, 0.07, 0.18), 0.9, emission=(0.05, 0.12, 0.3), e_strength=0.8)
PAPER = mat("Paper", (0.9, 0.88, 0.8), 0.9)

def prim(op, **kw):
    getattr(bpy.ops.mesh, op)(**kw)
    o = bpy.context.active_object
    # smooth shading for organic shapes
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o

def key(obj, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        obj.location = loc; obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot; obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale; obj.keyframe_insert("scale", frame=frame)

DESK_Z = 1.15  # desk top surface

# ---------- MUSE rig ----------
rig = bpy.data.objects.new("MuseRig", None)
bpy.context.collection.objects.link(rig)

def child(mesh_obj, loc, parent=rig):
    mesh_obj.parent = parent
    mesh_obj.location = loc
    return mesh_obj

body = child(prim('primitive_uv_sphere_add', radius=1.0, segments=24, ring_count=16),
             (0, 0, 1.25))
body.scale = (1.0, 0.88, 1.12)
body.data.materials.append(CREAM)
head = child(prim('primitive_uv_sphere_add', radius=0.72, segments=24, ring_count=16),
             (0, 0.18, 2.15))
head.data.materials.append(CREAM)
# eyes
eyeL = child(prim('primitive_uv_sphere_add', radius=0.155, segments=16, ring_count=12),
             (-0.3, -0.5, 2.32)); eyeL.data.materials.append(DARK)
eyeR = child(prim('primitive_uv_sphere_add', radius=0.155, segments=16, ring_count=12),
             (0.3, -0.5, 2.32)); eyeR.data.materials.append(DARK)
for ex in (-0.3, 0.3):
    hl = child(prim('primitive_uv_sphere_add', radius=0.05, segments=10, ring_count=8),
               (ex + 0.06, -0.63, 2.4)); hl.data.materials.append(WHITE)
# smile (talking mouth -> scale Y by envelope): bezier arc curve
curve_data = bpy.data.curves.new("SmileCurve", type='CURVE')
curve_data.dimensions = '3D'
spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(2)
pts = [(-0.26, 0, 0), (0, -0.16, 0), (0.26, 0, 0)]
for i, (px, py, pz) in enumerate(pts):
    bp = spline.bezier_points[i]
    bp.co = (px, py, pz)
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
curve_data.bevel_depth = 0.055
curve_data.bevel_resolution = 4
smile = bpy.data.objects.new("Smile", curve_data)
bpy.context.collection.objects.link(smile)
child(smile, (0, -0.62, 2.02))
smile.rotation_euler = (math.radians(90), 0, 0)
smile.data.materials.append(DARK)
# blush
for bx in (-0.52, 0.52):
    bl = child(prim('primitive_uv_sphere_add', radius=0.1, segments=10, ring_count=8),
               (bx, -0.5, 2.12))
    bl.scale = (1, 0.4, 0.7); bl.data.materials.append(PINK)
# arms (holding pose)
for ax in (-0.95, 0.95):
    arm = child(prim('primitive_uv_sphere_add', radius=0.3, segments=12, ring_count=10),
                (ax, -0.35, 1.45))
    arm.scale = (0.7, 0.9, 1.3); arm.data.materials.append(CREAM)
# feet
for fx in (-0.45, 0.45):
    ft = child(prim('primitive_uv_sphere_add', radius=0.28, segments=12, ring_count=10),
               (fx, 0.1, 0.28))
    ft.scale = (1, 1.3, 0.6); ft.data.materials.append(CREAM)
# ORB (chest level, like holding it)
orb = child(prim('primitive_ico_sphere_add', radius=0.28, subdivisions=3),
            (0, -0.8, 1.35))
orb.data.materials.append(ORB_MAT)
orb_light = bpy.data.lights.new("OrbLight", 'POINT')
orb_light.energy = 35; orb_light.color = (0.6, 0.45, 1.0)
orb_light.use_shadow = False
orb_light_obj = bpy.data.objects.new("OrbLightObj", orb_light)
bpy.context.collection.objects.link(orb_light_obj)
orb_light_obj.parent = rig; orb_light_obj.location = (0, -0.8, 1.35)

MUSE_HOME = (0.9, -0.1, 1.02)
rig.location = (MUSE_HOME[0], MUSE_HOME[1], -3.0)  # hidden below, rises in sc1

# ---------- HUMAN (stylized) ----------
hum = bpy.data.objects.new("Human", None)
bpy.context.collection.objects.link(hum)
def hchild(o, loc):
    o.parent = hum; o.location = loc; return o
torso = hchild(prim('primitive_cylinder_add', radius=0.55, depth=1.7, vertices=16), (0, 0, 1.0))
torso.data.materials.append(HOODIE)
hhead = hchild(prim('primitive_uv_sphere_add', radius=0.42, segments=20, ring_count=14), (0, 0, 2.2))
hhead.data.materials.append(SKIN)
hair = hchild(prim('primitive_uv_sphere_add', radius=0.44, segments=20, ring_count=14), (0, 0.12, 2.4))
hair.scale = (1, 1, 0.68); hair.data.materials.append(HAIR_MAT)
for ex in (-0.16, 0.16):
    he = hchild(prim('primitive_uv_sphere_add', radius=0.06, segments=10, ring_count=8),
                (ex, -0.38, 2.18))
    he.data.materials.append(DARK)
for gx in (-0.16, 0.16):
    gl = hchild(prim('primitive_torus_add', major_radius=0.13, minor_radius=0.025,
                     major_segments=12, minor_segments=8), (gx, -0.4, 2.18))
    gl.data.materials.append(DARK)
hum.location = (-2.9, -0.2, 0.35)
hum.rotation_euler = (0, 0, math.radians(-18))

# ---------- ENVIRONMENT ----------
floor = prim('primitive_plane_add', size=30, location=(0, 0, 0))
floor.data.materials.append(WOOD)
wall = prim('primitive_plane_add', size=30, location=(0, 7, 8))
wall.rotation_euler = (math.radians(90), 0, 0)
wall.data.materials.append(WALL_MAT)
# desk
desk = prim('primitive_cube_add', size=1, location=(0.3, 0, DESK_Z - 0.12))
desk.scale = (4.2, 1.7, 0.24); desk.data.materials.append(WOOD)
for lx, ly in [(-3.4, -1.3), (3.9, -1.3), (-3.4, 1.3), (3.9, 1.3)]:
    leg = prim('primitive_cylinder_add', radius=0.09, depth=DESK_Z - 0.2, vertices=10,
               location=(lx, ly, (DESK_Z - 0.2) / 2))
    leg.data.materials.append(WOOD)
# laptop
lap_base = prim('primitive_cube_add', size=1, location=(-0.7, -0.35, DESK_Z + 0.03))
lap_base.scale = (0.85, 0.6, 0.06); lap_base.data.materials.append(DARK)
lap_scr = prim('primitive_cube_add', size=1, location=(-0.7, 0.12, DESK_Z + 0.42))
lap_scr.scale = (0.85, 0.05, 0.62); lap_scr.rotation_euler = (math.radians(-12), 0, 0)
lap_scr.data.materials.append(DARK)
scr_face = prim('primitive_plane_add', size=1, location=(-0.7, 0.085, DESK_Z + 0.42))
scr_face.scale = (0.78, 0.55, 1); scr_face.rotation_euler = (math.radians(78), 0, 0)
scr_face.data.materials.append(SCREEN_MAT)
# code lines on screen (thin emissive boxes)
for i in range(8):
    cl = prim('primitive_cube_add', size=1,
              location=(-0.95 + (i % 3) * 0.12, 0.07, DESK_Z + 0.28 + i * 0.055))
    cl.scale = (0.28 - (i % 3) * 0.06, 0.012, 0.02)
    cl.rotation_euler = (math.radians(78), 0, 0)
    cl.data.materials.append(mat(f"Code{i}", (0.2, 0.6, 1.0), 0.4,
                                 emission=(0.25, 0.65, 1.0), e_strength=2.0))
# window + stars
win_frame = prim('primitive_cube_add', size=1, location=(4.6, 6.8, 4.6))
win_frame.scale = (1.6, 0.15, 2.2); win_frame.data.materials.append(DARK)
win_glass = prim('primitive_plane_add', size=1, location=(4.6, 6.72, 4.6))
win_glass.scale = (2.8, 3.8, 1); win_glass.rotation_euler = (math.radians(90), 0, 0)
win_glass.data.materials.append(NIGHT_MAT)
import random
random.seed(7)
for _ in range(24):
    st = prim('primitive_uv_sphere_add', radius=0.05, segments=6, ring_count=4,
              location=(4.6 + random.uniform(-1.3, 1.3), 6.68,
                        4.6 + random.uniform(-1.8, 1.8)))
    st.data.materials.append(mat("Star", (1, 1, 1), 0.5, emission=(1, 1, 1), e_strength=2.5))
# lamp
lamp_base = prim('primitive_cylinder_add', radius=0.3, depth=0.08, vertices=16,
                 location=(3.1, 0.9, DESK_Z + 0.04))
lamp_base.data.materials.append(DARK)
lamp_arm = prim('primitive_cylinder_add', radius=0.05, depth=1.6, vertices=10,
                location=(3.1, 0.9, DESK_Z + 0.8))
lamp_arm.data.materials.append(DARK)
bpy.ops.mesh.primitive_cone_add(radius1=0.45, depth=0.5, vertices=16,
                                location=(3.1, 0.9, DESK_Z + 1.7))
shade = bpy.context.active_object; shade.data.materials.append(DARK)
lamp_light = bpy.data.lights.new("LampLight", 'POINT')
lamp_light.energy = 0; lamp_light.color = (1.0, 0.75, 0.45)
lamp_light.use_shadow = False
lamp_obj = bpy.data.objects.new("LampObj", lamp_light)
bpy.context.collection.objects.link(lamp_obj)
lamp_obj.location = (3.1, 0.9, DESK_Z + 1.55)
# papers
for i, px in enumerate([-2.2, -1.7]):
    pp = prim('primitive_cube_add', size=1, location=(px, 0.6 + i * 0.25, DESK_Z + 0.02))
    pp.scale = (0.5, 0.35, 0.015); pp.rotation_euler = (0, 0, 0.2 * i)
    pp.data.materials.append(PAPER)

# ---------- lights ----------
bpy.ops.object.light_add(type='SUN', location=(5, -6, 8))
sun = bpy.context.active_object; sun.data.energy = 0.5
sun.rotation_euler = (math.radians(60), 0, math.radians(30))
bpy.ops.object.light_add(type='POINT', location=(-4, -4, 4))
fill = bpy.context.active_object
fill.data.energy = 120; fill.data.color = (0.35, 0.5, 0.9)
fill.data.use_shadow = False

# ---------- camera + focus ----------
bpy.ops.object.camera_add(location=(0.9, -3.2, 2.1))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
cam.data.lens = 40
focus = bpy.data.objects.new("Focus", None)
bpy.context.collection.objects.link(focus)
trk = cam.constraints.new('TRACK_TO')
trk.target = focus; trk.track_axis = 'TRACK_NEGATIVE_Z'; trk.up_axis = 'UP_Y'

def ck(frame, cam_loc, focus_loc):
    key(cam, frame, loc=cam_loc); key(focus, frame, loc=focus_loc)

def s2f(sec):
    return int(round(sec * FPS))

ORB_POS = (0.9, -0.95, 1.0)
# shot keyframes from scenes
for sc in SCENES:
    f0, f1, shot = s2f(sc["start"]), s2f(sc["end"]), sc["shot"]
    if shot == "orb":
        ck(f0, (0.9, -2.7, 1.7), ORB_POS)
        ck(f1, (0.9, -2.25, 1.6), ORB_POS)  # slow push-in
    elif shot == "wide":
        ck(f0, (0.2, -6.8, 3.4), (0.2, 0.2, 1.4))
        ck(f1, (0.2, -6.8, 3.4), (0.2, 0.2, 1.4))
    elif shot == "human":
        ck(f0, (-2.9, -3.2, 2.3), (-2.9, 0, 1.9))
        ck(f1, (-2.9, -3.2, 2.3), (-2.9, 0, 1.9))
    elif shot == "montage":
        cx, cy, r = 0.9, -0.1, 4.2
        for k in range(5):
            a = k / 4 * math.pi * 1.5
            ff = f0 + int((f1 - f0) * k / 4)
            ck(ff, (cx + r * math.sin(a + 2.6), cy - r * math.cos(a + 2.6), 2.4),
               (0.9, -0.1, 1.7))
    elif shot == "hero":
        ck(f0, (0.9, -4.8, 1.5), (0.9, 0.1, 2.1))
        ck(f1, (0.9, -4.3, 1.6), (0.9, 0.1, 2.1))

# ---------- muse animation ----------
# scene 1 (orb): rise from darkness fast, orb glowing (visible most of scene)
sc1 = SCENES[0]
key(rig, 0, loc=(MUSE_HOME[0], MUSE_HOME[1], -3.0))
key(rig, s2f(sc1["start"]) + 25, loc=(MUSE_HOME[0], MUSE_HOME[1], -0.55))
key(rig, s2f(sc1["end"]) - 6, loc=(MUSE_HOME[0], MUSE_HOME[1], -0.55))
# scene 2 (wide): jump onto desk with squash & stretch
sc2 = SCENES[1]
j0, j1 = s2f(sc2["start"]), s2f(sc2["start"]) + 24
key(rig, j0, loc=(MUSE_HOME[0], MUSE_HOME[1], -0.55))
key(rig, j0 + 12, loc=(MUSE_HOME[0], MUSE_HOME[1], 3.4),
    scale=(0.85, 0.85, 1.2))                       # stretch up
key(rig, j1, loc=MUSE_HOME, scale=(1.25, 1.25, 0.72))  # squash on land
key(rig, j1 + 10, scale=(1, 1, 1))
rig.location = MUSE_HOME
# hold home afterwards
key(rig, NFRAMES - 1, loc=MUSE_HOME)

# montage spin (scene 4)
sc4 = SCENES[3]
m0, m1 = s2f(sc4["start"]), s2f(sc4["end"])
key(rig, m0, rot=(0, 0, 0))
key(rig, m1, rot=(0, 0, math.pi * 4))
# hero happy hop (scene 6)
sc6 = SCENES[5]
h0 = s2f(sc6["start"])
key(rig, h0 + 6, loc=(MUSE_HOME[0], MUSE_HOME[1], MUSE_HOME[2] + 0.9))
key(rig, h0 + 16, loc=MUSE_HOME, scale=(1.2, 1.2, 0.75))
key(rig, h0 + 26, scale=(1, 1, 1))

# orb orbit during montage (local coords circle around muse)
for k in range(9):
    ff = m0 + int((m1 - m0) * k / 8)
    a = k / 8 * math.pi * 2
    key(orb, ff, loc=(1.3 * math.cos(a), -0.1 + 1.3 * math.sin(a),
                      1.7 + 0.5 * math.sin(a * 2)))
key(orb, NFRAMES - 1, loc=(0, -0.8, 1.35))  # back to hands
# orb light pulse
for f in range(0, NFRAMES, 12):
    e = 35 + 30 * (0.5 + 0.5 * math.sin(f * 0.11))
    orb_light.energy = e
    orb_light.keyframe_insert("energy", frame=f)

# lamp reveal: dark in sc1, on from sc2
lamp_light.energy = 0; lamp_light.keyframe_insert("energy", frame=0)
f_lamp = s2f(SCENES[1]["start"]) + 8
lamp_light.energy = 900; lamp_light.keyframe_insert("energy", frame=f_lamp)

# smile talking: scale Y from envelope (every 2nd frame)
for f in range(0, NFRAMES, 2):
    v = ENV[f] if f < len(ENV) else 0
    smile.scale = (1, 0.35 + v * 1.1, 1)
    smile.keyframe_insert("scale", frame=f)
# blink every ~3.5s
for b in range(0, NFRAMES, 105):
    for e in (eyeL, eyeR):
        key(e, b, scale=(1, 1, 1))
        key(e, b + 4, scale=(1, 1, 0.08))
        key(e, b + 8, scale=(1, 1, 1))

bpy.context.view_layer.update()

# ---------- render ----------
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 2
scene.cycles.transmission_bounces = 0
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = 40
scene.render.film_transparent = False
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.02, 0.035, 0.08, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = FRAMES_DIR + "/f"
scene.frame_start, scene.frame_end = 0, NFRAMES - 1

print("SCENE READY, frames:", NFRAMES)
import time
t0 = time.time()
if os.environ.get("SAVE_BLEND"):
    out = os.environ.get("BLEND_OUT") or os.path.join(os.getcwd(), "muse_scene.blend")
    out = os.path.abspath(out)
    print("Saving blend to:", out, "cwd:", os.getcwd(), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    if not os.path.exists(out):
        raise RuntimeError(f"Blend save FAILED, not found at {out}")
    print("BLEND SAVED:", out, f"({os.path.getsize(out)//1024} KB)")
elif os.environ.get("TEST_FRAMES"):
    # smoke test: render 3 scattered frames only
    for tf in [5, NFRAMES // 2, NFRAMES - 10]:
        scene.frame_set(tf)
        scene.render.filepath = FRAMES_DIR + f"/test_f{tf}"
        bpy.ops.render.render(write_still=True)
    print("SMOKE TEST DONE in", round(time.time() - t0, 1), "s")
else:
    # resumable per-frame loop (survives VM restarts)
    for f in range(NFRAMES):
        fp = f"{FRAMES_DIR}/f{f:04d}.png"
        if os.path.exists(fp):
            continue
        scene.frame_set(f)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        if f % 30 == 0:
            print(f"rendered {f}/{NFRAMES}", flush=True)
    print("FULL RENDER DONE in", round(time.time() - t0, 1), "s")
