from collections import OrderedDict


TOKEN_INTEGER = b"i"
TOKEN_LIST = b"l"
TOKEN_DICT = b"d"
TOKEN_END = b"e"
TOKEN_STRING_SEPARATOR = b":"


class Decoder:
    def __init__(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        self._data = data
        self._index = 0

    def decode(self):
        c = self._peek()
        if c is None:
            raise EOFError("Unexpected end-of-file")
        elif c == TOKEN_INTEGER:
            self._consume()
            return self._decode_int()
        elif c == TOKEN_LIST:
            self._consume()
            return self._decode_list()
        elif c == TOKEN_DICT:
            self._consume()
            return self._decode_dict()
        elif c in b"01234567899":
            return self._decode_string()
        elif c == TOKEN_END:
            return None
        else:
            raise RuntimeError("Unknown token")

    def _peek(self):
        if self._index + 1 >= len(self._data):
            return None
        return self._data[self._index : self._index + 1]

    def _consume(self):
        self._index += 1

    def _read(self, length: int) -> bytes:
        if self._index + length > len(self._data):
            raise IndexError("Not enough data")

        res = self._data[self._index : self._index + length]
        self._index += length
        return res

    def _read_until(self, token: bytes) -> bytes:
        try:
            occurance = self._data.index(token, self._index)
            result = self._data[self._index : occurance]
            self._index = occurance + 1
            return result
        except ValueError:
            raise RuntimeError("Token not found")

    def _decode_int(self):
        return int(self._read_until(TOKEN_END))

    def _decode_string(self):
        bytes_to_read = int(self._read_until(TOKEN_STRING_SEPARATOR))
        return self._read(bytes_to_read)

    def _decode_list(self):
        res = []
        while self._data[self._index : self._index + 1] != TOKEN_END:
            res.append(self.decode())
        self._consume()
        return res

    def _decode_dict(self):
        res = OrderedDict()
        while self._data[self._index : self._index + 1] != TOKEN_END:
            key = self.decode()
            obj = self.decode()
            res[key] = obj
        self._consume()
        return res


class Encoder:
    def __init__(self, data: bytes):
        self._data = data

    def encode(self):
        return self.encode_next(self._data)

    def encode_next(self, data: bytes):
        if type(data) == str:
            return self._encode_string(data)
        elif type(data) == int:
            return self._encode_int(data)
        elif type(data) == list:
            return self._encode_list(data)
        elif type(data) == dict or type(data) == OrderedDict:
            return self._encode_dict(data)
        elif type(data) == bytes:
            return self._encode_bytes(data)
        else:
            return None

    def _encode_int(self, value: int):
        return str.encode("i" + str(value) + "e")

    def _encode_string(self, value: str):
        res = str(len(value)) + ":" + value
        return str.encode(res)

    def _encode_bytes(self, value: bytes):
        res = bytearray()
        res += str.encode(str(len(value)))
        res += b":"
        res += value
        return res

    def _encode_list(self, data: list):
        res = bytearray("l", "utf-8")
        res += b"".join([self.encode_next(item) for item in data])
        res += b"e"
        return res

    def _encode_dict(self, data: dict) -> bytes:
        result = bytearray("d", "utf-8")
        for key, value in data.items():
            key = self.encode_next(key)
            value = self.encode_next(value)
            if key and value:
                result += key
                result += value
            else:
                raise RuntimeError("Invalid key or value")
        result += b"e"
        return result
