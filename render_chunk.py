"""Render a chunk of frames from a prebuilt .blend (for GitHub Actions matrix).
Usage: blender -b --python render_chunk.py -- START END
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index("--") + 1:]
start, end = int(argv[0]), int(argv[1])

blend_path = os.path.abspath(os.path.join(os.getcwd(), "muse_scene.blend"))
print("Opening blend:", blend_path, flush=True)
if not os.path.exists(blend_path):
    raise RuntimeError(f"Blend not found at {blend_path}")
bpy.ops.wm.open_mainfile(filepath=blend_path)
scene = bpy.context.scene
os.makedirs("frames", exist_ok=True)
for f in range(start, end + 1):
    fp = f"frames/f{f:04d}.png"
    if os.path.exists(fp):
        continue
    scene.frame_set(f)
    scene.render.filepath = fp
    bpy.ops.render.render(write_still=True)
    if (f - start) % 10 == 0:
        print(f"chunk {start}-{end}: frame {f}", flush=True)
print(f"CHUNK DONE {start}-{end}")
