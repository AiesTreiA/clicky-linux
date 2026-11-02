import os
import tempfile
import unittest
from PIL import Image
from clicky_linux.vision.optimizer import ImageOptimizer
from clicky_linux.core.config import ConfigManager
from clicky_linux.core.pool import TokenPoolManager
from clicky_linux.core.budget_guard import estimate_tokens, estimate_cost


class TestClickyCore(unittest.TestCase):

    def test_image_optimizer_downscaling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "raw_4k.png")
            # Create a synthetic 2560x1440 screenshot
            img = Image.new("RGB", (2560, 1440), color=(30, 40, 50))
            img.save(raw_path, "PNG")

            optimizer = ImageOptimizer(max_dimension=1280)
            opt_path, scale_x, scale_y = optimizer.optimize_for_vision(raw_path)

            self.assertTrue(os.path.exists(opt_path))
            self.assertAlmostEqual(scale_x, 2.0, places=2)
            self.assertAlmostEqual(scale_y, 2.0, places=2)

            with Image.open(opt_path) as opt_img:
                self.assertEqual(opt_img.size, (1280, 720))

    def test_config_manager_read_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = os.path.join(tmpdir, "config.json")
            cfg = ConfigManager(config_path=cfg_file)
            self.assertEqual(cfg.get("tokens.max_resolution_px"), 1280)

            cfg.set("tokens.max_resolution_px", 1024)
            cfg2 = ConfigManager(config_path=cfg_file)
            self.assertEqual(cfg2.get("tokens.max_resolution_px"), 1024)

    def test_token_pool_manager(self):
        pool_byok = TokenPoolManager(byok_key="test-key", allow_pool=True)
        res1 = pool_byok.select_active_node()
        self.assertEqual(res1["type"], "byok")

        pool_comm = TokenPoolManager(byok_key=None, allow_pool=True)
        res2 = pool_comm.select_active_node()
        self.assertEqual(res2["type"], "community_pool")

    def test_budget_guard_estimation(self):
        tokens = estimate_tokens("Hola mundo, esta es una prueba de Clicky Linux")
        self.assertGreater(tokens, 5)
        cost = estimate_cost("anthropic/claude-sonnet-5-5", 1000, 500)
        self.assertGreater(cost, 0.0)
        self.assertLess(cost, 0.05)


if __name__ == "__main__":
    unittest.main()
