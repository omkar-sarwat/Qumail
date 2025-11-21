import os
import secrets
import shutil
from pathlib import Path

"""Generate identical quantum key .cor files for KM1 and KM2.
Usage:
  python generate_quantum_keys.py --count 1000 --bytes 32 --out qkd_keys
This will create:
  qkd_keys/km1_keys/*.cor
  qkd_keys/km2_keys/*.cor
Each file contains cryptographically random bytes and both directories are byte-for-byte identical.
"""

import argparse

def generate_keys(count: int, key_bytes: int, out_dir: Path):
    km1 = out_dir / "km1_keys"
    km2 = out_dir / "km2_keys"
    km1.mkdir(parents=True, exist_ok=True)
    km2.mkdir(parents=True, exist_ok=True)

    for i in range(1, count + 1):
        data = secrets.token_bytes(key_bytes)
        filename = f"quantum_key_{i:04d}.cor"
        f1 = km1 / filename
        with open(f1, 'wb') as fh:
            fh.write(data)
        # Copy to km2 to ensure identical content
        f2 = km2 / filename
        shutil.copy2(f1, f2)
    print(f"Generated {count} keys of {key_bytes} bytes each in {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--bytes', dest='key_bytes', type=int, default=32)
    parser.add_argument('--out', type=str, default='qkd_keys')
    args = parser.parse_args()

    out_dir = Path(args.out)
    generate_keys(args.count, args.key_bytes, out_dir)

if __name__ == '__main__':
    main()
