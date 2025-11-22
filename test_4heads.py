"""
test_4heads.py - YOLOv7 四頭模型評估腳本

這個腳本用於評估 4 個獨立訓練的 YOLOv7 Head 模型的組合性能：
  - Head 1: 人與交通工具 (類別 0-13, 24, 26, 28, 32, 33, 36)
  - Head 2: 動物與運動 (類別 14-23, 25, 27, 29-31, 34, 35, 37, 38, 77)
  - Head 3: 家居與電子 (類別 56-75)
  - Head 4: 食物與餐具 (類別 39-55, 76, 78, 79)

評估流程：
  1. 加載 4 個訓練好的模型
  2. 對每張圖片運行 4 個模型的推理
  3. 過濾每個 Head 的預測，只保留其負責的類別
  4. 合併所有預測
  5. 應用全局 NMS 去除重複框
  6. 計算整體的 mAP 和其他指標

使用方法：
  python test_4heads.py --weights runs/train/head1/weights/best.pt \\
                                 runs/train/head2/weights/best.pt \\
                                 runs/train/head3/weights/best.pt \\
                                 runs/train/head4/weights/best.pt \\
                        --data data/coco.yaml \\
                        --img-size 640 --batch-size 32

注意：必須提供完整的 80 類 COCO 標註（使用 data/coco.yaml，不是 data/coco_headX.yaml）
"""

import argparse
import json
import os
from pathlib import Path
from threading import Thread

import numpy as np
import torch
import yaml
from tqdm import tqdm

from models.experimental import attempt_load
from utils.datasets import create_dataloader
from utils.general import coco80_to_coco91_class, check_dataset, check_file, check_img_size, check_requirements, \
    box_iou, non_max_suppression, scale_coords, xyxy2xywh, xywh2xyxy, set_logging, increment_path, colorstr
from utils.metrics import ap_per_class, ConfusionMatrix
from utils.plots import plot_images, output_to_target, plot_study_txt
from utils.torch_utils import select_device, time_synchronized, TracedModel


# ==================== 4 Heads 專用函數 ====================
# 定義每個 Head 負責的類別 ID
HEAD_CLASSES = {
    'head1': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 24, 26, 28, 32, 33, 36],  # 人與交通工具
    'head2': [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 27, 29, 30, 31, 34, 35, 37, 38, 77],  # 動物與運動
    'head3': [56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75],  # 家居與電子
    'head4': [39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 76, 78, 79]   # 食物與餐具
}


def filter_predictions_by_head(predictions, head_name):
    """
    過濾預測結果，只保留該 Head 負責的類別

    Args:
        predictions: tensor shape [N, 6] (x1, y1, x2, y2, conf, cls)
        head_name: 'head1', 'head2', 'head3', 或 'head4'

    Returns:
        filtered_predictions: 只包含負責類別的預測
    """
    if len(predictions) == 0:
        return predictions

    # 獲取該 Head 負責的類別 ID
    responsible_classes = HEAD_CLASSES[head_name]

    # 過濾：只保留負責類別的預測
    mask = torch.zeros(len(predictions), dtype=torch.bool, device=predictions.device)
    for class_id in responsible_classes:
        mask |= (predictions[:, 5] == class_id)

    return predictions[mask]


def merge_4heads_predictions(pred_list):
    """
    合併 4 個 Head 的預測結果

    Args:
        pred_list: list of 4 tensors, 每個 tensor shape [N, 6] (x1, y1, x2, y2, conf, cls)

    Returns:
        merged_predictions: 合併後的預測 tensor
    """
    # 過濾掉空的預測
    valid_preds = [p for p in pred_list if len(p) > 0]

    if len(valid_preds) == 0:
        return torch.zeros((0, 6), device=pred_list[0].device if len(pred_list) > 0 else 'cpu')

    # 沿著第 0 維度拼接所有預測
    merged = torch.cat(valid_preds, dim=0)

    return merged


def apply_global_nms(predictions, conf_thres, iou_thres):
    """
    對合併後的預測應用全局 NMS

    Args:
        predictions: tensor shape [N, 6] (x1, y1, x2, y2, conf, cls)
        conf_thres: 信心度閾值
        iou_thres: NMS 的 IoU 閾值

    Returns:
        nms_predictions: NMS 後的預測
    """
    if len(predictions) == 0:
        return predictions

    # 過濾低信心度的預測
    conf_mask = predictions[:, 4] > conf_thres
    predictions = predictions[conf_mask]

    if len(predictions) == 0:
        return predictions

    # 使用 torchvision 的 NMS（YOLOv7 內建方法）
    # 格式：[x1, y1, x2, y2, conf, cls]
    boxes = predictions[:, :4]
    scores = predictions[:, 4]
    classes = predictions[:, 5]

    # 對每個類別分別進行 NMS
    keep_indices = []
    for class_id in torch.unique(classes):
        class_mask = classes == class_id
        class_boxes = boxes[class_mask]
        class_scores = scores[class_mask]
        class_indices = torch.where(class_mask)[0]

        # 使用 torchvision.ops.nms
        from torchvision.ops import nms
        nms_indices = nms(class_boxes, class_scores, iou_thres)
        keep_indices.append(class_indices[nms_indices])

    if len(keep_indices) == 0:
        return torch.zeros((0, 6), device=predictions.device)

    # 合併所有保留的索引
    keep_indices = torch.cat(keep_indices)

    return predictions[keep_indices]
# ==================== 4 Heads 專用函數結束 ====================


def test(data,
         weights=None,
         batch_size=32,
         imgsz=640,
         conf_thres=0.001,
         iou_thres=0.6,  # for NMS
         save_json=False,
         single_cls=False,
         augment=False,
         verbose=False,
         model=None,
         dataloader=None,
         save_dir=Path(''),  # for saving images
         save_txt=False,  # for auto-labelling
         save_hybrid=False,  # for hybrid auto-labelling
         save_conf=False,  # save auto-label confidences
         plots=True,
         wandb_logger=None,
         compute_loss=None,
         half_precision=True,
         trace=False,
         is_coco=False,
         v5_metric=False):
    # Initialize/load model and set device
    training = model is not None
    if training:  # called by train.py
        device = next(model.parameters()).device  # get model device

    else:  # called directly
        set_logging()
        device = select_device(opt.device, batch_size=batch_size)

        # Directories
        save_dir = Path(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))  # increment run
        (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

        # ===== 修改：加載 4 個 Head 模型 =====
        # weights 參數應該是包含 4 個權重文件的列表
        # 例如：['runs/train/head1/weights/best.pt', 'runs/train/head2/weights/best.pt', ...]
        if not isinstance(weights, list) or len(weights) != 4:
            raise ValueError("使用 test_4heads.py 時，必須提供 4 個權重文件！\n"
                           "例如：--weights runs/train/head1/weights/best.pt "
                           "runs/train/head2/weights/best.pt "
                           "runs/train/head3/weights/best.pt "
                           "runs/train/head4/weights/best.pt")

        # 分別加載 4 個模型
        models = {}
        print(f"\n{'='*60}")
        print(f"加載 4 個 Head 模型...")
        print(f"{'='*60}")
        for i, (head_name, weight_path) in enumerate(zip(['head1', 'head2', 'head3', 'head4'], weights)):
            print(f"加載 {head_name}: {weight_path}")
            models[head_name] = attempt_load(weight_path, map_location=device)

        # 使用第一個模型獲取 grid size（所有模型架構相同）
        model = models['head1']  # 暫時使用 head1 模型獲取配置
        gs = max(int(model.stride.max()), 32)  # grid size (max stride)
        imgsz = check_img_size(imgsz, s=gs)  # check img_size

        if trace:
            # 對所有 4 個模型應用 tracing
            for head_name in ['head1', 'head2', 'head3', 'head4']:
                models[head_name] = TracedModel(models[head_name], device, imgsz)
        # ===== 修改結束 =====

    # ===== 修改：對所有 4 個模型應用 Half precision =====
    half = device.type != 'cpu' and half_precision  # half precision only supported on CUDA
    if half and not training:
        for head_name in ['head1', 'head2', 'head3', 'head4']:
            models[head_name].half()
    elif half and training:
        model.half()

    # Configure - 設置所有模型為評估模式
    if not training:
        for head_name in ['head1', 'head2', 'head3', 'head4']:
            models[head_name].eval()
    else:
        model.eval()
    # ===== 修改結束 =====
    if isinstance(data, str):
        is_coco = data.endswith('coco.yaml')
        with open(data) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
    check_dataset(data)  # check
    nc = 1 if single_cls else int(data['nc'])  # number of classes
    iouv = torch.linspace(0.5, 0.95, 10).to(device)  # iou vector for mAP@0.5:0.95
    niou = iouv.numel()

    # Logging
    log_imgs = 0
    if wandb_logger and wandb_logger.wandb:
        log_imgs = min(wandb_logger.log_imgs, 100)
    # Dataloader
    if not training:
        # ===== 修改：對所有 4 個模型進行 warmup =====
        if device.type != 'cpu':
            print("模型預熱中...")
            dummy_input = torch.zeros(1, 3, imgsz, imgsz).to(device)
            for head_name in ['head1', 'head2', 'head3', 'head4']:
                dummy_input_typed = dummy_input.type_as(next(models[head_name].parameters()))
                models[head_name](dummy_input_typed)  # warmup
        # ===== 修改結束 =====
        task = opt.task if opt.task in ('train', 'val', 'test') else 'val'  # path to train/val/test images
        dataloader = create_dataloader(data[task], imgsz, batch_size, gs, opt, pad=0.5, rect=True,
                                       prefix=colorstr(f'{task}: '))[0]

    if v5_metric:
        print("Testing with YOLOv5 AP metric...")
    
    seen = 0
    confusion_matrix = ConfusionMatrix(nc=nc)
    names = {k: v for k, v in enumerate(model.names if hasattr(model, 'names') else model.module.names)}
    coco91class = coco80_to_coco91_class()
    s = ('%20s' + '%12s' * 6) % ('Class', 'Images', 'Labels', 'P', 'R', 'mAP@.5', 'mAP@.5:.95')
    p, r, f1, mp, mr, map50, map, t0, t1 = 0., 0., 0., 0., 0., 0., 0., 0., 0.
    loss = torch.zeros(3, device=device)
    jdict, stats, ap, ap_class, wandb_images = [], [], [], [], []
    for batch_i, (img, targets, paths, shapes) in enumerate(tqdm(dataloader, desc=s)):
        img = img.to(device, non_blocking=True)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        targets = targets.to(device)
        nb, _, height, width = img.shape  # batch size, channels, height, width

        with torch.no_grad():
            # ===== 修改：運行 4 個模型並合併預測 =====
            if not training:
                # Step 1: 對 4 個模型分別進行推理
                t = time_synchronized()
                all_heads_outputs = {}  # 儲存每個 head 的原始輸出

                for head_name in ['head1', 'head2', 'head3', 'head4']:
                    head_out, head_train_out = models[head_name](img, augment=augment)
                    all_heads_outputs[head_name] = head_out

                t0 += time_synchronized() - t

                # Step 2: 對每個 head 的輸出進行 NMS（去除重複框，但不合併）
                # 這裡使用較低的閾值，保留更多候選框，在全局 NMS 時再最終篩選
                t = time_synchronized()
                targets[:, 2:] *= torch.Tensor([width, height, width, height]).to(device)  # to pixels
                lb = [targets[targets[:, 0] == i, 1:] for i in range(nb)] if save_hybrid else []

                all_heads_nms = {}  # 儲存每個 head 經過 NMS 的輸出
                for head_name in ['head1', 'head2', 'head3', 'head4']:
                    # 對每個 head 應用 NMS
                    head_nms_out = non_max_suppression(
                        all_heads_outputs[head_name],
                        conf_thres=conf_thres,
                        iou_thres=iou_thres,
                        labels=lb,
                        multi_label=True
                    )
                    all_heads_nms[head_name] = head_nms_out

                # Step 3: 對每個 batch 中的每張圖片，合併 4 個 head 的預測
                out = []  # 最終合併後的輸出（每張圖片一個 tensor）
                for img_idx in range(nb):  # 遍歷 batch 中的每張圖片
                    # 收集該圖片在 4 個 head 的預測
                    predictions_from_4heads = []

                    for head_name in ['head1', 'head2', 'head3', 'head4']:
                        head_pred = all_heads_nms[head_name][img_idx]  # shape: [N, 6]
                        # 過濾：只保留該 head 負責的類別
                        filtered_pred = filter_predictions_by_head(head_pred, head_name)
                        predictions_from_4heads.append(filtered_pred)

                    # 合併 4 個 head 的預測
                    merged_pred = merge_4heads_predictions(predictions_from_4heads)

                    # 對合併後的預測應用全局 NMS
                    final_pred = apply_global_nms(merged_pred, conf_thres=conf_thres, iou_thres=iou_thres)

                    out.append(final_pred)

                t1 += time_synchronized() - t

            else:
                # Training mode: 使用原始邏輯
                t = time_synchronized()
                out, train_out = model(img, augment=augment)  # inference and training outputs
                t0 += time_synchronized() - t

                # Compute loss
                if compute_loss:
                    loss += compute_loss([x.float() for x in train_out], targets)[1][:3]  # box, obj, cls

                # Run NMS
                targets[:, 2:] *= torch.Tensor([width, height, width, height]).to(device)  # to pixels
                lb = [targets[targets[:, 0] == i, 1:] for i in range(nb)] if save_hybrid else []  # for autolabelling
                t = time_synchronized()
                out = non_max_suppression(out, conf_thres=conf_thres, iou_thres=iou_thres, labels=lb, multi_label=True)
                t1 += time_synchronized() - t
            # ===== 修改結束 =====

        # Statistics per image
        for si, pred in enumerate(out):
            labels = targets[targets[:, 0] == si, 1:]
            nl = len(labels)
            tcls = labels[:, 0].tolist() if nl else []  # target class
            path = Path(paths[si])
            seen += 1

            if len(pred) == 0:
                if nl:
                    stats.append((torch.zeros(0, niou, dtype=torch.bool), torch.Tensor(), torch.Tensor(), tcls))
                continue

            # Predictions
            predn = pred.clone()
            scale_coords(img[si].shape[1:], predn[:, :4], shapes[si][0], shapes[si][1])  # native-space pred

            # Append to text file
            if save_txt:
                gn = torch.tensor(shapes[si][0])[[1, 0, 1, 0]]  # normalization gain whwh
                for *xyxy, conf, cls in predn.tolist():
                    xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                    line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                    with open(save_dir / 'labels' / (path.stem + '.txt'), 'a') as f:
                        f.write(('%g ' * len(line)).rstrip() % line + '\n')

            # W&B logging - Media Panel Plots
            if len(wandb_images) < log_imgs and wandb_logger.current_epoch > 0:  # Check for test operation
                if wandb_logger.current_epoch % wandb_logger.bbox_interval == 0:
                    box_data = [{"position": {"minX": xyxy[0], "minY": xyxy[1], "maxX": xyxy[2], "maxY": xyxy[3]},
                                 "class_id": int(cls),
                                 "box_caption": "%s %.3f" % (names[cls], conf),
                                 "scores": {"class_score": conf},
                                 "domain": "pixel"} for *xyxy, conf, cls in pred.tolist()]
                    boxes = {"predictions": {"box_data": box_data, "class_labels": names}}  # inference-space
                    wandb_images.append(wandb_logger.wandb.Image(img[si], boxes=boxes, caption=path.name))
            wandb_logger.log_training_progress(predn, path, names) if wandb_logger and wandb_logger.wandb_run else None

            # Append to pycocotools JSON dictionary
            if save_json:
                # [{"image_id": 42, "category_id": 18, "bbox": [258.15, 41.29, 348.26, 243.78], "score": 0.236}, ...
                image_id = int(path.stem) if path.stem.isnumeric() else path.stem
                box = xyxy2xywh(predn[:, :4])  # xywh
                box[:, :2] -= box[:, 2:] / 2  # xy center to top-left corner
                for p, b in zip(pred.tolist(), box.tolist()):
                    jdict.append({'image_id': image_id,
                                  'category_id': coco91class[int(p[5])] if is_coco else int(p[5]),
                                  'bbox': [round(x, 3) for x in b],
                                  'score': round(p[4], 5)})

            # Assign all predictions as incorrect
            correct = torch.zeros(pred.shape[0], niou, dtype=torch.bool, device=device)
            if nl:
                detected = []  # target indices
                tcls_tensor = labels[:, 0]

                # target boxes
                tbox = xywh2xyxy(labels[:, 1:5])
                scale_coords(img[si].shape[1:], tbox, shapes[si][0], shapes[si][1])  # native-space labels
                if plots:
                    confusion_matrix.process_batch(predn, torch.cat((labels[:, 0:1], tbox), 1))

                # Per target class
                for cls in torch.unique(tcls_tensor):
                    ti = (cls == tcls_tensor).nonzero(as_tuple=False).view(-1)  # prediction indices
                    pi = (cls == pred[:, 5]).nonzero(as_tuple=False).view(-1)  # target indices

                    # Search for detections
                    if pi.shape[0]:
                        # Prediction to target ious
                        ious, i = box_iou(predn[pi, :4], tbox[ti]).max(1)  # best ious, indices

                        # Append detections
                        detected_set = set()
                        for j in (ious > iouv[0]).nonzero(as_tuple=False):
                            d = ti[i[j]]  # detected target
                            if d.item() not in detected_set:
                                detected_set.add(d.item())
                                detected.append(d)
                                correct[pi[j]] = ious[j] > iouv  # iou_thres is 1xn
                                if len(detected) == nl:  # all targets already located in image
                                    break

            # Append statistics (correct, conf, pcls, tcls)
            stats.append((correct.cpu(), pred[:, 4].cpu(), pred[:, 5].cpu(), tcls))

        # Plot images
        if plots and batch_i < 3:
            f = save_dir / f'test_batch{batch_i}_labels.jpg'  # labels
            Thread(target=plot_images, args=(img, targets, paths, f, names), daemon=True).start()
            f = save_dir / f'test_batch{batch_i}_pred.jpg'  # predictions
            Thread(target=plot_images, args=(img, output_to_target(out), paths, f, names), daemon=True).start()

    # Compute statistics
    stats = [np.concatenate(x, 0) for x in zip(*stats)]  # to numpy
    if len(stats) and stats[0].any():
        p, r, ap, f1, ap_class = ap_per_class(*stats, plot=plots, v5_metric=v5_metric, save_dir=save_dir, names=names)
        ap50, ap = ap[:, 0], ap.mean(1)  # AP@0.5, AP@0.5:0.95
        mp, mr, map50, map = p.mean(), r.mean(), ap50.mean(), ap.mean()
        nt = np.bincount(stats[3].astype(np.int64), minlength=nc)  # number of targets per class
    else:
        nt = torch.zeros(1)

    # Print results
    pf = '%20s' + '%12i' * 2 + '%12.3g' * 4  # print format
    print(pf % ('all', seen, nt.sum(), mp, mr, map50, map))

    # Print results per class
    if (verbose or (nc < 50 and not training)) and nc > 1 and len(stats):
        for i, c in enumerate(ap_class):
            print(pf % (names[c], seen, nt[c], p[i], r[i], ap50[i], ap[i]))

    # Print speeds
    t = tuple(x / seen * 1E3 for x in (t0, t1, t0 + t1)) + (imgsz, imgsz, batch_size)  # tuple
    if not training:
        print('Speed: %.1f/%.1f/%.1f ms inference/NMS/total per %gx%g image at batch-size %g' % t)

    # Plots
    if plots:
        confusion_matrix.plot(save_dir=save_dir, names=list(names.values()))
        if wandb_logger and wandb_logger.wandb:
            val_batches = [wandb_logger.wandb.Image(str(f), caption=f.name) for f in sorted(save_dir.glob('test*.jpg'))]
            wandb_logger.log({"Validation": val_batches})
    if wandb_images:
        wandb_logger.log({"Bounding Box Debugger/Images": wandb_images})

    # Save JSON
    if save_json and len(jdict):
        w = Path(weights[0] if isinstance(weights, list) else weights).stem if weights is not None else ''  # weights
        anno_json = './coco/annotations/instances_val2017.json'  # annotations json
        pred_json = str(save_dir / f"{w}_predictions.json")  # predictions json
        print('\nEvaluating pycocotools mAP... saving %s...' % pred_json)
        with open(pred_json, 'w') as f:
            json.dump(jdict, f)

        try:  # https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocoEvalDemo.ipynb
            from pycocotools.coco import COCO
            from pycocotools.cocoeval import COCOeval

            anno = COCO(anno_json)  # init annotations api
            pred = anno.loadRes(pred_json)  # init predictions api
            eval = COCOeval(anno, pred, 'bbox')
            if is_coco:
                eval.params.imgIds = [int(Path(x).stem) for x in dataloader.dataset.img_files]  # image IDs to evaluate
            eval.evaluate()
            eval.accumulate()
            eval.summarize()
            map, map50 = eval.stats[:2]  # update results (mAP@0.5:0.95, mAP@0.5)
        except Exception as e:
            print(f'pycocotools unable to run: {e}')

    # Return results
    # ===== 修改：將所有模型設回 float 模式 =====
    if not training:
        for head_name in ['head1', 'head2', 'head3', 'head4']:
            models[head_name].float()
    else:
        model.float()  # for training
    # ===== 修改結束 =====
    if not training:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")
    maps = np.zeros(nc) + map
    for i, c in enumerate(ap_class):
        maps[c] = ap[i]
    return (mp, mr, map50, map, *(loss.cpu() / len(dataloader)).tolist()), maps, t


if __name__ == '__main__':
    # ===== 修改：更新程序名稱和權重參數說明 =====
    parser = argparse.ArgumentParser(prog='test_4heads.py')
    parser.add_argument('--weights', nargs='+', type=str,
                        default=['runs/train/head1/weights/best.pt',
                                'runs/train/head2/weights/best.pt',
                                'runs/train/head3/weights/best.pt',
                                'runs/train/head4/weights/best.pt'],
                        help='必須提供 4 個權重文件路徑，分別對應 head1, head2, head3, head4')
    parser.add_argument('--data', type=str, default='data/coco.yaml',
                        help='COCO 資料集配置檔案（使用完整的 80 類標註）')
    # ===== 修改結束 =====
    parser.add_argument('--batch-size', type=int, default=32, help='size of each image batch')
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.001, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.65, help='IOU threshold for NMS')
    parser.add_argument('--task', default='val', help='train, val, test, speed or study')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--single-cls', action='store_true', help='treat as single-class dataset')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--verbose', action='store_true', help='report mAP by class')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-hybrid', action='store_true', help='save label+prediction hybrid results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-json', action='store_true', help='save a cocoapi-compatible JSON results file')
    parser.add_argument('--project', default='runs/test', help='save to project/name')
    parser.add_argument('--name', default='exp', help='save to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--no-trace', action='store_true', help='don`t trace model')
    parser.add_argument('--v5-metric', action='store_true', help='assume maximum recall as 1.0 in AP calculation')
    opt = parser.parse_args()
    opt.save_json |= opt.data.endswith('coco.yaml')
    opt.data = check_file(opt.data)  # check file
    print(opt)
    #check_requirements()

    if opt.task in ('train', 'val', 'test'):  # run normally
        test(opt.data,
             opt.weights,
             opt.batch_size,
             opt.img_size,
             opt.conf_thres,
             opt.iou_thres,
             opt.save_json,
             opt.single_cls,
             opt.augment,
             opt.verbose,
             save_txt=opt.save_txt | opt.save_hybrid,
             save_hybrid=opt.save_hybrid,
             save_conf=opt.save_conf,
             trace=not opt.no_trace,
             v5_metric=opt.v5_metric
             )

    elif opt.task == 'speed':  # speed benchmarks
        for w in opt.weights:
            test(opt.data, w, opt.batch_size, opt.img_size, 0.25, 0.45, save_json=False, plots=False, v5_metric=opt.v5_metric)

    elif opt.task == 'study':  # run over a range of settings and save/plot
        # python test.py --task study --data coco.yaml --iou 0.65 --weights yolov7.pt
        x = list(range(256, 1536 + 128, 128))  # x axis (image sizes)
        for w in opt.weights:
            f = f'study_{Path(opt.data).stem}_{Path(w).stem}.txt'  # filename to save to
            y = []  # y axis
            for i in x:  # img-size
                print(f'\nRunning {f} point {i}...')
                r, _, t = test(opt.data, w, opt.batch_size, i, opt.conf_thres, opt.iou_thres, opt.save_json,
                               plots=False, v5_metric=opt.v5_metric)
                y.append(r + t)  # results and times
            np.savetxt(f, y, fmt='%10.4g')  # save
        os.system('zip -r study.zip study_*.txt')
        plot_study_txt(x=x)  # plot
