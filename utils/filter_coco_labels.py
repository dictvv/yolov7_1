"""
COCO Labels Filtering Script
過濾 COCO 標註檔案，只保留指定類別的標註

用法:
python utils/filter_coco_labels.py \
    --input coco/labels/train2017 \
    --output coco/labels_head1/train2017 \
    --keep-classes 0,1,2,3,4,5,6,7,8,9,10,11,12,13,24,26,28,32,33,36
"""

import argparse
import os
from pathlib import Path
from tqdm import tqdm


def filter_labels(input_dir, output_dir, keep_classes):
    """
    過濾標註檔案，只保留指定類別

    Args:
        input_dir: 原始標註資料夾
        output_dir: 輸出標註資料夾
        keep_classes: 要保留的類別 ID 列表
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 創建輸出資料夾
    output_path.mkdir(parents=True, exist_ok=True)

    # 轉換為 set 加快查找
    keep_classes_set = set(keep_classes)

    # 統計資訊
    total_files = 0
    total_objects_original = 0
    total_objects_filtered = 0
    empty_files = 0

    # 取得所有標註檔案
    label_files = list(input_path.glob('*.txt'))

    print(f"Processing {len(label_files)} label files...")

    for label_file in tqdm(label_files, desc="Filtering labels"):
        # 跳過 Mac 系統的元數據檔案
        if label_file.name.startswith('._'):
            continue

        total_files += 1

        # 讀取原始標註
        with open(label_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_objects_original += len(lines)

        # 過濾標註
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 取得類別 ID (第一個數字)
            parts = line.split()
            if len(parts) < 5:  # 格式：class_id x y w h
                continue

            class_id = int(parts[0])

            # 只保留指定類別
            if class_id in keep_classes_set:
                filtered_lines.append(line + '\n')

        total_objects_filtered += len(filtered_lines)

        # 寫入過濾後的標註
        output_file = output_path / label_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_lines)

        if len(filtered_lines) == 0:
            empty_files += 1

    # 顯示統計資訊
    print(f"\n{'='*60}")
    print(f"Filtering Summary:")
    print(f"{'='*60}")
    print(f"Total files processed: {total_files}")
    print(f"Empty files (no objects): {empty_files} ({empty_files/total_files*100:.1f}%)")
    print(f"Original objects: {total_objects_original}")
    print(f"Filtered objects: {total_objects_filtered}")
    print(f"Objects removed: {total_objects_original - total_objects_filtered}")
    print(f"Retention rate: {total_objects_filtered/total_objects_original*100:.1f}%")
    print(f"{'='*60}")
    print(f"Output saved to: {output_path}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Filter COCO labels by class')
    parser.add_argument('--input', type=str, required=True,
                        help='Input labels directory')
    parser.add_argument('--output', type=str, required=True,
                        help='Output labels directory')
    parser.add_argument('--keep-classes', type=str, required=True,
                        help='Comma-separated list of class IDs to keep (e.g., 0,1,2,3)')

    args = parser.parse_args()

    # 解析類別 ID
    keep_classes = [int(x.strip()) for x in args.keep_classes.split(',')]

    print(f"\nFiltering Configuration:")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Keep classes: {keep_classes}")
    print(f"  Total classes to keep: {len(keep_classes)}\n")

    # 執行過濾
    filter_labels(args.input, args.output, keep_classes)


if __name__ == '__main__':
    main()
