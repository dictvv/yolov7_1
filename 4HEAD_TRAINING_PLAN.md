# YOLOv7 4-Head Multi-Task Training Plan

## 專案概述

本專案實現了將 COCO 80 類物件檢測任務分解為 4 個專門化檢測頭的多任務學習架構。每個檢測頭專注於 20 個相關類別，採用分而治之的策略來提升檢測效能。

## 架構設計

### 類別分組策略

COCO 80 類被分為 4 組，每組 20 個類別：

#### Head 1: 交通與人物 (Classes 0-13, 24, 26, 28, 32, 33, 36)
- 配置檔案: `data/coco_head1.yaml`
- 類別: person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, backpack, handbag, suitcase, sports ball, kite, skateboard

#### Head 2: 動物與運動 (Classes 14-23, 25, 27, 29-31, 34, 35, 37, 38, 77)
- 配置檔案: `data/coco_head2.yaml`
- 類別: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, umbrella, tie, frisbee, skis, snowboard, baseball bat, baseball glove, surfboard, tennis racket, teddy bear

#### Head 3: 家居與電子 (Classes 56-75)
- 配置檔案: `data/coco_head3.yaml`
- 類別: chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase

#### Head 4: 食物與餐具 (Classes 39-55, 76, 78, 79)
- 配置檔案: `data/coco_head4.yaml`
- 類別: bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, scissors, hair drier, toothbrush

### 設計優勢

1. **類別相似性**: 同一 head 內的物件在視覺特徵和語義上相關
2. **負載平衡**: 每個 head 負責 20 個類別，訓練負載均衡
3. **專門化學習**: 每個 head 可以學習特定領域的特徵
4. **並行處理**: 4 個 head 可以獨立訓練和推理

## 資料準備

### COCO 資料集結構
```
coco/
├── images/
│   ├── train2017/     # 118,287 張訓練圖片
│   └── val2017/       # 5,000 張驗證圖片
├── labels/            # 原始標註（所有 80 類）
│   ├── train2017/
│   └── val2017/
├── labels_head1/      # Head 1 過濾後的標註
│   ├── train2017/
│   └── val2017/
├── labels_head2/      # Head 2 過濾後的標註
│   ├── train2017/
│   └── val2017/
├── labels_head3/      # Head 3 過濾後的標註
│   ├── train2017/
│   └── val2017/
└── labels_head4/      # Head 4 過濾後的標註
    ├── train2017/
    └── val2017/
```

### 標註過濾

使用 `utils/filter_coco_labels.py` 工具為每個 head 生成過濾後的標註：

```bash
# Head 1
python utils/filter_coco_labels.py \
  --input coco/labels/train2017 \
  --output coco/labels_head1/train2017 \
  --keep-classes 0,1,2,3,4,5,6,7,8,9,10,11,12,13,24,26,28,32,33,36

# Head 2
python utils/filter_coco_labels.py \
  --input coco/labels/train2017 \
  --output coco/labels_head2/train2017 \
  --keep-classes 14,15,16,17,18,19,20,21,22,23,25,27,29,30,31,34,35,37,38,77

# Head 3
python utils/filter_coco_labels.py \
  --input coco/labels/train2017 \
  --output coco/labels_head3/train2017 \
  --keep-classes 56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75

# Head 4
python utils/filter_coco_labels.py \
  --input coco/labels/train2017 \
  --output coco/labels_head4/train2017 \
  --keep-classes 39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,76,78,79
```

**注意**: 對 val2017 也需要執行相同的過濾操作。

## 訓練流程

### 階段 1: 獨立訓練 4 個檢測頭

每個 head 使用過濾後的標註獨立訓練。**重要**: nc 參數必須保持為 80（完整的 COCO 類別數），而非 20。

#### Head 1 訓練
```bash
# 訓練前：切換到 Head 1 標註
mv coco/labels coco/labels_backup
mv coco/labels_head1 coco/labels

# 訓練
python train.py \
  --workers 8 \
  --device 0 \
  --batch-size 32 \
  --data data/coco_head1.yaml \
  --img 640 640 \
  --cfg cfg/training/yolov7.yaml \
  --weights '' \
  --name yolov7_head1 \
  --hyp data/hyp.scratch.p5.yaml \
  --epochs 100

# 訓練後：恢復標註
mv coco/labels coco/labels_head1
mv coco/labels_backup coco/labels
```

#### Head 2 訓練
```bash
# 訓練前：切換到 Head 2 標註
mv coco/labels coco/labels_backup
mv coco/labels_head2 coco/labels

# 訓練
python train.py \
  --workers 8 \
  --device 0 \
  --batch-size 32 \
  --data data/coco_head2.yaml \
  --img 640 640 \
  --cfg cfg/training/yolov7.yaml \
  --weights '' \
  --name yolov7_head2 \
  --hyp data/hyp.scratch.p5.yaml \
  --epochs 100

# 訓練後：恢復標註
mv coco/labels coco/labels_head2
mv coco/labels_backup coco/labels
```

#### Head 3 訓練
```bash
# 訓練前：切換到 Head 3 標註
mv coco/labels coco/labels_backup
mv coco/labels_head3 coco/labels

# 訓練
python train.py \
  --workers 8 \
  --device 0 \
  --batch-size 32 \
  --data data/coco_head3.yaml \
  --img 640 640 \
  --cfg cfg/training/yolov7.yaml \
  --weights '' \
  --name yolov7_head3 \
  --hyp data/hyp.scratch.p5.yaml \
  --epochs 100

# 訓練後：恢復標註
mv coco/labels coco/labels_head3
mv coco/labels_backup coco/labels
```

#### Head 4 訓練
```bash
# 訓練前：切換到 Head 4 標註
mv coco/labels coco/labels_backup
mv coco/labels_head4 coco/labels

# 訓練
python train.py \
  --workers 8 \
  --device 0 \
  --batch-size 32 \
  --data data/coco_head4.yaml \
  --img 640 640 \
  --cfg cfg/training/yolov7.yaml \
  --weights '' \
  --name yolov7_head4 \
  --hyp data/hyp.scratch.p5.yaml \
  --epochs 100

# 訓練後：恢復標註
mv coco/labels coco/labels_head4
mv coco/labels_backup coco/labels
```

### 訓練參數說明

- `--workers 8`: 資料載入器使用 8 個執行緒
- `--device 0`: 使用第 0 張 GPU
- `--batch-size 32`: 批次大小為 32（根據 GPU 記憶體調整）
- `--img 640 640`: 輸入圖片大小 640x640
- `--cfg cfg/training/yolov7.yaml`: 使用標準 YOLOv7 架構
- `--weights ''`: 從頭訓練（不使用預訓練權重）
- `--epochs 100`: 訓練 100 個 epoch
- `--hyp data/hyp.scratch.p5.yaml`: 使用 P5 超參數配置

### 階段 2: 評估和測試

使用 `test_4heads.py` 評估組合模型效能：

```bash
python test_4heads.py \
  --data data/coco.yaml \
  --img 640 \
  --batch 32 \
  --conf 0.001 \
  --iou 0.65 \
  --device 0 \
  --weights1 runs/train/yolov7_head1/weights/best.pt \
  --weights2 runs/train/yolov7_head2/weights/best.pt \
  --weights3 runs/train/yolov7_head3/weights/best.pt \
  --weights4 runs/train/yolov7_head4/weights/best.pt \
  --name 4heads_eval
```

### 階段 3: 模型融合（可選）

如果需要將 4 個 head 融合為單一模型：

1. **特徵提取**: 使用共享的 backbone 提取特徵
2. **多頭檢測**: 4 個獨立的檢測頭並行處理
3. **結果合併**: 使用 NMS 合併 4 個 head 的檢測結果

## 評估指標

### 單一 Head 評估

每個 head 在其負責的 20 個類別上評估：
- mAP@0.5
- mAP@0.5:0.95
- Precision
- Recall

### 組合模型評估

4 個 head 組合後在完整 80 類上評估：
- 整體 mAP@0.5
- 整體 mAP@0.5:0.95
- 每個類別的 AP
- 推理速度（FPS）
- 記憶體使用量

## 已完成的工作

### ✅ 程式碼實現
1. **test_4heads.py**: 4-head 模型測試腳本（544 行）
   - 支援載入 4 個獨立訓練的模型
   - 實現預測過濾和合併
   - 全局 NMS 處理
   - COCO 格式結果輸出

2. **utils/filter_coco_labels.py**: 標註過濾工具（129 行）
   - 支援指定類別過濾
   - 處理 UTF-8 編碼
   - 過濾 macOS 元資料檔案

### ✅ 配置檔案
1. **data/coco_head1.yaml**: Head 1 配置
2. **data/coco_head2.yaml**: Head 2 配置
3. **data/coco_head3.yaml**: Head 3 配置
4. **data/coco_head4.yaml**: Head 4 配置

### ✅ 資料準備
- COCO 資料集標註已過濾完成
- 4 組 labels_head1-4 資料夾已建立
- 訓練和驗證集標註分別處理

### ✅ 版本控制
- 所有程式碼已提交到 GitHub
- 儲存庫: https://github.com/dictvv/yolov7_1.git

## 待完成的工作

### 🔲 訓練任務
1. 訓練 Head 1 模型
2. 訓練 Head 2 模型
3. 訓練 Head 3 模型
4. 訓練 Head 4 模型

### 🔲 評估任務
1. 評估單一 Head 效能
2. 評估組合模型效能
3. 與 baseline 模型比較
4. 分析每個類別的檢測效能

### 🔲 優化任務
1. 超參數調整
2. 資料增強策略優化
3. 推理速度優化
4. 模型壓縮（可選）

## 在 vast.ai 上訓練

### 環境設定

1. **SSH 連線**:
   ```bash
   ssh -p 42229 root@83.27.164.65 -L 8080:localhost:8080
   ```

2. **進入工作目錄**:
   ```bash
   cd /workspace/yolov7_1
   ```

3. **設定 Python 環境**:
   ```bash
   bash setup.sh
   source venv/bin/activate
   ```

4. **下載 COCO 資料集**:
   參考 `VAST_AI_REMOTE_SETUP.md` 中的指示

### 使用 tmux 監控訓練

```bash
# 創建 tmux 會話
tmux new -s train_head1

# 在會話中執行訓練
python train.py --workers 8 --device 0 --batch-size 32 \
  --data data/coco_head1.yaml --img 640 640 \
  --cfg cfg/training/yolov7.yaml --weights '' \
  --name yolov7_head1 --hyp data/hyp.scratch.p5.yaml --epochs 100

# 分離會話（Ctrl+B, D）
# 重新連接會話
tmux attach -t train_head1
```

## 遠端監控設定

### 本地 Claude Code 配置

配置檔案位置: `C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        "42229",
        "root@83.27.164.65",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

重啟 Claude Code 後即可透過 MCP 遠端監控訓練進度。

## 常見問題

### Q1: 為什麼 nc 必須是 80 而不是 20？
A: YOLOv7 的類別 ID 是固定的 0-79。即使某個 head 只負責 20 個類別，模型仍需要知道完整的類別空間來正確處理類別 ID。

### Q2: 如何處理標註切換？
A: 使用 mv 命令在訓練前後切換 labels 資料夾。訓練前將對應的 labels_headN 改名為 labels，訓練後再改回來。

### Q3: 4 個 head 可以並行訓練嗎？
A: 可以，如果有多張 GPU，可以同時訓練多個 head，每個使用不同的 GPU（透過 --device 參數指定）。

### Q4: 如何選擇最佳模型？
A: 訓練過程中會自動保存 best.pt（基於驗證集 mAP）和 last.pt（最後一個 epoch）。通常使用 best.pt 進行評估。

### Q5: 推理時如何使用 4-head 模型？
A: 使用 `test_4heads.py` 腳本，它會載入 4 個權重檔案，分別進行推理，然後合併結果並應用全局 NMS。

## 效能預期

基於 YOLOv7 的標準效能，預期結果：

### 單 Head 模型
- **訓練時間**: 約 10-15 小時/head（100 epochs，單 GPU）
- **mAP@0.5**: 65-70%（在負責的 20 類上）
- **推理速度**: ~100 FPS（640x640，V100 GPU）

### 組合模型
- **整體 mAP@0.5**: 55-60%（80 類）
- **推理速度**: ~25-30 FPS（4 個模型並行）
- **記憶體使用**: ~16GB GPU RAM（4 個模型同時載入）

## 參考資料

- YOLOv7 論文: https://arxiv.org/abs/2207.02696
- YOLOv7 官方儲存庫: https://github.com/WongKinYiu/yolov7
- COCO 資料集: https://cocodataset.org/
- 本專案儲存庫: https://github.com/dictvv/yolov7_1

## 版本歷史

- **2025-11-22**: 初始版本
  - 完成 4-head 架構設計
  - 實現標註過濾工具
  - 創建測試評估腳本
  - 設定遠端訓練環境

---

**文檔建立時間**: 2025-11-22
**最後更新**: 2025-11-22
**維護者**: Claude Code
