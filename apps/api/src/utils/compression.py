"""Compression utilities for the Black-Scholes Research Platform."""

import gzip
import io
import zlib


def compress_data(data: str | bytes, level: int = 6, method: str = "gzip") -> bytes:
    """
    Compress data using zlib or gzip.
    If data is a string, it will be encoded to utf-8 before compression.
    'gzip' method produces a valid gzip stream (RFC 1952).
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
    else:
        return zlib.compress(data, level=level)


def decompress_data(data: bytes, as_str: bool = False, method: str = "gzip") -> str | bytes:
    """
    Decompress data using zlib or gzip.
    If as_str is True, the result will be decoded from utf-8.
    """
    if method == "gzip":
        buf = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buf, mode="rb") as f:
            decompressed = f.read()
    else:
        decompressed = zlib.decompress(data)

    if as_str:
        return decompressed.decode("utf-8")
    return decompressed
