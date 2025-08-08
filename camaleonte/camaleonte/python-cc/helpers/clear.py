import sys
from googleapiclient.errors import HttpError
from src.mediums.drive_filesystem import GoogleDriveFilesystem

# --- Configuration ---
FOLDER_ID       = "1KBwGwewMn74HOKVTZrZup3ewc-Lv_cAV"  # your Drive folder ID
CREDENTIALS_PATH = "creds/credentials.json"          # path to your client_secrets.json

def main():
    """
    Clears all custom 'appProperties' from all files within the specified
    Google Drive folder (including the sync file).
    """
    try:
        print("Initializing Google Drive filesystem...")
        fs = GoogleDriveFilesystem(CREDENTIALS_PATH, FOLDER_ID)
        print("Authentication successful.\n")

        # This will set every appProperty to None for each file in the folder
        fs.clear_all_metadata()  
        print("All metadata cleared.")

    except HttpError as error:
        print(f"An error occurred (Drive API): {error}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
