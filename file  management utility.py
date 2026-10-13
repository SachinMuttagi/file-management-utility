"""
File Management Utility (single-file version)

Run:   python file_management_utility.py
Test:  python file_management_utility.py --test

Sections: 1) validators  2) file operations  3) CLI  4) unit tests
"""
import os
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------- 1. VALIDATORS
INVALID_CHARS = set('<>:"/\\|?*')


def validate_not_empty(value, label="Input"):
    value = value.strip()
    if not value:
        raise ValueError(f"{label} cannot be empty.")
    return value


def validate_filename(name):
    name = validate_not_empty(name, "File name")
    if any(c in INVALID_CHARS for c in name):
        raise ValueError(f"File name contains invalid characters: {''.join(sorted(INVALID_CHARS))}")
    return name


def validate_existing_path(path):
    path = validate_not_empty(path, "Path")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")
    return path


def validate_directory(path):
    path = validate_existing_path(path)
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a directory: {path}")
    return path


def validate_extension(ext):
    ext = validate_not_empty(ext, "Extension").lower()
    return ext if ext.startswith(".") else "." + ext


# ------------------------------------------------------------ 2. FILE OPERATIONS
def list_files(directory="."):
    return sorted(os.listdir(validate_directory(directory)))


def create_file(directory, name, content=""):
    directory = validate_directory(directory)
    path = os.path.join(directory, validate_filename(name))
    if os.path.exists(path):
        raise FileExistsError(f"File already exists: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def read_file(path):
    path = validate_existing_path(path)
    if not os.path.isfile(path):
        raise IsADirectoryError(f"Not a file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def rename_file(path, new_name):
    path = validate_existing_path(path)
    new_path = os.path.join(os.path.dirname(path), validate_filename(new_name))
    if os.path.exists(new_path):
        raise FileExistsError(f"Target already exists: {new_path}")
    os.rename(path, new_path)
    return new_path


def copy_file(src, dest_dir):
    return shutil.copy2(validate_existing_path(src), validate_directory(dest_dir))


def move_file(src, dest_dir):
    return shutil.move(validate_existing_path(src), validate_directory(dest_dir))


def delete_file(path):
    path = validate_existing_path(path)
    if os.path.isdir(path):
        raise IsADirectoryError("Use a file path (directories are not deleted).")
    os.remove(path)


def file_info(path):
    path = validate_existing_path(path)
    st = os.stat(path)
    return {
        "name": os.path.basename(path),
        "size_bytes": st.st_size,
        "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "type": "directory" if os.path.isdir(path) else "file",
    }


def search_by_extension(directory, ext):
    directory = validate_directory(directory)
    ext = validate_extension(ext)
    return sorted(f for f in os.listdir(directory)
                  if f.lower().endswith(ext) and os.path.isfile(os.path.join(directory, f)))


def organize_by_extension(directory):
    """Move files into sub-folders named after their extension."""
    directory = validate_directory(directory)
    moved = defaultdict(list)
    for name in os.listdir(directory):
        src = os.path.join(directory, name)
        if not os.path.isfile(src):
            continue
        ext = os.path.splitext(name)[1].lstrip(".").lower() or "no_extension"
        target = os.path.join(directory, ext)
        os.makedirs(target, exist_ok=True)
        shutil.move(src, os.path.join(target, name))
        moved[ext].append(name)
    return dict(moved)


# ------------------------------------------------------------------------ 3. CLI
MENU = """
===== File Management Utility =====
1. List files            6. Delete file
2. Create file           7. File info
3. Read file             8. Search by extension
4. Rename file           9. Organize folder by extension
5. Copy file            10. Move file
0. Exit
"""


def ask(prompt):
    return input(prompt).strip()


def handle(choice):
    if choice == "1":
        for f in list_files(ask("Directory [.]: ") or "."):
            print(" -", f)
    elif choice == "2":
        d, n = ask("Directory [.]: ") or ".", ask("File name: ")
        print("Created:", create_file(d, n, ask("Content: ")))
    elif choice == "3":
        print(read_file(ask("File path: ")))
    elif choice == "4":
        print("Renamed to:", rename_file(ask("File path: "), ask("New name: ")))
    elif choice == "5":
        print("Copied to:", copy_file(ask("Source file: "), ask("Destination folder: ")))
    elif choice == "6":
        p = ask("File path: ")
        if ask(f"Delete {p}? (y/n): ").lower() == "y":
            delete_file(p)
            print("Deleted.")
    elif choice == "7":
        for k, v in file_info(ask("Path: ")).items():
            print(f"{k}: {v}")
    elif choice == "8":
        res = search_by_extension(ask("Directory [.]: ") or ".", ask("Extension (e.g. txt): "))
        print("\n".join(res) if res else "No matches.")
    elif choice == "9":
        for ext, files in organize_by_extension(ask("Directory: ")).items():
            print(f"{ext}: {len(files)} file(s)")
    elif choice == "10":
        print("Moved to:", move_file(ask("Source file: "), ask("Destination folder: ")))
    else:
        print("Invalid choice. Enter a number from the menu.")


def main():
    while True:
        print(MENU)
        choice = ask("Choose an option: ")
        if choice == "0":
            print("Goodbye!")
            break
        try:
            handle(choice)
        except UnicodeDecodeError:
            print("Error: file is not a readable text file.")
        except (ValueError, OSError) as e:
            print("Error:", e)


# ------------------------------------------------------------------ 4. UNIT TESTS
class TestFileOps(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_read(self):
        self.assertEqual(read_file(create_file(self.d, "a.txt", "hello")), "hello")

    def test_duplicate_create(self):
        create_file(self.d, "a.txt")
        with self.assertRaises(FileExistsError):
            create_file(self.d, "a.txt")

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            create_file(self.d, "bad/name.txt")

    def test_rename_copy_delete(self):
        p = rename_file(create_file(self.d, "a.txt", "x"), "b.txt")
        os.makedirs(os.path.join(self.d, "sub"))
        copy_file(p, os.path.join(self.d, "sub"))
        self.assertTrue(os.path.exists(os.path.join(self.d, "sub", "b.txt")))
        delete_file(p)
        self.assertFalse(os.path.exists(p))

    def test_search_and_organize(self):
        create_file(self.d, "a.txt")
        create_file(self.d, "b.py")
        self.assertEqual(search_by_extension(self.d, "txt"), ["a.txt"])
        self.assertIn("py", organize_by_extension(self.d))
        self.assertTrue(os.path.exists(os.path.join(self.d, "txt", "a.txt")))

    def test_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            read_file(os.path.join(self.d, "nope.txt"))


if __name__ == "__main__":
    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0], "-v"])
    else:
        main()