# Documentation

This guide shows everything that the Python script has or does. It is used for testing and developing the Camaleonte Covert Channel with hashing and metadata encoding schemes. It currently supports Linux/NFS and Google Drive as mediums. All functionality has been implemented into Ruby and integrated with Metasploit (7/31/2025).

---

## File Tree

```     
hash-cc/        
├── client.py                           # Starts the covert channel client
├── server.py                           # Starts the covert channel server (models Metasploit behavior)
├── largefile.txt                       # Sample large file (~1.3 MB) for testing
├── smallfile.txt                       # Sample small file for quick testing

├── creds/                              # Google Drive authentication materials
│   ├── instructions.md                 # Setup guide for credentials/token
│   ├── credentials.json                # OAuth credentials (user-provided)
│   └── token.json                      # Access token (generated after login)

├── evaluation/                         # Local test harness (deprecated)
│   ├── benchmark.py                    # Hashing speed benchmark
│   ├── evaluation.ipynb                # Jupyter notebook for testing and graphing
│   └── test_scripts/       
│       ├── client.py                   # Local test client
│       └── server.py                   # Local test server

├── fileshare/                          # Simulated NFS drive (used in hash/NFS mode)

├── helpers/                            # Utility and test tools
│   ├── clear.py                        # Clears Google Drive metadata
│   ├── disrupter.py                    # Randomly modifies metadata for testing resilience
│   ├── printmetadata.py                # Prints Google Drive metadata fields
│   ├── setup.py                        # Populates fileshare/ with dummy files
│   └── wordlist.txt                    # Words used by setup.py to populate files

├── src/                                # Core logic for mediums and protocols
│   ├── utils.py                        # Shared helper functions
│   ├── mediums/        
│   │   ├── drive_filesystem.py         # Handles file creation/reading using Google Drive metadata
│   │   ├── filesystem.py               # Abstract base class for all mediums
│   │   ├── google_api.py               # Google API auth/session logic
│   │   └── linux_filesystem.py         # Interacts with local/NFS filesystems
│   └── protocol/
│       ├── hash_protocol.py            # Basic file hash-based protocol
│       ├── metadata_protocol.py        # Metadata-based covert encoding
│       ├── metadata_batch_protocol.py  # Optimized batched metadata protocol
│       └── protocol.py                 # Base protocol interface
```

---

## File Structure Explanation

### `hash-cc/` (Root Directory)

- `client.py`: Starts the client for the covert channel.
- `server.py`: Starts the server side (models what’s implemented in Metasploit).
- `largefile.txt` / `smallfile.txt`: Sample files for use in command-line transmission tests like:
  ```
  execute cat largefile.txt
  ```

---

### `creds/`

Used for Google Drive authentication. Not committed by default.

- `instructions.md`: Steps to create `credentials.json` and generate `token.json`
- `credentials.json`: OAuth2 credentials (create via Google Cloud Console)
- `token.json`: Automatically created after you authenticate once

---

### `evaluation/`

- `evaluation.ipynb`: Jupyter notebook for testing protocols and generating speed graphs
- `benchmark.py`: Script to compare hash algorithm performance
- `test_scripts/client.py` and `server.py`: Standalone client/server for local test harness

---

### `fileshare/`

Directory used to simulate a mounted filesystem like NFS. Automatically populated by `helpers/setup.py`.

---

### `helpers/`

Utilities for testing, debugging, and pre-populating the fileshare.

- `clear.py`: Resets appProperties metadata fields in Google Drive
- `disrupter.py`: Randomly modifies metadata to test resilience
- `printmetadata.py`: Inspects current metadata in Drive
- `setup.py`: Creates dummy files in `fileshare/` using `wordlist.txt`
- `wordlist.txt`: List of words used to generate fake file content

---

### `src/`

#### `src/utils.py`
General-purpose helper functions.

#### `src/mediums/`
- `filesystem.py`: Base medium abstract class
- `linux_filesystem.py`: NFS/Local disk implementation
- `drive_filesystem.py`: Metadata-based implementation using Google Drive
- `google_api.py`: Auth/token/session handling for Google Drive

#### `src/protocol/`
- `protocol.py`: Base protocol abstract class
- `hash_protocol.py`: Uses file hashes for encoding data
- `metadata_protocol.py`: Encodes commands into Google Drive metadata
- `metadata_batch_protocol.py`: Efficient version for sending in batches

---

## `src/` Documentation

Implement a covert channel by combining a medium and a protocol. This folder has two subdirectories (`protocol/` and `mediums`)

### `mediums/`

Mediums all use `filesystem.py` as a base class. Currently, we have implemented 


#### `filesystem.py`

Defines a "virtual filesystem" and notes the abstract methods that must be implemented within a filesystem. When creating a new protocol, like steganography, create another abstract class here to ensure that the filesystem implements the correct way to write and read.

##### Classes 

``` Python
class Signal(Enum)
```

- Declares signals to handle states between client and server write/read operations
  - CLEAR when resetting the channel
  - ACK when message has been received successfully (hashes match to verify integrity)
  - NACK when hashes do not match. Signal sender to resend last message until received correctly
  - DONE when sender/receiver has finished completing an action


```Python
class Filesystem(ABC):


    # Default constructor. Sets location of config file and stores the position of new clients (initialized to -1)
    def __init__(self) -> None:

    # Reads how many clients are connected from the config file
    def get_client_count(self) -> int:

    # Reads # of clients connected from config file and then sets to specified value
    def set_client_count(self, cnt: int) -> None:

    # Setter for self.channel_pos
    def set_channel_pos(self, pos: int) -> None:

    # Assigns files to be used by each client. These change when a new client connects
    def update_virtual_filesystem(self) -> None:

    # Wrapper for update_virtual_filesystem. Returns a list of all files, without the config file
    def get_files(self) -> list[str]:

    ### Abstract interfaces -- must be implemented by filesystem instances.
    @abstractmethod
    def get_all_files(self) -> list[str]: pass

    @abstractmethod
    def set_signal(self, signal: Signal) -> None: pass

    @abstractmethod
    def read_signal(self) -> Signal: pass

    @abstractmethod
    def write_content(self, file: str, data: bytes) -> None: pass

    @abstractmethod
    def read_content(self, file: str) -> bytes: pass
```

``` Python
# Hash encoding "mix-in". These are already covered by the base `filesystem` class so nothing is here, but this stub is included for readability / comprehension.
class HashEncoding(Filesystem):
    pass

```

``` Python

# Metadata encoding "mix-in". If a filesystem wants to work with metadata, add this to the class instantiation. Allows for flexibility when creating a new filesystem.
class MetadataEncoding(Filesystem):

    @property
    @abstractmethod
    # How large can one property be?
    def PROPERTY_SIZE(self) -> int: pass

    @property
    @abstractmethod
    # How many properties exist per file?
    def PROPERTY_COUNT(self) -> int: pass

    # Write a dictionary of properties to a specific file based on PROPERTY_SIZE and PROPERTY_COUNT
    @abstractmethod
    def write_properties(self, file: str, properties: dict) -> None: pass

    # Take a file and read all metadata properties. Return a dictionary.
    @abstractmethod
    def read_properties(self, file: str) -> dict: pass
```

#### `google_api.py`

Though not a medium itself, this file is a wrapper for Google OAuth 2.0 and Google Drive API v3, used to interact with Google Drive. It is not the purpose of this guide to detail the Google API v3 usage. Please review the following resources for more information:

Google Drive API v3: [Google Drive API v3](https://developers.google.com/drive/api/v3/about-sdk) 

OAuth: [OAuth 2.0 for Installed Applications](https://developers.google.com/identity/protocols/oauth2/native-app)

##### Class Definitions

``` Python
class GoogleDriveAPI:

    # Default constructor
    def __init__(self):

    # Use OAuth 2.0 and Drive API along with credentials.json to authenticate drive and generate a token.
    def authenticate_drive(self, credentials_path: str) -> None:

    # Upload file to drive
    def upload_file_to_drive(self, file_path: str, destination_id: str) -> None:

    # Download bytes from drive
    def download_file_from_drive_bytes(self, target_id: str) -> bytes:

    # Download file from drive
    def download_file_from_drive(self, destination: str, target_id: str) -> None:

    # Return appProperties from a single file
    def get_file_properties(self, target_id: str) -> dict:

    # Write to appProperties of a single file
    def update_properties(self, file_id: str, properties: dict) -> dict:

    # Read through all pages of files within a folder and list them.
    def list_files(self,
                   directory_id: str = None,
                   filename: str = None,
                   ignore_directories: bool = False) -> list[dict]:

    # Monitor a specific file for changes. Used for checking sync file for changes in signals.
    def watch_file(self, target_id: str, poll_interval=0.1, timeout=300) -> bool:

    # Replaces file content by uploading a new file.
    def edit_file(self, target_id: str, new_file_path: str) -> None:

    # Replaces file content with in-memory bytes.
    def edit_file_bytes(self, target_id: str, bytes_: bytes) -> None:

    # Moves a file to trash.
    def delete_file(self, target_id: str) -> None:

    # Restores a trashed file.
    def restore_file(self, target_id: str) -> None:

    # Permanently deletes all trashed files.
    def empty_bin(self) -> None:

    # Clears appProperties on every file in a folder (some edge cases noticed where flags do not get deleted. Recommend using the clear.py helper script if there are issues).
    def clear_all_file_properties_in_folder(self, folder_id: str) -> int:

    # Instead of writing to one file at a time, this function provides a way to write to all files at one time, greatly increasing speed. However, Google places limits upon API calls within one second. Therefore, this function sets `batch_size` as a parameter to reduce the number of API calls that happen at one time. If the program crashes due to excessive API calls, it attempts to resubmit up to `max_retries` attempts. Verified to work with ~500 API calls at a time. This function is not currently being implemented but relates to the `metadata_batch_protocol.py` file.
    def update_properties_batch(self,
                                file_properties_map: dict,
                                batch_size: int = 500,
                                max_retries: int = 3,
                                delay: float = 1.0) -> None:

    # Read all properties from all files at once.
    def get_properties_batch(self, file_ids: list[str]) -> dict:
```

#### `drive_filesystem.py`

Google Drive Filesystem supports hashing and metadata protocols, which is why it received the `HashEncoding` and `MetadataEncoding` mix-ins. This file draws from the GoogleDriveAPI file for functionality.

Google Drive uses appProperties to store metadata in key value pairs. A user may only use 30 properties per file, and each file stores ~124 bytes. These properties are considered private and no one else can see them. They are not visible, editable, or accessible by anything but our application. Currently, data is encoded with base64 but this is not really necessary. In the future, consider using hex instead for greater throughput. A user may not store bytes into appProperties.

##### Class Definitions

``` Python
# Uses hash encoding and metadata encoding mix-ins
class GoogleDriveFilesystem(HashEncoding, MetadataEncoding):

    # Default constructor. Requires the path to the credentials file from Google Cloud Console and the ID of the folder within Google Drive
    def __init__(self, cred_path: str, covert_folder_id: str):

    # Overloaded function definition of virtual filesystem. Additionally needs to clear properties of sync file so that old files used for writing don't surpass the property limit of 30 within Google Drive.
    def update_virtual_filesystem(self):

    # Wrapper for list_files() from Google API. Sorts files by alphabetical order and returns their file IDs.
    def get_all_files(self) -> List[str]:

    # Wrapper for edit_file_bytes() from Google API. Writes data into a file in Google Drive
    def write_content(self, file: str, data: bytes):

    # Wrapper for download_file_from_drive_bytes() from Google API. Reads data from a file in Google Drive.
    def read_content(self, file: str) -> bytes:

    # Clear existing properties and then rewrite properties to a file. Writes into appProperties of a file
    def write_properties(self, file: str, properties: Dict[str, str]) -> None:

    # Wrapper for get_file_properties() from Google API. Reads the properties of a file
    def read_properties(self, file: str) -> Dict[str, str]:   

    # Wrapper for update_properties_batch() from Google API. Writes to all files in a folder at once to reduce API latency.
    def write_properties_batch(self, props_map: Dict[str, Dict[str, str]]) -> None:

    # Wrapper for update_properties_batch() from Google API. Reads from all files in a folder at one time.
    def read_properties_batch(self, file_ids: List[str]) -> Dict[str, Dict[str, str]]:

    # Sets the current signal by writing to the designated sync file with the given signal.
    def set_signal(self, sig: Signal) -> None:

    # Polls based on constant READ_SIGNAL_DELAY. Otherwise, read current signal from sync file. If no signal is found, default to CLEAR.
    def read_signal(self) -> Signal:

    # Clear all metadata from files within the folder. This must be done one property at a time to avoid a bug with Google API.
    def clear_all_metadata(self) -> None:
```

#### `linux_filesystem.py`

This filesystem uses `HashEncoding` and `MetadataEncoding` mix-ins. It is meant to work on the Linux filesystem or NFS mounted drives.

The Linux filesystem uses `xattr` to write to metadata. It also works in the same way as ext4 NFS shared drives. The Linux filesystem defines PROPERTY_SIZE = 256 and PROPERTY_COUNT = 10. The upper bounds of data per file have not been adequately tested. Use `xattr_tester.py` to test on your own file system, but on ext4 drives it appears the theoretical limit is around 4 KB total per file. For some reason, we seem to not be able to write more than ~2.6 KB currently. 

##### Class Definition

``` Python


class LinuxFileSystem(HashEncoding, MetadataEncoding):
    # Define these constants for writing to metadata. Linux has no realistic limit on property count but appears to have 4 KB limit on total size of data stored within xattr.
    PROPERTY_SIZE = 256
    PROPERTY_COUNT = 12

    # Default constructor. Checks to ensure the path is valid and inherits from the __init__ method from the filesystem base class.
    def __init__(self, root_path: str) -> None:

    # Return a list of files in the specified folder, sorted alphabetically.
    def get_all_files(self) -> list[str]:

    # Read the contents of a file
    def read_content(self, filepath: str) -> bytes:

    # Write contents into a file
    def write_content(self, filepath: str, data: bytes) -> None:

    # Write into metadata using xattr. Currently, properties are stored with syntax (user.hash: data). If this changes, be sure to update the right and read properties functions, since they parse existing properties looking for these values.
    def write_properties(self, filepath: str, properties: dict[str, str]) -> None:

    # Read all properties from one file with xattr
    def read_properties(self, filepath: str) -> dict[str, str]:

    # Poll based on constant SIGNAL_READ_DELAY. 
    def read_signal(self) -> Signal:
```

### `protocols/`

Apart from mediums, we also define protocols. There is a base protocol defined in `protocol.py`, which is used to build the other protocols. Once these protocols are defined, we create a mix-in that lists the requirements of the protocol to work within the filesystem and then you are good to go!

#### `protocol.py`

This file contains logic to work with the virtual filesystem (connect, wait_for_connection). It also explicitly defines how to read and write using the signaling logic for error correction. If you want to update this logic, note that it will apply to all currently implemented protocols!! It also defines some abstract methods that each protocol must implement.

##### Class Definition

``` Python
class Protocol(ABC):

    # Default constructor.
    def __init__(self, filesystem: Filesystem) -> None:

    # Marks the connection within the virtual filesystem with a position. Currently, we assume that users never disconnect so specific connections always receive the same portion of file allotment within the virtual filesystem. This logic is implemented by the client when attempting to connect.
    def connect(self):

    # Polls based on CONNECTION_POLL_DELAY constant for incoming connections. It monitors for client_count to change, which only happens when a client tries to connect. This is implemented by the server, i.e. Metasploit.
    def wait_for_connection(self):

    # Reads data from all files within the virtual filesystem. Wait for DONE signal to begin. Checks the received hash vs. calculated hash to let the sender know if data has been altered in-transit. If the hashes match, return ACK and proceed with reading the next batch of data. A batch is defined as all of the data residing within all of the files (picture the files like a buffer broken into chunks. The chunks are each file). Reading continues until a terminator is found within the verified data. Consider using signals in the future or some other method to verify that no more data remains to be sent.
    def read(self) -> bytes:

    # Wait for CLEAR signal to begin. Break the data to be sent into batches (total amount of data that can be sent based on number of files) and chunks (amount of data that fits per file). Append checksum and terminator, and let the receiver know when this has been completed. Wait for a response from the receiver about if the data was received successfully. If unsuccessful, resend current batch. When done, set signal to CLEAR.
    def write(self, data: bytes) -> None:

    ### THESE METHODS NEED TO BE IMPLEMENTED

    # Determine how you would like to encode/write data in a file.
    @abstractmethod
    def encode_file(self, file: str, data: bytes) -> None:
        pass

    # Determine how you would like to decode/read data from a file.
    @abstractmethod
    def decode_file(self, file: str) -> bytes:
        pass

    # Set how much data fits within one file.
    @abstractmethod
    def data_per_file(self) -> int:
        pass
```

#### `hash_protocol.py`

This is a novel method to communicate through a filesystem with hashes of files. It uses CRC32. Consider using other algorithms if it suits your needs. Only the first byte of the hash is mined. For example, if the sender wanted to send `H`, we would run CRC32 until the first byte was equivalent to the ASCII value for `H`. Then proceed sending bytes in this manner until the entire message has been sent.

##### `Class Definition`

``` Python
class HashProtocol(Protocol):

    # Default constructor. Takes in the requirements from filesystem (HashEncoding)
    def __init__(self, filesystem: HashEncoding):

    # Mine hashes until the first byte = desired data
    def encode_file(self, filepath: str, data: bytes) -> None:

    # Read the first byte of a file's hash
    def decode_file(self, filepath: str) -> bytes:

    # Define how much data fits per file (1)
    def data_per_file(self):
```

#### `metadata_protocol.py`

Write to metadata of a file. The filesystem implements the specifics. Each different operating system or Cloud drive has a way to write to extended app properties. The only difference is the names and


``` Python
class MetadataProtocol(Protocol):

    # Default constructor. Takes in a filesystem that supports metadata encoding in the constructor.
    def __init__(self, filesystem: MetadataEncoding):

    # Breaks the data that needs to be written into pieces that the filesystem accepts as limitations. Then, encode in base64. 
    def encode_file(self, file: str, data: bytes) -> None:

    # Read from all given metadata properties that match the syntax from the encode_file() method. Stops when a terminator is found.
    def decode_file(self, file: str) -> bytes:

    # Define data per file. This is the number of properties times the size of data that fits in each property.
    def data_per_file(self):

```










