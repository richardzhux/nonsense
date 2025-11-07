import os
import gzip
import random
import shutil

# Settings
n_chars = 10**6  # 1 million characters per file
block_size = 1000
ascii_chars = [chr(i) for i in range(32, 127)]  # Printable ASCII characters

# Helper: Write plain text to file
def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

# Helper: Compress file and return compressed size in bytes
def compress_file(input_file, output_file):
    with open(input_file, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return os.path.getsize(output_file)

# 1. Completely random text file
random_content = ''.join(random.choices(ascii_chars, k=n_chars))
write_file("random.txt", random_content)

# 2. Completely ordered (uniform) file (e.g., all "A")
uniform_content = 'A' * n_chars
write_file("uniform.txt", uniform_content)

# 3. Block-ordered file (e.g., "A"*1000 + "B"*1000 + ... repeated)
block_chars = ascii_chars
block_pattern = ''.join(c * block_size for c in block_chars)
repeats = (n_chars + len(block_pattern) - 1) // len(block_pattern)  # ceil division

blocky_content = (block_pattern * repeats)[:n_chars]  # slice to exact length
write_file("blocky.txt", blocky_content)



# Compress each file and report results
for fname in ["random.txt", "uniform.txt", "blocky.txt"]:
    compressed_name = fname + ".gz"
    compressed_size = compress_file(fname, compressed_name)
    original_size = os.path.getsize(fname)
    ratio = compressed_size / original_size
    print(f"{fname}:")
    print(f"  Original size: {original_size / 1024:.2f} KB")
    print(f"  Compressed size: {compressed_size / 1024:.2f} KB")
    print(f"  Compression ratio: {ratio:.3f}\n")
