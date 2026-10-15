"""sha256 of a program ELF with trailing zero padding stripped (the convention solana-verify uses)."""
import hashlib, sys

print(hashlib.sha256(open(sys.argv[1], "rb").read().rstrip(b"\0")).hexdigest())
