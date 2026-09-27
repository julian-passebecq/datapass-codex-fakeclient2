import argparse
from pathlib import Path
from .mesh import export_obj


def main(argv=None):
    p = argparse.ArgumentParser(description="Synthetic blade OBJ generator")
    p.add_argument("--params", type=Path, default=Path("params/blade_v1.json"))
    p.add_argument("--out", type=Path, default=Path("out/blade_v1.obj"))
    p.add_argument("--study", type=Path)
    a = p.parse_args(argv)
    try:
        print(export_obj(a.params, a.out, a.study))
    except (OSError, ValueError, TypeError) as exc:
        p.exit(1, f"Mesh failed: {exc}\n")


if __name__ == "__main__":
    main()
