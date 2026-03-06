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
| Edit label | Double-click shape/arrow in Select mode, or F2, or right-click |
| Right-click menu | Right-click shape for label, send forward/back, delete |
| Connect | Arrow tool → click source → click target |
| Arrow style | Select arrow → use Style/Width dropdowns in Arrows toolbar |
| Multi-select | Ctrl+Click or Shift+Click items |
| Box select | Drag on empty canvas (rubber band) |
| Additive box select | Shift+drag to add to existing selection |
| Copy | Ctrl+C (copies selected shapes and their arrows) |
| Cut | Ctrl+X (copies then deletes selected items) |
| Paste | Ctrl+V (pastes with slight offset, auto-selected) |
| Delete | Select + Delete key |
| Undo | Ctrl+Z (10 levels, includes move/resize) |
| Redo | Ctrl+Y |
| Save | Ctrl+S |
| Open | Ctrl+O |
| Rename/Label | F2 (selected item) |
| Clear selection | Press Escape |
| Layer up | Select + press `+` or `=` |
| Layer down | Select + press `-` |
| Zoom in/out | Mouse wheel scroll |
| Toggle grid | Click "Grid" button in File toolbar |
| Toggle snap | Click "Snap" button in File toolbar |
| Import shapes | Click "Import" to merge JSON into canvas |

## Keyboard Shortcuts

| Key | Tool |
|-----|------|
| V | Select |
| R | Rectangle |
| S | Square |
| O | Oval |
| I | Circle |
| D | Diamond |
| H | Hexagon |
| G | Octagon |
| T | Triangle (Up) |
| X | Text Label |
| A | Arrow |
| W | Two-way Arrow |

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

## TODO

- [x] Grid overlay and snap-to-grid for alignment
- [x] Mouse wheel zoom in/out
- [x] Undo/Redo (Ctrl+Z / Ctrl+Y)
- [x] Keyboard shortcuts per tool (R, S, O, C, D, H, G, T, A, V, etc.)
- [x] Toolbar tabs/groups (Shapes, Triangles, Arrows, Formatting, File)
- [x] Import prebuilt shapes from JSON without clearing canvas
- [ ] Align selected items (left/right/top/bottom/center)
- [ ] Distribute evenly (equal spacing)
- [ ] Snap to other shapes (guide lines)
- [ ] Drag to create (click and drag to set shape size)
- [x] Double-click shape to edit label inline
- [ ] Arrow routing styles (straight, orthogonal, curved)
- [x] Arrow line styles (dashed, dotted, thick, thin)
- [ ] Shape border color and thickness separate from fill
- [ ] Opacity/transparency control
- [ ] Drop shadows toggle
- [ ] Background color picker for canvas
- [ ] Recent files list
- [ ] Auto-save / recovery
- [ ] Grouping (Ctrl+G) — treat multiple shapes as one unit
- [ ] Lock items — prevent accidental moves
- [ ] Zoom controls in toolbar (fit to page, zoom %)
- [ ] Minimap for large diagrams