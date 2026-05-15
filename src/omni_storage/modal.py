"""Modal Volume storage implementation."""

import io
from typing import BinaryIO, Literal, Union

import modal  # type: ignore

from .base import Storage
from .types import AppendResult


class ModalStorage(Storage):
    """Modal Volume storage implementation."""

    def __init__(self, volume_name: str):
        """Initialize Modal storage.

        Args:
            volume_name: Name of the Modal Volume
        """
        self.volume_name = volume_name
        self._login_if_credentials_present()
        try:
            modal.Volume.objects.create(volume_name, allow_existing=True)
        except Exception:
            pass
        self.vol = modal.Volume.from_name(volume_name)

    def _login_if_credentials_present(self):
        """Check for MODAL_CREDENTIALS environment variable and perform login if present."""
        import os
        import subprocess
        import json

        # Try to load .env file if python-dotenv is installed
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        creds_path = os.getenv("MODAL_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            try:
                with open(creds_path, "r") as f:
                    creds = json.load(f)

                token_id = creds.get("MODAL_TOKEN_ID")
                token_secret = creds.get("MODAL_TOKEN_SECRET")

                if token_id and token_secret:
                    # Use shell=True for Windows compatibility
                    command = f"modal token set --token-id {token_id} --token-secret {token_secret}"
                    subprocess.run(command, shell=True, check=True, capture_output=True)
            except Exception:
                # Silence errors in library code; user might have already logged in
                pass

        # Always show current profile to show which account is active
        print("--- Modal Account Info ---")
        subprocess.run("modal profile current", shell=True)

    def _normalize_path(self, file_path: str) -> str:
        """Ensure path starts with / for Modal Volume operations."""
        path = file_path.replace("\\", "/")
        if not path.startswith("/"):
            return "/" + path
        return path

    def save_file(
        self, file_data: Union[bytes, BinaryIO], destination_path: str
    ) -> str:
        """Save file to Modal Volume."""
        remote_path = self._normalize_path(destination_path)

        if isinstance(file_data, bytes):
            buf = io.BytesIO(file_data)
        else:
            buf = io.BytesIO(file_data.read())

        # If file exists, delete it first to simulate overwrite
        if self.exists(remote_path):
            self.delete_file(remote_path)

        with self.vol.batch_upload() as batch:
            batch.put_file(buf, remote_path)

        return remote_path

    def read_file(self, file_path: str) -> bytes:
        """Read file from Modal Volume."""
        remote_path = self._normalize_path(file_path)

        buf = io.BytesIO()
        for chunk in self.vol.read_file(remote_path):
            buf.write(chunk)
        return buf.getvalue()

    def get_file_url(self, file_path: str) -> str:
        """Get modal:// URI for the file."""
        remote_path = self._normalize_path(file_path)
        return f"modal://{self.volume_name}{remote_path}"

    def upload_file(self, file_path: str, destination_path: str) -> str:
        """Upload a local file to Modal Volume.

        Args:
            file_path: Path to the local file to upload.
            destination_path: Destination path inside the volume.

        Returns:
            str: The path of the saved file in the volume.
        """
        remote_path = self._normalize_path(destination_path)

        with open(file_path, "rb") as f:
            buf = io.BytesIO(f.read())

        # If file exists, delete it first to simulate overwrite
        if self.exists(remote_path):
            self.delete_file(remote_path)

        with self.vol.batch_upload() as batch:
            batch.put_file(buf, remote_path)

        return remote_path

    def exists(self, file_path: str) -> bool:
        """Check if a file exists in Modal Volume."""
        remote_path = self._normalize_path(file_path)
        
        # Get parent directory and target name
        if "/" in remote_path:
            parent, target_name = remote_path.rsplit("/", 1)
        else:
            parent, target_name = "", remote_path
        
        try:
            # listdir expects "" for root in some versions or "/" in others
            search_parent = parent if parent else "/"
            for entry in self.vol.listdir(search_parent):
                # entry.path is usually relative to the parent or absolute
                entry_name = entry.path.strip("/").split("/")[-1]
                if entry_name == target_name:
                    return True
            return False
        except Exception:
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Modal Volume using Modal CLI.

        Args:
            file_path: Path to the file to delete.

        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        import subprocess
        import os as _os
        remote_path = self._normalize_path(file_path)
        try:
            command = f"modal volume rm {self.volume_name} {remote_path}"
            env = _os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            if result.returncode == 0:
                return True
            print(f"Modal delete error for {remote_path}: {result.stderr.strip()}")
            return False
        except Exception as e:
            print(f"Modal delete error for {remote_path}: {e}")
            return False

    def download_file(self, file_path: str, local_path: str) -> bool:
        """Download a file from Modal Volume to local filesystem using Modal CLI.

        Args:
            file_path: Path to the file in Modal Volume to download.
            local_path: Local destination path to save the downloaded file.

        Returns:
            bool: True if downloaded successfully, False otherwise.
        """
        import subprocess
        import os as _os
        remote_path = self._normalize_path(file_path)
        try:
            # Ensure local directory exists
            local_dir = _os.path.dirname(local_path)
            if local_dir and not _os.path.exists(local_dir):
                _os.makedirs(local_dir, exist_ok=True)

            command = f"modal volume get {self.volume_name} {remote_path} {local_path}"
            env = _os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            if result.returncode == 0:
                return True
            print(f"Modal download error for {remote_path}: {result.stderr.strip()}")
            return False
        except Exception as e:
            print(f"Modal download error for {remote_path}: {e}")
            return False

    def append_file(
        self,
        content: Union[str, bytes, BinaryIO],
        filename: str,
        create_if_not_exists: bool = True,
        strategy: Literal["auto", "single", "multipart"] = "auto",
        part_size_mb: int = 100,
    ) -> AppendResult:
        """Append is not currently supported for Modal backend."""
        raise NotImplementedError("append_file is not yet supported for Modal storage backend.")
