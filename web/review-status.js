/* WMM GOV RADAR review-status v1: conservative, evidence-aware display labels.
 * Works in browser and Node.js. NEVER upgrades a record to 'verified' based on a URL.
 */
(function (root) {
  'use strict';
  function dateOnly(raw) {
    if (typeof raw !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;
    const value = Date.parse(raw + 'T00:00:00Z');
    return Number.isFinite(value) && new Date(value).toISOString().slice(0, 10) === raw ? raw : null;
  }
  function safeUrl(raw) {
    if (typeof raw !== 'string' || raw.length > 2048) return null;
    try {
      const url = new URL(raw);
      return (['http:', 'https:'].includes(url.protocol) && url.hostname) ? url.href : null;
    } catch (_) { return null; }
  }
  function evaluate(item, snapshot, todayUTC) {
    const row = item || {};
    const today = dateOnly(todayUTC) || new Date().toISOString().slice(0,10);
    const source = safeUrl(row.source_url || row.sourceUrl || row.url || row.source);
    const deadline = dateOnly(row.deadline);
    const snapshotDate = dateOnly(snapshot);
    const snapshotDays = snapshotDate ? Math.floor((Date.parse(today+'T00:00:00Z') - Date.parse(snapshotDate+'T00:00:00Z'))/86400000) : null;
    const reasons = [];
    if (!source) reasons.push('SOURCE_UNVERIFIED');
    if (!row.deadline) reasons.push('DEADLINE_UNKNOWN');
    else if (!deadline) reasons.push('DEADLINE_INVALID');
    else if (deadline < today) reasons.push('DEADLINE_PASSED');
    if (snapshotDays === null) reasons.push('SNAPSHOT_DATE_UNKNOWN');
    else if (snapshotDays > 30) reasons.push('SNAPSHOT_STALE');
    else if (snapshotDays < 0) reasons.push('SNAPSHOT_FUTURE_DATE');
    return {
      sourceUrl: source, deadline,
      deadlineStatus: !row.deadline ? 'unknown' : !deadline ? 'invalid' : deadline < today ? 'passed' : deadline === today ? 'today' : 'future',
      sourceStatus: source ? 'link_present_not_verified' : 'missing',
      freshnessStatus: snapshotDays === null ? 'unknown' : snapshotDays < 0 ? 'invalid' : snapshotDays > 30 ? 'stale' : 'recorded',
      verified: false, // independent verification must be recorded by the editorial review workflow
      commercialStatus: 'unverified_hypothesis',
      reasons
    };
  }
  const api = Object.freeze({ dateOnly, safeUrl, evaluate });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.WMMReviewStatus = api;
})(typeof window !== 'undefined' ? window : globalThis);
