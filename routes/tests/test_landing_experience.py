"""Landing presentation, shared themes and language defaults.

These tests are intentionally offline. They do not access routing services.
"""
from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase


class LandingExperienceTests(SimpleTestCase):
    def test_landing_is_distinct_from_the_working_planner(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.content.decode("utf-8")
        self.assertIn('lang="en" data-theme="dark"', page)
        self.assertIn('id="pageTitle"', page)
        self.assertIn('id="distanceSlider"', page)
        self.assertIn('id="rangeSegments"', page)
        self.assertIn('href="/demo/"', page)
        self.assertIn('href="#features"', page)
        self.assertIn("not verified pump entrances", page)
        self.assertNotIn("planner-preview.png", page)
        self.assertNotIn("planner-map-preview.png", page)
        self.assertNotIn('id="routeForm"', page)
        self.assertNotIn('id="map"', page)

    def test_both_pages_offer_dark_light_control(self):
        for route in ("/", "/demo/"):
            with self.subTest(route=route):
                html = self.client.get(route).content.decode("utf-8")
                self.assertIn('id="themeToggle"', html)
                self.assertIn("/static/routes/theme.js", html)
                self.assertIn("fuel-route-theme", html)

    def test_english_first_and_four_manual_languages(self):
        for route in ("/", "/demo/"):
            with self.subTest(route=route):
                page = self.client.get(route).content.decode("utf-8")
                self.assertIn('<html lang="en"', page)
                for language in ("en", "es", "fr", "pt"):
                    self.assertIn(f'<option value="{language}">', page)
                self.assertIn("/static/routes/" ,page)
        landing_js = Path(finders.find("routes/landing.js")).read_text(encoding="utf-8")
        self.assertIn("let language='en';", landing_js)
        self.assertIn("fuel-route-language-v2", landing_js)
        planner = self.client.get("/demo/").content.decode("utf-8")
        self.assertIn("let current = supported.includes(stored) ? stored : 'en';", planner)

    def test_styles_and_scripts_exist_in_django_staticfiles(self):
        for relative_path in (
            "routes/landing.css",
            "routes/landing.js",
            "routes/theme.js",
            "routes/theme.css",
        ):
            with self.subTest(path=relative_path):
                self.assertIsNotNone(finders.find(relative_path))
        landing_css = Path(finders.find("routes/landing.css")).read_text(encoding="utf-8")
        self.assertTrue(landing_css.startswith("/* Hallmark"))
        self.assertIn(':root[data-theme="light"]', landing_css)
        self.assertIn("prefers-reduced-motion", landing_css)
