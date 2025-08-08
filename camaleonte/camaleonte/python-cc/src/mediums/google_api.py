import io
import os
import time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import (
    MediaFileUpload,
    MediaIoBaseUpload,
    MediaIoBaseDownload,
)

from googleapiclient.errors import HttpError
import time

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = "creds/token.json"


class GoogleDriveAPI:
    """A wrapper for Google Drive API v3."""

    def __init__(self):
        self.service_worker = None

    def authenticate_drive(self, credentials_path: str) -> None:
        """
        Authenticates with the Google Drive API using OAuth 2.0.
        Requires a client_secrets.json at credentials_path.
        """
        creds = None
        if not os.path.isfile(TOKEN_PATH):
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())

        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        self.service_worker = build('drive', 'v3', credentials=creds)

    def upload_file_to_drive(self, file_path: str, destination_id: str) -> None:
        """
        Uploads a file from disk to Google Drive.

        Args:
            file_path: Local path to the file.
            destination_id: Drive folder ID to upload into.
        """
        assert self.service_worker, "Authenticate first."
        assert os.path.exists(file_path), f"No such file: {file_path}"
        metadata = {'name': os.path.basename(file_path), 'parents': [destination_id]}
        media = MediaFileUpload(file_path, resumable=True)
        self.service_worker.files().create(
            body=metadata, media_body=media, fields='id,name'
        ).execute()

    def download_file_from_drive_bytes(self, target_id: str) -> bytes:
        """
        Downloads a Drive file into memory and returns its bytes.

        Args:
            target_id: ID of the Drive file.
        """
        assert self.service_worker, "Authenticate first."
        request = self.service_worker.files().get_media(fileId=target_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer.read()

    def download_file_from_drive(self, destination: str, target_id: str) -> None:
        """
        Downloads a Drive file to local disk.

        Args:
            destination: Local file path to write.
            target_id: ID of the Drive file.
        """
        data = self.download_file_from_drive_bytes(target_id)
        with open(destination, 'wb') as f:
            f.write(data)

    def get_file_properties(self, target_id: str) -> dict:
        """
        Retrieves appProperties for a single file.

        Args:
            target_id: Drive file ID.
        """
        assert self.service_worker, "Authenticate first."
        resp = self.service_worker.files().get(
            fileId=target_id, fields='appProperties'
        ).execute()
        return resp.get('appProperties', {})

    def update_properties(self, file_id: str, properties: dict) -> dict:
        """
        Updates appProperties of a single file.

        Args:
            file_id: Drive file ID.
            properties: dict of key→value to set.
        Returns:
            The updated file resource.
        """
        assert self.service_worker, "Authenticate first."
        body = {'appProperties': properties}
        return self.service_worker.files().update(
            fileId=file_id, body=body
        ).execute()

    def list_files(self,
                   directory_id: str = None,
                   filename: str = None,
                   ignore_directories: bool = False) -> list[dict]:
        """
        Lists files in a Drive folder, optionally filtering.

        Args:
            directory_id: Folder ID to search within.
            filename: Exact filename to filter.
            ignore_directories: If True, skip folders.
        """
        assert self.service_worker, "Authenticate first."
        all_files = []
        page_token = None
        parts = []
        if directory_id:
            parts.append(f"'{directory_id}' in parents")
        if filename:
            parts.append(f"name = '{filename}'")
        if ignore_directories:
            parts.append("mimeType != 'application/vnd.google-apps.folder'")
        query = " and trashed=false and ".join(parts) if parts else "trashed=false"

        while True:
            resp = self.service_worker.files().list(
                q=query,
                orderBy="name",
                pageSize=1000,
                pageToken=page_token,
                fields="nextPageToken, files(id,name,mimeType,parents)"
            ).execute()
            all_files.extend(resp.get('files', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        return all_files

    def watch_file(self, target_id: str, poll_interval=0.1, timeout=300) -> bool:
        """
        Polls a file until modified or trashed.

        Args:
            target_id: Drive file ID.
            poll_interval: Seconds between polls.
            timeout: Max seconds to wait.
        """
        assert self.service_worker, "Authenticate first."
        start = time.time()
        meta = self.service_worker.files().get(
            fileId=target_id, fields='modifiedTime,trashed'
        ).execute()
        last_mod = meta['modifiedTime']

        while True:
            if time.time() - start > timeout:
                return False
            time.sleep(poll_interval)
            meta = self.service_worker.files().get(
                fileId=target_id, fields='modifiedTime,trashed'
            ).execute()
            if meta['trashed'] or meta['modifiedTime'] != last_mod:
                return True

    def edit_file(self, target_id: str, new_file_path: str) -> None:
        """
        Replaces file content by uploading a new file.

        Args:
            target_id: Drive file ID.
            new_file_path: Local path to replacement file.
        """
        assert self.service_worker, "Authenticate first."
        media = MediaFileUpload(new_file_path, resumable=True)
        self.service_worker.files().update(
            fileId=target_id, media_body=media
        ).execute()

    def edit_file_bytes(self, target_id: str, bytes_: bytes) -> None:
        """
        Replaces file content with in-memory bytes.

        Args:
            target_id: Drive file ID.
            bytes_: Byte data or BytesIO.
        """
        assert self.service_worker, "Authenticate first."
        buffer = bytes_ if isinstance(bytes_, io.BytesIO) else io.BytesIO(bytes_)
        buffer.seek(0)
        media = MediaIoBaseUpload(buffer, mimetype='application/octet-stream', resumable=False)
        self.service_worker.files().update(
            fileId=target_id, media_body=media
        ).execute()

    def delete_file(self, target_id: str) -> None:
        """Moves a file to Trash."""
        assert self.service_worker, "Authenticate first."
        self.service_worker.files().delete(fileId=target_id).execute()

    def restore_file(self, target_id: str) -> None:
        """Restores a trashed file."""
        assert self.service_worker, "Authenticate first."
        self.service_worker.files().update(
            fileId=target_id, body={'trashed': False}
        ).execute()

    def empty_bin(self) -> None:
        """Permanently deletes all trashed files."""
        assert self.service_worker, "Authenticate first."
        self.service_worker.files().emptyTrash().execute()

    def clear_all_file_properties_in_folder(self, folder_id: str) -> int:
        """
        Clears appProperties on every file in a folder.

        Args:
            folder_id: Drive folder ID.
        Returns:
            Number of files cleared.
        """
        assert self.service_worker, "Authenticate first."
        count = 0
        page_token = None

        while True:
            resp = self.service_worker.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id,name,appProperties)",
                pageSize=1000,
                pageToken=page_token
            ).execute()

            for f in resp.get('files', []):
                props = f.get('appProperties', {})
                if props:
                    self.service_worker.files().update(
                        fileId=f['id'],
                        body={'appProperties': {k: None for k in props}}
                    ).execute()
                    count += 1

            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        return count

    def update_properties_batch(self,
                                file_properties_map: dict,
                                batch_size: int = 500,
                                max_retries: int = 3,
                                delay: float = 1.0) -> None:
        """
        Updates up to batch_size files per batch request, with simple retries
        on 5xx (transient) errors and a fixed delay between attempts.
        """
        items = list(file_properties_map.items())

        for start in range(0, len(items), batch_size):
            sub_map = dict(items[start:start + batch_size])

            for attempt in range(1, max_retries + 1):
                batch = self.service_worker.new_batch_http_request()

                def _cb(request_id, response, exception):
                    if exception:
                        print(f"[ERROR] {request_id}: {exception}")

                # Queue up each file update
                for fid, props in sub_map.items():
                    req = self.service_worker.files().update(
                        fileId=fid,
                        body={'appProperties': props}
                    )
                    batch.add(req, callback=_cb, request_id=fid)

                try:
                    batch.execute()
                    # on success, break out of retry loop
                    break

                except HttpError as e:
                    status = getattr(e.resp, 'status', None)
                    # only retry on server/transient errors
                    if status and status >= 500:
                        print(f"[RETRY] batch #{start//batch_size+1} attempt {attempt} failed (status={status}), retrying in {delay}s…")
                        time.sleep(delay)
                        continue
                    # non‑transient (e.g. 403 propertyCountLimitExceeded) → re‑raise
                    raise

            else:
                # exhausted retries
                print(f"[FAIL] batch #{start//batch_size+1} failed after {max_retries} attempts.")
               
    def get_properties_batch(self, file_ids: list[str]) -> dict:
        """
        Retrieves appProperties for multiple files in one batch.

        Args:
            file_ids: List of Drive file IDs.
        Returns:
            { file_id: appProperties dict, … }
        """
        assert self.service_worker, "Authenticate first."
        out = {}

        batch = self.service_worker.new_batch_http_request()

        def _cb(req_id, resp, exc):
            if not exc:
                out[resp['id']] = resp.get('appProperties', {})

        for fid in file_ids:
            req = self.service_worker.files().get(
                fileId=fid, fields='id,appProperties'
            )
            batch.add(req, callback=_cb)

        batch.execute()
        return out
