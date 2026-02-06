from __future__ import annotations

import sys
from pathlib import Path
import open3d as o3d


def main():
    if len(sys.argv) < 2:
        print("usage: python o3d_viewer.py <path_to_ply/obj/stl>")
        sys.exit(2)

    p = Path(sys.argv[1])
    if not p.exists():
        print("file not found:", p)
        sys.exit(2)

    geom = None
    suf = p.suffix.lower()
    if suf in (".ply", ".pcd"):
        geom = o3d.io.read_point_cloud(str(p))
    elif suf in (".obj", ".stl"):
        geom = o3d.io.read_triangle_mesh(str(p))
        if geom is not None:
            geom.compute_vertex_normals()

    if geom is None:
        print("unsupported file:", p)
        sys.exit(2)

    o3d.visualization.draw_geometries([geom], window_name=f"Antares Viewer - {p.name}")


if __name__ == "__main__":
    main()
