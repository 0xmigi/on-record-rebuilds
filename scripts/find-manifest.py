"""Print the Cargo.toml (relative to cwd) whose [lib] name, or package name, is argv[1]."""
import glob, re, sys

lib = sys.argv[1]
for m in sorted(glob.glob("**/Cargo.toml", recursive=True)):
    if "/target/" in m or "node_modules" in m:
        continue
    t = open(m).read()
    libn = re.search(r'\[lib\][^\[]*?\bname\s*=\s*"([^"]+)"', t, re.S)
    pkg = re.search(r'\[package\][^\[]*?\bname\s*=\s*"([^"]+)"', t, re.S)
    if (libn and libn.group(1) == lib) or (pkg and pkg.group(1).replace("-", "_") == lib):
        print(m)
        sys.exit(0)
sys.exit(f"no Cargo.toml builds a library named {lib}")
