import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { DELHI_PLAN_FIXTURE } from "../frontend/src/test/fixtures/dailyPlan.ts";

const tools = createRequire(
  resolve(process.env.URBERO_AUDIT_TOOLS ?? "frontend", "package.json"),
);
const frontend = createRequire(resolve("frontend", "package.json"));
const jestAxe = createRequire(frontend.resolve("jest-axe"));
const { chromium } = tools("playwright");
const base = process.env.URBERO_AUDIT_URL ?? "http://127.0.0.1:8013";
const replayUrl = process.env.URBERO_AUDIT_REPLAY_URL;
const outageUrl = process.env.URBERO_AUDIT_OUTAGE_URL;
const executablePath = process.env.CHROME_PATH ?? chromium.executablePath();
const presets = [
  /South Delhi Joint Family/,
  /Andheri Mumbai/,
  /Salt Lake Kolkata/,
];
const isDailyPlan = (url) => new URL(url).pathname === "/api/plan/daily";
const isCommuteChunk = (url) => /\/assets\/CommuteBars-[^/]+\.js$/.test(url);

async function auditPage(browser, url, theme, width, exercise) {
  const origin = new URL(url).origin;
  const label = `${theme} ${width}px at ${origin}`;
  const page = await browser.newPage({
    viewport: { width, height: 900 },
    colorScheme: theme,
    reducedMotion: "reduce",
  });
  const consoleErrors = [];
  const uncaughtErrors = [];
  const externalRequests = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push({ text: message.text(), ...message.location() });
    }
  });
  page.on("pageerror", (error) =>
    uncaughtErrors.push(error.stack ?? error.message),
  );
  await page.addInitScript(() => {
    window.urberoCspViolations = [];
    document.addEventListener("securitypolicyviolation", (event) => {
      window.urberoCspViolations.push({
        directive: event.effectiveDirective,
        blockedUri: event.blockedURI,
        documentUri: event.documentURI,
        sourceFile: event.sourceFile,
        lineNumber: event.lineNumber,
        columnNumber: event.columnNumber,
      });
    });
  });
  await page.addInitScript({ path: jestAxe.resolve("axe-core/axe.min.js") });
  await page.route(
    (target) => /^https?:$/.test(target.protocol) && target.origin !== origin,
    async (route) => {
      externalRequests.push(route.request().url());
      await route.abort("blockedbyclient");
    },
  );

  try {
    await exercise(page);
  } finally {
    let cspViolations;
    try {
      cspViolations = await page.evaluate(
        () => window.urberoCspViolations ?? [],
      );
    } finally {
      console.log(`Browser diagnostics ${label}`, {
        cspViolations,
        uncaughtErrors,
        consoleErrors,
        externalRequests,
      });
      await page.close();
    }
    assert.deepEqual(
      cspViolations.filter(
        (item) =>
          item.directive.startsWith("script-src") &&
          new URL(item.documentUri).origin === origin &&
          !item.sourceFile.startsWith("chrome-extension://"),
      ),
      [],
      `${label} first-party CSP script violations`,
    );
    assert.deepEqual(uncaughtErrors, [], `${label} uncaught page errors`);
    assert.deepEqual(externalRequests, [], `${label} external requests`);
  }
}

async function openLocationGate(page, url) {
  const response = await page.goto(url);
  assert.equal(response?.status(), 200);
  const policy = (await response.headerValue("content-security-policy")) ?? "";
  const scripts = policy
    .split(";")
    .map((directive) => directive.trim())
    .find((directive) => directive.startsWith("script-src "));
  assert.equal(scripts, "script-src 'self'");
  await page.keyboard.press("Tab");
  assert.equal(
    await page.evaluate(() => document.activeElement?.textContent?.trim()),
    "Skip to main content",
  );
  await page.keyboard.press("Enter");
  assert.equal(
    await page.evaluate(() => document.activeElement?.id),
    "main-content",
  );
  await page.getByRole("button", { name: "Get Started" }).click();
  await page.getByRole("heading", { name: "Choose your location" }).waitFor();
  assert.equal(
    await page.evaluate(() => document.activeElement?.id),
    "location-gate-title",
  );
  await waitForOpaque(
    page.getByRole("region", { name: "Location Search and Geolocation" }),
  );
}

async function waitForOpaque(locator) {
  const element = await locator.elementHandle();
  try {
    await locator
      .page()
      .waitForFunction(
        (node) => getComputedStyle(node).opacity === "1",
        element,
      );
  } finally {
    await element.dispose();
  }
}

async function axeCheck(page, state) {
  const violations = await page.evaluate(async () => {
    const report = await window.axe.run({
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
      },
    });
    return report.violations.map(({ id, nodes }) => ({
      id,
      nodes: nodes.map(({ target, failureSummary }) => ({
        target,
        failureSummary,
      })),
    }));
  });
  assert.deepEqual(violations, [], `axe violations in ${state}`);
}

async function selectCity(page, city) {
  const response = page.waitForResponse((candidate) =>
    isDailyPlan(candidate.url()),
  );
  await page.getByRole("button", { name: city, exact: true }).click();
  return response;
}

async function advanceTab(page, id) {
  await page.keyboard.press("ArrowRight");
  const tab = page.locator(`#tab-${id}`);
  assert.equal(await tab.getAttribute("aria-selected"), "true");
  const panel = page.locator(`#${await tab.getAttribute("aria-controls")}`);
  await panel.waitFor();
  return panel;
}

function clockTime(hour) {
  const minutes = Math.round(hour * 60);
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}

async function exerciseErrands(page, routine) {
  const stops = [
    {
      name: "Pharmacy",
      category: "pharmacy",
      distance_from_home_km: 1,
      duration_minutes: 5,
    },
    {
      name: "Groceries",
      category: "groceries",
      distance_from_home_km: 2,
      duration_minutes: 10,
    },
  ];
  for (const [index, stop] of stops.entries()) {
    const label = `Stop ${index + 1}`;
    await routine.getByRole("button", { name: "Add errand" }).click();
    await routine.getByLabel(`${label} name`).fill(stop.name);
    await routine.getByLabel(`${label} category`).selectOption(stop.category);
    await routine
      .getByLabel(`${label} distance from home (km)`)
      .fill(String(stop.distance_from_home_km));
    await routine
      .getByLabel(`${label} duration (min)`)
      .fill(String(stop.duration_minutes));
  }

  const responsePromise = page.waitForResponse((response) =>
    isDailyPlan(response.url()),
  );
  await routine.getByRole("button", { name: "Apply errands" }).click();
  const response = await responsePromise;
  assert.equal(response.status(), 200);
  const submitted = response.request().postDataJSON().errands;
  assert.deepEqual(
    submitted.map(({ id, ...stop }) => stop),
    stops,
  );
  const { errand_merger: result } = await response.json();
  assert.equal(result.emissions_factor_g_per_km, 48);
  assert.notEqual(result.recommended_end_hour % 1, 0);

  const loop = routine.getByRole("region", { name: "Errand loop" });
  await loop.waitFor();
  assert.deepEqual(
    await loop.getByRole("listitem").allTextContents(),
    result.ordered_stops.map(
      (stop) => `${stop.name} (${stop.duration_minutes} min)`,
    ),
  );
  await loop
    .getByText(
      `${clockTime(result.recommended_start_hour)}–${clockTime(result.recommended_end_hour)}`,
      { exact: true },
    )
    .waitFor();
  const math = loop.getByRole("button", {
    name: /errand distances and emissions/i,
  });
  await math.focus();
  await page.keyboard.press("Enter");
  await waitForOpaque(math.locator("xpath=following-sibling::div[1]"));
  await loop
    .getByText(new RegExp(`${result.emissions_factor_g_per_km} g/km`))
    .waitFor();
  await axeCheck(page, "submitted errand loop");
}

async function exerciseRoomCalculation(page, indoor) {
  const length = indoor.getByRole("spinbutton", { name: "Length (m)" });
  const previous = Number(await length.inputValue());
  const next = previous + 1;
  await length.fill(String(next));
  await indoor.getByText(`Length (${previous}m)`, { exact: false }).waitFor();
  const responsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/exposure/cadr",
  );
  await indoor
    .getByRole("button", { name: "Update CADR & Sealing Advisory" })
    .click();
  const response = await responsePromise;
  assert.equal(response.status(), 200);
  assert.equal(response.request().postDataJSON().dimensions.length_m, next);
  const result = await response.json();
  await indoor.getByText(`Length (${next}m)`, { exact: false }).waitFor();
  await indoor
    .getByText(`Volume (${result.room_volume_m3} m³)`, { exact: false })
    .waitFor();
}

async function exerciseWorkspace(page, url, theme, replay) {
  const planRequests = [];
  const commuteChunks = [];
  page.on("request", (request) => {
    if (isDailyPlan(request.url())) planRequests.push(request.postDataJSON());
    if (isCommuteChunk(request.url())) commuteChunks.push(request.url());
  });
  if (!replay) {
    await page.route("**/api/plan/daily", (route) =>
      route.fulfill({ json: DELHI_PLAN_FIXTURE }),
    );
  }
  await openLocationGate(page, url);
  await axeCheck(page, "location gate");
  assert.equal(planRequests.length, 0);

  const firstPlan = await selectCity(page, "Noida");
  assert.equal(firstPlan.status(), 200);
  if (replay) {
    const plan = await firstPlan.json();
    assert.equal(plan.station_metadata.source, "Open-Meteo CAMS (Modelled)");
    assert.equal(plan.station_metadata.status, "modelled_live");
  }
  const overview = page.locator("#tab-overview");
  await overview.waitFor();
  const radios = page.getByRole("radio");
  assert.equal(await radios.count(), 3);
  for (const radio of await radios.all()) {
    assert.equal(await radio.getAttribute("aria-checked"), "false");
  }
  for (const preset of presets) {
    const response = page.waitForResponse((candidate) =>
      isDailyPlan(candidate.url()),
    );
    const radio = page.getByRole("radio", { name: preset });
    await radio.click();
    assert.equal((await response).status(), 200);
    assert.equal(await radio.getAttribute("aria-checked"), "true");
    const request = planRequests.at(-1);
    assert.equal(request.latitude, planRequests[0].latitude);
    assert.equal(request.longitude, planRequests[0].longitude);
  }

  await overview.focus();
  const routine = await advanceTab(page, "routine");
  const commuteTable = routine.getByRole("table", {
    name: /side-by-side commute mode/i,
  });
  await commuteTable.waitFor();
  await axeCheck(page, "routine table");
  assert.equal(commuteChunks.length, 0, "Commute chart must load on demand");
  const chart = page.waitForResponse((response) =>
    isCommuteChunk(response.url()),
  );
  await routine.getByRole("button", { name: "Visual Bars" }).click();
  assert.equal((await chart).status(), 200);
  assert.equal(commuteChunks.length, 1);
  await commuteTable.waitFor();
  await axeCheck(page, "routine chart");
  if (replay) await exerciseErrands(page, routine);
  await page.locator("#tab-routine").focus();

  const indoor = await advanceTab(page, "indoor");
  const math = indoor.getByRole("button", { name: /show the math/i }).first();
  await math.focus();
  assert.ok((await math.boundingBox()).height >= 44);
  await page.keyboard.press("Enter");
  assert.equal(await math.getAttribute("aria-expanded"), "true");
  await waitForOpaque(math.locator("xpath=following-sibling::div[1]"));
  await axeCheck(page, "open indoor math drawer");
  if (replay) await exerciseRoomCalculation(page, indoor);
  await page.locator("#tab-indoor").focus();
  await advanceTab(page, "briefings");
  await axeCheck(page, "briefings");
  assert.equal(
    await page.evaluate(() =>
      document.documentElement.classList.contains("dark"),
    ),
    theme === "dark",
  );
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
}

const browser = await chromium.launch({ executablePath });
try {
  for (const theme of ["light", "dark"]) {
    for (const width of [390, 1440]) {
      await auditPage(browser, base, theme, width, (page) =>
        exerciseWorkspace(page, base, theme, false),
      );
      console.log(
        `Playwright ${theme} ${width}px: CSP, presets, keyboard tabs, chart, math drawer and axe passed`,
      );
    }
  }
  if (replayUrl) {
    await auditPage(browser, replayUrl, "light", 390, (page) =>
      exerciseWorkspace(page, replayUrl, "light", true),
    );
    console.log("Playwright recorded-provider FastAPI workspace passed");
  }
  if (outageUrl) {
    await auditPage(browser, outageUrl, "dark", 1440, async (page) => {
      await openLocationGate(page, outageUrl);
      const response = await selectCity(page, "Noida");
      assert.equal(response.status(), 503);
      await page.getByText(/air quality is temporarily unavailable/i).waitFor();
      await page.getByRole("button", { name: "Retry", exact: true }).waitFor();
      await axeCheck(page, "provider outage");
    });
    console.log("Playwright FastAPI provider-unavailable state passed");
  }
} finally {
  await browser.close();
}

function recordLighthouse(result, state, theme, width) {
  const score = Math.round(
    (result?.lhr.categories.accessibility.score ?? 0) * 100,
  );
  console.log(`Lighthouse ${state} ${theme} ${width}px: ${score}/100`);
  if (score < 95) {
    for (const audit of Object.values(result?.lhr.audits ?? {})) {
      if (audit.score === 0) {
        console.log(
          audit.id,
          audit.details?.items
            ?.map((item) => item.node?.snippet)
            .filter(Boolean),
        );
      }
    }
    process.exitCode = 1;
  }
}

async function snapshotWorkspace(chrome, theme, width, options) {
  const { connect } = createRequire(tools.resolve("lighthouse"))(
    "puppeteer-core",
  );
  const { snapshot } = await import(
    pathToFileURL(tools.resolve("lighthouse")).href
  );
  const client = await connect({
    browserURL: `http://127.0.0.1:${chrome.port}`,
  });
  try {
    const page = await client.newPage();
    await page.setViewport({ width, height: 900, isMobile: width < 500 });
    await page.emulateMediaFeatures([
      { name: "prefers-color-scheme", value: theme },
      { name: "prefers-reduced-motion", value: "reduce" },
    ]);
    await page.goto(replayUrl);
    for (const label of ["Get Started", "Noida"]) {
      const button = await page.waitForFunction(
        (text) =>
          Array.from(document.querySelectorAll("button")).find(
            (element) => element.textContent.trim() === text,
          ),
        {},
        label,
      );
      await button.asElement().evaluate((element) => element.click());
      await button.dispose();
    }
    await page.waitForSelector("#tab-overview", { visible: true });
    return await snapshot(page, options);
  } finally {
    client.disconnect();
  }
}

if (process.env.URBERO_SKIP_LIGHTHOUSE !== "1") {
  const { default: lighthouse } = await import(
    pathToFileURL(tools.resolve("lighthouse")).href
  );
  const { launch } = tools("chrome-launcher");
  for (const [theme, width] of [
    ["light", 390],
    ["dark", 1440],
  ]) {
    const chrome = await launch({
      chromePath: executablePath,
      chromeFlags: [
        "--headless",
        "--disable-gpu",
        theme === "dark"
          ? "--force-dark-mode"
          : "--disable-features=WebContentsForceDark",
        ...(process.env.CI ? ["--no-sandbox"] : []),
      ],
    });
    try {
      const flags = {
        port: chrome.port,
        logLevel: "error",
        onlyCategories: ["accessibility"],
      };
      const config = {
        extends: "lighthouse:default",
        settings: {
          formFactor: width < 500 ? "mobile" : "desktop",
          screenEmulation: {
            mobile: width < 500,
            width,
            height: 900,
            deviceScaleFactor: 1,
            disabled: false,
          },
        },
      };
      recordLighthouse(
        await lighthouse(base, flags, config),
        "landing",
        theme,
        width,
      );
      if (replayUrl) {
        const result = await snapshotWorkspace(chrome, theme, width, {
          flags,
          config,
        });
        recordLighthouse(result, "recorded-provider workspace", theme, width);
      }
    } finally {
      await chrome.kill();
    }
  }
}
