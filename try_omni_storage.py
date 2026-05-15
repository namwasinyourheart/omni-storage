import os
import logging

# Biến môi trường này sẽ được ModalStorage tự động load từ .env (nếu có python-dotenv)
# Hoặc bạn có thể set trực tiếp ở đây
os.environ["MODAL_VOLUME_NAME"] = "my-volume"

from omni_storage.factory import get_storage

# Set up logging
logging.basicConfig(level=logging.INFO)

print("--- Initializing Storage ---")
# ModalStorage sẽ tự động gọi _login_if_credentials_present() bên trong __init__
# storage = get_storage()
storage = get_storage(storage_type="local")
print(f"Storage type: {type(storage).__name__}")

# Sử dụng tên file mới để tránh lỗi FileExistsError nếu chưa có force=True
test_file = "data/hello_omni.txt"

print(f"\n--- Testing save_file ---")
print(f"Target path: {test_file}")
storage.save_file(b"Hello Modal Volume from Omni-Storage!", test_file)
print("Save successful.")

print(f"\n--- Testing read_file ---")
content = storage.read_file(test_file)
print(f"Raw content: {content}")
print(f"Decoded content: {content.decode('utf-8')}")

print(f"\n--- Testing exists ---")
if storage.exists(test_file):
    print(f"Confirmed: {test_file} exists.")

print(f"\n--- Testing get_file_url ---")
url = storage.get_file_url(test_file)
print(f"File URL: {url}")

print(f"\n--- Testing delete_file ---")
success = storage.delete_file(test_file)
if success:
    print(f"Successfully deleted {test_file}")
    if not storage.exists(test_file):
        print("Verified: File no longer exists.")
else:
    print(f"Failed to delete {test_file}")

print(f"\n--- Testing upload_file ---")
# Create a local temp file to upload
local_test_file = "E:/projects/misc/temp_upload_test.txt"
with open(local_test_file, "w", encoding="utf-8") as f:
    f.write("This file was uploaded from local filesystem via omni-storage Modal backend.")
print(f"Created local file: {local_test_file}")

# Upload to Modal Volume
upload_dest = "data/uploaded_from_local.txt"
storage.upload_file(local_test_file, upload_dest)
print(f"Uploaded to: {upload_dest}")

# Verify upload by reading back
uploaded_content = storage.read_file(upload_dest)
print(f"Uploaded content: {uploaded_content.decode('utf-8')}")

# Cleanup local file
import os
os.remove(local_test_file)
print("Cleaned up local temp file.")

print(f"\n--- Testing download_file ---")
# First save a file to download
storage.save_file(b"Content to download", "data/to_download.txt")
print("Saved test file to Modal Volume.")

# Download it back
download_dest = "E:/projects/misc/downloaded_from_modal.txt"
success = storage.download_file("data/to_download.txt", download_dest)
if success:
    print(f"Successfully downloaded to: {download_dest}")
    # Verify content
    with open(download_dest, "r", encoding="utf-8") as f:
        print(f"Downloaded content: {f.read()}")
    os.remove(download_dest)
    print("Cleaned up downloaded file.")
else:
    print(f"Failed to download data/to_download.txt")

# Clean up test file
storage.delete_file("data/to_download.txt")
print("Cleaned up test file from Modal Volume.")

print("\n--- Testing append_file (Should fail) ---")
try:
    storage.append_file("This should raise NotImplementedError", test_file)
except NotImplementedError as e:
    print(f"Caught expected error: {e}")
except Exception as e:
    print(f"Caught unexpected error: {type(e).__name__}: {e}")