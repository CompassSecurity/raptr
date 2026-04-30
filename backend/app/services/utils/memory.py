"""
Memory management utilities for constrained environments (Docker/Podman).

CPython's memory allocator and glibc both hold on to freed pages by default.
After processing large data (file blobs, zip archives, report rendering),
call release_memory() to force both layers to return unused pages to the OS.
"""

import ctypes
import gc


def release_memory() -> None:
    """Force Python and glibc to release memory back to the OS.

    - gc.collect() reclaims Python objects with circular references.
    - malloc_trim(0) tells glibc to return unused heap pages to the kernel.
    """
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except OSError:
        pass  # Not on glibc Linux (macOS, musl, etc.)
