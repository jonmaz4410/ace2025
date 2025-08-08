import time
from abc import ABC, abstractmethod

from src.mediums.filesystem import Filesystem, Signal
from src.utils import TERMINATOR, CHECKSUM_HASH_SIZE, checksum_hash


CONNECTION_POLL_DELAY = .1

# TODO: add method to pause and recalculate batches when new client joins (VFS change)
class Protocol(ABC):
    def __init__(self, filesystem: Filesystem) -> None:
        self.filesystem = filesystem


    ### INITIAL CONNECTION
    def connect(self):
        # increment client count
        current_count = self.filesystem.get_client_count()
        self.filesystem.set_client_count(current_count+1)
        # set channel pos to index
        self.filesystem.set_channel_pos(current_count)
        # update vfs + clear sync
        self.filesystem.update_virtual_filesystem()
        self.filesystem.set_signal(Signal.CLEAR)


    def wait_for_connection(self):
        # wait for count to be incremented
        current_count = self.filesystem.get_client_count()
        while current_count == self.filesystem.get_client_count():
            time.sleep(CONNECTION_POLL_DELAY)
        # set the channel pos
        self.filesystem.set_channel_pos(current_count)
        # update vfs + clear sync
        self.filesystem.update_virtual_filesystem()
        self.filesystem.set_signal(Signal.CLEAR)

    ### READ/WRITE
    def read(self) -> bytes:
        data = b''
        # keep on reading until terminator found
        while True:
            # wait for a done signal
            while self.filesystem.read_signal() != Signal.DONE:
                pass
            print("[READ] DONE")
            # read the current batch
            current_batch = b''
            for file in self.filesystem.get_files():
                current_batch += self.decode_file(file)
                if TERMINATOR in current_batch:
                    break
            print("RECEIVED BATCH:", len(current_batch))
            print(current_batch)
            # verify the batch
            received_hash = current_batch[0:CHECKSUM_HASH_SIZE]
            calculated_hash = checksum_hash(current_batch[CHECKSUM_HASH_SIZE:])
            # if the hash is correct
            if received_hash == calculated_hash:
                data += current_batch[CHECKSUM_HASH_SIZE:]
                self.filesystem.set_signal(Signal.ACK)
            else:
                self.filesystem.set_signal(Signal.NACK)
            # check if we are done reading
            if TERMINATOR in data:
                data = data.split(TERMINATOR)[0]
                break
        return data

    def write(self, data: bytes) -> None:
        # ensure that signal is cleared
        while self.filesystem.read_signal() != Signal.CLEAR:
            pass
        # split up into "batches" or "packets"
        payload = data + TERMINATOR
        files = self.filesystem.get_files()
        total_files = len(files)
        # find if valid file count and amnt of data per batch
        DATA_PER_BATCH = self.data_per_file() * total_files - CHECKSUM_HASH_SIZE
        if DATA_PER_BATCH <= 0:
            Exception("NOT ENOUGH FILES")
        # split up data into batches
        batches = []
        for i in range(0, len(payload), DATA_PER_BATCH):
            batches.append(payload[i:i + DATA_PER_BATCH])
        # send all the batches
        cur_batch_i = 0
        while cur_batch_i < len(batches):
            # add the checksum to beginning
            batch = batches[cur_batch_i]
            print("Sent Hash:", checksum_hash(batch))
            batch = checksum_hash(batch) + batch
            # split up the batch into file sized chunks
            file_chunks = []
            for i in range(0, len(batch), self.data_per_file()):
                file_chunks.append(batch[i:i+self.data_per_file()])
            # write each file chunk
            for i, chunk in enumerate(file_chunks):
                self.encode_file(files[i], chunk)
            # tell receiver that we are done writing batch
            print("SENT BATCH:", len(batch))
            print(batch)
            self.filesystem.set_signal(Signal.DONE) 
            # wait for ACK or NACK
            while True:
                sig = self.filesystem.read_signal()
                if sig == Signal.ACK:
                    print("[READ] ACK")
                    cur_batch_i += 1
                    break
                if sig == Signal.NACK:
                    print("[READ] NACK")
                    break
        # done writing all batches
        self.filesystem.set_signal(Signal.CLEAR)

    ### THESE METHODS NEED TO BE IMPLEMENTED
    @abstractmethod
    def encode_file(self, file: str, data: bytes) -> None:
        pass

    @abstractmethod
    def decode_file(self, file: str) -> bytes:
        pass

    @abstractmethod
    # returns amount of bytes can be encoded per file
    def data_per_file(self) -> int:
        pass

    