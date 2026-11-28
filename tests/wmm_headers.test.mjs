import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const headers = readFileSync(resolve(root, "_headers"), "utf8");
const langs = ["ko", "en", "es", "fr", "ar", "vi", "id"];
const excluded = ["account", "thanks", "unlock"];
const sections = headers.split(/(?=^\/[^\s]+\s*$)/m);

test("every localized account/thanks/unlock route has noindex response headers", () => {
  for (const lang of langs) for (const route of excluded) {
    const pattern = `/${lang}/${route}/*`;
    const section = sections.find(s => s.trimStart().startsWith(pattern + "\n"));
    assert.ok(section, `Missing rule: ${pattern}`);
    assert.match(section, /^\s+X-Robots-Tag: noindex, nofollow, noarchive\s*$/m);
  }
});

test("original asset and data cache headers are preserved", () => {
  assert.match(headers, /\/assets\/\*\s*\n\s*Cache-Control: public, max-age=604800/m);
  assert.match(headers, /\/data\/\*\s*\n\s*Cache-Control: public, max-age=3600/m);
});

test("public homepage and prepare routes have no blanket noindex rule", () => {
  for (const lang of langs) {
    assert.equal(headers.includes(`/${lang}/*\n  X-Robots-Tag: noindex`), false);
    assert.equal(headers.includes(`/${lang}/prepare/*\n  X-Robots-Tag: noindex`), false);
  }
});
