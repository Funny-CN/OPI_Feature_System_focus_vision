#!/usr/bin/env python3
"""
轻量级 YOLOv5 PT -> ONNX 导出脚本（v2 - 兼容 PyTorch 2.12）
"""

"""YOLOv5 PT -> ONNX export (PyTorch 2.x compatible)"""
import torch, os, sys, onnx, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pt', default='yolo/weights/best.pt')
    parser.add_argument('--onnx', default='yolo/weights/best.onnx')
    parser.add_argument('--input-size', type=int, default=640)
    parser.add_argument('--opset', type=int, default=12)
    args = parser.parse_args()

    sys.path.insert(0, r'D:\python\Python_Projects\yolo')
    from models.common import DetectMultiBackend

    model = DetectMultiBackend(args.pt, device=torch.device('cpu'))
    pt_model = model.model
    pt_model.eval()
    for p in pt_model.parameters():
        p.data = p.data.detach().clone()

    dummy = torch.zeros(1, 3, args.input_size, args.input_size)
    with torch.no_grad():
        out = pt_model(dummy)
        print(f'Output: {len(out)} tensors' if isinstance(out,(list,tuple)) else f'Output: {out.shape}')

    print('Exporting ONNX...')
    os.makedirs(os.path.dirname(args.onnx) or '.', exist_ok=True)
    torch.onnx.export(pt_model, dummy, args.onnx,
        opset_version=args.opset, input_names=['images'], output_names=['output0'],
        dynamic_axes={'images': {0: 'batch', 2: 'height', 3: 'width'}})

    m = onnx.load(args.onnx)
    onnx.checker.check_model(m)
    print(f'ONNX OK: {os.path.getsize(args.onnx)/1024/1024:.1f} MB')

if __name__ == '__main__':
    main()
