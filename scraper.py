#!/usr/bin/env python3
"""Scrape emotiv.com into static HTML with local assets."""

import os
import re
import hashlib
import base64
import urllib.parse
import urllib.request
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.emotiv.com"
OUTPUT_DIR = Path("/Users/thenom4design/Documents/emotiv-static")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

def fetch(url, binary=False):
    """Fetch URL content."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content if binary else resp.text
    except Exception as e:
        print(f"WARN: Failed to fetch {url}: {e}")
        return None

def safe_filename(url):
    """Create a safe filename from URL."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        path = "index"
    # Keep extension
    name = Path(path).name
    if not name or "/" in name:
        name = hashlib.md5(url.encode()).hexdigest()[:12]
    # Sanitize
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return name

def download_asset(url, subfolder):
    """Download asset and return relative path."""
    if url.startswith("data:"):
        return url  # Already inline
    
    # Absolute URL
    if url.startswith("http"):
        abs_url = url
    elif url.startswith("//"):
        abs_url = "https:" + url
    elif url.startswith("/"):
        abs_url = BASE_URL + url
    else:
        abs_url = urllib.parse.urljoin(BASE_URL + "/", url)
    
    fname = safe_filename(abs_url)
    # Ensure extension
    if "." not in fname[-6:]:
        # Guess from URL or content-type
        if ".woff2" in abs_url:
            fname += ".woff2"
        elif ".woff" in abs_url:
            fname += ".woff"
        elif ".ttf" in abs_url:
            fname += ".ttf"
        elif ".mjs" in abs_url:
            fname += ".mjs"
        elif ".css" in abs_url:
            fname += ".css"
        elif ".js" in abs_url:
            fname += ".js"
        elif ".png" in abs_url:
            fname += ".png"
        elif ".jpg" in abs_url or ".jpeg" in abs_url:
            fname += ".jpg"
        elif ".svg" in abs_url:
            fname += ".svg"
        elif ".webp" in abs_url:
            fname += ".webp"
        elif ".mp4" in abs_url:
            fname += ".mp4"
        elif ".webm" in abs_url:
            fname += ".webm"
        else:
            fname += ".bin"
    
    dest_dir = OUTPUT_DIR / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / fname
    
    # Skip if exists
    if dest_path.exists():
        return f"./{subfolder}/{fname}"
    
    data = fetch(abs_url, binary=True)
    if data is None:
        return url  # Keep original on failure
    
    # For small images (< 20KB), inline as base64
    if subfolder in ("images",) and len(data) < 20 * 1024:
        mime = "image/png"
        if ".jpg" in fname or ".jpeg" in fname:
            mime = "image/jpeg"
        elif ".svg" in fname:
            mime = "image/svg+xml"
        elif ".webp" in fname:
            mime = "image/webp"
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    
    dest_path.write_bytes(data)
    print(f"  -> {subfolder}/{fname}")
    return f"./{subfolder}/{fname}"

def process_css(css_text, css_url):
    """Find url() references in CSS and rewrite them."""
    def replace_url(match):
        url = match.group(1).strip("'\"")
        # Skip data URIs and absolute HTTP (keep as-is for fonts from google)
        if url.startswith("data:"):
            return match.group(0)
        if "fonts.gstatic.com" in url or "fonts.googleapis" in url:
            return match.group(0)  # Keep google fonts remote
        
        new_url = download_asset(url, "assets")
        if new_url.startswith("data:"):
            return f"url({new_url})"
        return f"url({new_url})"
    
    return re.sub(r'url\(([^)]+)\)', replace_url, css_text)

def main():
    print("Fetching main page...")
    html = fetch(BASE_URL)
    if not html:
        print("Failed to fetch main page")
        return
    
    soup = BeautifulSoup(html, "lxml")
    
    # Process CSS links
    print("Processing CSS...")
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if not href:
            continue
        if "fonts.googleapis.com" in href:
            continue  # Keep Google Fonts remote
        
        css_text = fetch(href)
        if css_text:
            processed_css = process_css(css_text, href)
            # Save as inline <style> to avoid CORS/path issues
            style_tag = soup.new_tag("style")
            style_tag.string = processed_css
            link.replace_with(style_tag)
        else:
            print(f"  WARN: Could not fetch CSS {href}")
    
    # Process JS scripts
    print("Processing JS...")
    for script in soup.find_all("script", src=True):
        src = script.get("src")
        if not src:
            continue
        # Skip external analytics and tag managers
        if any(x in src for x in ["googletagmanager", "gtm", "analytics", "gomega", "cdn.", "framer.com/edit"]):
            script.decompose()
            continue
        
        new_src = download_asset(src, "js")
        if not new_src.startswith("data:"):
            script["src"] = new_src
        else:
            # Can't easily inline JS as data URI in src, keep remote or remove
            pass
    
    # Rename .bin files in js folder to .js if they contain JS
    js_dir = OUTPUT_DIR / "js"
    if js_dir.exists():
        for f in js_dir.glob("*.bin"):
            try:
                content = f.read_text(errors='ignore')
                if content.strip().startswith(("function", "var", "const", "let", "(", "!function", "window.", "document.")):
                    new_name = f.with_suffix(".js")
                    f.rename(new_name)
                    print(f"  -> renamed {f.name} to {new_name.name}")
            except Exception:
                pass
    
    # Process images
    print("Processing images...")
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            if "framerusercontent.com" in src or "emotiv.com" in src or src.startswith("http"):
                new_src = download_asset(src, "images")
                img["src"] = new_src
        
        srcset = img.get("srcset")
        if srcset:
            parts = []
            for part in srcset.split(","):
                items = part.strip().split(" ")
                if items:
                    url = items[0]
                    descriptor = " ".join(items[1:])
                    new_url = download_asset(url, "images")
                    parts.append(f"{new_url} {descriptor}".strip())
            img["srcset"] = ", ".join(parts)
    
    # Process source tags (picture elements)
    for source in soup.find_all("source"):
        srcset = source.get("srcset")
        if srcset:
            parts = []
            for part in srcset.split(","):
                items = part.strip().split(" ")
                if items:
                    url = items[0]
                    descriptor = " ".join(items[1:])
                    new_url = download_asset(url, "images")
                    parts.append(f"{new_url} {descriptor}".strip())
            source["srcset"] = ", ".join(parts)
    
    # Process video posters and sources
    print("Processing videos...")
    for video in soup.find_all("video"):
        poster = video.get("poster")
        if poster:
            video["poster"] = download_asset(poster, "images")
        for source in video.find_all("source"):
            src = source.get("src")
            if src:
                source["src"] = download_asset(src, "videos")
    
    # Also catch background videos / data-src patterns
    for div in soup.find_all("div"):
        for attr in ["data-src", "data-video", "data-bg", "data-poster"]:
            val = div.get(attr)
            if val and any(ext in val.lower() for ext in [".mp4", ".webm", ".mov", ".ogg"]):
                div[attr] = download_asset(val, "videos")
            elif val and any(ext in val.lower() for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
                div[attr] = download_asset(val, "images")
    
    # Process links (icons, preconnect, etc)
    for link in soup.find_all("link"):
        href = link.get("href")
        if href and link.get("rel") == ["icon"]:
            link["href"] = download_asset(href, "images")
        if href and link.get("rel") == ["apple-touch-icon"]:
            link["href"] = download_asset(href, "images")
    
    # Process meta tags with image URLs
    for meta in soup.find_all("meta"):
        content = meta.get("content", "")
        if content.startswith("http") and any(x in content for x in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
            meta["content"] = download_asset(content, "images")
    
    # Remove tracking/noscript tags
    for noscript in soup.find_all("noscript"):
        # Check if it's GTM noscript
        text = str(noscript)
        if "gtm" in text.lower() or "googletagmanager" in text.lower():
            noscript.decompose()
    
    # Remove inline scripts that are tracking
    for script in soup.find_all("script"):
        text = script.string or ""
        if "gtm" in text.lower() or "dataLayer" in text or "gomega" in text.lower():
            script.decompose()
    
    # Convert soup back to string for regex pass
    html_str = str(soup)
    
    # Generic regex pass: find all https?:// URLs that look like assets and replace them
    print("Doing regex pass for remaining assets...")
    
    # Find image URLs
    def replace_image_url(match):
        url = match.group(0)
        # Skip already processed or non-asset URLs
        if url.startswith("data:") or "fonts.googleapis" in url or "fonts.gstatic" in url:
            return url
        if any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]):
            return download_asset(url, "images")
        return url
    
    # Find video URLs
    def replace_video_url(match):
        url = match.group(0)
        if url.startswith("data:"):
            return url
        if any(ext in url.lower() for ext in [".mp4", ".webm", ".mov", ".ogg"]):
            return download_asset(url, "videos")
        return url
    
    # Regex for URLs in quotes or as bare URLs
    # Be careful not to replace URLs inside HTML attributes that we've already handled
    # Look for framerusercontent.com and emotiv CDN URLs specifically
    html_str = re.sub(
        r'https://framerusercontent\.com/images/[^\s"\'\)>]+',
        replace_image_url,
        html_str
    )
    html_str = re.sub(
        r'https://horizon-cdn\.emotiv\.com/[^\s"\'\)>]+',
        replace_video_url,
        html_str
    )
    
    # Save final HTML
    output_html = OUTPUT_DIR / "index.html"
    output_html.write_text(html_str)
    print(f"\nDone. Saved to {output_html}")
    
    # Print stats
    sizes = {}
    for subdir in ["images", "js", "assets", "videos"]:
        d = OUTPUT_DIR / subdir
        if d.exists():
            sizes[subdir] = sum(f.stat().st_size for f in d.iterdir() if f.is_file())
    print(f"Assets: {sizes}")

if __name__ == "__main__":
    main()
