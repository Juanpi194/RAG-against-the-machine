from .print_utils import print_error


def is_file_available(file_path: str) -> bool:
    """
    Checks if a file at the given file_path exists and if it has
    the read permissions. In that case, True will be returned. Otherwise,
    False will be returned.
    """
    try:
        f = open(file_path, "r")
        f.close()
        return True
    except FileNotFoundError as e:
        print_error(str(e), exit_program=False)
        return False
    except PermissionError as e:
        print_error(str(e), exit_program=False)
        return False
