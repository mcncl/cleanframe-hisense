// Exercise the full HTTP/browser boundary against --demo. Never contacts a TV.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const root = resolve(import.meta.dirname, '..');
const state = mkdtempSync(tmpdir() + '/cleanframe-check-');
const base = 'http://127.0.0.1:4796';
const proc = spawn(process.env.CLEANFRAME_PYTHON || root + '/.local/venv/bin/python', ['hisense/server.py', 'serve', '--demo', '--port', '4796'], {
  cwd: root, env: { ...process.env, SIDEE_STATE_DIR: state }
});
let output = '';
proc.stderr.on('data', data => { output += data; });
let browser;
async function statusOf(pendingResponse) {
  const response = await pendingResponse;
  // Drain even status-only checks, especially JPEGs. Unread bodies can crash
  // Node 22's HTTP parser when this HTTP/1.0 server closes the connection.
  await response.arrayBuffer();
  return response.status;
}
try {
  for (let i = 0; i < 80; i++) {
    try { if (await statusOf(fetch(base + '/health')) === 200) break; } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal((await (await fetch(base + '/health')).json()).demo, true);
  const config = await (await fetch(base + '/api/config.js')).text();
  const key = JSON.parse(config.slice(config.indexOf('=') + 1, -1)).controlKey;
  const post = (path, value, extra = {}) => fetch(base + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CleanFrame-Key': key, ...extra }, body: JSON.stringify(value)
  });
  assert.equal(await statusOf(post('/api/launch', { id: 'native.unknown' })), 400);
  assert.equal(await statusOf(post('/api/key', { key: 'power' })), 400);
  assert.equal(await statusOf(post('/api/key', { key: 'down' })), 200);
  assert.equal(await statusOf(post('/api/key', { key: 'ok' }, { Origin: 'https://unrelated.example' })), 403);
  assert.equal(await statusOf(post('/api/launch', { id: 'service.plex' }, { Origin: 'https://unrelated.example' })), 403);
  assert.equal(await statusOf(fetch(base + '/home/%2e%2e%2f.local/hisense/state/session.json')), 404);
  const fallback = await (await post('/api/launch', { id: 'service.smarters' })).json();
  assert.equal(fallback.destination, 'Fire TV Stick');
  assert.match(fallback.note, /Select IPTV Smarters/);
  assert.equal(await statusOf(post('/api/settings', { idle_seconds: 0, home_takeover: false })), 200);

  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errors = [];
  const launches = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', request => { if (request.url().endsWith('/api/launch')) launches.push(request.postDataJSON()); });
  await page.goto(base + '/home/');
  await page.waitForFunction(() => window.ShoreQA && ShoreQA.ready());
  assert.deepEqual(await page.evaluate(() => ShoreQA.state().dock), ['plex', 'sbs', 'abciview']);
  await page.evaluate(() => ShoreQA.look({ layout: 'list', apps: 'text' }));
  await page.reload();
  await page.waitForFunction(() => window.ShoreQA && ShoreQA.ready());
  assert.equal(await page.evaluate(() => ShoreQA.state().look.layout), 'list');
  mkdirSync(root + '/.local/qa', { recursive: true });
  await page.screenshot({ path: root + '/.local/qa/hisense-home.png' });
  // Wallpaper upload goes through the real decoder and produces every material.
  const image = readFileSync(root + '/app/assets/wallpapers/misty.jpg');
  assert.equal(await statusOf(fetch(base + '/api/wallpaper', { method: 'POST', headers: { 'X-CleanFrame-Key': key, 'Content-Type': 'image/jpeg' }, body: image })), 200);
  await page.reload();
  await page.waitForFunction(() => window.ShoreQA && ShoreQA.ready());
  await page.evaluate(() => ShoreQA.look({ wall: 'personal', layout: 'dock' }));
  await page.waitForFunction(() => ShoreQA.ready() && ShoreQA.state().wallpaper === 'personal');
  for (const suffix of ['', '-thumb', '-panel']) assert.equal(await statusOf(fetch(base + '/home/assets/wallpapers/personal' + suffix + '.jpg')), 200);
  for (const suffix of ['field-blur', 'field-clear', 'field-frost', 'study-soft']) assert.equal(await statusOf(fetch(base + '/home/assets/materials/personal-' + suffix + '.jpg')), 200);
  await page.screenshot({ path: root + '/.local/qa/hisense-personal-dock.png' });

  await page.route('**/api/config.js', async route => {
    const response = await route.fetch();
    await route.fulfill({ response, body: (await response.text()) + '\nwindow.CleanFramePlatform.idleSeconds=0.4;' });
  });
  await page.reload();
  await page.waitForFunction(() => window.CleanFrameAmbient && CleanFrameAmbient.sleeping());
  await page.keyboard.down('Enter');
  await page.keyboard.down('Enter');
  await page.keyboard.up('Enter');
  assert.equal(launches.length, 0, 'wake and repeated held OK must not launch an app');
  await Promise.all([page.waitForResponse(r => r.url().endsWith('/api/launch')), page.keyboard.press('Enter')]);
  assert.equal(launches.length, 1);
  assert.equal(launches[0].id, 'service.plex');
  assert.deepEqual(errors, []);
  console.log('Hisense integration passed: shortcuts, truthful Fire TV fallback, request protection, preference persistence, custom photo materials, idle fade and held-key wake.');
} catch (error) {
  console.error(output.slice(-3000));
  throw error;
} finally {
  if (browser) await browser.close();
  proc.kill('SIGTERM');
  await new Promise(resolve => proc.once('exit', resolve));
  rmSync(state, { recursive: true, force: true });
}
