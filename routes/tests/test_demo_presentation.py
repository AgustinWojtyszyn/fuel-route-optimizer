"""Regression tests for the self-contained multilingual route-planner demo."""
import base64
import re

from django.test import SimpleTestCase


class DemoPresentationTests(SimpleTestCase):
    def get_page(self):
        response = self.client.get("/demo/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_brand_images_are_embedded_and_valid(self):
        html = self.get_page()
        images = re.findall(r'(?:src|href)="data:image/png;base64,([^"]+)"', html)
        self.assertEqual(len(images), 2)  # favicon and compact navigation logo
        for image in images:
            binary = base64.b64decode(image, validate=True)
            self.assertTrue(binary.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertNotIn("{% static", html)
        self.assertNotIn('src="/static/routes/bomba-de-gas.png"', html)

    def test_four_languages_and_translated_ui_hooks_exist(self):
        html = self.get_page()
        for lang in ("en", "es", "fr", "pt"):
            self.assertIn(f'<option value="{lang}">', html)
            self.assertIn(f'"{lang}":', html)
        self.assertIn('id="languageSelect"', html)
        self.assertIn('data-i18n="approxBody"', html)
        self.assertIn("fuel:language-change", html)

    def test_route_planner_interactions_still_present(self):
        html = self.get_page()
        for element in ("routeForm", "submitButton", "map", "metrics",
                        "tripSummary", "stops", "copySummary", "fitRouteButton"):
            self.assertIn(f'id="{element}"', html)
        self.assertIn("/api/v1/routes/optimize/", html)
        self.assertIn("tiles.openfreemap.org/styles/liberty", html)

    def test_workspace_is_map_first_without_decorative_hero(self):
        html = self.get_page()
        self.assertNotIn('<div class="hero">', html)
        self.assertIn('class="layout"', html)
        self.assertIn('class="map-canvas"', html)
        self.assertIn('class="style-switcher"', html)
        self.assertIn('data-i18n="plannerTitle"', html)
