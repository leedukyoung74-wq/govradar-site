# GOV RADAR — site source (src branch)

Builds https://radar.wmm-hoa.com. Not deployed by Netlify (see netlify.toml).

Rebuild:
1. Export the ArtifactData collection "countries" of https://claude.ai/artifact/Atb1axCgRgoAShwSPRNN8e into export/countries/*.json
2. `python3 build.py` → dist/
3. Copy dist/ to the `main` branch and push (Netlify deploys main; 15 credits per deploy).
4. Member-only analysis: build writes private/m/**; `python3 tools/member.py encrypt` writes data_branch/m/** → push to the `data` branch (no Netlify deploy).

Never commit export/ (contains member-only analysis), private/ (master key, member codes) or dist/.
