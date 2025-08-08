from src.mediums.drive_filesystem import GoogleDriveFilesystem

# CONFIGURATION
CRED_PATH = "creds/credentials.json"
FOLDER_ID = "1hx8LGnjALicYlCFU5mowAUI7L7gb-Chm" # Replace with your actual folder ID

def main():
    fs = GoogleDriveFilesystem(cred_path=CRED_PATH, covert_folder_id=FOLDER_ID)

    print("\n[Metadata Dump]")
    all_files = fs.conn.list_files(directory_id=FOLDER_ID)
    
    for file in all_files:
        file_id = file["id"]
        file_name = file["name"]
        props = fs.conn.get_file_properties(file_id)

        print(f"\n📁 {file_name} (ID: {file_id})")
        if not props:
            print("  [EMPTY] No appProperties")
        else:
            for key, val in props.items():
                print(f"  {key}: {val}")

if __name__ == "__main__":
    main()
