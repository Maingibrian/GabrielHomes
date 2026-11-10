#!/usr/bin/env python3
"""Extract the multi-volume RAR archive of the gabriel-homes Django project."""
import os
import sys

from unrar.cffi import rarfile

UPLOAD = '/home/z/my-project/upload'
DEST = '/home/z/my-project'

part1 = os.path.join(UPLOAD, 'gabriel-homes-advanced-r64.part1.rar')
part2 = os.path.join(UPLOAD, 'gabriel-homes-advanced-r64.part2.rar')

rf = rarfile.RarFile(part1)
names = rf.namelist()
print(f'part1 entries: {len(names)}')

os.makedirs(DEST, exist_ok=True)

extracted = 0
errors = []
for name in names:
    target = os.path.join(DEST, name)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    try:
        data = rf.read(name)
        with open(target, 'wb') as f:
            f.write(data)
        extracted += 1
    except Exception as e:
        errors.append((name, str(e)))

print(f'extracted from part1: {extracted}')
if errors:
    print(f'errors: {len(errors)}')
    for n, e in errors[:10]:
        print(f'  {n}: {e}')

# Check part2 for any entries not in part1
try:
    rf2 = rarfile.RarFile(part2)
    names2 = rf2.namelist()
    print(f'part2 entries: {len(names2)}')
    extra = [n for n in names2 if n not in set(names)]
    print(f'extra entries in part2: {len(extra)}')
    for name in extra:
        target = os.path.join(DEST, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            data = rf2.read(name)
            with open(target, 'wb') as f:
                f.write(data)
            extracted += 1
        except Exception as e:
            errors.append((name, str(e)))
    print(f'total extracted: {extracted}')
except Exception as e:
    print(f'part2 error: {e}')
