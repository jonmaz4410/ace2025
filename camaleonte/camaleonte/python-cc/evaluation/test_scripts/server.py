
import sys
import os
from pathlib import Path

import sys

# Add the root of your project (e.g., hash-cc) to sys.path
project_root = Path().resolve().parent  # or manually set it
sys.path.append(str(project_root)) #Sets the path root to be the hash-cc folder in the project


from protocol.outdated.metadata_batch_protocol import *  
from src.mediums.drive_filesystem import *


import sys

from tqdm import tqdm



limit = int(sys.argv[1])
limit = None if limit == 0 else limit




fs = GoogleDriveFilesystem("./creds/arif_credentials.json", "19pNkpHor_zX06PSpp7msF9CbxVpyGQJ4",limit)
cc = MetadataProtocol(fs)



messages = ["echo h","ls","echo wow","ip link"]

for i in range(len(messages)):

    cmd = messages[i]
    cc.write(cmd.encode())
    output = cc.read()
