import math, time
from abc import ABC, abstractmethod
from enum import Enum
import math
from src.utils import set_hash_byte, get_hash_byte


# will poll sync file at max 60 times per second
POLL_SYNC_FILE_PERIOD = 1/60


class Signal(Enum):
    CLEAR = 0
    ACK = 1
    NACK = 2
    DONE = 3


class Filesystem(ABC):
    def __init__(self) -> None:
        self.channel_pos = -1
        self.client_count = 0 # this is used to optmize VFS calculation
        self.config_file = self.get_all_files()[0]

    def get_files(self) -> list[str]:
        self.update_virtual_filesystem()
        return self.virtual_filesystem[1::]

    def get_client_count(self) -> int:
        config_data = self.read_content(self.config_file)
        return get_hash_byte(config_data)

    def set_client_count(self, cnt: int) -> None:
        config_data = self.read_content(self.config_file)
        modified_config = set_hash_byte(config_data, cnt)
        self.write_content(self.config_file, modified_config)

    def set_channel_pos(self, pos: int) -> None:
        self.channel_pos = pos

    def update_virtual_filesystem(self) -> None:
        if self.channel_pos == -1:
            raise Exception("Didn't connect or wait for connection!")
        # only update if client count changed
        new_client_cnt = self.get_client_count()
        if self.client_count  == new_client_cnt:
            return
        self.client_count = new_client_cnt
        # calculate upper and lower bounds using geometric sequence formula
        all_files = self.get_all_files()
        base = 1
        ratio = 2
        if self.client_count <= base:
            max_clients = 1
        else:
            exponent = math.ceil(math.log(self.client_count/base,ratio))
            max_clients = base * (ratio**exponent)
        files_per_client = (len(all_files)-1) // max_clients
        start_index = self.channel_pos * files_per_client + 1
        # set the virtual_filesystem using the calculated bounds
        self.virtual_filesystem = all_files[start_index:start_index+files_per_client]
        # select the sync file as the first file in the vfs
        self.sync_file = self.virtual_filesystem[0]
        # set the signal of sync file to clear to avoid unintential read/write
        self.set_signal(Signal.CLEAR)
        print("SYNC FILE: ", self.sync_file, start_index, start_index+files_per_client)  # DEBUG

    # Abstract interface
    @abstractmethod
    def get_all_files(self) -> list[str]: pass

    @abstractmethod
    def set_signal(self) -> Signal:
        self.update_virtual_filesystem()
        pass

    @abstractmethod
    def read_signal(self) -> Signal:
        time.sleep(POLL_SYNC_FILE_PERIOD)
        self.update_virtual_filesystem()
        pass

    @abstractmethod
    def write_content(self, file: str, data: bytes) -> None: pass

    @abstractmethod
    def read_content(self, file: str) -> bytes: pass


class HashEncoding(Filesystem):
    pass


class MetadataEncoding(Filesystem):
    @property
    @abstractmethod
    def PROPERTY_SIZE(self) -> int: pass

    @property
    @abstractmethod
    def PROPERTY_COUNT(self) -> int: pass

    @abstractmethod
    def write_properties(self, file: str, properties: dict) -> None: pass

    @abstractmethod
    def read_properties(self, file: str) -> dict: pass
