import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const surveyId = 'cmrz46a4s002e01s3zt5ztqlq';
const surveyUrl = `https://intake.clearlinetechmethods.com/s/${surveyId}?brand=pews&page=qa&placement=automated_qa&intent=beta_early_access`;
const envPath = '/Users/citadel/Projects/CTMWebsite2025/formbricks/.api.env';
const env = Object.fromEntries((await fs.readFile(envPath, 'utf8')).split(/\r?\n/).filter((line) => line.includes('=') && !line.trim().startsWith('#')).map((line) => { const index = line.indexOf('='); return [line.slice(0, index).trim(), line.slice(index + 1).trim().replace(/^['"]|['"]$/g, '')]; }));
const headers = { 'x-api-key': env.FORMBRICKS_API_KEY };
const api = 'https://intake.clearlinetechmethods.com/api/v2/management/responses';

async function responses() {
  const response = await fetch(`${api}?limit=100&surveyId=${surveyId}`, { headers });
  if (!response.ok) throw new Error(`Response list failed: ${response.status}`);
  return (await response.json()).data;
}

const before = await responses();
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', (error) => pageErrors.push(error.message));
await page.goto(surveyUrl, { waitUntil: 'networkidle', timeout: 60000 });
await page.getByRole('button', { name: 'Start the early-access fit check' }).click();

for (const choice of ['Planning services and worship', 'Scheduling volunteers', 'Too many disconnected tools']) {
  await page.getByText(choice, { exact: true }).click();
}
await page.getByRole('button', { name: 'Next' }).click();

await page.getByText('A mix of several tools', { exact: true }).click();
await page.getByRole('button', { name: 'Next' }).click();

await page.getByText('100–249', { exact: true }).click();
await page.getByRole('button', { name: 'Next' }).click();

await page.getByText('Worship pastor or ministry leader', { exact: true }).click();
await page.getByRole('button', { name: 'Next' }).click();

await page.locator('textarea').fill('Synthetic QA: clear weekly ownership, service planning, and follow-up without duplicate entry.');
await page.getByRole('button', { name: 'Next' }).click();

await page.getByText('Within the next 3 months', { exact: true }).click();
await page.getByRole('button', { name: 'Next' }).click();

await page.getByText('Yes — if the preferred beta rate and scope make sense', { exact: true }).click();
await page.getByRole('button', { name: 'Next' }).click();

const fields = await page.locator('input').evaluateAll((inputs) => inputs.map((input) => ({ type: input.type, placeholder: input.placeholder })));
const textInputs = page.locator('input[type="text"]');
await textInputs.nth(0).fill('Friday');
await textInputs.nth(1).fill('QA');
await page.locator('input[type="email"]').fill('friday+pews-qa@clearlinelims.com');
await textInputs.nth(2).fill('Pews Synthetic QA Church');
await page.getByRole('button', { name: /Submit|Finish|Complete|Next/ }).click();
await page.getByText('You are on the early-access list.', { exact: true }).waitFor({ timeout: 30000 });
await page.screenshot({ path: 'qa/screenshots/formbricks-submission-proof.png', fullPage: true });
await context.close();
await browser.close();

const after = await responses();
const created = after.filter((item) => !before.some((oldItem) => oldItem.id === item.id));
const matching = created.find((item) => JSON.stringify(item.data || {}).includes('friday+pews-qa@clearlinelims.com'));
const proof = {
  surveyId,
  beforeCount: before.length,
  afterCount: after.length,
  createdCount: created.length,
  captured: Boolean(matching),
  responseId: matching?.id,
  finished: matching?.finished,
  createdAt: matching?.createdAt,
  syntheticEmailPresent: matching ? JSON.stringify(matching.data).includes('friday+pews-qa@clearlinelims.com') : false,
  fieldCount: fields.length,
  pageErrors,
};
await fs.writeFile('qa/submission-proof.json', JSON.stringify(proof, null, 2) + '\n');
console.log(JSON.stringify(proof, null, 2));
if (!matching || !matching.finished || pageErrors.length) process.exit(1);
