import os

def get_xattr_usage(path):
    total_size = 0
    for key in os.listxattr(path):
        value = os.getxattr(path, key)
        total_size += len(key.encode('utf-8')) + len(value)
    return total_size

def test_xattr_capacity(file_path="xattr_testfile.txt", value_size=128, max_keys=1000):
    print("Starting xattr test on:", file_path)
    
    with open(file_path, "w") as f:
        f.write("test\n")  # Create a file with some content

    key_prefix = "user.x"
    success = []
    failure_reason = None

    try:
        for i in range(max_keys):
            key = f"{key_prefix}{i}"
            value = b'x' * value_size
            try:
                os.setxattr(file_path, key, value)
                used = get_xattr_usage(file_path)
                success.append((key, value_size, used))
                print(f"Set {key}: {value_size} bytes (total used: {used} bytes)")
            except OSError as e:
                failure_reason = f"Failed at key #{i} ({key}): {e}"
                break
    finally:
        os.remove(file_path)

    print("\n--- Test Summary ---")
    print(f"Total keys stored: {len(success)}")
    if success:
        print(f"Final total xattr space used: {success[-1][2]} bytes")
    if failure_reason:
        print(failure_reason)
    else:
        print("No failure detected (may not have reached system limit)")

if __name__ == "__main__":
    test_xattr_capacity()
