"""RegionDefiner's normalized, column-staggered flat-top hex geometry.

The editable region overlay uses this mapping to enforce the same claimed
30x30 hex footprint selected on screen. MMO parcels use their separate square
claim lattice and are not changed.
"""

def region_cell_for_point(x, y, shape="square", columns=30, rows=30):
    px = min(1.0, max(0.0, float(x)))
    py = min(1.0, max(0.0, float(y)))
    if str(shape).lower() != "hex":
        column = min(columns - 1, int(min(px, .999999) * columns))
        row = min(rows - 1, int(min(py, .999999) * rows))
        return row * columns + column
    width = columns * .75 + .25
    height = rows + .5
    best, best_distance = 0, float("inf")
    for cell in range(columns * rows):
        column, row = cell % columns, cell // columns
        cx = (column * .75 + .5) / width
        cy = (row + (column % 2) * .5 + .5) / height
        distance = (cx-px)**2 + (cy-py)**2
        if distance < best_distance:
            best, best_distance = cell, distance
    return best
