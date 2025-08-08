import base64

from src.mediums.filesystem import MetadataEncoding
from .protocol import Protocol

from src.utils import TERMINATOR


class MetadataProtocol(Protocol):
    def __init__(self, filesystem: MetadataEncoding):
        self.filesystem = filesystem

    # TODO: make this 
    # TODO: to be more covert preserve existing metadata fields if they exist
    # TODO: dont name the fields covert_data_x (too obvious)
    def encode_file(self, file: str, data: bytes) -> None:
        # split up into chunks for each property
        property_chunks = [
            data[i:i+self.filesystem.PROPERTY_SIZE]
            for i in range(0, len(data), self.filesystem.PROPERTY_SIZE)
        ]
        # set each property
        properties = {}
        for i, chunk in enumerate(property_chunks):
            prop_index = i
            properties[f'hash_{prop_index}'] = base64.b64encode(
                chunk).decode('utf-8')
        # update the filesystem
        self.filesystem.write_properties(file, properties)

    def decode_file(self, file: str) -> bytes:
        decoded = b''
        properties = self.filesystem.read_properties(file)
        # read data from properties of file
        for i in range(self.filesystem.PROPERTY_COUNT):
            key = f'hash_{i}'
            # if property doesnt exist... break
            if key not in properties:
                break
            cur_chunk = base64.b64decode(
                properties[key].encode('utf-8')
            )
            decoded += cur_chunk
            # if current chunk is the last one
            if TERMINATOR in cur_chunk:
                break
        return decoded

    def data_per_file(self):
        return self.filesystem.PROPERTY_SIZE * self.filesystem.PROPERTY_COUNT
