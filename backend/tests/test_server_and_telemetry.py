# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for Consolidated FastAPI Server, Real-Time SSE Telemetry & ZIP Downloads.
Milestone 3 & Milestone 4 Verification Suite.
"""
import os
import sys
import json
import time
import zipfile
import tempfile
import unittest
import httpx

# Ensure backend in sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
AGENTS_DIR = os.path.join(BACKEND_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from server import app
from manga_pipeline_service import MangaPipelineService, active_tasks


class TestServerAndTelemetry(unittest.IsolatedAsyncioTestCase):
    """
    Test suite verifying all M3 & M4 REST endpoints, SSE streaming, ZIP generation, and telemetry.
    """

    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://test")
        self.test_manga = "The_Ultimate_of_All_Ages"
        self.test_chapter = "531"

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_01_health_endpoint_contract(self):
        """Verify GET /api/health returns version 4.0.0 and correct storage paths."""
        response = await self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["version"], "4.0.0")
        self.assertIn("storage", data)
        self.assertIn("public_storage", data)
        self.assertIn("data_storage", data)
        print("\n  [PASS] test_01_health_endpoint_contract: Healthcheck returns 4.0.0 online contract.")

    async def test_02_chapters_list_endpoint(self):
        """Verify GET /api/chapters/{manga} returns structured chapter versions."""
        response = await self.client.get(f"/api/chapters/{self.test_manga}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["manga"], self.test_manga)
        self.assertIn("chapters", data)
        self.assertIsInstance(data["chapters"], list)
        if len(data["chapters"]) > 0:
            first_ch = data["chapters"][0]
            self.assertIn("number", first_ch)
            self.assertIn("versions", first_ch)
        print(f"\n  [PASS] test_02_chapters_list_endpoint: Found {len(data['chapters'])} chapters with layer mappings.")

    async def test_03_studio_mangas_list_endpoint(self):
        """Verify GET /api/studio/mangas lists all available manga titles and chapter arrays."""
        response = await self.client.get("/api/studio/mangas")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("mangas", data)
        self.assertIsInstance(data["mangas"], list)
        found_target = any(m["name"] == self.test_manga for m in data["mangas"])
        self.assertTrue(found_target, f"Expected {self.test_manga} in manga list")
        print(f"\n  [PASS] test_03_studio_mangas_list_endpoint: Manga titles listed correctly ({len(data['mangas'])} titles).")

    async def test_04_studio_translate_trigger_and_status(self):
        """Verify POST /api/studio/translate launches task and REST status endpoint retrieves it."""
        payload = {
            "manga_name": self.test_manga,
            "chapter_num": "999",
            "source_lang": "auto",
            "target_lang": "ru"
        }
        res = await self.client.post("/api/studio/translate", json=payload)
        self.assertEqual(res.status_code, 200)
        start_data = res.json()
        self.assertEqual(start_data["status"], "started")
        self.assertIn("task_id", start_data)
        self.assertIn("stream_url", start_data)

        task_id = start_data["task_id"]

        # Poll status
        status_res = await self.client.get(f"/api/studio/tasks/{task_id}")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertEqual(status_data["task_id"], task_id)
        self.assertEqual(status_data["manga"], self.test_manga)
        self.assertEqual(status_data["chapter"], "999")
        self.assertIn("status", status_data)
        self.assertIn("progress", status_data)
        self.assertIn("logs", status_data)
        print(f"\n  [PASS] test_04_studio_translate_trigger_and_status: Task {task_id} launched & polled successfully.")

    async def test_05_sse_telemetry_event_broadcasting(self):
        """Verify GET /api/pipeline/stream/{task_id} emits real-time SSE telemetry events."""
        # Create a mock task
        task_id = MangaPipelineService.create_task(
            manga_name="Test_SSE_Manga",
            chapter_num="100"
        )
        # Emit several granular sub-step events
        MangaPipelineService.emit_task_event(
            task_id=task_id,
            stage="2-Pass OCR",
            progress=25,
            log_msg="[Test_SSE_Manga Ch.100] [Page 1/4] -> 2-Pass OCR & NMS",
            status="processing",
            page=1,
            total_pages=4
        )
        MangaPipelineService.emit_task_event(
            task_id=task_id,
            stage="Telea Inpaint",
            progress=50,
            log_msg="[Test_SSE_Manga Ch.100] [Page 1/4] -> Telea Inpaint",
            status="processing",
            page=1,
            total_pages=4
        )
        MangaPipelineService.emit_task_event(
            task_id=task_id,
            stage="Complete",
            progress=100,
            log_msg="✓ [Test_SSE_Manga Ch.100] Processing complete.",
            status="completed",
            page=4,
            total_pages=4,
            extra={"zip_url": "/api/studio/download/Test_SSE_Manga/100/v3", "read_url": "/reader/Test_SSE_Manga?chapter=chapter_100"}
        )

        # Connect SSE stream
        async with self.client.stream("GET", f"/api/pipeline/stream/{task_id}") as stream_res:
            self.assertEqual(stream_res.status_code, 200)
            self.assertIn("text/event-stream", stream_res.headers.get("content-type", ""))
            
            lines = []
            async for line in stream_res.aiter_lines():
                if line:
                    lines.append(line)

        # Verify emitted events
        event_lines = [line for line in lines if line.startswith("data:")]
        self.assertGreaterEqual(len(event_lines), 3)

        parsed_events = [json.loads(line.replace("data:", "").strip()) for line in event_lines]
        stages = [e.get("stage") for e in parsed_events]
        self.assertIn("2-Pass OCR", stages)
        self.assertIn("Telea Inpaint", stages)
        self.assertIn("Complete", stages)

        final_ev = parsed_events[-1]
        self.assertEqual(final_ev["status"], "completed")
        self.assertEqual(final_ev["progress"], 100)
        self.assertIn("zip_url", final_ev)
        print("\n  [PASS] test_05_sse_telemetry_event_broadcasting: SSE stream emitted and verified 3+ fine-grained events.")

    async def test_06_zip_download_endpoint(self):
        """Verify GET /api/studio/download/{manga}/{chapter}/v3 returns a valid zip archive."""
        # Download Chapter 531 v3
        res = await self.client.get(f"/api/studio/download/{self.test_manga}/{self.test_chapter}/v3")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/zip")
        self.assertIn("attachment", res.headers.get("content-disposition", ""))
        self.assertIn(".zip", res.headers.get("content-disposition", ""))

        # Verify ZIP content in memory
        temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        try:
            temp_zip.write(res.content)
            temp_zip.close()

            with zipfile.ZipFile(temp_zip.name, 'r') as zf:
                namelist = zf.namelist()
                self.assertGreater(len(namelist), 0, "ZIP archive should contain translated pages")
                for fn in namelist:
                    self.assertTrue(fn.endswith(('.webp', '.png', '.jpg', '.jpeg')), f"Unexpected file in zip: {fn}")
            print(f"\n  [PASS] test_06_zip_download_endpoint: Downloaded valid ZIP containing {len(namelist)} pages.")
        finally:
            if os.path.exists(temp_zip.name):
                os.remove(temp_zip.name)

    async def test_07_not_found_tasks_and_sse_error(self):
        """Verify 404 on non-existent task polling and SSE error event on invalid task."""
        # Polling 404
        poll_res = await self.client.get("/api/studio/tasks/nonexistent_task_9999")
        self.assertEqual(poll_res.status_code, 404)

        # SSE invalid task error stream
        async with self.client.stream("GET", "/api/pipeline/stream/nonexistent_task_9999") as sse_res:
            self.assertEqual(sse_res.status_code, 200)
            lines = []
            async for l in sse_res.aiter_lines():
                if l and l.startswith("data:"):
                    lines.append(l)
            self.assertGreaterEqual(len(lines), 1)
            err_data = json.loads(lines[0].replace("data:", "").strip())
            self.assertEqual(err_data.get("status"), "error")
            self.assertIn("error", err_data)
        print("\n  [PASS] test_07_not_found_tasks_and_sse_error: Error states handled transparently with honest diagnostics.")

    async def test_08_multi_chapter_batch_range_trigger(self):
        """Verify POST /api/studio/translate handles batch ranges (e.g. 901-902)."""
        payload = {
            "manga_name": self.test_manga,
            "chapters": "901-902",
            "source_lang": "auto",
            "target_lang": "ru"
        }
        res = await self.client.post("/api/studio/translate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "started")
        self.assertIn("task_ids", data)
        self.assertEqual(len(data["task_ids"]), 2)
        print("\n  [PASS] test_08_multi_chapter_batch_range_trigger: Successfully created batch tasks for range 901-902.")

    async def test_09_legacy_compatibility_endpoints(self):
        """Verify legacy compatibility endpoints (/api/pipeline/run and /api/pipeline/status)."""
        run_res = await self.client.post("/api/pipeline/run", json={"manga": self.test_manga, "chapter": "905"})
        self.assertEqual(run_res.status_code, 200)
        self.assertIn("task_id", run_res.json())

        status_res = await self.client.get("/api/pipeline/status")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertIn("status", status_data)
        self.assertIn("current_agent", status_data)
        print("\n  [PASS] test_09_legacy_compatibility_endpoints: Legacy endpoints operational.")


if __name__ == "__main__":
    unittest.main()
