"""Compiler fingerprints from platform-tools' prebuilt compiler_builtins.

extract <rlib> -> JSON {function: normalized-hex} for every function in the rlib's object files
scan <program.so> <db.json> -> which toolchains' functions appear verbatim in the program's .text
Normalization zeroes call immediates and lddw immediates (relocated at link time); jumps are kept.
"""
import json, struct, sys, hashlib

def ar_members(b):
    assert b[:8] == b"!<arch>\n"
    o, names = 8, None
    while o + 60 <= len(b):
        h = b[o:o+60]; size = int(h[48:58].decode().strip()); name = h[:16].decode().strip()
        data = b[o+60:o+60+size]
        if name == "//": names = data
        elif name.startswith("/") and name[1:].isdigit() and names is not None:
            i = int(name[1:]); name = names[i:names.index(b"/\n", i)].decode()
        yield name, data
        o += 60 + size + (size & 1)

def sections(e):
    shoff = struct.unpack_from("<Q", e, 0x28)[0]; shentsize, shnum, shstrndx = struct.unpack_from("<HHH", e, 0x3A)
    S = [struct.unpack_from("<IIQQQQIIQQ", e, shoff + i * shentsize) for i in range(shnum)]
    stro = S[shstrndx][4]
    nm = lambda off: e[off:e.index(b"\0", off)].decode()
    return [(nm(stro + s[0]),) + s for s in S]

def norm(code):
    out, i = bytearray(), 0
    while i + 8 <= len(code):
        ins = bytearray(code[i:i+8]); op = ins[0]
        if op == 0x18 and i + 16 <= len(code):
            nxt = bytearray(code[i+8:i+16]); ins[4:8] = b"\0\0\0\0"; nxt[4:8] = b"\0\0\0\0"; out += ins + nxt; i += 16; continue
        if op == 0x85: ins[4:8] = b"\0\0\0\0"
        out += ins; i += 8
    return bytes(out)

def funcs_from_obj(e):
    secs = sections(e)
    symtab = next((s for s in secs if s[2] == 2), None)
    if not symtab: return {}
    strtab = secs[symtab[7]]
    out = {}
    for k in range(symtab[6] // 24):
        st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from("<IBBHQQ", e, symtab[5] + k * 24)
        if st_info & 0xF != 2 or st_size < 48 or st_shndx == 0 or st_shndx >= len(secs): continue
        name = e[strtab[5] + st_name: e.index(b"\0", strtab[5] + st_name)].decode()
        sec = secs[st_shndx]
        code = e[sec[5] + st_value: sec[5] + st_value + st_size]
        out[name] = norm(code).hex()
    return out

def extract(rlib):
    b = open(rlib, "rb").read(); out = {}
    for name, data in ar_members(b):
        if data[:4] == b"\x7fELF": out.update(funcs_from_obj(data))
    return out

def text_of(so):
    e = open(so, "rb").read() + b"\0" * 4096  # deployed bytes have trailing zero padding stripped
    for s in sections(e):
        if s[0] == ".text": return norm(e[s[5]: s[5] + s[6]])
    return b""

if __name__ == "__main__":
    if sys.argv[1] == "extract":
        json.dump(extract(sys.argv[2]), sys.stdout)
    elif sys.argv[1] == "scan":
        t = text_of(sys.argv[2]); db = json.load(open(sys.argv[3]))
        res = []
        for tool, fns in db.items():
            hits = [f for f, h in fns.items() if bytes.fromhex(h) in t]
            res.append((len(hits), tool, len(fns)))
        for n, tool, tot in sorted(res, reverse=True)[:8]: print(f"{n:4d} of {tot:4d}  {tool}")
