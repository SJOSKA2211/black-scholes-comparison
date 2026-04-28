"""Compression utilities for the Black-Scholes Research Platform."""

import gzip
import io
import lzma
import zlib


def compress_data(data: str | bytes, level: int = 6, method: str = "gzip") -> bytes:
    """
    Compress data using gzip, xz (lzma), or zlib.
    If data is a string, it will be encoded to utf-8 before compression.
    'gzip' method (default) produces a valid gzip stream (RFC 1952).
    'xz' method produces a LZMA2 compressed stream.
    'zlib' method produces a zlib stream (RFC 1950).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    if method == "gzip":
        # Using gzip module for proper RFC 1952 headers
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=level) as f:
            f.write(data)
        return buf.getvalue()
    elif method == "xz":
        return lzma.compress(data, preset=level)
    else:
        return zlib.compress(data, level=level)


def decompress_data(data: bytes, as_str: bool = False, method: str = "gzip") -> str | bytes:
    """
    Decompress data using gzip, xz (lzma), or zlib.
    If as_str is True, the result will be decoded from utf-8.
    """
    if method == "gzip":
        buf = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buf, mode="rb") as f:
            decompressed = f.read()
    elif method == "xz":
        decompressed = lzma.decompress(data)
    else:
        decompressed = zlib.decompress(data)

    if as_str:
        return decompressed.decode("utf-8")
    return decompressed
