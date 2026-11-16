Only for Cloudflare Pages preview builds of branches other than `live`.
The project publishes a top-level `public/` folder with no build step; `live` has the real site there, other branches
had none, so every preview build failed with `Error: Output directory "public" not found.` (log 2026-11-16).
This folder makes those previews succeed and send visitors to https://radar.wmm-hoa.com. It is never part of the real site.
