"""Build a new Cloudflare review directory from an existing GOV RADAR dist."""
import argparse
import re
import shutil
from pathlib import Path


OVERLAY = Path(__file__).resolve().parent
NETLIFY_FORM = re.compile(r'(<form\b[^>]*data-netlify="true"[^>]*?)action="(/[^\"]*)"')
WITH_TOKENS = '    const user = await j("/user", { headers: { authorization: "Bearer " + tok.access_token } });'
LOGOUT = '  function logout() { const t = S && S.access_token;'
LOGOUT_HANDLER = 'lo.addEventListener("click", () => { window.WMMAuth.logout(); location.href = "/" + (window.RADAR_LANG || "en") + "/"; });'


def replace_one(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f'Expected exactly one occurrence in the source build: {old}')
    return text.replace(old, new, 1)


def prepare(source, output):
    dist = source / 'dist'
    if output == source or source in output.parents:
        raise SystemExit('Choose a new output directory outside the source project.')
    if output.exists():
        raise SystemExit('Output directory must be new.')
    if not (dist / 'assets' / 'auth.js').is_file() or not (source / 'cf' / 'extra' / 'intro' / 'index.html').is_file():
        raise SystemExit('Source must include a completed dist build and the Cloudflare sources.')

    auth = (dist / 'assets' / 'auth.js').read_text(encoding='utf-8')
    auth = replace_one(auth, WITH_TOKENS, WITH_TOKENS + '''
    const gate = await fetch("/gate/session", { method: "POST", headers: { authorization: "Bearer " + tok.access_token } });
    if (!gate.ok) throw new Error("Membership could not be verified");''')
    auth = replace_one(auth, LOGOUT, '''  async function logout() {
    const gate = await fetch("/gate/logout", { method: "POST" });
    if (!gate.ok) throw new Error("Membership session could not be closed");
    const t = S && S.access_token;''')
    site = (dist / 'assets' / 'site.js').read_text(encoding='utf-8')
    site = replace_one(site, LOGOUT_HANDLER, '''lo.addEventListener("click", async () => {
    lo.disabled = true;
    try {
      await window.WMMAuth.logout();
      location.href = "/access/" + (window.RADAR_LANG || "en") + "/";
    } catch {
      lo.disabled = false;
      alert((window.RADAR_LANG || "en") === "ko" ? "로그아웃을 완료하지 못했습니다." : "Sign-out could not be completed.");
    }
  });''')

    public = output / 'public'
    shutil.copytree(dist, public, ignore=shutil.ignore_patterns('private'))
    shutil.copytree(source / 'cf' / 'extra', public, dirs_exist_ok=True, ignore=shutil.ignore_patterns('private'))
    shutil.copytree(source / 'cf' / 'functions', output / 'functions')
    shutil.copytree(OVERLAY / 'public', public, dirs_exist_ok=True)
    shutil.copytree(OVERLAY / 'functions', output / 'functions', dirs_exist_ok=True)
    shutil.copy2(OVERLAY / 'package.json', output / 'package.json')
    (public / 'assets' / 'auth.js').write_text(auth, encoding='utf-8')
    (public / 'assets' / 'site.js').write_text(site, encoding='utf-8')

    for page in public.rglob('*.html'):
        html = page.read_text(encoding='utf-8')
        updated = NETLIFY_FORM.sub(r'\1action="/nfform?next=\2"', html)
        if updated != html:
            page.write_text(updated, encoding='utf-8')
    print(f'Prepared review project: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.source.resolve(), args.output.resolve())
