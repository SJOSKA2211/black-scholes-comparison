import gzip
import io

def test_compression():
    data = b"Hello world " * 100
    original_size = len(data)
    
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as f:
        f.write(data)
    compressed_data = buffer.getvalue()
    compressed_size = len(compressed_data)
    
    print(f"Original size: {original_size}")
    print(f"Compressed size: {compressed_size}")
    assert compressed_size < original_size
    
    # Decompress to verify
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_data), mode="rb") as f:
        decompressed_data = f.read()
    assert decompressed_data == data
    print("Compression/Decompression successful!")

if __name__ == "__main__":
    test_compression()
