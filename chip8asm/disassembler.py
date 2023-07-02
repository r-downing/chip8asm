import logging
import re
from typing import Optional

log = logging.getLogger(__name__)


def disassemble(bin_data: bytes, *, sprite_addrs: Optional[list[int]] = None):
    sprite_addrs = sprite_addrs or []
    start_addr = 0x200
    end_addr = start_addr + len(bin_data)
    addr = start_addr

    def handle_goto(nnn):
        dest = int(nnn, 16)
        if start_addr <= dest <= end_addr:
            return f"goto @label{nnn}"
        log.warning(f"goto beyond program bounds: addr 0x{addr:x}, goto 0x{nnn}")
        return f"goto 0x{nnn}"

    def handle_call(nnn):
        dest = int(nnn, 16)
        if start_addr <= dest <= end_addr:
            return f"call @label{nnn}"
        log.warning(f"call beyond program bounds: addr 0x{addr:x}, call 0x{nnn}")
        return f"call 0x{nnn}"

    def handle_set_i(nnn):
        dest = int(nnn, 16)
        if start_addr <= dest <= end_addr:
            return f"i = @label{nnn}"
        log.warning(f"set i beyond program bounds: addr 0x{addr:x}, i = 0x{nnn}")
        return f"i = 0x{nnn}"

    patterns = {
        "00e0": lambda: "clear",
        "00ee": lambda: "return",
        "1(...)": handle_goto,
        "2(...)": handle_call,
        "3(.)(..)": lambda x, nn: f"if v{x} != 0x{nn}",
        "4(.)(..)": lambda x, nn: f"if v{x} == 0x{nn}",
        "5(.)(.)0": lambda x, y: f"if v{x} != v{y}",
        "6(.)(..)": lambda x, nn: f"v{x} = 0x{nn}",
        "7(.)(..)": lambda x, nn: f"v{x} += 0x{nn}",
        "8(.)(.)0": lambda x, y: f"v{x} = v{y}",
        "8(.)(.)1": lambda x, y: f"v{x} |= v{y}",
        "8(.)(.)2": lambda x, y: f"v{x} &= v{y}",
        "8(.)(.)3": lambda x, y: f"v{x} ^= v{y}",
        "8(.)(.)4": lambda x, y: f"v{x} += v{y}",
        "8(.)(.)5": lambda x, y: f"v{x} -= v{y}",
        "8(.)(.)6": lambda x, y: f"v{x} >>= 1",
        "8(.)(.)7": lambda x, y: f"v{x} =- v{y}",
        "8(.)(.)e": lambda x, y: f"v{x} <<= 1",
        "9(.)(.)0": lambda x, y: f"if v{x} == v{y}",
        "a(...)": handle_set_i,
        "b(...)": lambda nnn: f"pc = v0 + 0x{nnn}",
        "c(.)(..)": lambda x, nn: f"v{x} = rand 0x{nn}",
        "d(.)(.)(.)": lambda x, y, n: f"draw v{x} v{y} 0x{n}",
        "e(.)9e": lambda x: f"if !key v{x}",
        "e(.)a1": lambda x: f"if key v{x}",
        "f(.)07": lambda x: f"v{x} = delay",
        "f(.)0a": lambda x: f"v{x} = key",
        "f(.)15": lambda x: f"delay = v{x}",
        "f(.)18": lambda x: f"sound = v{x}",
        "f(.)1e": lambda x: f"i += v{x}",
        "f(.)29": lambda x: f"i = font v{x}",
        "f(.)33": lambda x: f"bcd v{x}",
        "f(.)55": lambda x: f"dump v{x}",
        "f(.)65": lambda x: f"load v{x}",
    }

    data = {}
    labels = {}
    while bin_data:
        word = bin_data[:2]
        bin_data = bin_data[2:]
        if addr in sprite_addrs:
            data[addr] = f"u8 0b{word[0]:08b}"
            data[addr + 1] = f"u8 0b{word[1]:08b}"
            addr += 2
            continue

        hex_word = f"{int.from_bytes(word, byteorder='big'):04x}"
        pattern = next((pattern for pattern in patterns if re.match(pattern, hex_word)), None)
        if not pattern:
            log.warning(f"unmatched {hex_word}, {addr=:03x}")
            data[addr] = f"u16 0x{hex_word}"
            addr += 2
            continue

        m = re.match(pattern, hex_word)
        data[addr] = patterns[pattern](*m.groups())
        if hex_word[0] in "12a":
            labels[int(hex_word[1:], 16)] = f"@label{hex_word[1:]}"

        addr += 2

    ret = []
    for key in sorted(data.keys()):
        if key in labels:
            ret.append(labels[key])
        ret.append(data[key])

    return "\n".join(ret)


def main():
    import argparse
    import sys

    def int_or_range(arg):
        if ":" in arg:
            start, end = arg.split(":")
            return list(range(int(start, 0), int(end, 0)))

        return [int(arg, 0)]

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("binfile", help="Path to the input bin file")
    parser.add_argument("outputfile", help="Path to the output assembly text file destination")
    parser.add_argument(
        "--sprite-addrs",
        nargs="*",
        type=int_or_range,
        help="Optional series of <addr> int or <start:end> ranges to be interpreted as raw sprite data rather than instructions",
    )

    args = parser.parse_args()
    sprite_addrs = [i for e in args.sprite_addrs for i in e] if args.sprite_addrs else None

    with open(args.binfile, "rb") as fp:
        bin_data = fp.read()

    with open(args.outputfile, "w") as fp:
        print(f"# {sys.argv}", file=fp)
        fp.write(disassemble(bin_data, sprite_addrs=sprite_addrs))


if __name__ == "__main__":
    main()
