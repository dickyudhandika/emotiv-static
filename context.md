# Emotiv Static Site

## Stack
- **Type**: Static HTML (extracted from Framer)
- **Hosting**: Cloudflare Workers (`workers_dev: true`)
- **URL**: https://emotiv-static.dicky-996.workers.dev
- **Build step**: None (plain static, `wrangler deploy`)

## Structure
- `index.html` — single-page site (937 KB after optimization)
- `styles.css` — externalized CSS (430 KB, extracted from inline <style>)
- `images/` — all WebP format, no JPEG/PNG remaining
- `videos/` — hero_section.mp4 (5.5 MB) + real_world_neuroscience.mp4 (13.5 MB)

## Recent Changes
- 2026-06-02: Perf overhaul — externalized CSS, decoded 32 base64 images to files, fixed heading hierarchy, added aria-labels, video captions, LCP preload, converted all images to WebP. HTML dropped from 2,028 KB → 937 KB. Lighthouse mobile: Perf 87→TBD, A11y 91→TBD.

## Notes
- Deployed via `wrangler deploy` from root
- No JS framework — pure static HTML + CSS
- Videos have poster + preload="none" + captions track
