"""SPL Token build: exe hash, spl_token's crate hash (from its v0 symbol names),
whether that hash sorts before the __rustc allocator shims' hash, and whether
the spl_token free functions really landed before __rust_alloc in .text.
Usage: spl-token-order.py <label> <deploy.so> <unstripped.so>"""
import hashlib, re, struct, sys

label, deploy, unstripped = sys.argv[1:4]
exe = hashlib.sha256(open(deploy, "rb").read().rstrip(b"\0")).hexdigest()
d = open(unstripped, "rb").read()


def symbols(d):
    shoff, = struct.unpack_from("<Q", d, 0x28)
    shentsize, shnum = struct.unpack_from("<HH", d, 0x3A)
    secs = [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * shentsize) for i in range(shnum)]
    for s in secs:
        if s[1] != 2:  # SHT_SYMTAB
            continue
        strtab = secs[s[6]]
        for off in range(s[4], s[4] + s[5], 24):
            name, info, _, _, value, _ = struct.unpack_from("<IBBHQQ", d, off)
            start = strtab[4] + name
            yield d[start:d.index(b"\0", start)].decode(), value


syms = dict(symbols(d))
lib_fn = next(n for n in syms if re.match(r"_RNvCs\w+?_9spl_token25try_ui_amount_into_amount$", n))
crate = re.match(r"_RNvCs(\w+?)_9spl_token", lib_fn).group(1)
shim = next(n for n in syms if n.endswith("___rustc12___rust_alloc"))
shim_hash = re.match(r"_RNvCs(\w+?)_7___rustc", shim).group(1)
predicted = "spl_token first" if f"_RNvCs{crate}_9spl_token" < f"_RNvCs{shim_hash}_7___rustc" else "shims first"
actual = "spl_token first" if syms[lib_fn] < syms[shim] else "shims first"
print(f"{label}: {exe[:16]} | spl_token crate hash {crate} vs __rustc {shim_hash} | "
      f"predicted {predicted}, actual {actual}")
