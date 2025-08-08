import os
import time

from .filesystem import HashEncoding, MetadataEncoding, Signal
from src.utils import get_hash_byte, set_hash_byte


# TODO: Add client disconnect code + other contingencies
#       Contingency 1: Client disconnect
#       Contingency 2: New client wants to connect while other clients sending message
#       Contingency 3: Not enough space to add a new client
class LinuxFileSystem(HashEncoding, MetadataEncoding):
    PROPERTY_SIZE = 256
    PROPERTY_COUNT = 10

    def __init__(self, root_path: str) -> None:
        # check if valid root path
        if not os.path.isdir(root_path):
            raise ValueError("Invalid filesystem path provided!")
        if root_path[-1] != '/':
            root_path += '/'
        self.root_path = root_path

        # finish initialization by calling super
        super().__init__()

    ### FILESYSTEM SPECIFIC METHODS
    def get_all_files(self) -> list[str]:
        files = []
        for m in os.scandir(self.root_path):
            if m.is_file():
                files.append(m.path)
        return sorted(files)

    def read_content(self, filepath: str) -> bytes:
        with open(filepath, 'rb') as fil:
            return fil.read()

    def write_content(self, filepath: str, data: bytes) -> None:
        with open(filepath, 'wb') as fil:
            fil.write(data)

    def write_properties(self, filepath: str, properties: dict[str, str]) -> None:
        # clear any old covertdata* attrs
        for attr in os.listxattr(filepath):
            if attr.startswith("user.hash"):
                os.removexattr(filepath, attr)
        # write data to each property
        for key, val in properties.items():
            attr_name = f"user.{key}"
            os.setxattr(filepath, attr_name, val.encode())

    def read_properties(self, filepath: str) -> dict[str, str]:
        out = {}
        # loop through all properties
        for attr in os.listxattr(filepath):
            if attr.startswith("user.hash"):
                raw = os.getxattr(filepath, attr)
                out[attr.split("user.", 1)[1]] = raw.decode('utf-8')
        return out

    # NOTE: its kind of expensive updates VFS everytime
    def read_signal(self) -> Signal:
        super().read_signal()
        # read signal from first byte of hash
        file_data = self.read_content(self.sync_file)
        sig_val = get_hash_byte(file_data)
        try:
            sig = Signal(sig_val)
        except:
            sig = Signal.CLEAR
        return sig

    def set_signal(self, sig: Signal) -> None:
        super().set_signal()
        print(f"[SEND] {sig.name}")
        # encode signal into hash
        file_data = self.read_content(self.sync_file)
        modified_data = set_hash_byte(file_data, sig.value)
        self.write_content(self.sync_file, modified_data)
 