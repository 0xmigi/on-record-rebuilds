"""Print the Cargo.toml (relative to cwd) whose [lib] name, or package name, is argv[1]."""
import glob, sys, tomllib

lib = sys.argv[1]
for m in sorted(glob.glob("**/Cargo.toml", recursive=True)):
    if "/target/" in m or "node_modules" in m:
        continue
    try:
        t = tomllib.load(open(m, "rb"))
    except Exception:
        continue
    libn = (t.get("lib") or {}).get("name")
    pkg = (t.get("package") or {}).get("name")
    if libn == lib or (isinstance(pkg, str) and pkg.replace("-", "_") == lib):
        print(m)
        sys.exit(0)
sys.exit(f"no Cargo.toml builds a library named {lib}")
