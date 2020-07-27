import os
import tempfile
import json
from types import SimpleNamespace

import yaml

currpath = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(currpath, 'config.yaml')) as f:
    _config = yaml.safe_load(f)

theme = tempfile.NamedTemporaryFile(mode='w')
json.dump(_config['theme'], theme)
theme.flush()

class cfg:
    waterfall_server = SimpleNamespace(
        **_config.get('waterfall_server', {})
    )
    display = SimpleNamespace(
        **_config['system']['display'],
        size=(_config['system']['display']['DISPLAY_W'], _config['system']['display']['DISPLAY_H'])
    )
    switcher = SimpleNamespace(**_config['system']['switcher'])
    modules = {}
    for m in _config['modules'].values():
        modules[m['display_name']] = SimpleNamespace(
            type=m['type'],
            display_name=m['display_name'],
            config=SimpleNamespace(**m['config'])
        )
    theme_file = theme.name
