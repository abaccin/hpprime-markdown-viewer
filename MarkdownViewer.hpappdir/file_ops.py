from hpprime import eval

def list_files():
    """List all available files."""
    return eval("AFiles()")


def get_file_size(filename):
    """Get file size in bytes. Returns 0 on error."""
    try:
        f = open(filename, 'rb')
        f.seek(0, 2)
        sz = f.tell()
        f.close()
        return sz
    except:
        return 0
