import json
try:
    import torch
    print(json.dumps({'ok': True, 'cuda': torch.cuda.is_available(), 'version': torch.__version__}))
except Exception as e:
    print(json.dumps({'ok': False, 'error': str(e)}))
