import http.client
import http.server
import os
import subprocess
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import local_ai_starter as app


class UpdateStartupTests(unittest.TestCase):
    def test_incomplete_response_is_nonfatal(self):
        with patch.object(app, "DRY_RUN", False), patch.dict(os.environ, {"LOCAL_AI_STARTER_NO_UPDATE": "0"}), \
                patch.object(app, "http_json", side_effect=http.client.IncompleteRead(b"partial", 20)), \
                patch.object(app, "say") as output:
            app.check_for_update([])
            output.assert_called_once()

    def test_mac_launcher_with_truncated_update_response(self):
        class Truncated(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b"partial")

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Truncated)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = dict(os.environ, LOCAL_AI_STARTER_UPDATE_API=f"http://127.0.0.1:{server.server_port}/",
                       LOCAL_AI_STARTER_NO_UPDATE="0", LOCAL_AI_STARTER_DRY_RUN="0", LOCAL_AI_STARTER_LANG="en")
            result = subprocess.run([str(Path(app.APP_DIR) / "RunMe.command"), "--menu"], input="2\n",
                                    capture_output=True, text=True, env=env, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn(app.STRINGS["en"]["update_check_failed"], result.stdout)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
