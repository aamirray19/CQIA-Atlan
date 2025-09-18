import os
import subprocess
import tempfile
import shutil
import stat
from urllib.parse import urlparse

def _on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.

    If the error is due to an access error (read only file),
    it attempts to add write permission and then retries the deletion.

    If the error is for another reason, it re-raises the error.
    This is specifically to handle read-only files in .git directories on Windows.
    """
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

class Ingestor:
    """
    A class to handle ingestion of code from various sources like
    local files, directories, and GitHub repositories, with intelligent filtering.
    """

    def __init__(self):
        """Initializes the Ingestor with filtering configurations."""
        self.IGNORED_DIRECTORIES = {
            ".git", "__pycache__", "node_modules", ".vscode", ".idea",
            "build", "dist", "env", "venv",
        }
        self.IGNORED_FILES = {
            ".gitignore", "package-lock.json", "yarn.lock", ".DS_Store",
            "LICENSE", "README.md",
        }
        self.IGNORED_EXTENSIONS = {
            ".pyc", ".pyo", ".so", ".o", ".a", ".dll", ".exe",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".ico", ".svg",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".tar", ".gz", ".rar", ".7z",
            ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
            ".ttf", ".otf", ".woff", ".woff2",
            ".lock", ".log",
        }

    def _is_useful_file(self, filepath):
        """
        Checks if a file should be ingested based on its name, extension, and path.
        """
        filename = os.path.basename(filepath)
        _, extension = os.path.splitext(filename)

        if filename in self.IGNORED_FILES:
            return False
        if extension.lower() in self.IGNORED_EXTENSIONS:
            return False
        return True

    def ingest_file(self, filepath):
        """
        Ingests a single file. Returns a dictionary with {filename: content} if it's useful.
        """
        filename = os.path.basename(filepath)
        print(f"Checking file: {filename}...")
        if self._is_useful_file(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                print(f"  -> Ingested: {filename}")
                return {filename: content}
            except Exception as e:
                print(f"  -> Could not read file {filename}: {e}")
        else:
            print(f"  -> Filtered out: {filename}")
        
        return {}

    def ingest_folder(self, root_dir):
        """
        Traverses a directory and returns a dictionary of {relative_path: content}
        for all useful files.
        """
        ingested_data = {}
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in self.IGNORED_DIRECTORIES]

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(filepath, root_dir)
                print(f"Checking file: {relative_path}...")

                if self._is_useful_file(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        ingested_data[relative_path] = content
                        print(f"  -> Ingested: {relative_path}")
                    except Exception as e:
                        print(f"  -> Could not read file {relative_path}: {e}")
                else:
                    print(f"  -> Filtered out: {relative_path}")
        return ingested_data

    def _clone_github_repo(self, repo_url):
        """
        Clones a GitHub repository into a temporary directory.
        """
        try:
            temp_dir = tempfile.mkdtemp()
            print(f"Cloning {repo_url} into {temp_dir}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            print("Cloning successful.")
            return temp_dir
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        except FileNotFoundError:
            print(f"Error: 'git' command not found. Please ensure Git is installed.")
            return None

    def ingest_github_repo(self, repo_url):
        """
        Ingests a GitHub repository. Returns a dictionary of {filepath: content}.
        """
        temp_repo_path = self._clone_github_repo(repo_url)
        if temp_repo_path:
            try:
                return self.ingest_folder(temp_repo_path)
            finally:
                print(f"Cleaning up temporary directory: {temp_repo_path}")
                shutil.rmtree(temp_repo_path, onerror=_on_rm_error)
        return {}
