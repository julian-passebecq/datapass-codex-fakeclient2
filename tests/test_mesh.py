import copy
import json
import math
from pathlib import Path
import subprocess
import sys
from collections import Counter
import pytest
from blade3d import build_mesh, export_obj, load_study

ROOT=Path(__file__).resolve().parents[1]
PARAMS=ROOT/"params/blade_v1.json"


def test_vertex_triangle_counts_and_closed_surface():
    vertices,faces=build_mesh(json.loads(PARAMS.read_text()))
    assert len(vertices)==16 and len(faces)==28
    edges=Counter(tuple(sorted((f[i],f[(i+1)%3]))) for f in faces for i in range(3))
    assert set(edges.values())=={2}
    assert all(1<=i<=len(vertices) for f in faces for i in f)


def test_bounds_and_zero_twist():
    params=json.loads(PARAMS.read_text())
    for s in params["stations"]: s["twist_deg"]=0
    v,_=build_mesh(params)
    assert min(p[2] for p in v)==0 and max(p[2] for p in v)==3
    assert min(p[0] for p in v)==pytest.approx(-0.15)
    assert max(p[0] for p in v)==pytest.approx(0.45)
    assert max(abs(p[1]) for p in v)==pytest.approx(0.036)


def test_invalid_parameters():
    original=json.loads(PARAMS.read_text())
    bad=[]
    for key,value in (("length_m",-1),("length_m",True),("thickness_ratio",0),("version","2.0"),("synthetic",False)):
        p=copy.deepcopy(original);p[key]=value;bad.append(p)
    for key,value in (("span_m",2),("chord_m",0),("twist_deg",float("nan"))):
        p=copy.deepcopy(original);p["stations"][0][key]=value;bad.append(p)
    for p in bad:
        with pytest.raises(ValueError):build_mesh(p)


def test_obj_written_and_optional_study_never_changes_geometry(tmp_path):
    a=export_obj(PARAMS,tmp_path/"a.obj")
    b=export_obj(PARAMS,tmp_path/"b.obj",ROOT/"fixtures/study_result.json")
    geom=lambda p:[line for line in p.read_text().splitlines() if not line.startswith("#")]
    assert geom(a)==geom(b) and len(geom(a))==45
    assert "Synthetic annual energy" in b.read_text()


def test_bad_study_preserves_previous_output(tmp_path):
    out=export_obj(PARAMS,tmp_path/"mesh.obj")
    before=out.read_bytes();bad=tmp_path/"bad.json"
    bad.write_text('{"version":"1.0","synthetic":false}')
    with pytest.raises(ValueError):export_obj(PARAMS,out,bad)
    assert out.read_bytes()==before and not list(tmp_path.glob(".mesh-*"))


def test_cli_and_repository_independence(tmp_path):
    subprocess.run([sys.executable,"-m","blade3d","--params",str(PARAMS),"--out",str(tmp_path/"blade.obj")],cwd=ROOT,check=True,capture_output=True)
    assert (tmp_path/"blade.obj").is_file()
    assert not (ROOT/".datapass").exists()
    assert load_study(ROOT/"fixtures/study_result.json")["synthetic"] is True
