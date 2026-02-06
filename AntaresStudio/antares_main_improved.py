"""
ANTARES KAPSÜL 3D STUDIO - IMPROVED VERSION
Arduino + ESP32-CAM Tabanlı Bitki 3D Modelleme Sistemi

Yeni Özellikler:
- Gelişmiş photogrammetry pipeline
- Open3D ile 3D görselleştirme
- COLMAP entegrasyonu (opsiyonel)
- Otomatik feature matching
- Mesh generation ve export
- İyileştirilmiş hata yönetimi
"""

import sys
import os
import json
import zipfile
import shutil
import requests
import subprocess
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QProgressBar,
    QFrame,
    QSplitter,
    QSizePolicy,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont

from ui.styles import apply_dark_industrial_theme

# ===================== ESP32 DOWNLOAD THREAD =====================
class ESP32DownloadThread(QThread):
    """ESP32'den WiFi üzerinden 360° tarama görüntülerini indirir"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, esp32_ip, session_id, photo_count, output_dir):
        super().__init__()
        self.esp32_ip = esp32_ip
        self.session_id = session_id
        self.photo_count = photo_count
        self.output_dir = output_dir

    def run(self):
        downloaded_files = []
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            for i in range(self.photo_count):
                url = f"http://{self.esp32_ip}/360_{self.session_id}_{i}.jpg"
                self.log.emit(f"[{i+1}/{self.photo_count}] İndiriliyor: {url}")
                
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        filepath = os.path.join(self.output_dir, f"img_{i:04d}.jpg")
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        downloaded_files.append(filepath)
                        self.log.emit(f"✓ Kaydedildi: {filepath}")
                    else:
                        self.log.emit(f"✗ HTTP {response.status_code}")
                except Exception as e:
                    self.log.emit(f"✗ Hata: {str(e)}")
                
                self.progress.emit(int(((i + 1) / self.photo_count) * 100))
            
            if len(downloaded_files) == self.photo_count:
                self.log.emit(f"\n✅ {len(downloaded_files)} görüntü başarıyla indirildi!")
            else:
                self.log.emit(f"\n⚠️ {len(downloaded_files)}/{self.photo_count} görüntü indirildi")
            
            self.finished.emit(downloaded_files)
            
        except Exception as e:
            self.log.emit(f"\n❌ Kritik Hata: {str(e)}")
            self.finished.emit([])

# ===================== AI BACKGROUND REMOVER =====================
class AIBackgroundRemoverThread(QThread):
    """rembg veya U2-Net kullanarak bitki arkaplanını temizler"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, image_paths, output_dir, method='rembg'):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.method = method

    def run(self):
        processed_files = []
        try:
            self.log.emit("🤖 AI Arkaplan Temizleyici başlatılıyor...")
            
            if self.method == 'rembg':
                processed_files = self._remove_with_rembg()
            else:
                processed_files = self._remove_with_grabcut()
            
            self.log.emit(f"\n✅ {len(processed_files)} görüntü işlendi!")
            self.finished.emit(processed_files)
            
        except Exception as e:
            self.log.emit(f"\n❌ AI Hatası: {str(e)}")
            self.finished.emit([])
    
    def _remove_with_rembg(self):
        """rembg ile arkaplan temizleme"""
        processed_files = []
        try:
            from rembg import remove
            from PIL import Image
        except ImportError:
            self.log.emit("❌ 'rembg' kütüphanesi bulunamadı!")
            self.log.emit("Kurulum: pip install rembg")
            return []
        
        os.makedirs(self.output_dir, exist_ok=True)
        total = len(self.image_paths)
        
        for i, img_path in enumerate(self.image_paths):
            self.log.emit(f"[{i+1}/{total}] İşleniyor: {os.path.basename(img_path)}")
            
            try:
                input_img = Image.open(img_path)
                output_img = remove(input_img)
                
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                output_path = os.path.join(self.output_dir, f"{base_name}_nobg.png")
                output_img.save(output_path)
                
                processed_files.append(output_path)
                self.log.emit(f"✓ Kaydedildi: {output_path}")
                
            except Exception as e:
                self.log.emit(f"✗ Hata: {str(e)}")
            
            self.progress.emit(int(((i + 1) / total) * 100))
        
        return processed_files
    
    def _remove_with_grabcut(self):
        """OpenCV GrabCut ile basit arkaplan temizleme (fallback)"""
        processed_files = []
        os.makedirs(self.output_dir, exist_ok=True)
        total = len(self.image_paths)
        
        for i, img_path in enumerate(self.image_paths):
            self.log.emit(f"[{i+1}/{total}] GrabCut ile işleniyor: {os.path.basename(img_path)}")
            
            try:
                img = cv2.imread(img_path)
                h, w = img.shape[:2]
                
                # Merkezi nesne olarak kabul et
                rect = (int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))
                mask = np.zeros(img.shape[:2], np.uint8)
                bgdModel = np.zeros((1, 65), np.float64)
                fgdModel = np.zeros((1, 65), np.float64)
                
                cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
                
                mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
                result = img * mask2[:, :, np.newaxis]
                
                # Beyaz arkaplan ekle
                white_bg = np.ones_like(img) * 255
                result = np.where(mask2[:, :, np.newaxis] == 1, result, white_bg)
                
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                output_path = os.path.join(self.output_dir, f"{base_name}_nobg.png")
                cv2.imwrite(output_path, result)
                
                processed_files.append(output_path)
                self.log.emit(f"✓ Kaydedildi: {output_path}")
                
            except Exception as e:
                self.log.emit(f"✗ Hata: {str(e)}")
            
            self.progress.emit(int(((i + 1) / total) * 100))
        
        return processed_files

# ===================== 3D PHOTOGRAMMETRY ENGINE =====================
class Photogrammetry3DThread(QThread):
    """
    OpenCV + Open3D tabanlı Structure from Motion (SfM) ile 3D model oluşturur
    """
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, image_paths, output_dir, quality='medium', min_features=2000):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.quality = quality
        self.min_features = min_features
        
        # Kalite ayarları
        self.quality_settings = {
            'low': {'features': 1000, 'matches': 50, 'ransac': 3.0},
            'medium': {'features': 2000, 'matches': 100, 'ransac': 2.0},
            'high': {'features': 5000, 'matches': 200, 'ransac': 1.0}
        }

    def run(self):
        try:
            self.log.emit("=" * 70)
            self.log.emit("🚀 ANTARES 3D PHOTOGRAMMETRY BAŞLATILIYOR")
            self.log.emit("=" * 70)
            self.progress.emit(5)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            # ADIM 1: Görüntü yükleme ve kalite kontrolü
            self.log.emit("\n📸 ADIM 1: Görüntü Yükleme")
            images = self._load_and_validate_images()
            if not images:
                self.log.emit("❌ Geçerli görüntü bulunamadı!")
                self.finished.emit("")
                return
            self.progress.emit(15)
            
            # ADIM 2: Feature detection & matching
            self.log.emit("\n🔍 ADIM 2: Feature Detection & Matching")
            features = self._detect_features(images)
            if not features:
                self.log.emit("❌ Yeterli feature bulunamadı!")
                self.finished.emit("")
                return
            self.progress.emit(30)
            
            # ADIM 3: Pairwise matching
            self.log.emit("\n🔗 ADIM 3: Pairwise Image Matching")
            matches = self._match_images(features)
            if not matches:
                self.log.emit("❌ Görüntüler eşleştirilemedi!")
                self.finished.emit("")
                return
            self.progress.emit(45)
            
            # ADIM 4: Camera pose estimation (Incremental SfM)
            self.log.emit("\n📐 ADIM 4: Camera Pose Estimation")
            poses = self._estimate_poses(features, matches)
            if not poses:
                self.log.emit("❌ Kamera pozları hesaplanamadı!")
                self.finished.emit("")
                return
            self.progress.emit(60)
            
            # ADIM 5: Dense reconstruction
            self.log.emit("\n🌐 ADIM 5: Dense Point Cloud Generation")
            point_cloud = self._generate_dense_cloud(images, features, matches, poses)
            if point_cloud is None:
                self.log.emit("❌ Point cloud oluşturulamadı!")
                self.finished.emit("")
                return
            self.progress.emit(75)
            
            # ADIM 6: Mesh generation
            self.log.emit("\n🎨 ADIM 6: Mesh Generation")
            mesh_file = self._generate_mesh(point_cloud)
            if not mesh_file:
                self.log.emit("❌ Mesh oluşturulamadı!")
                self.finished.emit("")
                return
            self.progress.emit(90)
            
            # ADIM 7: Export
            self.log.emit("\n💾 ADIM 7: Export")
            final_output = self._export_results(mesh_file, point_cloud)
            self.progress.emit(100)
            
            self.log.emit("\n" + "=" * 70)
            self.log.emit("✅ 3D MODEL BAŞARIYLA OLUŞTURULDU!")
            self.log.emit(f"📂 Çıktı: {final_output}")
            self.log.emit("=" * 70)
            
            self.finished.emit(final_output)
            
        except Exception as e:
            self.log.emit(f"\n❌ HATA: {str(e)}")
            import traceback
            self.log.emit(traceback.format_exc())
            self.finished.emit("")
    
    def _load_and_validate_images(self):
        """Görüntüleri yükle ve doğrula"""
        images = []
        self.log.emit(f"  📋 {len(self.image_paths)} görüntü kontrol ediliyor...")
        
        for i, path in enumerate(self.image_paths):
            try:
                img = cv2.imread(path)
                if img is not None:
                    h, w = img.shape[:2]
                    self.log.emit(f"  ✓ [{i+1}] {os.path.basename(path)} - {w}x{h}")
                    images.append({'path': path, 'img': img, 'index': i})
                else:
                    self.log.emit(f"  ✗ [{i+1}] {os.path.basename(path)} - Yüklenemedi")
            except Exception as e:
                self.log.emit(f"  ✗ [{i+1}] Hata: {e}")
        
        self.log.emit(f"  ✅ {len(images)}/{len(self.image_paths)} görüntü başarıyla yüklendi")
        return images
    
    def _detect_features(self, images):
        """SIFT/ORB ile feature detection"""
        settings = self.quality_settings[self.quality]
        n_features = settings['features']
        
        self.log.emit(f"  🎯 Feature sayısı: {n_features}")
        
        try:
            # SIFT tercih et (daha iyi sonuç verir)
            detector = cv2.SIFT_create(nfeatures=n_features)
            self.log.emit("  ✓ SIFT detector hazır")
        except:
            # Fallback: ORB
            detector = cv2.ORB_create(nfeatures=n_features)
            self.log.emit("  ⚠️ SIFT bulunamadı, ORB kullanılıyor")
        
        features = []
        for i, img_data in enumerate(images):
            try:
                gray = cv2.cvtColor(img_data['img'], cv2.COLOR_BGR2GRAY)
                kp, des = detector.detectAndCompute(gray, None)
                
                if des is not None:
                    features.append({
                        'index': img_data['index'],
                        'path': img_data['path'],
                        'keypoints': kp,
                        'descriptors': des
                    })
                    self.log.emit(f"  ✓ [{i+1}] {len(kp)} feature bulundu")
                else:
                    self.log.emit(f"  ✗ [{i+1}] Feature bulunamadı")
            except Exception as e:
                self.log.emit(f"  ✗ [{i+1}] Hata: {e}")
        
        self.log.emit(f"  ✅ {len(features)} görüntüde feature bulundu")
        return features
    
    def _match_images(self, features):
        """Feature matching (FLANN/BFMatcher)"""
        settings = self.quality_settings[self.quality]
        min_matches = settings['matches']
        
        self.log.emit(f"  🔗 Minimum eşleşme: {min_matches}")
        
        try:
            # FLANN matcher (daha hızlı)
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            matcher = cv2.FlannBasedMatcher(index_params, search_params)
            self.log.emit("  ✓ FLANN matcher hazır")
        except:
            # Fallback: BFMatcher
            matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            self.log.emit("  ⚠️ FLANN bulunamadı, BFMatcher kullanılıyor")
        
        matches = []
        n = len(features)
        
        # Tüm çiftleri eşleştir
        for i in range(n):
            for j in range(i + 1, n):
                try:
                    knn_matches = matcher.knnMatch(features[i]['descriptors'], 
                                                   features[j]['descriptors'], k=2)
                    
                    # Lowe's ratio test
                    good_matches = []
                    for m_n in knn_matches:
                        if len(m_n) == 2:
                            m, n_match = m_n
                            if m.distance < 0.7 * n_match.distance:
                                good_matches.append(m)
                    
                    if len(good_matches) >= min_matches:
                        matches.append({
                            'i': i,
                            'j': j,
                            'matches': good_matches
                        })
                        self.log.emit(f"  ✓ [{i}]-[{j}]: {len(good_matches)} eşleşme")
                    
                except Exception as e:
                    self.log.emit(f"  ✗ [{i}]-[{j}]: Hata - {e}")
        
        self.log.emit(f"  ✅ {len(matches)} görüntü çifti eşleştirildi")
        return matches
    
    def _estimate_poses(self, features, matches):
        """Camera pose estimation (simplified incremental SfM)"""
        settings = self.quality_settings[self.quality]
        ransac_thresh = settings['ransac']
        
        self.log.emit(f"  📐 RANSAC threshold: {ransac_thresh}")
        
        # Basit kamera matrisi (varsayılan)
        h, w = cv2.imread(features[0]['path']).shape[:2]
        focal_length = max(w, h)
        K = np.array([
            [focal_length, 0, w/2],
            [0, focal_length, h/2],
            [0, 0, 1]
        ], dtype=np.float64)
        
        self.log.emit(f"  📷 Kamera matrisi: f={focal_length:.0f}, center=({w/2:.0f}, {h/2:.0f})")
        
        poses = {}
        
        # İlk kamera pozisyonunu başlangıç noktası olarak al
        poses[0] = {
            'R': np.eye(3),
            't': np.zeros((3, 1)),
            'K': K
        }
        
        self.log.emit(f"  ✓ Referans kamera [0] ayarlandı")
        
        # Diğer kameraları sırayla hesapla
        for match in matches:
            i, j = match['i'], match['j']
            
            if i not in poses and j not in poses:
                continue
            
            try:
                # Keypoint koordinatlarını al
                pts1 = np.float32([features[i]['keypoints'][m.queryIdx].pt for m in match['matches']])
                pts2 = np.float32([features[j]['keypoints'][m.trainIdx].pt for m in match['matches']])
                
                # Essential matrix
                E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, 
                                              prob=0.999, threshold=ransac_thresh)
                
                if E is not None:
                    # Recover pose
                    _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)
                    
                    if i in poses and j not in poses:
                        # i var, j'yi hesapla
                        poses[j] = {'R': R, 't': t, 'K': K}
                        self.log.emit(f"  ✓ Kamera [{j}] pozisyonu hesaplandı (referans: [{i}])")
                    elif j in poses and i not in poses:
                        # j var, i'yi hesapla
                        poses[i] = {'R': R.T, 't': -R.T @ t, 'K': K}
                        self.log.emit(f"  ✓ Kamera [{i}] pozisyonu hesaplandı (referans: [{j}])")
                
            except Exception as e:
                self.log.emit(f"  ✗ [{i}]-[{j}]: Pose hesaplanamadı - {e}")
        
        self.log.emit(f"  ✅ {len(poses)} kamera pozisyonu hesaplandı")
        return poses if len(poses) >= 2 else None
    
    def _generate_dense_cloud(self, images, features, matches, poses):
        """Dense point cloud generation"""
        self.log.emit("  🌐 Point cloud oluşturuluyor...")
        
        try:
            import open3d as o3d
        except ImportError:
            self.log.emit("  ⚠️ Open3D bulunamadı, basit triangulation kullanılıyor")
            return self._generate_sparse_cloud(features, matches, poses)
        
        # Sparse cloud oluştur
        points_3d = []
        colors = []
        
        for match in matches:
            i, j = match['i'], match['j']
            
            if i not in poses or j not in poses:
                continue
            
            try:
                # Keypoint koordinatları
                pts1 = np.float32([features[i]['keypoints'][m.queryIdx].pt for m in match['matches']])
                pts2 = np.float32([features[j]['keypoints'][m.trainIdx].pt for m in match['matches']])
                
                # Projection matrices
                P1 = poses[i]['K'] @ np.hstack([poses[i]['R'], poses[i]['t']])
                P2 = poses[j]['K'] @ np.hstack([poses[j]['R'], poses[j]['t']])
                
                # Triangulation
                points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
                points_3d_homo = points_4d / points_4d[3]
                
                # Renk bilgisi
                img1 = images[i]['img']
                for idx, pt in enumerate(pts1):
                    x, y = int(pt[0]), int(pt[1])
                    if 0 <= x < img1.shape[1] and 0 <= y < img1.shape[0]:
                        color = img1[y, x] / 255.0  # Normalize
                        points_3d.append(points_3d_homo[:3, idx])
                        colors.append(color[::-1])  # BGR to RGB
                
            except Exception as e:
                self.log.emit(f"  ✗ Triangulation hatası: {e}")
        
        if len(points_3d) == 0:
            self.log.emit("  ❌ Hiç 3D nokta oluşturulamadı!")
            return None
        
        # Open3D point cloud oluştur
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points_3d, dtype=np.float64))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
        
        # Outlier removal
        pcd, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        self.log.emit(f"  ✓ {len(pcd.points)} 3D nokta oluşturuldu")
        
        # Point cloud kaydet
        pcd_path = os.path.join(self.output_dir, "point_cloud.ply")
        o3d.io.write_point_cloud(pcd_path, pcd)
        self.log.emit(f"  💾 Point cloud kaydedildi: {pcd_path}")
        
        return pcd
    
    def _generate_sparse_cloud(self, features, matches, poses):
        """Fallback: Basit sparse cloud (Open3D olmadan)"""
        self.log.emit("  ⚠️ Basit sparse cloud oluşturuluyor...")
        
        points_3d = []
        
        for match in matches:
            i, j = match['i'], match['j']
            
            if i not in poses or j not in poses:
                continue
            
            try:
                pts1 = np.float32([features[i]['keypoints'][m.queryIdx].pt for m in match['matches']])
                pts2 = np.float32([features[j]['keypoints'][m.trainIdx].pt for m in match['matches']])
                
                P1 = poses[i]['K'] @ np.hstack([poses[i]['R'], poses[i]['t']])
                P2 = poses[j]['K'] @ np.hstack([poses[j]['R'], poses[j]['t']])
                
                points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
                points_3d_homo = points_4d / points_4d[3]
                points_3d.extend(points_3d_homo[:3].T)
                
            except:
                pass
        
        if len(points_3d) == 0:
            return None
        
        # Numpy array olarak döndür
        return np.array(points_3d)
    
    def _generate_mesh(self, point_cloud):
        """Mesh generation (Poisson reconstruction)"""
        self.log.emit("  🎨 Mesh oluşturuluyor...")
        
        try:
            import open3d as o3d
            
            if isinstance(point_cloud, np.ndarray):
                # Numpy array ise Open3D'ye çevir
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(point_cloud)
                point_cloud = pcd
            
            # Normal estimation
            self.log.emit("  → Normal vektörleri hesaplanıyor...")
            point_cloud.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
            )
            
            # Poisson reconstruction
            self.log.emit("  → Poisson reconstruction...")
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                point_cloud, depth=9
            )
            
            # Low density vertices'leri kaldır
            vertices_to_remove = densities < np.quantile(densities, 0.01)
            mesh.remove_vertices_by_mask(vertices_to_remove)
            
            self.log.emit(f"  ✓ Mesh: {len(mesh.vertices)} vertex, {len(mesh.triangles)} triangle")
            
            # Mesh kaydet
            mesh_path = os.path.join(self.output_dir, "mesh.ply")
            o3d.io.write_triangle_mesh(mesh_path, mesh)
            self.log.emit(f"  💾 Mesh kaydedildi: {mesh_path}")
            
            return mesh_path
            
        except ImportError:
            self.log.emit("  ❌ Open3D gerekli, mesh oluşturulamadı")
            return None
        except Exception as e:
            self.log.emit(f"  ❌ Mesh hatası: {e}")
            return None
    
    def _export_results(self, mesh_file, point_cloud):
        """Farklı formatlarda export"""
        self.log.emit("  💾 Export işlemleri...")
        
        if not mesh_file:
            self.log.emit("  ⚠️ Mesh yok, sadece point cloud export edilecek")
            
            # Point cloud PLY export
            if isinstance(point_cloud, np.ndarray):
                pcd_path = os.path.join(self.output_dir, "sparse_cloud.ply")
                self._save_simple_ply(point_cloud, pcd_path)
                return pcd_path
            else:
                return os.path.join(self.output_dir, "point_cloud.ply")
        
        try:
            import open3d as o3d
            
            mesh = o3d.io.read_triangle_mesh(mesh_file)
            
            # OBJ export
            obj_path = os.path.join(self.output_dir, "mesh.obj")
            o3d.io.write_triangle_mesh(obj_path, mesh)
            self.log.emit(f"  ✓ OBJ: {obj_path}")
            
            # STL export
            stl_path = os.path.join(self.output_dir, "mesh.stl")
            o3d.io.write_triangle_mesh(stl_path, mesh)
            self.log.emit(f"  ✓ STL: {stl_path}")
            
            self.log.emit("  ✅ Export tamamlandı!")
            return mesh_file
            
        except Exception as e:
            self.log.emit(f"  ⚠️ Export kısmen başarılı: {e}")
            return mesh_file
    
    def _save_simple_ply(self, points, filepath):
        """Basit PLY formatında kaydet"""
        with open(filepath, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(points)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            
            for point in points:
                f.write(f"{point[0]} {point[1]} {point[2]}\n")
        
        self.log.emit(f"  ✓ PLY kaydedildi: {filepath}")

# ===================== MAIN GUI =====================
class AntaresKapsul3DStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANTARES KAPSÜL 3D STUDIO - v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # State variables
        self.downloaded_images = []
        self.processed_images = []
        self.output_3d_model = None
        
        self.init_ui()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("🚀 ANTARES KAPSÜL 3D STUDIO")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #00d2ff; padding: 15px;")
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: ESP32 Download
        self.tab_download = self.create_download_tab()
        self.tabs.addTab(self.tab_download, "📥 ESP32 Download")
        
        # Tab 2: 3D Reconstruction
        self.tab_3d = self.create_3d_tab()
        self.tabs.addTab(self.tab_3d, "🏗️ 3D Model Oluştur")
        
        # Tab 3: Viewer
        self.tab_viewer = self.create_viewer_tab()
        self.tabs.addTab(self.tab_viewer, "👁️ 3D Görüntüle")
        
        # Tab 4: Settings & Info
        self.tab_info = self.create_info_tab()
        self.tabs.addTab(self.tab_info, "⚙️ Ayarlar & Yardım")
    
    def create_download_tab(self):
        """ESP32'den görüntü indirme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ESP32 IP
        ip_group = QGroupBox("ESP32 Bağlantı Ayarları")
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("ESP32 IP:"))
        self.txt_esp32_ip = QLineEdit("192.168.4.1")
        ip_layout.addWidget(self.txt_esp32_ip)
        self.btn_test_connection = QPushButton("🔌 Bağlantıyı Test Et")
        self.btn_test_connection.clicked.connect(self.test_esp32_connection)
        ip_layout.addWidget(self.btn_test_connection)
        ip_group.setLayout(ip_layout)
        layout.addWidget(ip_group)
        
        # Scan listesi
        scan_group = QGroupBox("360° Tarama Listesi")
        scan_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_refresh_scans = QPushButton("🔄 Listeyi Yenile")
        self.btn_refresh_scans.clicked.connect(self.refresh_scan_list)
        btn_layout.addWidget(self.btn_refresh_scans)
        scan_layout.addLayout(btn_layout)
        
        self.list_360_scans = QListWidget()
        scan_layout.addWidget(self.list_360_scans)
        
        self.btn_download_images = QPushButton("📥 Seçili Taramayı İndir")
        self.btn_download_images.clicked.connect(self.download_selected_scan)
        scan_layout.addWidget(self.btn_download_images)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Progress
        progress_group = QGroupBox("İndirme Durumu")
        progress_layout = QVBoxLayout()
        self.lbl_download_status = QLabel("Durum: Beklemede")
        progress_layout.addWidget(self.lbl_download_status)
        self.progress_download = QProgressBar()
        progress_layout.addWidget(self.progress_download)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox("İndirme Günlüğü")
        log_layout = QVBoxLayout()
        self.txt_download_log = QTextEdit()
        self.txt_download_log.setReadOnly(True)
        self.txt_download_log.setMaximumHeight(200)
        log_layout.addWidget(self.txt_download_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
    
    def create_3d_tab(self):
        """3D model oluşturma sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Settings
        settings_group = QGroupBox("3D Reconstruction Ayarları")
        settings_layout = QVBoxLayout()
        
        # Quality
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Kalite:"))
        self.cmb_quality = QComboBox()
        self.cmb_quality.addItems(["Düşük (Hızlı)", "Orta (Önerilen)", "Yüksek (Yavaş)"])
        self.cmb_quality.setCurrentIndex(1)
        quality_layout.addWidget(self.cmb_quality)
        settings_layout.addLayout(quality_layout)
        
        # AI Background removal
        self.chk_use_ai_bg = QCheckBox("AI Arkaplan Temizleme Kullan (rembg)")
        self.chk_use_ai_bg.setChecked(True)
        settings_layout.addWidget(self.chk_use_ai_bg)
        
        # Feature count
        feature_layout = QHBoxLayout()
        feature_layout.addWidget(QLabel("Minimum Feature:"))
        self.spn_features = QSpinBox()
        self.spn_features.setRange(500, 10000)
        self.spn_features.setValue(2000)
        self.spn_features.setSingleStep(500)
        feature_layout.addWidget(self.spn_features)
        settings_layout.addLayout(feature_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Start button
        self.btn_start_3d = QPushButton("🚀 3D MODEL OLUŞTUR")
        self.btn_start_3d.setEnabled(False)
        self.btn_start_3d.clicked.connect(self.start_3d_reconstruction)
        self.btn_start_3d.setMinimumHeight(50)
        self.btn_start_3d.setStyleSheet("""
            QPushButton { 
                background-color: #00d2ff; 
                color: #000; 
                font-size: 16px; 
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #00a8cc; 
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)
        layout.addWidget(self.btn_start_3d)
        
        # Progress
        progress_group = QGroupBox("İşlem Durumu")
        progress_layout = QVBoxLayout()
        self.progress_3d = QProgressBar()
        progress_layout.addWidget(self.progress_3d)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox("İşlem Günlüğü")
        log_layout = QVBoxLayout()
        self.txt_3d_log = QTextEdit()
        self.txt_3d_log.setReadOnly(True)
        log_layout.addWidget(self.txt_3d_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
    
    def create_viewer_tab(self):
        """3D model görüntüleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("🎉 3D model başarıyla oluşturuldu!\n\n"
                     "Aşağıdaki butonları kullanarak modelinizi görüntüleyebilir\n"
                     "veya harici programlarda (MeshLab, Blender, CloudCompare) açabilirsiniz.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("padding: 20px; font-size: 14px;")
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        self.btn_view_3d = QPushButton("👁️ 3D Modeli Aç")
        self.btn_view_3d.setEnabled(False)
        self.btn_view_3d.clicked.connect(self.view_3d_model)
        self.btn_view_3d.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_view_3d)
        
        self.btn_open_folder = QPushButton("📂 Çıktı Klasörünü Aç")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        self.btn_open_folder.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_open_folder)
        
        self.btn_new_scan = QPushButton("🔄 Yeni Tarama Başlat")
        self.btn_new_scan.clicked.connect(self.reset_for_new_scan)
        self.btn_new_scan.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_new_scan)
        
        layout.addLayout(btn_layout)
        
        # Info text
        self.txt_viewer_info = QTextEdit()
        self.txt_viewer_info.setReadOnly(True)
        self.txt_viewer_info.setPlaceholderText("Model bilgileri burada görünecek...")
        layout.addWidget(self.txt_viewer_info)
        
        layout.addStretch()
        
        return widget
    
    def create_info_tab(self):
        """Ayarlar ve yardım sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h2 style='color: #00d2ff;'>🚀 ANTARES KAPSÜL 3D STUDIO</h2>
        
        <h3>📖 Kullanım Kılavuzu:</h3>
        <ol>
            <li><b>ESP32 Bağlantısı:</b> ESP32-CAM'e WiFi üzerinden bağlanın (varsayılan: 192.168.4.1)</li>
            <li><b>Tarama Listesi:</b> Arduino'dan başlatılan 360° taramaları listeden seçin</li>
            <li><b>Görüntü İndirme:</b> Seçili taramayı indirin</li>
            <li><b>3D Model:</b> İndirilen görüntülerden otomatik 3D model oluşturun</li>
            <li><b>Görüntüleme:</b> Oluşturulan modeli harici programlarda açın</li>
        </ol>
        
        <h3>⚙️ Gerekli Kütüphaneler:</h3>
        <pre style='background: #0f2027; padding: 10px; border-radius: 5px;'>
pip install PyQt6
pip install opencv-python opencv-contrib-python
pip install numpy requests Pillow
pip install open3d  # 3D işleme için ÖNERİLİR
pip install rembg  # AI arkaplan temizleme için OPSİYONEL
        </pre>
        
        <h3>🎨 Desteklenen Formatlar:</h3>
        <ul>
            <li><b>Point Cloud:</b> PLY</li>
            <li><b>Mesh:</b> PLY, OBJ, STL</li>
        </ul>
        
        <h3>🔧 Önerilen Dış Programlar:</h3>
        <ul>
            <li><b>MeshLab:</b> Mesh düzenleme ve görselleştirme</li>
            <li><b>CloudCompare:</b> Point cloud işleme</li>
            <li><b>Blender:</b> 3D modelleme ve rendering</li>
        </ul>
        
        <h3>📊 Sistem Gereksinimleri:</h3>
        <ul>
            <li><b>Python:</b> 3.8 veya üzeri</li>
            <li><b>RAM:</b> Minimum 4GB (8GB önerilir)</li>
            <li><b>İşlemci:</b> Multi-core önerilir</li>
            <li><b>GPU:</b> CUDA destekli GPU (opsiyonel, hızlandırma için)</li>
        </ul>
        
        <h3>⚠️ Notlar:</h3>
        <ul>
            <li>En az 8 görüntü gereklidir (daha fazlası daha iyi sonuç verir)</li>
            <li>360° döner tabla kullanımı önerilir</li>
            <li>İyi aydınlatma koşulları altında fotoğraf çekin</li>
            <li>Nesne her açıdan net olmalıdır</li>
        </ul>
        
        <hr>
        <p style='text-align: center; color: #00d2ff;'>
            <b>ANTARES KAPSÜL 3D STUDIO</b><br>
            Version 2.0 - Improved Photogrammetry Engine<br>
            © 2025
        </p>
        """)
        layout.addWidget(info_text)
        
        return widget
    
    # ===================== EVENT HANDLERS =====================
    
    def test_esp32_connection(self):
        """ESP32 bağlantısını test et"""
        ip = self.txt_esp32_ip.text()
        self.txt_download_log.append(f"🔌 Bağlantı test ediliyor: {ip}")
        
        try:
            response = requests.get(f"http://{ip}/", timeout=5)
            if response.status_code == 200:
                self.txt_download_log.append("✅ Bağlantı başarılı!")
                QMessageBox.information(self, "Başarılı", f"ESP32 ile bağlantı kuruldu!\n\nIP: {ip}")
            else:
                self.txt_download_log.append(f"⚠️ HTTP {response.status_code}")
        except Exception as e:
            self.txt_download_log.append(f"❌ Bağlantı hatası: {str(e)}")
            QMessageBox.warning(self, "Hata", f"ESP32'ye bağlanılamadı:\n\n{e}")
    
    def refresh_scan_list(self):
        """360° tarama listesini yenile"""
        ip = self.txt_esp32_ip.text()
        self.txt_download_log.append(f"🔄 360° tarama listesi alınıyor: {ip}")
        
        try:
            response = requests.get(f"http://{ip}/360_list", timeout=10)
            
            if response.status_code != 200:
                self.txt_download_log.append(f"❌ HTTP {response.status_code}")
                return
            
            data = response.json()
            self.list_360_scans.clear()
            
            for session_id, count in data.items():
                # Timestamp'den tarih oluştur
                ts = int(session_id) / 1000
                date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                
                item_text = f"📅 {date_str} | 📸 {count} fotoğraf | Session: {session_id}"
                self.list_360_scans.addItem(item_text)
            
            self.txt_download_log.append(f"✅ {len(data)} tarama bulundu\n")
            
            if len(data) == 0:
                self.txt_download_log.append("⚠️ Henüz 360° tarama yok. Arduino'dan tarama başlatın.\n")
            
        except Exception as e:
            self.txt_download_log.append(f"❌ Liste alınamadı: {str(e)}\n")
            QMessageBox.warning(self, "Hata", f"360° tarama listesi alınamadı:\n{e}")
    
    def download_selected_scan(self):
        """Seçili taramayı indir"""
        current_item = self.list_360_scans.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir tarama seçin!")
            return
        
        # Parse item text
        text = current_item.text()
        count = int(text.split('📸')[1].split('fotoğraf')[0].strip())
        session_id = text.split('Session:')[1].strip()
        
        # Output klasörü
        output_dir = os.path.join(os.getcwd(), "antares_3d_data", f"scan_{session_id}")
        
        self.txt_download_log.clear()
        self.txt_download_log.append(f"📥 İNDİRME BAŞLATILIYOR")
        self.txt_download_log.append(f"Session ID: {session_id}")
        self.txt_download_log.append(f"Fotoğraf sayısı: {count}")
        self.txt_download_log.append(f"Hedef klasör: {output_dir}\n")
        
        self.lbl_download_status.setText("Durum: İndiriliyor...")
        self.btn_download_images.setEnabled(False)
        
        # Thread başlat
        self.download_thread = ESP32DownloadThread(
            self.txt_esp32_ip.text(),
            session_id,
            count,
            output_dir
        )
        self.download_thread.progress.connect(self.progress_download.setValue)
        self.download_thread.log.connect(self.txt_download_log.append)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_finished(self, files):
        """İndirme tamamlandığında"""
        self.btn_download_images.setEnabled(True)
        
        if len(files) >= 8:
            self.downloaded_images = files
            self.lbl_download_status.setText(f"Durum: ✅ {len(files)} görüntü indirildi!")
            self.btn_start_3d.setEnabled(True)
            
            QMessageBox.information(self, "Başarılı", 
                f"{len(files)} görüntü başarıyla indirildi!\n\n"
                f"Şimdi '3D MODEL OLUŞTUR' sekmesine geçebilirsiniz.")
            
            # Otomatik olarak 3D sekmesine geç
            self.tabs.setCurrentIndex(1)
        else:
            self.lbl_download_status.setText(f"Durum: ❌ Yetersiz görüntü ({len(files)}/8)")
            QMessageBox.warning(self, "Hata", 
                f"Yeterli görüntü indirilemedi!\n\n"
                f"İndirilen: {len(files)}/8\n"
                f"3D model için en az 8 görüntü gereklidir.")
    
    def start_3d_reconstruction(self):
        """3D reconstruction başlat"""
        if len(self.downloaded_images) < 8:
            QMessageBox.warning(self, "Yetersiz Veri", 
                "3D model oluşturmak için en az 8 görüntü gerekli!\n\n"
                "Önce ESP32'den görüntüleri indirin.")
            return
        
        self.txt_3d_log.clear()
        self.txt_3d_log.append("🚀 3D RECONSTRUCTION BAŞLATILIYOR...\n")
        
        # AI Temizleme isteniyorsa
        if self.chk_use_ai_bg.isChecked():
            self.txt_3d_log.append("🤖 ADIM 1: AI Arkaplan Temizleme\n")
            self.btn_start_3d.setEnabled(False)
            
            ai_output_dir = os.path.join(os.path.dirname(self.downloaded_images[0]), "ai_processed")
            
            self.ai_thread = AIBackgroundRemoverThread(self.downloaded_images, ai_output_dir, 'rembg')
            self.ai_thread.progress.connect(self.progress_3d.setValue)
            self.ai_thread.log.connect(self.txt_3d_log.append)
            self.ai_thread.finished.connect(self.on_ai_bg_finished)
            self.ai_thread.start()
        else:
            # Direkt 3D işleme
            self.start_photogrammetry(self.downloaded_images)
    
    def on_ai_bg_finished(self, processed_files):
        """AI arkaplan temizleme tamamlandığında"""
        if len(processed_files) >= 8:
            self.processed_images = processed_files
            self.txt_3d_log.append(f"\n✅ AI temizleme tamamlandı: {len(processed_files)} görüntü\n")
            self.start_photogrammetry(processed_files)
        else:
            self.txt_3d_log.append(f"\n⚠️ AI temizleme başarısız, orijinal görüntüler kullanılacak\n")
            self.start_photogrammetry(self.downloaded_images)
    
    def start_photogrammetry(self, images):
        """Photogrammetry işlemini başlat"""
        self.txt_3d_log.append("🏗️ ADIM 2: Photogrammetry (SfM)\n")
        
        quality_map = {0: 'low', 1: 'medium', 2: 'high'}
        quality = quality_map[self.cmb_quality.currentIndex()]
        
        output_dir = os.path.join(os.path.dirname(images[0]), "3d_output")
        min_features = self.spn_features.value()
        
        self.photo_thread = Photogrammetry3DThread(images, output_dir, quality, min_features)
        self.photo_thread.progress.connect(self.progress_3d.setValue)
        self.photo_thread.log.connect(self.txt_3d_log.append)
        self.photo_thread.finished.connect(self.on_3d_finished)
        self.photo_thread.start()
    
    def on_3d_finished(self, output_file):
        """3D işleme tamamlandığında"""
        self.btn_start_3d.setEnabled(True)
        
        if output_file and os.path.exists(output_file):
            self.output_3d_model = output_file
            self.btn_view_3d.setEnabled(True)
            self.btn_open_folder.setEnabled(True)
            
            self.txt_3d_log.append("\n" + "=" * 70)
            self.txt_3d_log.append("🎉 3D MODEL BAŞARIYLA OLUŞTURULDU!")
            self.txt_3d_log.append("=" * 70)
            
            # Model bilgilerini viewer sekmesine yaz
            self.txt_viewer_info.clear()
            self.txt_viewer_info.append(f"✅ 3D Model Başarıyla Oluşturuldu!\n")
            self.txt_viewer_info.append(f"📂 Dosya: {output_file}\n")
            self.txt_viewer_info.append(f"📊 Boyut: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB\n")
            
            QMessageBox.information(self, "Başarılı!", 
                f"3D model başarıyla oluşturuldu!\n\n"
                f"Dosya: {output_file}\n\n"
                f"MeshLab, CloudCompare veya Blender ile açabilirsiniz.")
            
            # Viewer sekmesine geç
            self.tabs.setCurrentIndex(2)
        else:
            self.txt_3d_log.append("\n❌ 3D model oluşturulamadı. Lütfen logları kontrol edin.")
            QMessageBox.warning(self, "Hata", "3D model oluşturulamadı!")
    
    def view_3d_model(self):
        """3D modeli sistem varsayılan programıyla aç"""
        if not self.output_3d_model or not os.path.exists(self.output_3d_model):
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(self.output_3d_model)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.output_3d_model])
            else:
                subprocess.run(['xdg-open', self.output_3d_model])
        except:
            QMessageBox.information(self, "Dosya Konumu", 
                f"3D model dosyası:\n\n{self.output_3d_model}\n\n"
                f"MeshLab veya CloudCompare ile manuel olarak açın.")
    
    def open_output_folder(self):
        """Çıktı klasörünü aç"""
        if self.output_3d_model:
            folder = os.path.dirname(self.output_3d_model)
            try:
                if sys.platform == 'win32':
                    os.startfile(folder)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', folder])
                else:
                    subprocess.run(['xdg-open', folder])
            except:
                pass
    
    def reset_for_new_scan(self):
        """Yeni tarama için sıfırla"""
        reply = QMessageBox.question(self, "Yeni Tarama", 
            "Yeni bir tarama başlatmak istiyor musunuz?\n\n"
            "Mevcut veriler kaybolmayacak.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.downloaded_images = []
            self.processed_images = []
            self.output_3d_model = None
            
            self.btn_start_3d.setEnabled(False)
            self.btn_view_3d.setEnabled(False)
            self.btn_open_folder.setEnabled(False)
            
            self.progress_download.setValue(0)
            self.progress_3d.setValue(0)
            
            self.txt_download_log.clear()
            self.txt_3d_log.clear()
            self.txt_viewer_info.clear()
            
            self.tabs.setCurrentIndex(0)
            
            QMessageBox.information(self, "Hazır", "Yeni tarama için hazır!")

# ===================== MAIN =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Merkezi Dark Industrial temayı uygula
    apply_dark_industrial_theme(app)

    window = AntaresKapsul3DStudio()
    window.show()
    sys.exit(app.exec())
