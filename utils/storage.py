import json
import os
from typing import Dict, Tuple

def loaddata(datapath: str) -> Tuple[Dict[int, int], Dict[int, Dict[str, int]]]:
    if os.path.exists(datapath):
        with open(datapath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('partners', {}), data.get('messages', {})
    return {}, {}

def savedata(datapath: str, partners: Dict[int, int], messages: Dict[int, Dict[str, int]]):
    os.makedirs(os.path.dirname(datapath), exist_ok=True)
    data = {'partners': partners, 'messages': messages}
    with open(datapath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
