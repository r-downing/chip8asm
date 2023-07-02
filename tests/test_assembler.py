import unittest

from chip8asm.assembler import assemble


class TestC(unittest.TestCase):
    def test_comments(self):
        assert bytes.fromhex("00e0") == assemble("# top comment\n" "" "clear #inline comment")

    def test_define(self):
        assert bytes.fromhex("4356") == assemble("define myconst 0x56\n" "define myvar v3\n" "if myvar == myconst")

    def test_clear(self):
        assert bytes.fromhex("00e0") == assemble("clear")

    def test_return(self):
        assert bytes.fromhex("00ee") == assemble("return")

    def test_goto(self):
        assert bytes.fromhex("1202") == assemble("goto @mylabel\n" "@mylabel")
        assert bytes.fromhex("1200") == assemble("@mylabel\n" "goto @mylabel")

    def test_call(self):
        assert bytes.fromhex("2202") == assemble("call @mylabel\n" "@mylabel")
        assert bytes.fromhex("2200") == assemble("@mylabel\n" "call @mylabel")

    def test_if_vx_equals_nn(self):
        assert bytes.fromhex("4356") == assemble("if v3 == 0x56")

    def test_if_vx_not_equals_nn(self):
        assert bytes.fromhex("3d56") == assemble("if vd != 86")

    def test_if_vx_equals_vy(self):
        assert bytes.fromhex("9ba0") == assemble("if vb == va")

    def test_if_vx_not_equals_vy(self):
        assert bytes.fromhex("5b20") == assemble("if vb != v2")

    def test_set_vx_nn(self):
        assert bytes.fromhex("6123") == assemble("v1 = 35")
        assert bytes.fromhex("6123") == assemble("v1 = 0x23")
        assert bytes.fromhex("6123") == assemble("v1 = 0b100011")

    def test_vx_plus_equals_nn(self):
        assert bytes.fromhex("7123") == assemble("v1 += 35")

    def test_set_vx_vy(self):
        assert bytes.fromhex("8620") == assemble("v6 = v2")

    def test_vx_bitwise_or_vy(self):
        assert bytes.fromhex("8621") == assemble("v6 |= v2")

    def test_vx_bitwise_and_vy(self):
        assert bytes.fromhex("8622") == assemble("v6 &= v2")

    def test_vx_bitwise_xor_vy(self):
        assert bytes.fromhex("8623") == assemble("v6 ^= v2")

    def test_vx_plus_equals_vy(self):
        assert bytes.fromhex("8624") == assemble("v6 += v2")

    def test_vx_minus_equals_vy(self):
        assert bytes.fromhex("8625") == assemble("v6 -= v2")

    def test_vx_shift_right(self):
        assert bytes.fromhex("8306") == assemble("v3 >>= 1")

    def test_vx_equals_minus_vy(self):
        assert bytes.fromhex("8327") == assemble("v3 =- v2")

    def test_vx_shift_left(self):
        assert bytes.fromhex("830E") == assemble("v3 <<= 1")

    def test_set_i_nnn(self):
        assert bytes.fromhex("a765") == assemble("i = 0x765")

    def test_set_vx_rand(self):
        assert bytes.fromhex("c980") == assemble("v9 = rand 0x80")

    def test_draw(self):
        assert bytes.fromhex("d234") == assemble("draw v2 v3 4")

    def test_if_key_vx(self):
        assert bytes.fromhex("e4a1") == assemble("if key v4")

    def test_if_not_key_vx(self):
        assert bytes.fromhex("e49e") == assemble("if !key v4")

    def test_get_delay(self):
        assert bytes.fromhex("f107") == assemble("v1 = delay")

    def test_get_key(self):
        assert bytes.fromhex("f80a") == assemble("v8 = key")

    def test_set_delay(self):
        assert bytes.fromhex("fb15") == assemble("delay = vb")

    def test_set_sound(self):
        assert bytes.fromhex("fb18") == assemble("sound = vb")

    def test_i_plus_equals_vx(self):
        assert bytes.fromhex("f71e") == assemble("i += v7")

    def test_set_i_font_vx(self):
        assert bytes.fromhex("fb29") == assemble("i = font vb")

    def test_bcd_vx(self):
        assert bytes.fromhex("f933") == assemble("bcd v9")

    def test_dump_vx(self):
        assert bytes.fromhex("fa55") == assemble("dump va")

    def test_load_vx(self):
        assert bytes.fromhex("f365") == assemble("load v3")

    def test_literals(self):
        assert bytes.fromhex("0105") == assemble("u8 0x1\n" "u8 0b101")
        assert bytes.fromhex("f000") == assemble("u16 0xf000")
