import unittest
from collections import OrderedDict

from yufka.bencoding import Decoder, Encoder

print("Imported")


class DecodingTests(unittest.TestCase):
    def test_peek_iis_idempotent(self):
        decoder = Decoder(b"42")
        self.assertEqual(decoder._peek(), b"4")
        self.assertEqual(decoder._peek(), b"4")

    def test_peek_should_handle_end(self):
        decoder = Decoder(b"1")  # Single character
        decoder._index = 1  # Make index out of bounds

        self.assertEqual(decoder._peek(), None)

    def test_read_until_works(self):
        decoder = Decoder(b"123456")
        self.assertEqual(decoder._read_until(b"3"), b"12")

    def test_read_until_not_found(self):
        decoder = Decoder(b"123456")
        with self.assertRaises(RuntimeError):
            decoder._read_until(b"7")

    def test_empty_string(self):
        with self.assertRaises(EOFError):
            Decoder(b"").decode()

    def test_not_a_string(self):
        with self.assertRaises(TypeError):
            Decoder(42).decode()
        with self.assertRaises(TypeError):
            Decoder({"a": 1}).decode()

    def test_integer(self):
        res = Decoder(b"i42e").decode()
        self.assertEqual(int(res), 42)

    def test_string(self):
        res = Decoder(b"4:spam").decode()
        self.assertEqual(res, b"spam")

    def test_min_string(self):
        res = Decoder(b"1:a").decode()
        self.assertEqual(res, b"a")

    def test_string_with_zero_length(self):
        res = Decoder(b"0:").decode()
        self.assertEqual(res, b"")

    def test_string_with_space(self):
        res = Decoder(b"4:spam spam").decode()
        self.assertEqual(res, b"spam")

    def test_list(self):
        res = Decoder(b"l4:spam4:eggse").decode()
        self.assertEqual(res, [b"spam", b"eggs"])
        self.assertEqual(res[0], b"spam")
        self.assertEqual(res[1], b"eggs")

    def test_dict(self):
        res = Decoder(b"d3:cow3:moo4:spam4:eggse").decode()
        self.assertEqual(res, {b"cow": b"moo", b"spam": b"eggs"})
        self.assertEqual(res[b"cow"], b"moo")
        self.assertEqual(res[b"spam"], b"eggs")

    def test_malformed_key_in_dict_should_failed(self):
        with self.assertRaises(EOFError):
            res = Decoder(b"d3:moo4:spam4:eggse").decode()
            print(res)


class EncodingTests(unittest.TestCase):
    def test_empty_encoding(self):
        res = Encoder(None).encode()
        self.assertEqual(res, None)

    def test_integer(self):
        res = Encoder(42).encode()
        self.assertEqual(res, b"i42e")

    def test_string(self):
        res = Encoder("spam").encode()
        self.assertEqual(res, b"4:spam")

    def test_list(self):
        res = Encoder(["spam", "eggs"]).encode()
        self.assertEqual(res, b"l4:spam4:eggse")

    def test_dict(self):
        d = OrderedDict()
        d["cow"] = "moo"
        d["spam"] = "eggs"
        res = Encoder(d).encode()
        self.assertEqual(res, b"d3:cow3:moo4:spam4:eggse")

    def test_nested_structure(self):
        outer = OrderedDict()
        b = OrderedDict()
        b["ba"] = "foo"
        b["bb"] = "bar"
        outer["a"] = 123
        outer["b"] = b
        outer["c"] = [["a", "b"], "z"]
        res = Encoder(outer).encode()

        self.assertEqual(res, b"d1:ai123e1:bd2:ba3:foo2:bb3:bare1:cll1:a1:be1:zee")
