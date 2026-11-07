#!/usr/bin/env python3
"""Diagnostic: print frond tip positions per tree from the generator."""
import math, sys
sys.path.insert(0, "/home/z/my-project/gabriel-homes/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gen", "/home/z/my-project/gabriel-homes/scripts/r60_gen_palms.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

for name, tree in (("LEFT", gen.LEFT_TREE), ("RIGHT", gen.RIGHT_TREE)):
    crown = tree["crown"]
    print(f"== {name} crown={crown} base={tree['base']} "
          f"lean_dx={crown[0]-tree['base'][0]:.0f} "
          f"trunk_top=({crown[0]},{crown[1]+6})")
    for (variant, target, scale, mirror, layer) in tree["placements"]:
        shape = gen.ARCH if variant == "arch" else gen.DROOP
        rot = gen.rot_for(shape, target, mirror)
        tx, ty = shape[2][0]*gen.FROND_LEN, shape[2][1]*gen.FROND_LEN
        sx = -1.0 if mirror else 1.0
        mx, my = tx*sx*scale, ty*scale
        rad = math.radians(rot)
        px = crown[0] + mx*math.cos(rad) - my*math.sin(rad)
        py = crown[1] + mx*math.sin(rad) + my*math.cos(rad)
        ang = math.degrees(math.atan2(py-crown[1], px-crown[0]))
        dist = math.hypot(px-crown[0], py-crown[1])
        print(f"  {layer:5} {variant:5} target={target:4} rot={rot:7.1f} "
              f"mirror={mirror!s:5} tip=({px:6.1f},{py:6.1f}) "
              f"angle={ang:7.1f} dist={dist:5.1f}")
