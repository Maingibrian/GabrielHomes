#!/usr/bin/env python3
"""VLM helper: z-ai vision -i <img> -p <prompt>, parse JSON from first '{'."""
import subprocess, sys, json

def vlm(img, prompt):
    r = subprocess.run(["z-ai", "vision", "-i", img, "-p", prompt],
                       capture_output=True, text=True, timeout=180)
    out = r.stdout
    i = out.find("{")
    if i < 0:
        return "VLM-ERROR: " + out[:300]
    try:
        return json.loads(out[i:])["choices"][0]["message"]["content"]
    except Exception:
        return "PARSE-ERROR: " + out[:300]

if __name__ == "__main__":
    img, prompt = sys.argv[1], sys.argv[2]
    print(vlm(img, prompt))
