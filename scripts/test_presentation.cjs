/* Browser regression suite. npm install puppeteer in a separate tools directory,
 * then FUEL_BROWSER_MODULE=/path/to/node_modules/puppeteer node scripts/test_presentation.cjs.
 * Run Django on BASE_URL (default http://127.0.0.1:8127).
 * Synthetic route responses below are TEST FIXTURES, never published product data.
 */
const puppeteer = require(process.env.FUEL_BROWSER_MODULE || "puppeteer");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const base = process.env.BASE_URL || "http://127.0.0.1:8127";
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--ignore-certificate-errors", "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader"],
  });
  const page = await browser.newPage();
  const errors = [];
  let checks = 0;
  page.on("pageerror", (e) => errors.push(e.message));
  const check = (value, message) => {
    assert.ok(value, message);
    checks++;
  };
  fs.mkdirSync("docs/redesign/after", { recursive: true });
  try {
    for (const width of [375, 768, 1280, 1440]) {
      await page.setViewport({ width, height: width < 800 ? 900 : 960 });
      for (const [name, path, language] of [
        ["landing", "/", "#language"],
        ["planner", "/demo/", "#languageSelect"],
      ]) {
        await page.setViewport({width,height:width < 800 ? 900 : 960});
        await page.goto(base + path, { waitUntil: "networkidle2" });
        if (name === "planner") await page.waitForSelector("#map canvas");
        for (const lang of ["en", "es", "fr", "pt"]) {
          await page.select(language, lang);
          check(
            await page.evaluate(
              (l) => document.documentElement.lang.startsWith(l),
              lang,
            ),
            `${name} ${lang} language`,
          );
          check(
            await page.evaluate(
              () => document.documentElement.scrollWidth <= innerWidth,
            ),
            `${name} ${lang} ${width}: horizontal overflow`,
          );
          check(
            await page.evaluate(
              () => document.querySelector("h1").textContent.trim().length > 0,
            ),
            "heading translated",
          );
          if (name === "planner")
            check(
              await page.evaluate(
                () =>
                  document.querySelector("#startCity").getBoundingClientRect()
                    .height >= 44,
              ),
              "input touch target",
            );
        }
        await page.select(language, "en");
        await page.evaluate(() => document.fonts.ready);
        if (name === "planner") {
          await page.$eval("#map", (element) => element.scrollIntoView({block: "center"}));
          await pause(6000); // Render the WebGL canvas in the visible viewport before capture.
        }
        // A real full-height viewport keeps offscreen WebGL content in the compositor.
        const captureHeight=await page.evaluate(()=>document.documentElement.scrollHeight);
        await page.setViewport({width,height:captureHeight});
        await page.evaluate(()=>window.scrollTo(0,0));
        await pause(1500);
        if(name === "planner") check(await page.$eval("#map canvas",canvas=>canvas.width >= canvas.clientWidth), "map drawing buffer covers canvas after resize");
        await page.screenshot({
          path: `docs/redesign/after/${name}-${width}.png`,
          fullPage: false,
        });
      }
    }
    await page.setViewport({ width: 1440, height: 960 });
    await page.goto(base + "/demo/", { waitUntil: "networkidle2" });
    await page.waitForSelector("#map canvas");
    await page.click("#swapButton");
    check(
      (await page.$eval("#startCity", (e) => e.value)) === "Denver",
      "swap cities",
    );
    await page.click(".preset");
    check(
      (await page.$eval("#startCity", (e) => e.value)) === "Chicago",
      "preset restores cities",
    );
    for (const style of ["positron", "dark", "liberty"]) {
      await page.click(`[data-map-style="${style}"]`);
      check(
        (await page.$eval(`[data-map-style="${style}"]`, (e) =>
          e.getAttribute("aria-pressed"),
        )) === "true",
        "map style selection",
      );
    }
    await page.focus("#startCity");
    await page.$eval("#startCity", (e) => {
      e.value = "Chic";
      e.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForSelector('#startCityOptions [role="option"]', {
      timeout: 10000,
    });
    await page.keyboard.press("ArrowDown");
    check(
      await page.$eval(
        "#startCity",
        (e) => !!e.getAttribute("aria-activedescendant"),
      ),
      "keyboard highlight",
    );
    await page.keyboard.press("Enter");
    check(
      (await page.$eval("#startCity", (e) =>
        e.getAttribute("aria-expanded"),
      )) === "false",
      "keyboard choose closes list",
    );
    await page.$eval("#startCity", (e) => {
      e.value = "zzzzzzzzzzzzz";
      e.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForSelector("#startCityOptions .city-none");
    await pause(500);
    check(
      await page.$eval("#startCityOptions", (e) =>
        e.textContent.includes("No matches"),
      ),
      "real empty city catalog response",
    );
    await page.keyboard.press("Escape");
    let mode = "cities-error";
    let pending = null;
    await page.setRequestInterception(true);
    // Only local API requests are mocked. Real map assets and city success/empty were tested above.
    page.on("request", async (req) => {
      if (req.url().includes("/api/v1/cities/") && mode === "cities-error")
        return req.respond({
          status: 503,
          contentType: "application/json",
          body: "{}",
        });
      if (req.url().includes("/api/v1/routes/optimize/")) {
        pending = JSON.parse(req.postData());
        await pause(350);
        if (mode === "route-error")
          return req.respond({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({
              error: { message: "Test service unavailable" },
            }),
          });
        const fixture = {
          route: {
            distance_miles: 100,
            duration_minutes: 120,
            geometry: {
              type: "LineString",
              coordinates: [
                [-87.63, 41.88],
                [-86.16, 39.77],
              ],
            },
          },
          fuel: {
            purchased_en_route_usd: 0,
            estimated_total_trip_cost_usd: 30,
            initial_fuel_estimated_cost_usd: 30,
          },
          stops: [],
          meta: { routing_api_calls: 1, cache_hit: false, warnings: [] },
        };
        if (mode === "route-stops") {
          fixture.stops = [
            {
              name: "Synthetic test stop",
              city: "Test city",
              state: "IL",
              address: "Test only",
              lat: 41,
              lon: -87,
              gallons_to_buy: 2,
              price_usd_per_gallon: 3,
              stop_cost_usd: 6,
            },
          ];
          fixture.fuel.purchased_en_route_usd = 6;
        }
        return req.respond({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(fixture),
        });
      }
      req.continue();
    });
    await page.focus("#startCity");
    await page.$eval("#startCity", (e) => {
      e.value = "Chicago";
      e.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await pause(650);
    check(
      await page.$eval("#startCityOptions", (e) =>
        e.textContent.includes("unavailable"),
      ),
      "city failure visible",
    );
    await page.keyboard.press("Escape");
    mode = "route-error";
    await page.click("#submitButton");
    await page.waitForSelector('#routeForm[aria-busy="true"]');
    check(
      await page.$eval("#resultLoading", (e) => !e.hidden),
      "result loading skeleton",
    );
    await page.waitForSelector("#status.error");
    check(
      await page.$eval("#submitButton", (e) => !e.disabled),
      "retry enabled after error",
    );
    mode = "route-empty";
    await page.click("#submitButton");
    await page.waitForSelector("#status.success");
    check(
      await page.$eval("#metrics", (e) => !e.hidden),
      "metrics visible on success",
    );
    check(
      await page.$eval("#stops", (e) =>
        e.textContent.includes("No additional"),
      ),
      "zero purchase explanation",
    );
    check(
      pending.start.city === "Chicago" && pending.finish.city === "Denver",
      "original endpoint payload",
    );
    for (const lang of ["es", "fr", "pt", "en"]) {
      await page.select("#languageSelect", lang);
      check(
        await page.$eval("#tripTotal", (e) => /30/.test(e.textContent)),
        "currency remains on language change",
      );
    }
    mode = "route-stops";
    await page.click("#submitButton");
    await page.waitForSelector(".stop-focus");
    await page.click(".stop-focus");
    check(
      await page.$eval("#fitRouteButton", (e) => !e.hidden),
      "fit route available",
    );
    await page.click("#fitRouteButton");
    check(
      (await page.$$eval(".stop-pin", (e) => e.length)) === 1,
      "stop marker retained",
    );
    await page
      .browserContext()
      .overridePermissions(base, [
        "clipboard-read",
        "clipboard-sanitized-write",
      ]);
    await page.click("#copySummary");
    await page.waitForFunction(() =>
      document.querySelector("#copySummary").textContent.includes("Copied"),
    );
    check(
      await page.evaluate(async () =>
        (await navigator.clipboard.readText()).includes("Fuel Route Optimizer"),
      ),
      "copy summary",
    );
    check(errors.length === 0, "no browser exceptions: " + errors.join("; "));
    const report = {
      checks,
      widths: [375, 768, 1280, 1440],
      languages: ["en", "es", "fr", "pt"],
      browser: await browser.version(),
      errors,
      externalRouting:
        "Not exercised: no provider credentials; UI result/error tests use explicit synthetic fixtures.",
    };
    fs.writeFileSync(
      "docs/redesign/browser-results.json",
      JSON.stringify(report, null, 2) + "\n",
    );
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
