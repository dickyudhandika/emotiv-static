# Emotiv Static Site

## Stack
- **Type**: Static HTML (extracted from Framer)
- **Hosting target**: Cloudflare Pages via GitHub
- **Build step**: None (plain static)

## Structure
- `index.html` — single-page site (hero, features, testimonials, footer)
- `images/` — downloaded image assets
- `videos/` — downloaded video assets
- `js/` — minimal JS (mostly stripped; Framer hydration removed)

## Recent Changes
- Extracted emotiv.com homepage into self-contained static HTML
- Stripped all Framer JavaScript animations and hydration scripts
- All content now renders immediately without JS
- Converted remote image/video URLs to local relative paths

## Notes
- Ready for Cloudflare Pages deployment
- No build command needed; output directory is root `/`
