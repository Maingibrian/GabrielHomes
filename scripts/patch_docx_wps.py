#!/usr/bin/env python3
"""WPS-compat post-process for gabriel-homes-launch-checklist.docx:
1. Patch footer instrText bare PAGE -> PAGE \\* arabic \\* MERGEFORMAT
2. Remove empty <w:pgNumType/> from the cover section (confuses WPS)."""
import re
import shutil
import zipfile

SRC = "/home/z/my-project/download/gabriel-homes-launch-checklist.docx"
TMP = SRC + ".tmp"

with zipfile.ZipFile(SRC, "r") as zin:
    items = zin.infolist()
    data = {i.filename: zin.read(i.filename) for i in items}

changed = []
for name in list(data.keys()):
    if re.match(r"word/footer\d*\.xml$", name):
        xml = data[name].decode("utf-8")
        if "PAGE" in xml and "arabic" not in xml:
            xml2 = xml.replace(
                "> PAGE <", "> PAGE \\* arabic \\* MERGEFORMAT <"
            ).replace(
                ">PAGE<", ">PAGE \\* arabic \\* MERGEFORMAT<"
            )
            # generic: any instrText containing bare PAGE without switches
            xml2 = re.sub(
                r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
                r"\1 PAGE \\* arabic \\* MERGEFORMAT \2",
                xml2,
            )
            if xml2 != xml:
                data[name] = xml2.encode("utf-8")
                changed.append(name + ": PAGE -> arabic")
    if name == "word/document.xml":
        xml = data[name].decode("utf-8")
        xml2 = xml.replace("<w:pgNumType/>", "")
        if xml2 != xml:
            data[name] = xml2.encode("utf-8")
            changed.append("document.xml: stripped empty pgNumType")

with zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED) as zout:
    for i in items:
        zout.writestr(i, data[i.filename])

shutil.move(TMP, SRC)
print("PATCHED:", changed if changed else "nothing to change")
