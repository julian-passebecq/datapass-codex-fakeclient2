# Wind blade 3D - synthetic pilot

Python 3.11+, standard library at runtime. This creates a closed triangle mesh from four rectangular sections in `params/blade_v1.json`: 16 vertices, 28 triangles. This is teaching geometry, not an aerodynamic, structural or manufacturing design.

```sh
python -m blade3d --params params/blade_v1.json --out out/blade_v1.obj
python -m blade3d --study fixtures/study_result.json
python -m pip install 'pytest>=8,<9'
python -m pytest -q
```

Coordinates: z is span in metres, x is chord and y is thickness. Twist is in degrees, about quarter-chord; default thickness is 12% of chord. Stations must increase from zero to the declared length. Invalid or nonfinite inputs fail before output replacement. Output is atomic and deterministic.

## View

Run `python -m http.server 8000` from this repository and open `http://localhost:8000/viewer/`. The plain JavaScript canvas viewer fetches `out/blade_v1.obj`, supports rotation and uses no library or CDN. Alternatively open `viewer/index.html` directly and select an OBJ with the file picker. Without a generated file the viewer gives an explicit message, not an empty-success state.

## Exchange and independence

The optional study JSON is a versioned, synthetic fixture copied from the study CLI, not a cross-repository import. It contributes metadata only; it never changes blade dimensions or claims physical consistency. Supply a newly generated file with `--study PATH` to test a real file exchange. Both repositories work independently and without any bridge.

The six tests check counts, closed-surface connectivity, bounds, invalid inputs, file generation, optional exchange and CLI execution. CI runs on Python 3.11/3.12/3.13; viewer interaction is a separate check, not implied by Python tests.
