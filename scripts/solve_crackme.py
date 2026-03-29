#!/usr/bin/env python3

from __future__ import annotations


ENC_KEY = bytes.fromhex("47 49 5a 51 67 69 7a 75 6d 62 63 6e 78 6b 57")
ENC_FLAG = bytes.fromhex(
    "e4 41 00 b1 ca 85 ef 07 5c a3 ea 04 6c 44 e3 42 35 89 8d 08 90 24 a0 21"
)


def decode_key() -> str:
    return "".join(chr(b ^ 0x2A) for b in ENC_KEY)


def rotl32(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def decode_flag(seed: int = 0x0300B127) -> str:
    state = seed ^ 0xA5C319D7
    out = []
    for index, byte in enumerate(ENC_FLAG):
        state = (state + index - 0x61C88647) & 0xFFFFFFFF
        state = rotl32(state, 7)
        out.append(chr(byte ^ (state & 0xFF)))
    return "".join(out)


def main() -> None:
    key = decode_key()
    flag = decode_flag()
    print(f"key:  {key}")
    print(f"flag: {flag}")


if __name__ == "__main__":
    main()
