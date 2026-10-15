"""Compare a built program with the deployed one, byte for byte.

Usage: compare.py <built.so> <deployed.so> <label>
Prints a short report and appends a side-by-side table to $GITHUB_STEP_SUMMARY.
Both files are compared with trailing zero padding stripped (the deployed
account is padded to its allocated size; solana-verify hashes the same way).
"""
import hashlib, os, sys

built = open(sys.argv[1], "rb").read().rstrip(b"\0")
chain = open(sys.argv[2], "rb").read().rstrip(b"\0")
label = sys.argv[3]
hb, hc = hashlib.sha256(built).hexdigest(), hashlib.sha256(chain).hexdigest()
n = min(len(built), len(chain))
differ = sum(1 for i in range(n) if built[i] != chain[i]) + abs(len(built) - len(chain))
same = hb == hc
print(f"deployed: {len(chain):,} bytes  sha256 {hc}")
print(f"rebuilt:  {len(built):,} bytes  sha256 {hb}")
print("MATCH: every byte identical" if same else f"DIFFERENT: {differ:,} bytes differ")
s = os.environ.get("GITHUB_STEP_SUMMARY")
if s:
    with open(s, "a") as f:
        f.write(f"## {'✅ Byte-for-byte match' if same else '❌ Does not match'}: {label}\n\n")
        f.write("| | size | sha256 fingerprint |\n|---|---|---|\n")
        f.write(f"| **Deployed on mainnet** | {len(chain):,} bytes | `{hc}` |\n")
        f.write(f"| **Rebuilt from public source** | {len(built):,} bytes | `{hb}` |\n\n")
        f.write(f"{'All ' + format(len(chain), ',') + ' bytes are identical.' if same else format(differ, ',') + ' bytes differ.'}\n")
sys.exit(0 if same else 1)
