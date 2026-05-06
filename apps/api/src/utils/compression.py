"""Compression utilities for the research platform."""
import gzip
import lzma
from typing import Union

def compress_data(
    data: Union[str, bytes], method: str = "gzip", level: int = 6
) -> bytes:
    """Compresses data using specified method (gzip or xz)."""
    if isinstance(data, str):
        data = data.encode()
    
    if method == "gzip":
        return gzip.compress(data, compresslevel=level)
    elif method == "xz":
        return lzma.compress(data, preset=level)
    else:
        raise ValueError(f"Unsupported compression method: {method}")

def decompress_data(
    data: bytes, as_str: bool = False, method: str = "gzip"
) -> Union[str, bytes]:
    """Decompresses data using specified method."""
    if method == "gzip":
        decompressed = gzip.decompress(data)
    elif method == "xz":
        decompressed = lzma.decompress(data)
    else:
        raise ValueError(f"Unsupported compression method: {method}")
    
    if as_str:
        return decompressed.decode()
    return decompressed
