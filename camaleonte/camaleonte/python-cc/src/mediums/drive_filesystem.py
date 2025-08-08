# src/mediums/drive_filesystem.py

from typing import List, Dict

from .filesystem import MetadataEncoding, HashEncoding, Signal
from .google_api import GoogleDriveAPI


class GoogleDriveFilesystem(HashEncoding, MetadataEncoding):
    PROPERTY_SIZE = 75
    PROPERTY_COUNT = 30

    def __init__(self, cred_path: str, covert_folder_id: str):
        # connect to google drive
        self.conn = GoogleDriveAPI()
        self.conn.authenticate_drive(credentials_path=cred_path)
        self.covert_folder_id = covert_folder_id
        # finish initialization by calling super
        super().__init__()

    def update_virtual_filesystem(self):
        super().update_virtual_filesystem()
        # clear properties of sync file
        existing = self.conn.get_file_properties(self.sync_file)
        if existing:
            clear_payload = {k: None for k in existing}
            self.conn.update_properties(self.sync_file, clear_payload)

    ### FILESYSTEM SPECIFIC METHODS
    def get_all_files(self) -> List[str]:
        files = self.conn.list_files(self.covert_folder_id)
        ids = [f["id"] for f in files]
        return sorted(ids)

    def write_content(self, file: str, data: bytes):
        self.conn.edit_file_bytes(file, data)

    def read_content(self, file: str) -> bytes:
        return self.conn.download_file_from_drive_bytes(file)

    def write_properties(self, file: str, properties: Dict[str, str]) -> None:
        existing = self.conn.get_file_properties(file)
        to_update = {k: None for k in existing}
        to_update.update(properties)
        if to_update:
            self.conn.update_properties(file, to_update)

    def read_properties(self, file: str) -> Dict[str, str]:   
        return self.conn.get_file_properties(file)

    def write_properties_batch(self, props_map: Dict[str, Dict[str, str]]) -> None:
        self.conn.update_properties_batch(props_map)

    def read_properties_batch(self, file_ids: List[str]) -> Dict[str, Dict[str, str]]:
        return self.conn.get_properties_batch(file_ids)

    def set_signal(self, sig: Signal) -> None:
        print(f"[SEND] {sig.name}")
        self.conn.update_properties(self.sync_file, {'sync_status': sig.name})

    def read_signal(self) -> Signal:
        props = self.conn.get_file_properties(self.sync_file)
        status = props.get('sync_status')
        if status in Signal.__members__:
            return Signal[status]
        return Signal.CLEAR

    def clear_all_metadata(self) -> None:
        all_files = self.conn.list_files(directory_id=self.covert_folder_id)
        cleared = 0
        for f in all_files:
            props = self.conn.get_file_properties(f["id"])
            if props:
                nulls = {k: None for k in props}
                self.conn.update_properties(f["id"], nulls)
                cleared += 1