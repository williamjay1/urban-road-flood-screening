# Derived input dictionary

An area identifier is the GISCO Urban Audit 2018 functional urban area code. The complete code/name/stratum mapping is supplied in the reporting sampling audit and article Table 1.

## Static graph NPZ

The `strategic_static.npz` and `expanded_static.npz` files use the same definitions. They are NumPy ZIP archives and can be opened with `numpy.load` without pickle.

| Array | Definition |
|---|---|
| nodes | Integer one-meter coordinate keys in ETRS89 LAEA Europe, EPSG:3035; row number is the node index. |
| u, v | End node indices of each physical geometry segment. |
| xy | Original geometry segment endpoint longitude/latitude pairs, ordered x1,y1,x2,y2, EPSG:4326. |
| parent | Zero-based row index in the scope-specific frozen source road table; not an OSM way ID. |
| length | Projected physical segment length in kilometers. |
| base | Dry physical segment traversal time in minutes. |
| au, av | Directed arc source and target node indices. |
| phys | Physical segment index associated with each directed arc. |
| bridge, tunnel | Boolean tag interpretation for each physical segment. |
| grade | Boolean bridge or tunnel flag. |
| anchors | Frozen original sparse anchor node indices; dense anchors are generated as a nested extension. |
| junction_groups | Group identifier used for the conventional junction edge representation control. |
| terminal | Boolean node flag for junction/endpoint/attribute-transition termination in that control. |
| base_times | Original sparse dry path matrix; retained for provenance, not read by the fresh primary recomputation. |
| fixed_weights | Original sparse strategic weights, where present; not read by the fresh primary recomputation. |

## Hazard NPZ

`strategic_hazard.npz` and `expanded_hazard.npz` contain the raw RP100 layer's exact grid traversal inputs. They are paired by physical segment index with their own static graph.

| Array | Definition |
|---|---|
| spans | Start-inclusive, end-exclusive offsets into the cell-intersection arrays, one row per segment. |
| fractions | Fraction of segment length represented by each positive-length cell intersection; sums to one for each segment. |
| values | Depth in meters after the documented no-impedance encoding outside valid flood cells and nonnegative clipping. |
| spurious_mask | Whether each cell intersection lies in the provider's spurious depth caution mask. |

The cell fractions use geographic straight segments and projected segment lengths, as described in the article; they are not exact geodesic lengths. Depth zero may represent the model's outside-flood encoding and must not be interpreted as observed safety.

## Result JSON

`D` is the capped relative detour/disconnection loss, `U` its unreachable-weight component, and `fixed_denominator_loss` repeats the calculation with strategic dry time in the denominator. All are dimensionless. `theta` is in minutes; null denotes uniform pair weights. `mask_policy` is retained or spurious_zero_bound. `grade` is exposed or bridge_immune. An anchor count changes the evaluated support and the normalization of its synthetic weights. Scores at different anchor counts are therefore density diagnostics, not replicate observations.
