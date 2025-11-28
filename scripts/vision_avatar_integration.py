"""Tools to run vision model inference on avatar asset collections and export predictions.

This utility accepts a model checkpoint and a folder of images (either flat or organized into class subfolders)
and outputs a JSON file mapping each file to its predicted class + confidence score. Optionally exports
feature vectors for each image which can be used for clustering or indexing for retrieval.

Use-case: integrate predictions into avatar pipelines where you have many head/pose/expression assets and
want to assign labels or cluster them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

try:
    import torch
except Exception as e:  # pragma: no cover
    print('PyTorch required for vision inference:', e)
    raise

from PIL import Image, ImageDraw, ImageFont
import numpy as np

from scripts.train_vision import TinyConvNet


def _gather_image_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob('*'):
        if p.suffix.lower() in ('.png', '.jpg', '.jpeg') and p.is_file():
            files.append(p)
    return sorted(files)


def _preprocess_image(pth: Path, img_size: int):
    im = Image.open(pth).convert('RGB')
    im = im.resize((img_size, img_size), Image.BILINEAR)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).contiguous()
    return tensor


def run_inference(checkpoint: Path, assets_dir: Path, out_json: Path, img_size=64, batch_size=32, save_annotated: bool=False, export_features: bool=False):
    ck = torch.load(str(checkpoint), map_location='cpu', weights_only=True)
    classes = ck.get('classes')
    if not classes:
        raise RuntimeError('Checkpoint missing classes')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TinyConvNet(num_classes=len(classes)).to(device)
    model.load_state_dict(ck['model'])
    model.eval()

    files = _gather_image_files(assets_dir)
    if not files:
        raise RuntimeError('No supported image files found in ' + str(assets_dir))

    results = {}
    all_features = []
    # create a simple features extractor by removing last linear layer
    # model.net is sequential; features will be output after Flatten (right before linear)
    feat_net = torch.nn.Sequential(*list(model.net.children())[:-1]).to(device)

    for i in range(0, len(files), batch_size):
        batch_files = files[i:i+batch_size]
        tensors = [ _preprocess_image(p, img_size) for p in batch_files ]
        xb = torch.cat(tensors, dim=0).to(device)
        with torch.no_grad():
            logits = model(xb)
            probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()
            preds = logits.argmax(dim=1).cpu().tolist()
            feats = feat_net(xb).cpu().numpy()

        for pth, pred, prob, feat in zip(batch_files, preds, probs, feats):
            results[str(pth)] = {
                'predicted_idx': int(pred),
                'predicted_label': classes[pred],
                'confidence': float(float(prob[pred])),
            }
            if export_features:
                results[str(pth)]['features'] = [float(x) for x in feat.tolist()]

            if save_annotated:
                out_dir = out_json.parent / 'annotated'
                out_dir.mkdir(parents=True, exist_ok=True)
                try:
                    im = Image.open(pth).convert('RGB')
                    draw = ImageDraw.Draw(im)
                    txt = f"{classes[pred]} {prob[pred]:.3f}"
                    try:
                        font = ImageFont.load_default()
                    except Exception:
                        font = None
                    draw.rectangle([(0, 0), (im.width, 18)], fill=(0, 0, 0))
                    draw.text((4, 1), txt, fill=(255, 255, 255), font=font)
                    im.save(out_dir / pth.name)
                except Exception as e:
                    print('Warning: failed to save annotated image for', pth, e)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2))
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--assets-dir', required=True)
    ap.add_argument('--out-json', default='data_out/avatar_predictions.json')
    ap.add_argument('--img-size', type=int, default=64)
    ap.add_argument('--batch-size', type=int, default=32)
    ap.add_argument('--save-annotated', action='store_true')
    ap.add_argument('--export-features', action='store_true')
    args = ap.parse_args()

    r = run_inference(Path(args.checkpoint), Path(args.assets_dir), Path(args.out_json), img_size=args.img_size, batch_size=args.batch_size, save_annotated=args.save_annotated, export_features=args.export_features)
    print('Wrote predictions for', len(r), 'files to', args.out_json)
