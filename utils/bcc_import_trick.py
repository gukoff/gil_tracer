import importlib.util
import sys

locations = [
    # Debian - https://packages.debian.org/sid/all/python3-bpfcc/filelist
    "/usr/lib/python3/dist-packages/bcc/__init__.py",
    # Another common installation path contains an explicit the Python version:
    # e.g. Arch - https://archlinux.org/packages/extra/x86_64/python-bcc/
    # e.g. Fedora - https://koji.fedoraproject.org/koji/rpminfo?rpmID=38773035
    "/usr/lib/python3.7/site-packages/bcc/__init__.py",
    "/usr/lib/python3.8/site-packages/bcc/__init__.py",
    "/usr/lib/python3.9/site-packages/bcc/__init__.py",
    "/usr/lib/python3.10/site-packages/bcc/__init__.py",
    "/usr/lib/python3.12/site-packages/bcc/__init__.py",
    "/usr/lib/python3.13/site-packages/bcc/__init__.py"
    "/usr/lib/python3.14/site-packages/bcc/__init__.py"
    "/usr/lib/python3.15/site-packages/bcc/__init__.py",
]


def bcc_import_trick():
    """
    At the moment, bcc can not be installed in a virtualenv: https://github.com/iovisor/bcc/issues/3029

    This function attempts to find and import the bcc package from the global location
    if it's not found in the default PYTHONPATH.
    """
    try:
        import bcc
    except ImportError:
        for candidate_location in locations:
            spec = importlib.util.spec_from_file_location("bcc", candidate_location)
            if spec:
                module = importlib.util.module_from_spec(spec)
                sys.modules["bcc"] = module
                spec.loader.exec_module(module)
                break
