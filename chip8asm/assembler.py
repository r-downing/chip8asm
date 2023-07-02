"""
Chip8 Assembler


Assembly Language Reference:

define X Y    # create an alias X for Y
@label        # create a label named "label" at current offset
clear         # clear the screen
return        # return from subroutine
goto @label   # jump to the address of label
call @label   # call subroutine at address of label
if vx == nn   # if true, do next instr
if vx != nn   # if true, do next instruction
if vx == vy   # if true, do next instruction
vx = nn       # set vx to nn
vx += nn      # add, vf not affected
vx = vy       # set vx to vy
vx |= vy      # bitwise or
vx &= vy      # bitwise and
draw vx vy n  # draw sprite@i at pos vx, vy, 8xN
if key vx     # do next instr if key[vx] pressed
if !key vx    # do next instr if key[vx] not pressed
vx = delay    # get remaining delay
vx = key      # block until key press, store in vx
delay = vx    # set delay timer to vx
sound = vx    # set sound timer to vx
i = nnn       # set i to nnn
i = @label    # set i to offset of label
i += vx       # set i to i + vx
i = font vx   # set i to font[vx] (0-f)
vx = rand nn  # set vx to rand & nn 
bcd vx        # dump binary-coded decimal of vx to mem[i:i+3]
dump vx       # dump reg v0-vx to mem[i:i+x+1]
load vx       # load mem[i:i+x+1] to v0-vx
u8 nn         # literal binary 8-bit val 
u16 nnnn      # literal binary 16-bit val
"""

import logging
import re

log = logging.getLogger(__name__)


def assemble(asm_code: str) -> bytes:
    labels = {}

    def lambda_cap(func, *a, **kw):
        return lambda: func(*a, **kw)

    def ifequal(a: str, b: str):
        r"""if ([^\s]+) == ([^\s]+)"""
        assert a.startswith("v")
        x = a[1].upper()
        if b.startswith("v"):
            y = b[1].upper()
            return f"9{x}{y}0"
        nn = int(b, 0)
        return f"4{x}{nn:02X}"

    def ifnotequal(a: str, b: str):
        r"""if ([^\s]+) != (\S+)"""
        assert a.startswith("v")
        x = a[1].upper()
        if b.startswith("v"):
            y = b[1].upper()
            return f"5{x}{y}0"
        nn = int(b, 0)
        return f"3{x}{nn:02X}"

    def setvx(x: str, rest: str):
        r"""v([0-9a-f]) = (.*)"""
        if rest.startswith("v"):
            y = rest[1]
            return f"8{x}{y}0"
        if rest.startswith("rand"):
            nn = int(rest.split()[-1], 0)
            return f"C{x}{nn:02x}"
        if rest.startswith("delay"):
            return f"F{x}07"
        if rest.startswith("key"):
            return f"F{x}0a"
        else:
            nn = int(rest, 0)
            return f"6{x}{nn:02x}"

    def arithmetic(x, op, y):
        r"""v([0-9a-f]) (\S\S\S?) v([0-9a-f])"""
        ops = {"|=": 1, "&=": 2, "^=": 3, "+=": 4, "-=": 5, "=-": 7}
        return f"8{x}{y}{ops[op]}"

    patterns = {
        r"goto @(\w+)": lambda lbl: lambda_cap(lambda l: f"1{labels[l]:03x}", lbl),
        r"goto (\w+)": lambda nnn: f"1{int(nnn, 0):03x}",
        r"call @(\w+)": lambda lbl: lambda_cap(lambda l: f"2{labels[l]:03x}", lbl),
        r"call (\w+)": lambda nnn: f"2{int(nnn, 0):03x}",
        "clear": lambda: "00E0",
        "return": lambda: "00EE",
        ifequal.__doc__: ifequal,
        ifnotequal.__doc__: ifnotequal,
        setvx.__doc__: setvx,
        arithmetic.__doc__: arithmetic,
        r"v([0-9a-f]) >>= .*": lambda x: f"8{x}06",
        r"v([0-9a-f]) <<= .*": lambda x: f"8{x}0E",
        r"i = (\w+)$": lambda nnn: f"A{int(nnn, 0):03X}",
        r"i = @(\w+)$": lambda lbl: lambda_cap(lambda l: f"A{labels[l]:03X}", lbl),
        r"pc = v0 \+ (\S+)": lambda nnn: f"B{int(nnn, 0):03X}",
        r"draw v([0-9a-f]) v([0-9a-f]) (\S+)": lambda x, y, n: f"D{x}{y}{int(n, 0):x}",
        r"if (!?)key v([0-9a-f])": lambda excl, x: f"E{x}{'9e' if excl else 'a1'}",
        r"v([0-9a-f]) \+= ([^v]+)": lambda x, nn: f"7{x}{int(nn, 0):02X}",
        r"delay = v([0-9a-f])": lambda x: f"F{x}15",
        r"sound = v([0-9a-f])": lambda x: f"F{x}18",
        r"i \+= v([0-9a-f])": lambda x: f"F{x}1E",
        r"i = font v([0-9a-f])": lambda x: f"F{x}29",
        r"bcd v([0-9a-f])": lambda x: f"F{x}33",
        r"dump v([0-9a-f])": lambda x: f"F{x}55",
        r"load v([0-9a-f])": lambda x: f"F{x}65",
    }

    lines = asm_code.split("\n")
    nums_lines = ((i + 1, e) for i, e in enumerate(lines))
    nums_lines = ((num, line.split("#")[0].strip()) for num, line in nums_lines)
    nums_lines = ((num, line) for num, line in nums_lines if line)
    addr = 0x200
    ret = []
    defines = {}
    for num, raw_line in nums_lines:
        parts = raw_line.split()
        for i in range(len(parts)):
            if parts[i] in defines:
                parts[i] = defines[parts[i]]

        if parts[0] == "define":
            defines[parts[1]] = parts[2]
            continue

        if parts[0] == "u8":
            u8 = int(parts[1], 0)
            assert u8 < 0x100
            ret.append(f"{u8:02x}")
            addr += 1
            continue

        if parts[0] == "u16":
            u16 = int(parts[1], 0)
            assert u16 < 0x10000
            ret.append(f"{u16:04x}")
            addr += 2
            continue

        line = " ".join(parts)
        log.debug(f"{num:03}: {raw_line}  ---> {line}")

        if line.startswith("@"):
            new_label = line[1:].strip()
            labels[new_label] = addr
            log.debug(f"{new_label=}, 0x{addr=:03X}")

            continue

        pattern = next((p for p in patterns if re.match(p, line)), None)
        if pattern is None:
            raise Exception(f"Invalid format on line#{num} {raw_line}")
        m = re.match(pattern, line)
        log.debug(f"{pattern=}, {m=}, {m.groups()=}")
        ret.append(patterns[pattern](*m.groups()))
        addr += 2

    for i in range(len(ret)):
        log.debug(ret[i])
        if callable(ret[i]):
            ret[i] = ret[i]()

    return bytes.fromhex("".join(ret))


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("asmfile", help="Path to the input assembly language text file")
    parser.add_argument("outputfile", help="Path to the output binary file destination")

    args = parser.parse_args()
    with open(args.asmfile, "r") as fp:
        asm = fp.read()

    with open(args.outputfile, "wb") as fp:
        fp.write(assemble(asm))


if __name__ == "__main__":
    main()
