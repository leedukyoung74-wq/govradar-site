#!/usr/bin/env python3
"""WMM GOV RADAR agent patch boundary; outputs a patch, never commits or pushes.

This must run from a trusted copy made BEFORE the AI coding step. All GitHub
jobs use contents:read. A human reviews patches before any source-branch merge.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ALLOWED_PREFIXES=("tests/","web/","src/review_pages/","docs/","schemas/")
ALLOWED_FILES=frozenset(("build.py","pages3.py"))
MAX_FILES=8
MAX_PATCH_BYTES=250_000

def allowed(path):
    if not isinstance(path,str) or not path or path.startswith(("/",".","-")):
        return False
    if "\\" in path or ".." in Path(path).parts or "\n" in path:
        return False
    return path in ALLOWED_FILES or any(path.startswith(p) for p in ALLOWED_PREFIXES)

def execute(*cmd):
    result=subprocess.run(cmd,check=True,capture_output=True)
    return result.stdout

def names_in_patch(patch):
    if b"GIT binary patch" in patch or b"Binary files " in patch or b"new file mode 120000" in patch:
        raise ValueError("Binary or symlink patches are forbidden")
    if len(patch)>MAX_PATCH_BYTES:
        raise ValueError("Patch exceeds review size limit")
    text=patch.decode("utf-8")
    if any(line.startswith(("rename from ","rename to ","copy from ","copy to ")) for line in text.splitlines()):
        raise ValueError("Rename and copy patches are not allowed")
    paths=[]
    for line in text.splitlines():
        if line.startswith("diff --git "):
            match=re.fullmatch(r"diff --git a/([^ ]+) b/([^ ]+)",line)
            if not match or match.group(1)!=match.group(2):
                raise ValueError("Unsupported patch path")
            paths.append(match.group(1))
    if len(paths)>MAX_FILES or not paths:
        raise ValueError("Patch must modify 1 to 8 permitted files")
    if len(paths)!=len(set(paths)):
        raise ValueError("Duplicate paths in patch")
    for path in paths:
        if not allowed(path):
            raise ValueError("Forbidden path: "+path)
    return paths

def collect(output):
    # Include new files only after validating paths; git add -N does not commit.
    new_files=execute("git","ls-files","--others","--exclude-standard","-z").decode("utf-8").split("\0")
    for path in filter(None,new_files):
        if not allowed(path):
            raise ValueError("Disallowed untracked path: "+path)
        execute("git","add","-N","--",path)
    changed=execute("git","diff","--name-only","-z","HEAD").decode("utf-8").split("\0")
    for path in filter(None,changed):
        if not allowed(path):
            raise ValueError("Forbidden changed path: "+path)
    patch=execute("git","diff","--binary","HEAD")
    paths=names_in_patch(patch)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(patch)
    print("Proposed review patch (not pushed):",", ".join(paths))
    return 0

def validate(patchfile):
    patch=Path(patchfile).read_bytes()
    paths=names_in_patch(patch)
    print("Reviewed paths:",", ".join(paths))
    return 0

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("collect","validate"))
    parser.add_argument("--patch",required=True)
    opts=parser.parse_args()
    try:
        raise SystemExit(collect(opts.patch) if opts.mode=="collect" else validate(opts.patch))
    except (ValueError, OSError, UnicodeError, subprocess.CalledProcessError) as error:
        print("BLOCKED:",error,file=sys.stderr)
        raise SystemExit(2)
