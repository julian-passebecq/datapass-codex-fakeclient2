from __future__ import annotations
import json
import math
import os
from pathlib import Path
import tempfile


def number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def build_mesh(params: dict) -> tuple[list[tuple], list[tuple]]:
    """Loft rectangular teaching sections; coordinates in metres, twist in degrees.

    z = span, x = chord, y = thickness. Twist pivots around quarter-chord.
    Four vertices per station; all faces are triangles, with closed end caps.
    """
    if params.get("version") != "1.0" or params.get("synthetic") is not True:
        raise ValueError("requires version 1.0 synthetic parameters")
    length = number(params.get("length_m"), "length_m")
    ratio = number(params.get("thickness_ratio", 0.12), "thickness_ratio")
    stations = params.get("stations")
    if length <= 0 or not 0 < ratio <= 1 or not isinstance(stations, list) or len(stations) < 2:
        raise ValueError("positive length, 0 < thickness_ratio <= 1 and at least two stations required")
    vertices, faces = [], []
    previous = -1.0
    for station in stations:
        if not isinstance(station, dict):
            raise ValueError("station must be an object")
        z = number(station.get("span_m"), "span_m")
        chord = number(station.get("chord_m"), "chord_m")
        angle = math.radians(number(station.get("twist_deg"), "twist_deg"))
        if not 0 <= z <= length or z <= previous or chord <= 0:
            raise ValueError("spans must increase within the length; chord must be positive")
        previous = z
        for x, y in ((-0.25*chord,-0.5*ratio*chord),(0.75*chord,-0.5*ratio*chord),
                     (0.75*chord,0.5*ratio*chord),(-0.25*chord,0.5*ratio*chord)):
            vertices.append((x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle), z))
    if vertices[0][2] != 0 or vertices[-1][2] != length:
        raise ValueError("first and last stations must be at 0 and length_m")
    for i in range(len(stations)-1):
        for j in range(4):
            a, b = 4*i+j+1, 4*i+(j+1)%4+1
            c, d = b+4, a+4
            faces.extend(((a,b,c),(a,c,d)))
    last = len(vertices)-4
    faces.extend(((1,3,2),(1,4,3),(last+1,last+2,last+3),(last+1,last+3,last+4)))
    return vertices, faces


def load_study(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "1.0" or data.get("synthetic") is not True:
        raise ValueError("requires version 1.0 synthetic study_result.json")
    value = number(data.get("annual_energy_kwh_estimate"), "annual_energy_kwh_estimate")
    if value < 0:
        raise ValueError("annual energy estimate cannot be negative")
    return data


def export_obj(params_path: str | Path, output: str | Path, study_path: str | Path | None = None) -> Path:
    params = json.loads(Path(params_path).read_text(encoding="utf-8"))
    if not isinstance(params, dict):
        raise ValueError("parameters must be an object")
    vertices, faces = build_mesh(params)
    study = load_study(study_path) if study_path is not None else None
    lines = ["# Synthetic teaching blade; units: metres; not engineering geometry", "o blade_v1"]
    if study is not None:
        lines.append(f"# Synthetic annual energy estimate (kWh): {study['annual_energy_kwh_estimate']:.6f}")
    lines.extend("v " + " ".join(f"{v:.9f}" for v in vertex) for vertex in vertices)
    lines.extend("f " + " ".join(map(str, face)) for face in faces)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=output.parent,
                                         prefix=".mesh-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write("\n".join(lines) + "\n")
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output
