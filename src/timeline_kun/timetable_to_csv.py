import os
import shutil


def check_file_locked(file_path):
    try:
        with open(file_path, "r+") as f:
            pass
    except PermissionError:
        return True
    return False


def move_to_backup_folder(file_path):
    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, os.path.basename(file_path))
    if os.path.exists(file_path):
        shutil.move(file_path, backup_file)
