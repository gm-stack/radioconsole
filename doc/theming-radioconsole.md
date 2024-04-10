# Theming Radioconsole

Radioconsole uses [pygame_gui](https://pygame-gui.readthedocs.io/en/latest/quick_start.html) for drawing a lot of the UI components. This supports user provided theme files.

Radioconsole will take the theme defined in `config_theme.yaml`, convert it to JSON, and provide it to `pygame_gui` at load time. See [here](https://pygame-gui.readthedocs.io/en/latest/theme_guide.html) for some information on how to theme `pygame_gui`.

``` yaml
defaults:
  colours:
    normal_bg: "#4c5052"
    hovered_bg: "#63686b"
    disabled_bg: "#25292e"
    selected_bg: "#365880"
    active_bg: "#365880"
    dark_bg: "#21282d"
    disabled_dark_bg: "#181818"
    normal_text: "#bbbbbb"
    hovered_text: "#bbbbbb"
    disabled_text: "#808080"
    selected_text: "#bbbbbb"
    active_text: "#bbbbbb"
    normal_border: "#5c6062"
    hovered_border: "#73787b"
    disabled_border: "#35393e"
    selected_border: "#466890"
    active_border: "#466890"
    link_text: "#6897bb"
    link_hover: "#84bfed"
    link_selected: "#84bfed"
    text_shadow: "#777777"
    filled_bar: "#f4251b"
    unfilled_bar: "#CCCCCC"
'#param_label':
  colours:
    normal_text: "#FF00FF"
    dark_bg: "#151D22"
  font:
    name: "fira_code"
    size: 14
    bold: 1
'#param_value':
  colours:
    normal_text: "#bbbbbb"
    dark_bg: "#21282d"
  font:
    name: "fira_code"
    size: 14
    bold: 0
```