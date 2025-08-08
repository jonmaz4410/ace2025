import time
import random
import string
from src.mediums.google_api import GoogleDriveAPI

# --- Configuration ---
CREDENTIALS_FILE = "creds/credentials.json"
FOLDER_ID = "1hx8LGnjALicYlCFU5mowAUI7L7gb-Chm" 
TAMPER_INTERVAL = 2  # Time in seconds between each tampering attempt
PROPERTY_LIMIT = 30 # Google Drive's appProperties limit per app

def tamper_with_metadata(gdrive_api):
    """
    Randomly modifies the metadata of a file in the specified folder
    to simulate interference. It will either add, modify, or delete a property.
    """
    print("--- TAMPERING ---")
    
    try:
        # Get all files, find the sync file to exclude it
        all_files = gdrive_api.list_files(directory_id=FOLDER_ID)
        if not all_files:
            print("No files found in the specified folder.")
            return

        sync_file = sorted(all_files, key=lambda f: f['name'])[0]
        data_files = [f for f in all_files if f['id'] != sync_file['id']]

        if not data_files:
            print("No data files to tamper with.")
            return

        # Select a random file to tamper with
        target_file = random.choice(data_files)
        file_id = target_file['id']
        file_name = target_file['name']

        print(f"Tampering with file: {file_name} (ID: {file_id})")

        # Get current properties
        properties = gdrive_api.get_file_properties(file_id)
        if properties is None:
            properties = {}

        # Decide on an action: 0=add, 1=modify, 2=delete
        # We prioritize adding if the file has few properties, and modifying/deleting if it has many.
        if len(properties) == 0:
            action = 0 # Must add
        elif len(properties) >= PROPERTY_LIMIT:
            action = random.choice([1, 2]) # Can't add, so modify or delete
        else:
            action = random.choice([0, 1, 2])
        
        if action == 1 and properties: # Modify
            key_to_modify = random.choice(list(properties.keys()))
            new_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            properties[key_to_modify] = new_value
            print(f"Action: MODIFIED property '{key_to_modify}' to '{new_value}'")
        
        elif action == 2 and properties: # Delete
            key_to_delete = random.choice(list(properties.keys()))
            properties[key_to_delete] = None  # Setting a property to None deletes it
            print(f"Action: DELETED property '{key_to_delete}'")
            
        else: # Add (or default if modify/delete fails)
            random_key = f"tamper_{''.join(random.choices(string.ascii_lowercase, k=4))}"
            random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            properties[random_key] = random_value
            print(f"Action: ADDED property '{random_key}': '{random_value}'")

        # Apply the changes
        gdrive_api.update_properties(file_id, properties)
        print(f"Successfully tampered with {file_name}.")

    except Exception as e:
        print(f"An error occurred during tampering: {e}")
    
    print("--- TAMPERING COMPLETE ---\n")

if __name__ == "__main__":
    print("Initializing filesystem for automated tampering...")
    try:
        # Use the GoogleDriveAPI directly to manipulate properties
        gdrive = GoogleDriveAPI()
        gdrive.authenticate_drive(CREDENTIALS_FILE)
        print(f"Filesystem initialized. Will tamper with a file every {TAMPER_INTERVAL} seconds.")
        print("Press Ctrl+C to stop.")
    except Exception as e:
        print(f"Failed to initialize filesystem: {e}")
        exit()

    try:
        while True:
            time.sleep(TAMPER_INTERVAL)
            tamper_with_metadata(gdrive)
    except KeyboardInterrupt:
        print("\nTampering script stopped by user.")