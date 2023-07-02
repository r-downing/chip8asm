import unittest

from chip8asm.assembler import assemble
from chip8asm.disassembler import disassemble

test_program = """
goto @start

@sprites
u16 0xFF00
u16 0x00FF
u8 0b10101010
u8 0b01010101

@start
clear
if v3 == 21
if v4 != 0x21
if v5 == v6
v7 = 6
v8 += 12
v9 = va
vb |= vc
vd &= ve
v1 ^= v2
v3 += v4
v5 -= v6
v7 >>= 1
v8 =- v9
va <<= 1
if vb != vc
i = 0x321
v3 = rand 0x7
draw v3 v6 7
i = @sprites
i = 789

if key v5
if !key v6
v7 = delay
v8 = key
delay = v9
sound = va

i += vb
i = font vc

bcd vd
dump v4
load v6

call @func
goto @start


@func

return

"""


class TestDisassembler(unittest.TestCase):
    def test_reassemble(self):
        test_assembled = assemble(test_program)

        test_disassembled = "# disassembed\n" + disassemble(test_assembled, sprite_addrs=[0x202, 0x204, 0x206])
        test_reassembled = assemble(test_disassembled)

        assert test_assembled == test_reassembled
