import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { DELHI_PLAN_FIXTURE } from "../frontend/src/test/fixtures/dailyPlan.ts";

const tools = createRequire(
  resolve(process.env.URBERO_AUDIT_TOOLS ?? "frontend", "package.json"),
);
const { chromium } = tools("playwright");
const { default: lighthouse } = await import(
  pathToFileURL(tools.resolve("lighthouse")).href
);
const { launch } = tools("chrome-launcher");
const base = process.env.URBERO_AUDIT_URL ?? "http://127.0.0.1:8013";
const executablePath = process.env.CHROME_PATH ?? chromium.executablePath();
const browser = await chromium.launch({ executablePath });

try {
  for (const [theme, width] of [
    ["light", 390],
    ["dark", 1440],
  ]) {
    const page = await browser.newPage({
      viewport: { width, height: 900 },
      colorScheme: theme,
      reducedMotion: "reduce",
    });
    const planRequests = [];
    await page.route("**/api/plan/daily", async (route) => {
      planRequests.push(route.request().postDataJSON());
      await route.fulfill({ json: DELHI_PLAN_FIXTURE });
    });
    await page.goto(base);
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
    assert.equal(planRequests.length, 0);
    await page.getByRole("button", { name: "Noida", exact: true }).click();
    await page
      .locator("#tab-overview")
      .getByText("Overview", { exact: false })
      .first()
      .waitFor({ state: "attached" });
    const radios = page.getByRole("radio");
    assert.equal(await radios.count(), 3);
    for (const radio of await radios.all())
      assert.equal(await radio.getAttribute("aria-checked"), "false");
    await page.getByRole("radio", { name: /Andheri Mumbai/ }).click();
    await page.waitForFunction(() =>
      document.querySelector('[aria-busy="false"] [role="tablist"]'),
    );
    assert.equal(planRequests.at(-1).latitude, planRequests[0].latitude);
    assert.equal(planRequests.at(-1).longitude, planRequests[0].longitude);
    await page.locator("#tab-overview").focus();
    for (const tab of ["routine", "indoor", "briefings"]) {
      await page.keyboard.press("ArrowRight");
      const active = page.locator(`#tab-${tab}`);
      assert.equal(await active.getAttribute("aria-selected"), "true");
      const panel = await active.getAttribute("aria-controls");
      await page.locator(`#${panel}`).waitFor();
    }
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
    console.log(
      `Playwright ${theme} ${width}px: location gate, preset, keyboard tabs and page width passed`,
    );
    await page.close();
  }
} finally {
  await browser.close();
}

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
    const result = await lighthouse(
      base,
      {
        port: chrome.port,
        logLevel: "error",
        onlyCategories: ["accessibility"],
      },
      {
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
      },
    );
    const score = Math.round(
      (result?.lhr.categories.accessibility.score ?? 0) * 100,
    );
    console.log(`Lighthouse landing ${theme} ${width}px: ${score}/100`);
    if (score < 95) {
      for (const audit of Object.values(result?.lhr.audits ?? {})) {
        if (audit.score === 0)
          console.log(
            audit.id,
            audit.details?.items
              ?.map((item) => item.node?.snippet)
              .filter(Boolean),
          );
      }
      process.exitCode = 1;
    }
  } finally {
    await chrome.kill();
  }
}
