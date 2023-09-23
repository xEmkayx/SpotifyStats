import os


def get_current_file_name(file):
    return os.path.basename(file).strip(".py")
