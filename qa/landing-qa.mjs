import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PEWS_LANDING_URL || 'http://127.0.0.1:19432/';
const formUrl = 'https://intake.clearlinetechmethods.com/s/cmrz46a4s002e01s3zt5ztqlq';
const attributedUrl = new URL(baseUrl);
attributedUrl.searchParams.set('utm_source', 'qa');
attributedUrl.searchParams.set('utm_campaign', 'marketing_ready');
const outDir = path.resolve('qa/screenshots');
await fs.mkdir(outDir, { recursive: true });

const viewports = [
  { name: 'desktop', width: 1440, height: 1000 },
  { name: 'tablet', width: 1024, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
];

const browser = await chromium.launch({ headless: true });
const report = { baseUrl, formUrl, viewports: [], formbricks: {}, failures: [] };

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('requestfailed', (request) => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));

  const response = await page.goto(attributedUrl.toString(), { waitUntil: 'networkidle', timeout: 60000 });
  if (!response || response.status() !== 200) report.failures.push(`${viewport.name}: landing HTTP ${response?.status()}`);
  await page.waitForSelector('[data-fit-check-link]');

  const metrics = await page.evaluate(() => ({
    innerWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    title: document.title,
    h1: document.querySelector('h1')?.innerText,
    fitCheckHref: document.querySelector('[data-fit-check-link]')?.href,
    robots: document.querySelector('meta[name="robots"]')?.content,
    canonical: document.querySelector('link[rel="canonical"]')?.href,
  }));
  if (metrics.scrollWidth > metrics.innerWidth) report.failures.push(`${viewport.name}: horizontal overflow ${metrics.scrollWidth} > ${metrics.innerWidth}`);
  if (!metrics.fitCheckHref?.includes('cmrz46a4s002e01s3zt5ztqlq')) report.failures.push(`${viewport.name}: incorrect fit-check destination`);
  if (!metrics.fitCheckHref?.includes('utm_source=qa') || !metrics.fitCheckHref?.includes('utm_campaign=marketing_ready')) report.failures.push(`${viewport.name}: attribution not propagated`);
  if (!metrics.fitCheckHref?.includes('landing_page=')) report.failures.push(`${viewport.name}: landing-page attribution missing`);
  if (!metrics.robots?.includes('index')) report.failures.push(`${viewport.name}: page is not indexable`);
  if (!metrics.canonical?.startsWith('https://')) report.failures.push(`${viewport.name}: canonical missing`);

  const pageText = await page.locator('body').innerText();
  if (!pageText.includes('$39') || !pageText.includes('$399')) report.failures.push(`${viewport.name}: founding price missing`);
  if (!pageText.includes('Planning Center stays') || !pageText.includes('Full Planning Center replacement')) report.failures.push(`${viewport.name}: beta boundary missing`);
  if (!pageText.includes('Know what needs attention') || !pageText.includes('Less chasing. Fewer dropped handoffs.')) report.failures.push(`${viewport.name}: prospect value copy missing`);
  const loadedFont = await page.evaluate(() => document.fonts.check('16px Inter'));
  if (!loadedFont) report.failures.push(`${viewport.name}: bundled Inter font did not load`);

  const targetIssues = await page.evaluate(() => {
    const candidates = [...document.querySelectorAll('a, button, summary')]
      .filter((element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
      });
    return candidates
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return { label: element.textContent?.trim().slice(0, 60), width: Math.round(rect.width), height: Math.round(rect.height) };
      })
      .filter((item) => item.height < 44 && item.width < 44);
  });
  if (viewport.name === 'mobile' && targetIssues.length) report.failures.push(`mobile: undersized isolated targets ${JSON.stringify(targetIssues)}`);

  const axe = await new AxeBuilder({ page }).exclude('iframe').analyze();
  const serious = axe.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact));
  if (serious.length) report.failures.push(`${viewport.name}: axe ${serious.map((item) => item.id).join(', ')}`);

  await page.screenshot({ path: path.join(outDir, `${viewport.name}-full.png`), fullPage: true });
  await page.locator('#join').screenshot({ path: path.join(outDir, `${viewport.name}-access.png`) });
  report.viewports.push({
    ...viewport,
    metrics,
    loadedFont,
    axeViolations: axe.violations.length,
    seriousAxeViolations: serious.length,
    targetIssues,
    consoleErrors,
    pageErrors,
    failedRequests,
  });
  if (consoleErrors.length || pageErrors.length || failedRequests.length) {
    report.failures.push(`${viewport.name}: browser errors console=${consoleErrors.length} page=${pageErrors.length} requests=${failedRequests.length}`);
  }
  await context.close();
}

{
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const response = await page.goto(formUrl, { waitUntil: 'networkidle', timeout: 60000 });
  const bodyText = await page.locator('body').innerText();
  const metrics = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth, title: document.title }));
  const axe = await new AxeBuilder({ page }).analyze();
  const serious = axe.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact));
  report.formbricks = {
    status: response?.status(),
    metrics,
    hasWelcomeCopy: bodyText.includes('Could your church help shape Pews?'),
    hasStartButton: bodyText.includes('Start the early-access fit check'),
    seriousAxeViolations: serious.map((item) => item.id),
    pageErrors: errors,
  };
  if (response?.status() !== 200) report.failures.push(`Formbricks HTTP ${response?.status()}`);
  if (!report.formbricks.hasWelcomeCopy || !report.formbricks.hasStartButton) report.failures.push('Formbricks welcome content missing');
  if (metrics.scrollWidth > metrics.innerWidth) report.failures.push(`Formbricks mobile overflow ${metrics.scrollWidth} > ${metrics.innerWidth}`);
  if (serious.length) report.failures.push(`Formbricks axe ${serious.map((item) => item.id).join(', ')}`);
  if (errors.length) report.failures.push(`Formbricks page errors ${errors.length}`);
  await page.screenshot({ path: path.join(outDir, 'formbricks-mobile.png'), fullPage: true });
  await context.close();
}

await browser.close();
await fs.writeFile('qa/report.json', JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
if (report.failures.length) process.exit(1);
