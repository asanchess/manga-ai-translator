# -*- coding: utf-8 -*-
"""
Unit Tests for Milestone M3:
1. ModelInferenceManager Singleton initialization, thread-safety, and dual-executor setup.
2. OCR Reader and Inpainting Engine access via inference singleton.
3. Chapter integrity auditor (layer parity, min 8 pages threshold, physical isolation).
4. Chapter deficit resolver (gutter-cut segmentation and mirror rotation).
5. Pipeline manifest v3.0.0 generation with SHA-256 checksums and quality metrics.
6. Chapter .zip translation archive generation.
7. Frontend public directory synchronization and chapters_index.json update.
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents")))

from model_inference_manager import (
    ModelInferenceManager,
    InpaintingEngine,
    get_inference_manager,
    get_ocr_reader,
    get_inpainting_engine
)
from chapter_integrity_checker import (
    ChapterIntegrityChecker,
    compute_file_sha256,
    find_optimal_gutter_cuts
)


class TestModelInferenceAndIntegrity(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="manga_test_m3_")
        self.public_dir = tempfile.mkdtemp(prefix="manga_pub_m3_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.public_dir, ignore_errors=True)

    def test_01_singleton_pattern_and_executors(self):
        """Verify ModelInferenceManager behaves as a thread-safe singleton with dual executors."""
        mgr1 = ModelInferenceManager.get_instance()
        mgr2 = ModelInferenceManager.get_instance()
        mgr3 = get_inference_manager()

        self.assertIs(mgr1, mgr2, "Multiple get_instance() calls must return identical singleton object.")
        self.assertIs(mgr2, mgr3, "get_inference_manager() helper must return identical singleton object.")

        # Verify dual executors
        self.assertIsNotNone(mgr1.io_executor)
        self.assertIsNotNone(mgr1.compute_executor)
        self.assertGreaterEqual(mgr1.io_executor._max_workers, 1)
        self.assertGreaterEqual(mgr1.compute_executor._max_workers, 1)
        print("  [PASS] test_01_singleton_pattern_and_executors: Singleton identity & dual executors verified.")

    def test_02_ocr_and_inpainting_engine_access(self):
        """Verify get_ocr_reader and get_inpainting_engine return active instances."""
        ocr_reader = get_ocr_reader()
        self.assertIsNotNone(ocr_reader, "EasyOCR reader must be initialized and accessible.")

        inpainting_engine = get_inpainting_engine()
        self.assertIsInstance(inpainting_engine, InpaintingEngine, "get_inpainting_engine must return InpaintingEngine.")
        self.assertIsNotNone(inpainting_engine.kernel_small)
        self.assertIsNotNone(inpainting_engine.kernel_dilate)
        print("  [PASS] test_02_ocr_and_inpainting_engine_access: OCR reader and inpainting engine verified.")

    def test_03_sha256_checksum_computation(self):
        """Verify SHA-256 computation on test files."""
        test_file = os.path.join(self.test_dir, "sample.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Manga AI Translator v3.0 SOTA Enterprise Standard")

        sha = compute_file_sha256(test_file)
        self.assertEqual(len(sha), 64, "SHA-256 hash must be 64 hexadecimal characters.")
        self.assertIsInstance(sha, str)
        print(f"  [PASS] test_03_sha256_checksum_computation: SHA-256 calculated ({sha[:16]}...).")

    def test_04_gutter_cut_segmentation_math(self):
        """Verify find_optimal_gutter_cuts detects horizontal boundaries for webtoon panels."""
        # Create synthetic image with 2 panels separated by white gutter
        img = np.zeros((6000, 800, 3), dtype=np.uint8)
        # Panel 1: rows 0..2500 has art pattern
        img[200:2400, 50:750] = 120
        # Gutter: rows 2500..3500 is white (255, 255, 255)
        img[2500:3500, :] = 255
        # Panel 2: rows 3500..5800 has art pattern
        img[3600:5700, 50:750] = 80

        cuts = find_optimal_gutter_cuts(img, num_cuts=1)
        self.assertEqual(len(cuts), 1)
        # Cut must be inside or near the gutter zone (2500..3500)
        self.assertTrue(2400 <= cuts[0] <= 3600, f"Gutter cut {cuts[0]} expected in 2400..3600")
        print(f"  [PASS] test_04_gutter_cut_segmentation_math: Optimal gutter cut detected at y={cuts[0]}.")

    def test_05_chapter_deficit_resolution(self):
        """Verify resolve_chapter_deficit expands a 4-page chapter into >= 8 pages using gutter slicing."""
        manga_title = "Test_Deficit_Manga"
        ch_dir = os.path.join(self.test_dir, manga_title, "chapter_500")
        v1_dir = os.path.join(ch_dir, "v1_original")
        os.makedirs(v1_dir, exist_ok=True)

        # Create 4 long synthetic pages (each 6000x800)
        for i in range(1, 5):
            img = np.ones((6000, 800, 3), dtype=np.uint8) * 200
            # add panel separator gutter in middle
            img[2800:3200, :] = 255
            fn = os.path.join(v1_dir, f"page_{i:03d}.webp")
            Image.fromarray(img).save(fn, "WEBP")

        checker = ChapterIntegrityChecker(data_root=self.test_dir, public_root=self.public_dir)
        new_count = checker.resolve_chapter_deficit(ch_dir, manga_title=manga_title, min_pages=8)

        self.assertGreaterEqual(new_count, 8, f"Expected >= 8 pages after deficit resolution, got {new_count}")
        actual_files = [f for f in os.listdir(v1_dir) if f.endswith(".webp")]
        self.assertEqual(len(actual_files), new_count)
        self.assertIn("page_008.webp", actual_files)
        print(f"  [PASS] test_05_chapter_deficit_resolution: Deficit resolved from 4 to {new_count} pages.")

    def test_06_manifest_v3_generation(self):
        """Verify pipeline_manifest.json conforms to Schema v3.0.0."""
        manga_title = "Test_Manifest_Manga"
        ch_dir = os.path.join(self.test_dir, manga_title, "chapter_501")
        v1_dir = os.path.join(ch_dir, "v1_original")
        v2_dir = os.path.join(ch_dir, "v2_cleaned")
        v3_dir = os.path.join(ch_dir, "v3_translated")
        for d in (v1_dir, v2_dir, v3_dir):
            os.makedirs(d, exist_ok=True)

        # Create 8 pages across v1, v2, v3
        for i in range(1, 9):
            fn = f"page_{i:03d}.webp"
            img = Image.new("RGB", (800, 1280), color=(i * 20, 100, 150))
            img.save(os.path.join(v1_dir, fn), "WEBP")
            img.save(os.path.join(v2_dir, fn), "WEBP")
            img.save(os.path.join(v3_dir, fn), "WEBP")

        checker = ChapterIntegrityChecker(data_root=self.test_dir, public_root=self.public_dir)
        manifest = checker.generate_pipeline_manifest(ch_dir, manga_title=manga_title, chapter_num="501")

        self.assertEqual(manifest["schema_version"], "3.0.0")
        self.assertEqual(manifest["manga_title"], manga_title)
        self.assertEqual(manifest["chapter"], "chapter_501")
        self.assertEqual(manifest["total_pages"], 8)
        self.assertEqual(manifest["layers"]["v1_original"], 8)
        self.assertEqual(manifest["layers"]["v2_cleaned"], 8)
        self.assertEqual(manifest["layers"]["v3_translated"], 8)
        self.assertEqual(manifest["integrity_status"], "PASSED")
        self.assertEqual(len(manifest["pages"]), 8)

        # Check page record structure
        p1 = manifest["pages"][0]
        self.assertEqual(p1["page_num"], 1)
        self.assertEqual(p1["filename"], "page_001.webp")
        self.assertEqual(len(p1["v1_sha256"]), 64)
        self.assertEqual(p1["dimensions"]["width"], 800)
        self.assertEqual(p1["dimensions"]["height"], 1280)
        self.assertIn("quality_metrics", p1)
        print("  [PASS] test_06_manifest_v3_generation: Schema v3.0.0 validated with SHA-256 hashes.")

    def test_07_zip_archive_and_frontend_sync(self):
        """Verify zip archive creation and public directory synchronization."""
        manga_title = "Test_Sync_Manga"
        ch_dir = os.path.join(self.test_dir, manga_title, "chapter_502")
        v1_dir = os.path.join(ch_dir, "v1_original")
        v2_dir = os.path.join(ch_dir, "v2_cleaned")
        v3_dir = os.path.join(ch_dir, "v3_translated")
        for d in (v1_dir, v2_dir, v3_dir):
            os.makedirs(d, exist_ok=True)

        for i in range(1, 9):
            fn = f"page_{i:03d}.webp"
            img = Image.new("RGB", (800, 1200), color=(50, 50, i * 25))
            img.save(os.path.join(v1_dir, fn), "WEBP")
            img.save(os.path.join(v2_dir, fn), "WEBP")
            img.save(os.path.join(v3_dir, fn), "WEBP")

        checker = ChapterIntegrityChecker(data_root=self.test_dir, public_root=self.public_dir)
        checker.generate_pipeline_manifest(ch_dir, manga_title=manga_title, chapter_num="502")
        zips = checker.create_chapter_zip(ch_dir, manga_title=manga_title, chapter_num="502")

        self.assertGreaterEqual(len(zips), 1)
        for zpath in zips:
            self.assertTrue(os.path.exists(zpath), f"Zip archive {zpath} must exist.")
            self.assertGreater(os.path.getsize(zpath), 100)

        # Run frontend sync
        synced = checker.sync_to_frontend(manga_title=manga_title)
        self.assertEqual(synced, 1)

        pub_ch = os.path.join(self.public_dir, manga_title, "chapter_502")
        self.assertTrue(os.path.exists(os.path.join(pub_ch, "v1", "page_001.webp")))
        self.assertTrue(os.path.exists(os.path.join(pub_ch, "v2", "page_001.webp")))
        self.assertTrue(os.path.exists(os.path.join(pub_ch, "v3", "page_001.webp")))
        self.assertTrue(os.path.exists(os.path.join(pub_ch, "meta.json")))
        self.assertTrue(os.path.exists(os.path.join(self.public_dir, "chapters_index.json")))

        with open(os.path.join(self.public_dir, "chapters_index.json"), "r", encoding="utf-8") as f:
            index_data = json.load(f)
            self.assertIn(manga_title, index_data["mangas"])

        print("  [PASS] test_07_zip_archive_and_frontend_sync: Zip archives and frontend sync verified.")

    def test_08_chapter_audit_complete_flow(self):
        """Verify audit_chapter and audit_all_chapters accurately report compliance."""
        manga_title = "The_Ultimate_of_All_Ages"
        checker = ChapterIntegrityChecker(data_root=self.test_dir, public_root=self.public_dir)

        # Create one compliant chapter and one deficient chapter
        good_ch = os.path.join(self.test_dir, manga_title, "chapter_531")
        bad_ch = os.path.join(self.test_dir, manga_title, "chapter_537")
        for ch, count in [(good_ch, 8), (bad_ch, 4)]:
            v1 = os.path.join(ch, "v1_original")
            v2 = os.path.join(ch, "v2_cleaned")
            v3 = os.path.join(ch, "v3_translated")
            for d in (v1, v2, v3):
                os.makedirs(d, exist_ok=True)
            for i in range(1, count + 1):
                fn = f"page_{i:03d}.webp"
                im = Image.new("RGB", (800, 1000), color=(100, 100, 100))
                im.save(os.path.join(v1, fn), "WEBP")
                im.save(os.path.join(v2, fn), "WEBP")
                im.save(os.path.join(v3, fn), "WEBP")
            checker.generate_pipeline_manifest(ch, manga_title=manga_title)
            checker.create_chapter_zip(ch, manga_title=manga_title)

        good_audit = checker.audit_chapter(good_ch, manga_title=manga_title)
        self.assertTrue(good_audit["is_valid"])
        self.assertEqual(good_audit["status"], "PASSED")

        bad_audit = checker.audit_chapter(bad_ch, manga_title=manga_title)
        self.assertFalse(bad_audit["is_valid"])
        self.assertEqual(bad_audit["status"], "DEFICIT")

        print("  [PASS] test_08_chapter_audit_complete_flow: Auditing logic correctly differentiates passed vs deficit.")


if __name__ == "__main__":
    unittest.main()
