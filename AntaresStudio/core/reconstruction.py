from __future__ import annotations

import gc
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable

import numpy as np
import cv2
import open3d as o3d

from .processing_strategies import Mode, FeatureAlgo, FeatureConfig, create_detector, to_gray


@dataclass(frozen=True)
class ReconstructionResult:
    point_cloud_path: Path
    mesh_ply_path: Optional[Path]
    mesh_obj_path: Optional[Path]
    mesh_stl_path: Optional[Path]


def _match(desc1, desc2, algo: FeatureAlgo):
    if desc1 is None or desc2 is None:
        return []
    if algo in (FeatureAlgo.ORB, FeatureAlgo.AKAZE):
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    else:
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

    matches = bf.knnMatch(desc1, desc2, k=2)
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)
    return good


def reconstruct_sparse(
    bgr_images: List[np.ndarray],
    out_dir: Path,
    *,
    mode: Mode = Mode.FAST,
    progress_cb: Optional[Callable[[float], None]] = None,
    message_cb: Optional[Callable[[str], None]] = None,
    cancel_event=None
) -> ReconstructionResult:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Algo select
    algo = FeatureAlgo.ORB if mode == Mode.FAST else FeatureAlgo.SIFT
    cfg = FeatureConfig(algo=algo, max_features=4000)
    det = create_detector(cfg)

    # Intrinsics (rough)
    h, w = bgr_images[0].shape[:2]
    f = float(max(w, h))
    K = np.array([[f, 0, w / 2.0], [0, f, h / 2.0], [0, 0, 1.0]], dtype=np.float64)

    R_global = np.eye(3)
    t_global = np.zeros((3, 1))
    points_3d = []

    n_pairs = max(0, len(bgr_images) - 1)
    for i in range(n_pairs):
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("İşlem iptal edildi")

        if message_cb:
            message_cb(f"Eşleştirme: {i+1}/{n_pairs}")

        g1 = to_gray(bgr_images[i])
        g2 = to_gray(bgr_images[i + 1])

        kp1, des1 = det.detectAndCompute(g1, None)
        kp2, des2 = det.detectAndCompute(g2, None)

        good = _match(des1, des2, algo)
        if len(good) < 12:
            continue

        pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in good])

        E, inliers = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
        if E is None:
            continue

        in_mask = (inliers.ravel() > 0)
        pts1i = pts1[in_mask]
        pts2i = pts2[in_mask]

        if len(pts1i) < 10:
            continue

        _, R, t, _ = cv2.recoverPose(E, pts1i, pts2i, K)

        # Accumulate pose (simple chaining)
        R_global = R @ R_global
        t_global = t_global + (R_global @ t)

        P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
        P2 = K @ np.hstack([R_global, t_global])

        X_h = cv2.triangulatePoints(P1, P2, pts1i.T, pts2i.T)  # 4xN
        X = (X_h[:3, :] / (X_h[3, :] + 1e-9)).T  # Nx3

        # Filter finite
        X = X[np.isfinite(X).all(axis=1)]
        if len(X) > 0:
            points_3d.append(X)

        # Memory cleanup
        del g1, g2, kp1, kp2, des1, des2, good, pts1, pts2, pts1i, pts2i, X_h, X
        gc.collect()

        if progress_cb:
            progress_cb(100.0 * (i + 1) / max(1, n_pairs))

    if not points_3d:
        raise RuntimeError("Yeterli eşleşme bulunamadı. FAST yerine HQ deneyin veya daha net görseller kullanın.")

    pts = np.vstack(points_3d)
    # Normalize scale
    pts = pts - pts.mean(axis=0, keepdims=True)
    s = np.linalg.norm(pts, axis=1).mean()
    pts = pts / (s + 1e-9)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts.astype(np.float64))
    pcd.estimate_normals()

    point_cloud_path = out_dir / "point_cloud.ply"
    o3d.io.write_point_cloud(str(point_cloud_path), pcd, write_ascii=False, compressed=True)

    mesh_ply_path = mesh_obj_path = mesh_stl_path = None
    try:
        alpha = 0.08 if mode == Mode.FAST else 0.05
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
        mesh.compute_vertex_normals()

        mesh_ply_path = out_dir / "mesh.ply"
        mesh_obj_path = out_dir / "mesh.obj"
        mesh_stl_path = out_dir / "mesh.stl"

        o3d.io.write_triangle_mesh(str(mesh_ply_path), mesh, write_ascii=False, compressed=True)
        o3d.io.write_triangle_mesh(str(mesh_obj_path), mesh, write_ascii=False)
        o3d.io.write_triangle_mesh(str(mesh_stl_path), mesh, write_ascii=False)
    except Exception:
        # Mesh üretimi her zaman mümkün olmayabilir → point cloud yeterli
        pass

    return ReconstructionResult(
        point_cloud_path=point_cloud_path,
        mesh_ply_path=mesh_ply_path,
        mesh_obj_path=mesh_obj_path,
        mesh_stl_path=mesh_stl_path,
    )
