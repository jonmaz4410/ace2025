from src.mediums.filesystem import MetadataEncoding, Signal
from src.protocol.protocol import Protocol
import base64
import zlib
import time
import math

def crc32_hash(data: bytes) -> bytes:
    return zlib.crc32(data).to_bytes(4, 'little')


TERMINATOR = b'\x04'
HASH_SIZE = 4

class MetadataBatchingProtocol(Protocol):
    """Implements the covert channel protocol using batched metadata writes across multiple files."""
    def __init__(self, filesystem: MetadataEncoding):
        self.filesystem = filesystem

    def encode_batch(self, file_ids: list[str], batch_payload: bytes) -> None:
        """
        Clears and writes one full batch payload across needed files using properties.
        """
        # determine per-file capacity
        DATA_PER_FILE = self.filesystem.PROPERTY_SIZE * self.filesystem.PROPERTY_COUNT
        # split payload into per-file slices
        slices = [
            batch_payload[i:i + DATA_PER_FILE]
            for i in range(0, len(batch_payload), DATA_PER_FILE)
        ]
        used_files = len(slices)
        total_files = len(file_ids)
        # select only needed file IDs to minimize API calls
        needed_file_ids = file_ids[:used_files]
        print(f"[DEBUG] Clearing and writing to {used_files}/{total_files} files")
        # clear old properties on needed files
        clear_map = {fid: {} for fid in needed_file_ids}
        self.filesystem.write_properties_batch(clear_map)
        # build new properties map for needed files
        props_map: dict[str, dict[str, str]] = {}
        for fid, chunk in zip(needed_file_ids, slices):
            props: dict[str, str] = {}
            for j in range(0, len(chunk), self.filesystem.PROPERTY_SIZE):
                idx = j // self.filesystem.PROPERTY_SIZE
                seg = chunk[j:j + self.filesystem.PROPERTY_SIZE]
                props[f'covert_data_{idx}'] = base64.b64encode(seg).decode('utf-8')
            props_map[fid] = props
        # batch write new properties
        self.filesystem.write_properties_batch(props_map)

        print(f"[INFO] Wrote {len(props_map)} files for this batch.")

    def decode_batch(self, file_ids: list[str]) -> bytes:
        """
        Reads and concatenates all chunks from all files in one batch.
        """
        props_map = self.filesystem.read_properties_batch(file_ids)
        decoded = b''
        for fid in file_ids:
            props = props_map.get(fid, {})
            for i in range(self.filesystem.PROPERTY_COUNT):
                key = f'covert_data_{i}'
                if key not in props:
                    break
                chunk = base64.b64decode(props[key])
                decoded += chunk
                if TERMINATOR in chunk:
                    return decoded
        return decoded

    def write(self, data: bytes) -> None:
        # wait for CLEAR signal
        print("[WRITE] Waiting for CLEAR signal")
        while self.filesystem.read_signal() != Signal.CLEAR:
            time.sleep(0.5)

        # batch up files
        payload = data + TERMINATOR
        all_file_ids = self.filesystem.get_files()
        total_files = len(all_file_ids)
        DATA_PER_FILE = self.filesystem.PROPERTY_SIZE * self.filesystem.PROPERTY_COUNT
        DATA_PER_BATCH = (total_files * DATA_PER_FILE) - HASH_SIZE

        # split into hash+payload batches
        batches = [
            payload[i:i + DATA_PER_BATCH]
            for i in range(0, len(payload), DATA_PER_BATCH)
        ]
        num_batches = len(batches)
        print(f"[WRITE] Starting to send {num_batches} batch(es); capacity {DATA_PER_BATCH} bytes per batch")

        for idx, batch_data in enumerate(batches, start=1):
            batch_hash = crc32_hash(batch_data)
            batch_blob = batch_hash + batch_data
            # determine slices needed for this batch
            slices_needed = math.ceil(len(batch_blob) / DATA_PER_FILE)
            print(
                f"[WRITE] Batch {idx}/{num_batches}: data {len(batch_data)} bytes, "
                f"blob {len(batch_blob)} bytes, using {slices_needed}/{total_files} files, "
                f"hash {batch_hash.hex()}"
            )

            # encode batch
            self.encode_batch(all_file_ids, batch_blob)

            # signal completion
            print(f"[WRITE] Sent DONE for batch {idx}, waiting for ACK/NACK")
            self.filesystem.set_signal(Signal.DONE)

            # await ACK or retry
            while True:
                sig = self.filesystem.read_signal()
                print(f"[WRITE] Received signal {sig.name}")
                if sig == Signal.ACK:
                    print(f"[WRITE] ACK received for batch {idx}")
                    break
                if sig == Signal.NACK:
                    print(f"[WRITE] NACK received for batch {idx}, retrying")
                    self.encode_batch(all_file_ids, batch_blob)
                    self.filesystem.set_signal(Signal.DONE)
                time.sleep(1)

        # final clear
        print("[WRITE] All batches sent, sending final CLEAR")
        self.filesystem.set_signal(Signal.CLEAR)

    def read(self) -> bytes:
        all_data = b''
        all_file_ids = self.filesystem.get_files()
        batch_count = 0

        while True:
            # 1) wait for DONE from the sender
            print("[READ] Ready to read! Waiting for DONE signal")
            while self.filesystem.read_signal() != Signal.DONE:
                time.sleep(0.1)
            print("[READ] DONE received, clearing sync id")
            self.filesystem.set_signal(Signal.CLEAR)

            # 2) pull down the batch and inspect size
            batch_bytes = self.decode_batch(all_file_ids)
            print(f"[READ] Retrieved {len(batch_bytes)}-byte batch payload")

            # 3) separate hash vs data
            if len(batch_bytes) < HASH_SIZE:
                print("[READ] ERROR: batch too small for hash, NACK’ing")
                self.filesystem.set_signal(Signal.NACK)
                continue

            recv_hash = batch_bytes[:HASH_SIZE]
            recv_data = batch_bytes[HASH_SIZE:]
            expected_hash = crc32_hash(recv_data)

            # 4) if it matches, increment count, ACK, and append
            if recv_hash == expected_hash:
                batch_count += 1
                print(f"[READ] Batch {batch_count} hash match ({recv_hash.hex()})")
                self.filesystem.set_signal(Signal.ACK)
                all_data += recv_data

                # check for terminator
                if TERMINATOR in all_data:
                    result = all_data.split(TERMINATOR)[0]
                    print(f"[READ] TERMINATOR found; returning {len(result)} bytes")
                    return result

            # 5) otherwise NACK and retry (without touching batch_count)
            else:
                print(
                    f"[READ] Hash mismatch: received {recv_hash.hex()}, "
                    f"expected {expected_hash.hex()}, retrying batch"
                )
                self.filesystem.set_signal(Signal.NACK)
                # batch_count is NOT changed here
                continue

