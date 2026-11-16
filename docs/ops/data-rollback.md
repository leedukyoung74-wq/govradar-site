# Restoring the previous good feed data (data branch)

The public site reads `feeds/*.json` from the `data` branch in the browser, so a bad feed shows up on the site within minutes
and a restore also shows up within minutes. No site (live) deploy is involved. Every collection run is one commit on `data`,
and nothing ever force-pushes it, so every earlier state is still there.

## 1. Stop the next run from overwriting the fix (owner)
GitHub → Actions → "Scheduled feeds" → ⋯ → Disable workflow. (Or `gh workflow disable schedule.yml`.)

## 2. Find the bad run
GitHub → branch `data` → History. Feed runs are titled `Feed daily <time>`. Note the commit id of the first bad one.
`git show --stat <bad>` lists exactly which files it changed.

## 3. Undo that run as a new commit (no force push)
```
git clone --branch data --single-branch https://github.com/leedukyoung74-wq/govradar-site.git data && cd data
git revert --no-edit <bad>          # repeat for each bad run, newest first
python3 -c "import json;t=json.load(open('feeds/tenders.json'));print(t['updated'],t['count'])"   # sanity check
git push origin HEAD:data
```
`git revert` restores files the run modified and removes files it added, and leaves other jobs' commits
(for example `Situation summary`) untouched. If a later run changed the same files, revert the later runs too.

## 4. Check the site, then re-enable the schedule
`python tools/check_site.py` (from src) must print `"result": "PASS"`. Then re-enable "Scheduled feeds".

## Rehearsal (2026-11-16, not pushed)
On a scratch clone of `data`, `git revert --no-edit e53cc40` (the first run after PR #1) produced a tree byte-identical to the
state before it (`261fc41`): tenders.json back to 2026-11-16T03:39Z / 905 notices, the 155 files the run touched restored or removed.
