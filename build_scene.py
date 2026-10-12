"""v5: emotional 1-min 3D short - proper human + improved Muse + real laptop.
Reads scenes.json + envelope.json (script-relative). SAVE_BLEND / TEST_FRAMES supported."""
import bpy, json, math, os, random

BASE = os.path.dirname(os.path.abspath(__file__))
print("BASE:", BASE, flush=True)
SC = json.load(open(f"{BASE}/scenes.json"))
SCENES, TOTAL, FPS = SC["scenes"], SC["total"], SC["fps"]
ENV = json.load(open(f"{BASE}/envelope.json"))
NFRAMES = int(TOTAL * FPS)
FRAMES_DIR = f"{BASE}/frames5"
os.makedirs(FRAMES_DIR, exist_ok=True)
random.seed(11)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

def mat(name, color, rough=0.6, emission=None, e_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = e_strength
    return m

CREAM = mat("Cream", (0.93, 0.87, 0.77), 0.9)
DARK = mat("Dark", (0.04, 0.05, 0.07), 0.15)
WHITE = mat("White", (1, 1, 1), 0.25)
PINK = mat("Pink", (1.0, 0.6, 0.6), 0.7)
MOUTH_M = mat("MouthIn", (0.35, 0.08, 0.1), 0.6)
ORB_MAT = mat("Orb", (0.4, 0.3, 1.0), 0.2, emission=(0.55, 0.35, 1.0), e_strength=1.2)
WOOD = mat("Wood", (0.32, 0.2, 0.11), 0.8)
WALL_MAT = mat("Wall", (0.05, 0.08, 0.16), 0.95)
SKIN = mat("Skin", (0.87, 0.64, 0.47), 0.65)
HAIR_MAT = mat("Hair", (0.12, 0.1, 0.1), 0.85)
SHIRT = mat("Shirt", (0.16, 0.28, 0.42), 0.85)
PANTS = mat("Pants", (0.1, 0.1, 0.14), 0.9)
SCREEN_MAT = mat("Screen", (0.04, 0.09, 0.18), 0.4, emission=(0.25, 0.55, 1.0), e_strength=1.4)
NIGHT_MAT = mat("Night", (0.03, 0.07, 0.18), 0.9, emission=(0.05, 0.12, 0.3), e_strength=0.8)
PAPER = mat("Paper", (0.9, 0.88, 0.8), 0.9)
MUG_M = mat("Mug", (0.7, 0.2, 0.15), 0.5)

def prim(op, **kw):
    getattr(bpy.ops.mesh, op)(**kw)
    o = bpy.context.active_object
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

def s2f(s): return int(round(s * FPS))

DESK_Z = 1.02  # desk top

# ================= MUSE (improved, faces -Y) =================
muse = bpy.data.objects.new("MuseRig", None)
bpy.context.collection.objects.link(muse)
def mchild(o, loc):
    o.parent = muse; o.location = loc; return o

mbody = mchild(prim('primitive_uv_sphere_add', radius=0.85, segments=24, ring_count=16), (0, 0, 0.95))
mbody.scale = (1.0, 0.9, 1.05); mbody.data.materials.append(CREAM)
mhead = mchild(prim('primitive_uv_sphere_add', radius=0.62, segments=24, ring_count=16), (0, -0.08, 1.78))
mhead.data.materials.append(CREAM)
# big glossy eyes (white + pupils)
muse_eye_whites = []
for ex in (-0.24, 0.24):
    ew = mchild(prim('primitive_uv_sphere_add', radius=0.155, segments=14, ring_count=10), (ex, -0.6, 1.9))
    ew.data.materials.append(WHITE); muse_eye_whites.append(ew)
    ep = mchild(prim('primitive_uv_sphere_add', radius=0.075, segments=10, ring_count=8), (ex, -0.72, 1.9))
    ep.data.materials.append(DARK)
    hl = mchild(prim('primitive_uv_sphere_add', radius=0.035, segments=8, ring_count=6), (ex+0.05, -0.78, 1.95))
    hl.data.materials.append(WHITE)
# brows
for bx in (-0.24, 0.24):
    br = mchild(prim('primitive_cube_add', size=1, location=(bx, -0.62, 2.12)), (bx, -0.62, 2.12))
    br.scale = (0.16, 0.03, 0.045); br.rotation_euler = (0, 0, -0.15 if bx < 0 else 0.15)
    br.data.materials.append(DARK)
# mouth (lip-sync): dark cavity scaled by envelope
mmouth = mchild(prim('primitive_uv_sphere_add', radius=0.13, segments=12, ring_count=10), (0, -0.66, 1.58))
mmouth.scale = (1.25, 0.45, 0.55); mmouth.data.materials.append(MOUTH_M)
# blush
for bx in (-0.44, 0.44):
    bl = mchild(prim('primitive_uv_sphere_add', radius=0.09, segments=10, ring_count=8), (bx, -0.55, 1.64))
    bl.scale = (1, 0.4, 0.7); bl.data.materials.append(PINK)
# typing arms: pivot empties at shoulders
marmL_piv = bpy.data.objects.new("MuseArmL", None); bpy.context.collection.objects.link(marmL_piv)
marmL_piv.parent = muse; marmL_piv.location = (-0.62, -0.35, 1.05)
marmR_piv = bpy.data.objects.new("MuseArmR", None); bpy.context.collection.objects.link(marmR_piv)
marmR_piv.parent = muse; marmR_piv.location = (0.62, -0.35, 1.05)
for piv, sx in ((marmL_piv, -1), (marmR_piv, 1)):
    arm = prim('primitive_uv_sphere_add', radius=0.22, segments=12, ring_count=10)
    arm.parent = piv; arm.location = (sx * 0.1, -0.25, -0.15)
    arm.scale = (0.8, 1.0, 1.5); arm.data.materials.append(CREAM)
    hand = prim('primitive_uv_sphere_add', radius=0.14, segments=10, ring_count=8)
    hand.parent = piv; hand.location = (sx * 0.12, -0.42, -0.42)
    hand.data.materials.append(CREAM)
# feet
for fx in (-0.35, 0.35):
    ft = mchild(prim('primitive_uv_sphere_add', radius=0.24, segments=12, ring_count=10), (fx, 0.05, 0.16))
    ft.scale = (1, 1.3, 0.55); ft.data.materials.append(CREAM)
# orb beside (not blocking face)
orb = mchild(prim('primitive_ico_sphere_add', radius=0.26, subdivisions=3), (0.95, -0.25, 0.45))
orb.data.materials.append(ORB_MAT)
orb_light = bpy.data.lights.new("OrbLight", 'POINT')
orb_light.energy = 30; orb_light.color = (0.6, 0.45, 1.0); orb_light.use_shadow = False
orb_light_obj = bpy.data.objects.new("OrbLightObj", orb_light)
bpy.context.collection.objects.link(orb_light_obj)
orb_light_obj.parent = muse; orb_light_obj.location = (0.95, -0.25, 0.6)

MUSE_HOME = (0.2, 1.15, DESK_Z)
muse.location = MUSE_HOME

# ================= HUMAN (proper, faces +Y) =================
hum = bpy.data.objects.new("HumanRig", None)
bpy.context.collection.objects.link(hum)
def hchild(o, loc):
    o.parent = hum; o.location = loc; return o

torso = hchild(prim('primitive_cylinder_add', radius=0.5, depth=1.35, vertices=18), (0, 0, 1.35))
torso.data.materials.append(SHIRT)
# shoulders
for sx in (-0.52, 0.52):
    sh = hchild(prim('primitive_uv_sphere_add', radius=0.2, segments=12, ring_count=10), (sx, 0, 1.9))
    sh.data.materials.append(SHIRT)
# arms: upper down, forearm forward onto desk (static, relaxed)
for sx in (-0.55, 0.55):
    up = hchild(prim('primitive_cylinder_add', radius=0.13, depth=0.75, vertices=12), (sx, 0, 1.5))
    up.data.materials.append(SHIRT)
    fo = hchild(prim('primitive_cylinder_add', radius=0.11, depth=0.7, vertices=12), (sx*0.9, 0.42, 1.15))
    fo.rotation_euler = (math.radians(80), 0, 0); fo.data.materials.append(SKIN)
    ha = hchild(prim('primitive_uv_sphere_add', radius=0.13, segments=10, ring_count=8), (sx*0.9, 0.72, 1.02))
    ha.data.materials.append(SKIN)
# right forearm pivot for gesture (scene 7)
# (gesture done via whole-torso lean instead - simpler & smooth)
neck = hchild(prim('primitive_cylinder_add', radius=0.15, depth=0.35, vertices=12), (0, 0, 2.12))
neck.data.materials.append(SKIN)
# head group (for nods)
headG = bpy.data.objects.new("HeadG", None); bpy.context.collection.objects.link(headG)
headG.parent = hum; headG.location = (0, 0, 2.18)
def hdchild(o, loc):
    o.parent = headG; o.location = loc; return o
hhead = hdchild(prim('primitive_uv_sphere_add', radius=0.45, segments=22, ring_count=16), (0, 0, 0.32))
hhead.data.materials.append(SKIN)
for ex in (-0.17, 0.17):  # eyes: white + pupils
    ew = hdchild(prim('primitive_uv_sphere_add', radius=0.105, segments=12, ring_count=10), (ex, 0.38, 0.4))
    ew.data.materials.append(WHITE)
    ep = hdchild(prim('primitive_uv_sphere_add', radius=0.05, segments=8, ring_count=6), (ex, 0.46, 0.4))
    ep.data.materials.append(DARK)
human_eye_whites = [o for o in headG.children if o.data and any(m.name == "White" for m in o.data.materials)]
# brows
for bx in (-0.17, 0.17):
    br = hdchild(prim('primitive_cube_add', size=1), (bx, 0.4, 0.6))
    br.scale = (0.18, 0.035, 0.05); br.rotation_euler = (0, 0, 0.12 if bx < 0 else -0.12)
    br.data.materials.append(HAIR_MAT)
nose = hdchild(prim('primitive_uv_sphere_add', radius=0.06, segments=8, ring_count=6), (0, 0.44, 0.3))
nose.data.materials.append(SKIN)
# mouth (lip-sync)
hmouth = hdchild(prim('primitive_uv_sphere_add', radius=0.1, segments=12, ring_count=10), (0, 0.4, 0.12))
hmouth.scale = (1.5, 0.45, 0.6); hmouth.data.materials.append(MOUTH_M)
for ex in (-0.44, 0.44):  # ears
    ea = hdchild(prim('primitive_uv_sphere_add', radius=0.09, segments=8, ring_count=6), (ex, 0, 0.32))
    ea.data.materials.append(SKIN)
hair = hdchild(prim('primitive_uv_sphere_add', radius=0.48, segments=20, ring_count=14), (0, -0.07, 0.44))
hair.scale = (1, 1, 0.72); hair.data.materials.append(HAIR_MAT)
# legs (thighs forward, shins down)
for sx in (-0.22, 0.22):
    th = hchild(prim('primitive_cylinder_add', radius=0.16, depth=0.8, vertices=12), (sx, 0.35, 0.62))
    th.rotation_euler = (math.radians(90), 0, 0); th.data.materials.append(PANTS)
    sh2 = hchild(prim('primitive_cylinder_add', radius=0.13, depth=0.65, vertices=12), (sx, 0.68, 0.32))
    sh2.data.materials.append(PANTS)
HUM_HOME = (0.2, -2.1, 0.0)
hum.location = HUM_HOME
# chair
chair = prim('primitive_cube_add', size=1, location=(0.2, -2.15, 0.45))
chair.scale = (0.65, 0.6, 0.12); chair.data.materials.append(WOOD)
chback = prim('primitive_cube_add', size=1, location=(0.2, -2.62, 1.0))
chback.scale = (0.65, 0.1, 0.9); chback.data.materials.append(WOOD)
for lx, lz in [(-0.25, -2.4), (0.65, -2.4), (-0.25, -1.9), (0.65, -1.9)]:
    leg = prim('primitive_cylinder_add', radius=0.05, depth=0.45, vertices=8, location=(lx, lz, 0.22))
    leg.data.materials.append(WOOD)

# ================= ENVIRONMENT =================
floor = prim('primitive_plane_add', size=34, location=(0, 0, 0)); floor.data.materials.append(WOOD)
wall = prim('primitive_plane_add', size=34, location=(0, 7.5, 9))
wall.rotation_euler = (math.radians(90), 0, 0); wall.data.materials.append(WALL_MAT)
# desk
desk = prim('primitive_cube_add', size=1, location=(0.2, 0, DESK_Z - 0.11))
desk.scale = (2.6, 1.15, 0.22); desk.data.materials.append(WOOD)
for lx, ly in [(-2.0, -0.9), (2.4, -0.9), (-2.0, 0.9), (2.4, 0.9)]:
    leg = prim('primitive_cylinder_add', radius=0.08, depth=DESK_Z - 0.2, vertices=10,
               location=(lx, ly, (DESK_Z - 0.2) / 2)); leg.data.materials.append(WOOD)
# laptop (proper)
lap_base = prim('primitive_cube_add', size=1, location=(0.2, 0.1, DESK_Z + 0.035))
lap_base.scale = (0.95, 0.65, 0.07); lap_base.data.materials.append(DARK)
# keyboard: inset lighter panel + key rows
kb = prim('primitive_cube_add', size=1, location=(0.2, 0.08, DESK_Z + 0.075))
kb.scale = (0.85, 0.4, 0.012); kb.data.materials.append(mat("Keys", (0.16, 0.17, 0.2), 0.7))
lap_scr = prim('primitive_cube_add', size=1, location=(0.2, 0.42, DESK_Z + 0.42))
lap_scr.scale = (0.95, 0.05, 0.62); lap_scr.rotation_euler = (math.radians(-14), 0, 0)
lap_scr.data.materials.append(DARK)
scr_face = prim('primitive_plane_add', size=1, location=(0.2, 0.385, DESK_Z + 0.42))
scr_face.scale = (0.88, 0.55, 1); scr_face.rotation_euler = (math.radians(76), 0, 0)
scr_face.data.materials.append(SCREEN_MAT)
for i in range(9):  # code lines
    cl = prim('primitive_cube_add', size=1, location=(-0.12 + (i % 3) * 0.14, 0.365, DESK_Z + 0.24 + i * 0.052))
    cl.scale = (0.3 - (i % 3) * 0.07, 0.012, 0.02); cl.rotation_euler = (math.radians(76), 0, 0)
    cl.data.materials.append(mat(f"Code{i}", (0.2, 0.6, 1.0), 0.4, emission=(0.3, 0.7, 1.0), e_strength=2.2))
# screen glow
scr_light = bpy.data.lights.new("ScrLight", 'POINT')
scr_light.energy = 25; scr_light.color = (0.4, 0.6, 1.0); scr_light.use_shadow = False
scr_light_obj = bpy.data.objects.new("ScrLightObj", scr_light)
bpy.context.collection.objects.link(scr_light_obj)
scr_light_obj.location = (0.2, -0.1, DESK_Z + 0.5)
# mug
mug = prim('primitive_cylinder_add', radius=0.14, depth=0.3, vertices=14, location=(-1.6, -0.5, DESK_Z + 0.15))
mug.data.materials.append(MUG_M)
# lamp
lamp_base = prim('primitive_cylinder_add', radius=0.28, depth=0.08, vertices=14, location=(2.3, 0.7, DESK_Z + 0.04))
lamp_base.data.materials.append(DARK)
lamp_arm = prim('primitive_cylinder_add', radius=0.045, depth=1.5, vertices=8, location=(2.3, 0.7, DESK_Z + 0.75))
lamp_arm.data.materials.append(DARK)
bpy.ops.mesh.primitive_cone_add(radius1=0.42, depth=0.5, vertices=14, location=(2.3, 0.35, DESK_Z + 1.55))
shade = bpy.context.active_object; shade.data.materials.append(DARK)
shade.rotation_euler = (math.radians(35), 0, 0)
lamp_light = bpy.data.lights.new("LampLight", 'POINT')
lamp_light.energy = 700; lamp_light.color = (1.0, 0.78, 0.5); lamp_light.use_shadow = False
lamp_obj = bpy.data.objects.new("LampObj", lamp_light)
bpy.context.collection.objects.link(lamp_obj); lamp_obj.location = (2.3, 0.35, DESK_Z + 1.4)
# window + stars
win_frame = prim('primitive_cube_add', size=1, location=(-3.2, 7.3, 4.8))
win_frame.scale = (1.7, 0.15, 2.3); win_frame.data.materials.append(DARK)
win_glass = prim('primitive_plane_add', size=1, location=(-3.2, 7.22, 4.8))
win_glass.scale = (3.0, 4.0, 1); win_glass.rotation_euler = (math.radians(90), 0, 0)
win_glass.data.materials.append(NIGHT_MAT)
for _ in range(26):
    st = prim('primitive_uv_sphere_add', radius=0.05, segments=6, ring_count=4,
              location=(-3.2 + random.uniform(-1.4, 1.4), 7.18, 4.8 + random.uniform(-1.9, 1.9)))
    st.data.materials.append(mat("Star", (1, 1, 1), 0.5, emission=(1, 1, 1), e_strength=2.5))
# papers
for i, px in enumerate([-1.1, -0.6]):
    pp = prim('primitive_cube_add', size=1, location=(px, -0.55 + i * 0.2, DESK_Z + 0.02))
    pp.scale = (0.5, 0.35, 0.015); pp.rotation_euler = (0, 0, 0.25 * i); pp.data.materials.append(PAPER)
# lights
bpy.ops.object.light_add(type='SUN', location=(5, -6, 9))
sun = bpy.context.active_object; sun.data.energy = 0.45
sun.rotation_euler = (math.radians(60), 0, math.radians(30))
bpy.ops.object.light_add(type='POINT', location=(-4, -5, 4.5))
fill = bpy.context.active_object
fill.data.energy = 90; fill.data.color = (0.35, 0.5, 0.9); fill.data.use_shadow = False

# ================= CAMERA =================
bpy.ops.object.camera_add(location=(-4.5, -1.5, 2.6))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
cam.data.lens = 42
focus = bpy.data.objects.new("Focus", None)
bpy.context.collection.objects.link(focus)
trk = cam.constraints.new('TRACK_TO')
trk.target = focus; trk.track_axis = 'TRACK_NEGATIVE_Z'; trk.up_axis = 'UP_Y'

def ck(frame, cam_loc, focus_loc):
    key(cam, frame, loc=cam_loc); key(focus, frame, loc=focus_loc)

for sc in SCENES:
    f0, f1, shot = s2f(sc["start"]), s2f(sc["end"]), sc["shot"]
    if shot == "two":
        ck(f0, (-6.2, -1.0, 3.6), (0.3, -0.5, 1.6))
        ck(f1, (-5.8, -0.8, 3.5), (0.3, -0.5, 1.6))
    elif shot == "muse":
        ck(f0, (2.7, -2.9, 2.65), (0.2, 1.0, 1.9))
        ck(f1, (2.5, -2.7, 2.6), (0.2, 1.0, 1.9))
    elif shot == "human":
        ck(f0, (2.7, -1.1, 2.9), (0.2, -2.0, 2.2))
        ck(f1, (2.5, -1.0, 2.85), (0.2, -2.0, 2.2))
    elif shot == "over":
        ck(f0, (1.7, -3.6, 2.9), (0.2, 0.7, 1.6))
        ck(f1, (1.5, -3.3, 2.8), (0.2, 0.7, 1.6))

# ================= ANIMATION =================
# speaker per frame
def speaker_at(f):
    sec = f / FPS
    for sc in SCENES:
        if sc["start"] <= sec < sc["end"]:
            return sc["speaker"]
    return None

# mouths: lip-sync gated by speaker (every 2nd frame)
for f in range(0, NFRAMES, 2):
    v = ENV[f] if f < len(ENV) else 0
    spk = speaker_at(f)
    my = 0.45 + (v * 1.3 if spk == "muse" else 0)
    mmouth.scale = (1.25, my, 0.55); mmouth.keyframe_insert("scale", frame=f)
    hy = 0.45 + (v * 1.4 if spk == "human" else 0)
    hmouth.scale = (1.5, hy, 0.6); hmouth.keyframe_insert("scale", frame=f)

# Muse typing: arms alternate + body bob during MUSE scenes
for sc in SCENES:
    if sc["speaker"] != "muse":
        continue
    f0, f1 = s2f(sc["start"]), s2f(sc["end"])
    for f in range(f0, f1, 6):
        ph = (f - f0) / 6
        aL = math.sin(ph * math.pi) * 0.35
        aR = math.sin(ph * math.pi + math.pi) * 0.35
        marmL_piv.rotation_euler = (aL, 0, 0); marmL_piv.keyframe_insert("rotation_euler", frame=f)
        marmR_piv.rotation_euler = (aR, 0, 0); marmR_piv.keyframe_insert("rotation_euler", frame=f)
        bob = abs(math.sin(ph * math.pi)) * 0.06
        muse.location = (MUSE_HOME[0], MUSE_HOME[1], MUSE_HOME[2] + bob)
        muse.keyframe_insert("location", frame=f)
key(muse, NFRAMES - 1, loc=MUSE_HOME)
marmL_piv.rotation_euler = (0, 0, 0); marmL_piv.keyframe_insert("rotation_euler", frame=NFRAMES - 1)
marmR_piv.rotation_euler = (0, 0, 0); marmR_piv.keyframe_insert("rotation_euler", frame=NFRAMES - 1)

# Muse looks up at human on line 8 (scene idx 7)
sc8 = SCENES[7]
key(muse, s2f(sc8["start"]), rot=(0, 0, 0))
key(muse, s2f(sc8["start"]) + 20, rot=(math.radians(-12), 0, math.radians(18)))
key(muse, s2f(sc8["end"]), rot=(0, 0, 0))

# Human: nod on line 7 (idx 6), lean-in on line 5 (idx 4), soft tilt line 9 (idx 8)
sc7, sc5, sc9 = SCENES[6], SCENES[4], SCENES[8]
f = s2f(sc7["start"])
key(headG, f, rot=(0, 0, 0)); key(headG, f + 12, rot=(math.radians(14), 0, 0))
key(headG, f + 24, rot=(0, 0, 0)); key(headG, f + 36, rot=(math.radians(14), 0, 0))
key(headG, f + 48, rot=(0, 0, 0))
f = s2f(sc5["start"])
key(hum, f, loc=HUM_HOME, rot=(0, 0, 0))
key(hum, f + 18, loc=(HUM_HOME[0], HUM_HOME[1] + 0.35, HUM_HOME[2]), rot=(math.radians(-8), 0, 0))
key(hum, s2f(sc5["end"]), loc=HUM_HOME, rot=(0, 0, 0))
f = s2f(sc9["start"])
key(headG, f, rot=(0, 0, 0)); key(headG, f + 20, rot=(0, 0, math.radians(10)))
key(headG, s2f(sc9["end"]), rot=(0, 0, 0))

# blinking (eye whites only)
blink_targets = list(muse_eye_whites) + list(human_eye_whites)
for b in range(40, NFRAMES, 110):
    for e in blink_targets:
        sx, sy, sz = e.scale.x, e.scale.y, e.scale.z
        key(e, b, scale=(sx, sy, sz))
        key(e, b + 4, scale=(sx, sy, 0.12))
        key(e, b + 8, scale=(sx, sy, sz))

# orb gentle pulse
for f in range(0, NFRAMES, 15):
    orb_light.energy = 30 + 14 * (0.5 + 0.5 * math.sin(f * 0.09))
    orb_light.keyframe_insert("energy", frame=f)

bpy.context.view_layer.update()

# ================= RENDER =================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 20
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

print("SCENE READY, frames:", NFRAMES, flush=True)
import time
t0 = time.time()
if os.environ.get("SAVE_BLEND"):
    out = os.environ.get("BLEND_OUT") or os.path.join(os.getcwd(), "muse_scene.blend")
    out = os.path.abspath(out)
    print("Saving blend to:", out, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    if not os.path.exists(out):
        raise RuntimeError(f"Blend save FAILED at {out}")
    print("BLEND SAVED:", out, flush=True)
elif os.environ.get("TEST_FRAMES"):
    for tf in [10, 103, 239, 793]:
        scene.frame_set(tf)
        scene.render.filepath = FRAMES_DIR + f"/test_f{tf}"
        bpy.ops.render.render(write_still=True)
    print("SMOKE TEST DONE in", round(time.time() - t0, 1), "s")
else:
    for f in range(NFRAMES):
        fp = f"{FRAMES_DIR}/f{f:04d}.png"
        if os.path.exists(fp):
            continue
        scene.frame_set(f)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        if f % 60 == 0:
            print(f"rendered {f}/{NFRAMES}", flush=True)
    print("FULL RENDER DONE in", round(time.time() - t0, 1), "s")
