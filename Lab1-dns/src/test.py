def generate_request(url) -> bytes:
    import random

    id = random.randint(0, 65535)
    res = bytearray(12)
    print(bin(id))
    print(bin(id & 0xff))
    res[0] = id & 0xFF    # 取后八位
    res[1] = id >> 8     # 取前八位
    res[2] = 0x01
    res[3] = 0x00
    res[4] = 0x00
    res[5] = 0x01
    res[6] = 0x00
    res[7] = 0x00
    res[8] = 0x00
    res[9] = 0x00
    res[10] = 0x00
    res[11] = 0x00
    octets = url.split(".")
    question = bytearray(len(url) + 2 + 4)
    idx = 0
    for oct in octets:
        question[idx] = len(oct)
        idx += 1
        question[idx: idx + len(oct)] = oct.encode()
        idx += len(oct)
    question[idx] = 0x00
    assert idx + 5 == len(question)
    question[idx + 1: idx + 3] = b"\x00\x00"
    question[idx + 3: idx + 5] = b"\x00\x00"
    return bytes(res + question)


by = generate_request("pic1.zhimg.com")     # 返回一个随机数的前八位，后八位，主机名的每段之间的长度与该段
print(by)
# b'\xd8X\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04pic1\x05zhimg\x03com\x00\x00\x00\x00\x00'