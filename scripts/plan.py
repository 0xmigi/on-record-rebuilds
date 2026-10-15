"""Work out how to rebuild one program from its on-chain recipe and its source.

Usage: plan.py <recipe args as JSON> <source dir>
Writes key=value lines (for $GITHUB_OUTPUT) to stdout.

Version choice, in order: the recipe's --base-image, [workspace.metadata.cli]
in Cargo.toml, Anchor.toml's [toolchain] solana_version, then the solana-program
version in Cargo.lock (the last two are what solana-verify falls back on, and
what a developer's own toolchain is usually pinned to). The chosen version is
matched to a real Solana/Agave release; if that exact release does not exist,
the newest patch release of the same minor version is used.
"""
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def parse_args(raw):
    flags, cargo, it = {}, [], iter(raw)
    for a in it:
        if a == "--":
            cargo = list(it)
            break
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            flags[k] = v.strip('"').strip("'")
        elif a in ("--bpf",):
            flags["bpf"] = "1"
        elif a.startswith("--"):
            flags[a[2:]] = next(it, "")
    return flags, cargo


def read(p):
    try:
        return open(p).read()
    except OSError:
        return ""


def version_from_sources(ws):
    m = re.search(r"\[workspace\.metadata\.cli\][^\[]*?solana\s*=\s*\"([0-9.]+)\"", read(os.path.join(ws, "Cargo.toml")), re.S)
    if m:
        return m.group(1), "Cargo.toml [workspace.metadata.cli]"
    m = re.search(r"\[toolchain\][^\[]*?solana_version\s*=\s*\"([0-9.]+)\"", read(os.path.join(ws, "Anchor.toml")), re.S)
    if m:
        return m.group(1), "Anchor.toml solana_version"
    lock = read(os.path.join(ws, "Cargo.lock"))
    for crate in ("solana-program", "solana-program-error", "solana-account-info"):
        m = re.search(r'name = "%s"\nversion = "([0-9.]+)"' % crate, lock)
        if m:
            return m.group(1), f"Cargo.lock {crate}"
    return None, None


def resolve_release(version):
    rels = [l.split() for l in open(os.path.join(DATA, "releases.txt")) if l.strip()]
    tags = {t: r for r, t in rels}
    if "v" + version in tags:
        return tags["v" + version], "v" + version
    mm = ".".join(version.split(".")[:2])
    same = [t for t in tags if re.fullmatch(r"v%s\.\d+" % re.escape(mm), t)]
    if same:
        best = max(same, key=lambda t: int(t.rsplit(".", 1)[1]))
        return tags[best], best
    return None, None


def main():
    raw = json.loads(sys.argv[1])
    src = sys.argv[2]
    flags, cargo = parse_args(raw)
    out = {}
    if "bpf" in flags:
        out["skip"] = "recipe uses the legacy cargo build-bpf"
    mount = flags.get("mount-path", ".").strip("/") or "."
    ws = os.path.join(src, flags.get("workspace-path", mount).strip("/") or ".")
    version, source = None, None
    img = flags.get("base-image", "")
    if img:
        if "@sha256:" in img:
            digests = json.load(open(os.path.join(DATA, "image-digests.json")))
            version = digests.get(img.split("@sha256:")[1])
        elif ":" in img:
            version = img.rsplit(":", 1)[1].lstrip("v")
        source = f"recipe --base-image {img}"
        if version and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            version = None
    if not version:
        version, source = version_from_sources(ws)
    if not version:
        out.setdefault("skip", "could not determine a Solana version")
    else:
        repo, tag = resolve_release(version)
        if not tag:
            out.setdefault("skip", f"no Solana/Agave release for {version}")
        else:
            out.update(agave_repo=repo, agave_tag=tag)
    sbf = shlex.split(flags.get("cargo-build-sbf-args", ""))
    if flags.get("arch"):
        sbf += ["--arch", flags["arch"]]
    out.update(
        version=version or "",
        version_source=source or "",
        lib=flags.get("library-name", ""),
        mount=mount,
        sbf_args=" ".join(shlex.quote(a) for a in sbf),
        cargo_args=" ".join(shlex.quote(a) for a in cargo),
    )
    for k, v in out.items():
        print(f"{k}={v}")


main()
