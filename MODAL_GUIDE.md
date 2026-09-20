# Modal Storage Backend Guide

This guide provides detailed instructions and examples for using the Modal Volume storage backend with `omni-storage`.

## Prerequisites

- A [Modal](https://modal.com) account.
- `modal` client installed: `pip install modal`.
- A Modal Volume created (e.g., via CLI: `modal volume create my-volume`).

## Configuration

The Modal backend can be configured using environment variables.

### Required Environment Variables

- `STORAGE_TYPE=modal`: Explicitly set the backend to Modal.
- `MODAL_VOLUME_NAME`: The name of the Modal Volume you want to use.

### Authentication

There are two ways to authenticate with Modal:

1.  **System-wide Authentication**: If you have already run `modal setup` or `modal token set` on your machine, the backend will automatically use the active profile.
2.  **Automatic Login via Credentials File**: You can provide a path to a JSON credentials file using the `MODAL_CREDENTIALS` environment variable.

#### Credentials JSON format:
```json
{
  "MODAL_TOKEN_ID": "ak-...",
  "MODAL_TOKEN_SECRET": "as-..."
}
```

#### Example `.env` setup:
```env
MODAL_VOLUME_NAME=my-volume
MODAL_CREDENTIALS=/path/to/credentials.json
```

## Usage Examples

### Initialization

```python
from omni_storage.factory import get_storage

# Auto-detects Modal backend if MODAL_VOLUME_NAME is set
storage = get_storage()

# Or explicitly
storage = get_storage(storage_type="modal")
```

### Basic File Operations

```python
# Save file (simulates overwrite by deleting existing file first)
storage.save_file(b"Hello Modal!", "data/test.txt")

# Read file
content = storage.read_file("data/test.txt")
print(content.decode())

# Check existence
if storage.exists("data/test.txt"):
    print("File exists!")

# Delete file
storage.delete_file("data/test.txt")
```

### Advanced Operations

The Modal backend supports directory-level operations and local file synchronization.

#### Uploading a local file
```python
storage.upload_file("local_image.png", "remote/images/image.png")
```

#### Uploading a local directory
```python
# Uploads all contents of 'local_folder' to 'remote_folder' in the volume
storage.upload_dir("local_folder", "remote_folder")
```

#### Downloading a file to local filesystem
```python
storage.download_file("remote/data.json", "local_backup.json")
```

#### Deleting a directory
```python
# Recursively deletes the directory and all its contents
storage.delete_dir("remote_folder")
```

## Technical Details

- **Implementation**: Uses a combination of the `modal` Python SDK and the Modal CLI (`modal volume`) for operations like deletion and directory uploads where the SDK has limitations.
- **Path Normalization**: All paths are automatically normalized to ensure they start with a leading `/`, consistent with Modal Volume expectations.
- **Encoding**: Commands executed via CLI use UTF-8 encoding to handle Unicode characters (like the success checkmark `✓`) correctly, especially on Windows.

## Limitations

- `append_file` is not currently supported for the Modal backend.
