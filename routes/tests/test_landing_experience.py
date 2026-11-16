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
        self.assertIn('class="brand-type"', page)
        self.assertIn('href="/static/routes/favicon.svg"', page)
        self.assertNotIn("data:image/png;base64,", page)
        self.assertIn('class="instrument__scale"', page)
        self.assertEqual(page.count('class="lab__preset"'), 3)


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
            "routes/favicon.svg",
        ):
            with self.subTest(path=relative_path):
                self.assertIsNotNone(finders.find(relative_path))
        landing_css = Path(finders.find("routes/landing.css")).read_text(encoding="utf-8")
        self.assertTrue(landing_css.startswith("/* Hallmark"))
        self.assertIn(':root[data-theme="light"]', landing_css)
        self.assertIn("prefers-reduced-motion", landing_css)

    def test_range_instrument_explains_assumptions_once(self):
        html = self.client.get("/").content.decode("utf-8")
        self.assertIn('data-i18n="instrumentTitle">Assumed driving range', html)
        self.assertIn('data-i18n="instrumentCaption">Based on a full 50-gallon tank', html)
        self.assertNotIn('data-i18n="instrumentFormula"', html)
        self.assertNotIn('class="instrument__bottom"', html)
        self.assertNotIn('A calibrated 500-mile reference scale', html)

    def test_own_brand_is_used_consistently_across_both_pages(self):
        for route in ("/", "/demo/"):
            with self.subTest(route=route):
                html = self.client.get(route).content.decode("utf-8")
                self.assertIn('class="brand-type__main"', html)
                self.assertIn('href="/static/routes/favicon.svg"', html)
                self.assertNotIn("data:image/png;base64,", html)
                self.assertNotIn("bomba-de-gas.png", html)

    def test_landing_illustrations_remain_arithmetic_only(self):
        html = self.client.get("/").content.decode("utf-8")
        self.assertIn('aria-valuenow="500"', html)
        self.assertIn('data-i18n="labWarning"', html)
        self.assertIn('id="distanceSlider"', html)
        self.assertNotIn('api/v1/routes/optimize/', html)
        js_path = Path(finders.find("routes/landing.js"))
        script = js_path.read_text(encoding="utf-8")
        self.assertIn("button.dataset.distance", script)
        self.assertIn("Math.ceil(distance/500)-1", script)
