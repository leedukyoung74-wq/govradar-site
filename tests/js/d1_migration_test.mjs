// Migration check: a database made with 0001 and holding data, updated with 0002, keeps its rows and ends with
// the same tables/columns as a fresh database made from schema.sql. Run: node --experimental-sqlite tests/js/d1_migration_test.mjs
import { DatabaseSync } from "node:sqlite"; import fs from "node:fs"; import path from "node:path"; import { fileURLToPath } from "node:url";
const R = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..") + "/cf/d1/";
const shape = db => Object.fromEntries(db.prepare("select name from sqlite_master where type in ('table','trigger') and name not like 'sqlite_%' order by name").all()
  .map(t => [t.name, db.prepare(`select name from pragma_table_info('${t.name}') order by name`).all().map(c => c.name).join(",")]));
const fresh = new DatabaseSync(":memory:"); fresh.exec(fs.readFileSync(R + "schema.sql", "utf8"));
const old = new DatabaseSync(":memory:"); old.exec(fs.readFileSync(R + "migrations/0001_requests.sql", "utf8"));
old.exec("insert into requests (req_no, created_at, month, user_key, email, type, body, dedupe) values ('RQ-OLD-1','2026-11-01T00:00:00Z','2026-11','u:a','a@example.com','tender','keep me','d')");
old.exec(fs.readFileSync(R + "migrations/0002_retention.sql", "utf8"));
const fail = [], a = shape(fresh), b = shape(old);
for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) if (a[k] !== b[k]) fail.push(`${k}: fresh=${a[k]} migrated=${b[k]}`);
const row = old.prepare("select body, purge_body_at, legal_hold from requests where req_no='RQ-OLD-1'").get();
if (!(row && row.body === "keep me" && row.purge_body_at && row.legal_hold === 0)) fail.push("row:" + JSON.stringify(row));
if (old.prepare("select v from schema_version").get().v !== 2 || fresh.prepare("select v from schema_version").get().v !== 2) fail.push("version");
old.exec("update requests set status='done' where req_no='RQ-OLD-1'");
if (!old.prepare("select completed_at from requests where req_no='RQ-OLD-1'").get().completed_at) fail.push("trigger-after-migration");
if (fail.length) { console.error("FAIL", fail.join(" | ")); process.exit(1); } else console.log("d1_migration OK");
