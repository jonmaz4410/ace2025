import zlib, base64


TERMINATOR = b'\x04'


def get_hash_byte(data: bytes) -> int:
    return zlib.crc32(data) % 256


# TODO: make this modify differently based on filetype
def set_hash_byte(data: bytes, desired: int) -> bytes:
    while zlib.crc32(data) % 256 != desired:
        data += b' '
    return data


# get the bytes of the crc32 hash
def crc32_hash(data: bytes) -> bytes:
    return zlib.crc32(data).to_bytes(4, 'little')


# TODO: analyze if more robust checksum required
CHECKSUM_HASH_SIZE = 4
def checksum_hash(data: bytes) -> bytes:
    return base64.b64encode(crc32_hash(data))[0:4]


def encode_base64(data: bytes) -> bytes:
    return base64.b64encode(data)


def decode_base64(data: bytes) -> bytes:
    return base64.b64decode(data)
