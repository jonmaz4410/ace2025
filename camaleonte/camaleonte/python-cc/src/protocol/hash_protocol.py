from src.mediums.filesystem import HashEncoding
from .protocol import Protocol

from src.utils import get_hash_byte, set_hash_byte


class HashProtocol(Protocol):
    def __init__(self, filesystem: HashEncoding):
        self.filesystem = filesystem

    def encode_file(self, filepath: str, data: bytes) -> None:
        filedata = self.filesystem.read_content(filepath)
        # mine until desired hash
        filedata = set_hash_byte(filedata, ord(data))
        # update the file
        self.filesystem.write_content(filepath, filedata)

    def decode_file(self, filepath: str) -> bytes:
        filedata = self.filesystem.read_content(filepath)
        received_byte = get_hash_byte(filedata)
        # return as a 'bytes' type
        return chr(received_byte).encode()
    
    def data_per_file(self):
        return 1