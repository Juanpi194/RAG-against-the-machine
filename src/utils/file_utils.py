from .print_utils import print_error, print_debug


def is_file_available(file_path: str) -> bool:
    """
    Checks if a file at the given file_path exists and if it has
    the read permissions. In that case, True will be returned. Otherwise,
    False will be returned.
    """
    try:
        with open(file_path, "r"):
            print_debug(f"File {file_path} is available")
        return True
    except FileNotFoundError as e:
        print_error(str(e), exit_program=False)
        return False
    except PermissionError as e:
        print_error(str(e), exit_program=False)
        return False
