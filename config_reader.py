import yaml
import os
from types import SimpleNamespace

currpath = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(currpath, 'config.yaml')) as f:
    _config = yaml.safe_load(f)

class cfg:
    display = SimpleNamespace(**_config['system']['display'])
    switcher = SimpleNamespace(**_config['system']['switcher'])
    modules = {}
    for m in _config['modules'].values():
        modules[m['display_name']] = SimpleNamespace(
            type=m['type'],
            display_name=m['display_name'],
            config=SimpleNamespace(**m['config'])
        )