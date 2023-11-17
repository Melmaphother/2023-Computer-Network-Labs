class DNSPacket:  # 一个DNS Frame实例，用于解析和生成DNS帧
    def __init__(self, data: bytes):
        self.default_TTL = 62
        self.data = data
        msg = bytearray(data)
        # ID
        self.ID = (msg[0] << 8) + msg[1]
        # FLAGS
        self.QR = msg[2] >> 7  # 指示该消息是一个查询（0）还是一个响应（1）
        self.OPCODE = (msg[2] % 128) >> 3  # 定义 DNS 操作的类型，0:标准查询，1:反向查询，2:服务器状态
        self.AA = (msg[2] % 8) >> 2  # 指示响应的权威性 1 表示响应来自权威服务器，0 表示响应来自缓存或非权威服务器。
        self.TC = (msg[2] % 4) >> 1  # 指示消息是否太大，已经被截断。1 表示消息太大，已被截断，0 表示未被截断。
        self.RD = msg[2] % 2  # 指示递归解析的期望。1 表示发起者期望递归解析，0 表示不期望
        self.RA = msg[3] >> 7  # 在响应中指示服务器是否支持递归解析。1 表示服务器支持递归解析，0 表示不支持。
        self.Z = (msg[3] % 128) >> 4  # 保留位，通常为 0
        """
            指示响应的状态。
            常见值：
            0：没有错误
            1：格式错误
            2：服务器错误
            3：域名不存在
            4：查询类型不支持
            5：拒绝查询
        """
        self.RCODE = msg[3] % 16
        # 资源记录数量
        self.QDCOUNT = (msg[4] << 8) + msg[5]
        self.ANCOUNT = (msg[6] << 8) + msg[7]
        self.NSCOUNT = (msg[8] << 8) + msg[9]
        self.ARCOUNT = (msg[10] << 8) + msg[11]
        # query内容解析
        self.name = ""
        idx = 12
        self.name_length = 0
        while msg[idx] != 0x0:
            # print(self.name)
            for i in range(idx + 1, idx + msg[idx] + 1):
                self.name = self.name + chr(msg[i])
            self.name_length = self.name_length + msg[idx] + 1
            idx = idx + msg[idx] + 1
            if msg[idx] != 0x0:
                self.name = self.name + "."
        self.name_length = self.name_length + 1
        # print(self.name)
        self.name.casefold()
        idx = idx + 1
        self.qtype = (msg[idx] << 8) + msg[idx + 1]
        self.qclass = (msg[idx + 2] << 8) + msg[idx + 3]

    def generate_response(self, ip: str, intercepted: bool) -> bytes:
        """
        TODO: 根据IP地址构建DNS应答数据包，其中intercepted参数表示是否对该客户端请求的域名
        进行拦截
        1. 如果intercepted为True的话，设置RCODE为域名差错状态，构造报错的应答数据包
        2. 如果intercepted为False的话，在应答数据包相应的字段填充正确的IP地址，构造正确的应答数据包
        """
        if not intercepted:
            res = bytearray(32 + self.name_length)
            res[0] = self.ID >> 8
            res[1] = self.ID % 256
            res[2] = 0x81
            res[3] = 0x80
            res[4] = 0x00
            res[5] = 0x01
            res[6] = 0x0
            res[7] = 0x1
            res[8] = 0x0
            res[9] = 0x0
            res[10] = 0x0
            res[11] = 0x0
            for i in range(12, 16 + self.name_length):
                res[i] = self.data[i]
            idx = self.name_length + 16
            res[idx] = 0xC0
            res[idx + 1] = 0x0C
            res[idx + 2] = 0x0
            res[idx + 3] = 0x1
            res[idx + 4] = 0x0
            res[idx + 5] = 0x1
            res[idx + 6] = self.default_TTL >> 24
            res[idx + 7] = (self.default_TTL >> 16) % 256
            res[idx + 8] = (self.default_TTL >> 8) % 256
            res[idx + 9] = self.default_TTL % 256
            res[idx + 10] = 0x0
            res[idx + 11] = 0x4
            ip_tup = ip.split(sep=".")
            res[idx + 12] = int(ip_tup[0])
            res[idx + 13] = int(ip_tup[1])
            res[idx + 14] = int(ip_tup[2])
            res[idx + 15] = int(ip_tup[3])
            # print("res")
            # print(res)
            return bytes(res)
        else:
            res = bytearray(16 + self.name_length)
            res[0] = self.ID >> 8
            res[1] = self.ID % 256
            res[2] = 0x81
            res[3] = 0x83
            res[4] = 0x0
            res[5] = 0x1
            res[6] = 0x0
            res[7] = 0x0
            res[8] = 0x0
            res[9] = 0x0
            res[10] = 0x0
            res[11] = 0x0
            for i in range(12, 16 + self.name_length):
                res[i] = self.data[i]
            return bytes(res)

    @classmethod
    def generate_request(cls, url: str) -> bytes:
        import random

        id = random.randint(0, 65535)
        res = bytearray(12)
        res[0] = id & 0xFF
        res[1] = id >> 8
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
