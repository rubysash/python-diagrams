# Diagram Builder

A simple diagram tool built with PyQt5.

## Install

```bash
pip install PyQt5
```

## Run

```bash
python main.py
```

## Controls

| Action | How |
|--------|-----|
| Add shape | Double-click canvas |
| Select | Click shape/arrow |
| Move | Drag selected shape |
| Resize | Drag corner handles |
| Label | Right-click shape/arrow (uses selected label color) |
| Connect | Arrow tool → click source → click target |
| Delete | Select + Delete key |
| Clear all | Press Escape |
| Layer up | Select + press `+` or `=` |
| Layer down | Select + press `-` |

## Color Pickers

| Picker | Purpose |
|--------|---------|
| Fill | Shape fill color - click to change selected shape's color |
| Label | Label text color - select color, then right-click to add label |

**Tip:** To add a colored label:
1. Select the label color you want from the "Label" color picker
2. Right-click on a shape or arrow
3. Enter your label text and press Enter
4. The label appears in your selected color

## Save/Load

| Action | How |
|--------|-----|
| Save | Click "Save" → saves diagram state as JSON |
| Load | Click "Load" → restores diagram from JSON file |

## Export

| Format | Description |
|--------|-------------|
| SVG | Vector graphics (clean, no metadata) |
| PNG | Raster image at 2x resolution |