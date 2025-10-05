#!/usr/bin/env python3
"""
Fix torch.load calls for PyTorch 2.6+ compatibility
Adds weights_only=False to all torch.load calls
"""

import re
import os
from pathlib import Path

def fix_torch_load_in_file(file_path):
    """Add weights_only=False to torch.load calls in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Pattern 1: torch.load(arg) -> torch.load(arg, weights_only=False)
    # Only if weights_only is not already present
    if 'weights_only' not in content:
        # Match torch.load with various patterns
        patterns = [
            # torch.load(path)
            (r'torch\.load\(([^,)]+)\)', r'torch.load(\1, weights_only=False)'),
            # torch.load(path, map_location=...)
            (r'torch\.load\(([^,]+),\s*map_location=([^)]+)\)',
             r'torch.load(\1, map_location=\2, weights_only=False)'),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    # Files to fix
    files_to_fix = [
        'detect.py',
        'hubconf.py',
        'train_aux.py',
        'models/experimental.py',
        'utils/aws/resume.py',
        'utils/general.py',
    ]

    base_dir = Path(__file__).parent
    fixed_count = 0

    for file_path in files_to_fix:
        full_path = base_dir / file_path
        if full_path.exists():
            if fix_torch_load_in_file(full_path):
                print(f"✓ Fixed: {file_path}")
                fixed_count += 1
            else:
                print(f"- Skipped: {file_path} (already fixed or no torch.load)")
        else:
            print(f"✗ Not found: {file_path}")

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
