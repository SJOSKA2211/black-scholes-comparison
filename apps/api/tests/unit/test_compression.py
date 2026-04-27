"""Unit tests for compression utilities."""

import pytest
from src.utils.compression import compress_data, decompress_data

@pytest.mark.unit
def test_compression_cycle_gzip():
    original = "This is a test string for compression. " * 10
    compressed = compress_data(original, method="gzip")
    assert isinstance(compressed, bytes)
    assert len(compressed) < len(original.encode())
    
    decompressed = decompress_data(compressed, as_str=True, method="gzip")
    assert decompressed == original

@pytest.mark.unit
def test_compression_cycle_zlib():
    original = "This is a test string for compression. " * 10
    compressed = compress_data(original, method="zlib")
    assert isinstance(compressed, bytes)
    assert len(compressed) < len(original.encode())
    
    decompressed = decompress_data(compressed, as_str=True, method="zlib")
    assert decompressed == original

@pytest.mark.unit
def test_compression_bytes():
    original = b"Some bytes data" * 10
    compressed = compress_data(original)
    decompressed = decompress_data(compressed)
    assert decompressed == original

@pytest.mark.unit
def test_compression_levels():
    data = "High compression level data test" * 100
    c1 = compress_data(data, level=1)
    c9 = compress_data(data, level=9)
    assert len(c9) <= len(c1)
