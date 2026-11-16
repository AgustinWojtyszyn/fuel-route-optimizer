"""Regression tests for the self-contained multilingual route-planner demo."""
import json
import re

from django.test import SimpleTestCase


class DemoPresentationTests(SimpleTestCase):
    def get_page(self):
        response = self.client.get("/demo/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_custom_brand_uses_no_flaticon_png(self):
        html = self.get_page()
        self.assertIn('href="/static/routes/favicon.svg"', html)
        self.assertIn('class="brand-type"', html)
        self.assertIn('class="brand-type__main"', html)
        self.assertNotIn("data:image/png;base64,", html)
        self.assertNotIn("bomba-de-gas.png", html)

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

    def test_translation_catalogs_cover_all_four_languages(self):
        html = self.get_page()
        match = re.search(r"const translations = (\{.*?\});\s*const supported", html, re.S)
        self.assertIsNotNone(match)
        catalog = json.loads(match.group(1))
        self.assertEqual(set(catalog), {"en", "es", "fr", "pt"})
        english_keys = set(catalog["en"])
        self.assertGreaterEqual(len(english_keys), 80)
        for language, messages in catalog.items():
            with self.subTest(language=language):
                self.assertEqual(set(messages), english_keys)
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in messages.values()))

    def test_accessible_page_heading_and_landmark(self):
        html = self.get_page()
        self.assertEqual(len(re.findall(r"<h1\b", html)), 1)
        self.assertIn('<h1 data-i18n="plannerTitle">', html)
        self.assertIn('role="status"', html)
        self.assertIn('aria-live="polite"', html)
