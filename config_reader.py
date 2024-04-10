import os
import tempfile
import json
from types import SimpleNamespace

import yaml

currpath = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(currpath, 'config.yaml')) as f:
    _config = yaml.safe_load(f)

with open(os.path.join(currpath, 'config_theme.yaml')) as f:
    _theme = yaml.safe_load(f)

theme = tempfile.NamedTemporaryFile(mode='w')
json.dump(_theme, theme)
theme.flush()

system_display = {
    "top_bar_size": 64,
    "top_bar_app_label_width": 192,
    "target_fps": 60
}
system_display.update(_config['system']['display'])

system_switcher = {
    "buttons_x": 4,
    "button_h": 64,
    "button_margin": 2
}
system_switcher.update(_config['system'].get('switcher', {}))

class cfg:
    waterfall_server = SimpleNamespace(
        **_config.get('waterfall_server', {})
    )
    display = SimpleNamespace(
        **system_display,
        size=(system_display['display_w'], system_display['display_h'])
    )
    switcher = SimpleNamespace(**system_switcher)
    modules = {}
    for m in _config['modules'].values():
        modules[m['display_name']] = SimpleNamespace(
            type=m['type'],
            display_name=m['display_name'],
            config=m['config']
        )
    theme_file = theme.name
    theme = _theme
