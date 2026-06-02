import re

with open('index.html') as f:
    html = f.read()

with open('styles.css') as f:
    css = f.read()

tags = re.findall(r'<\w+', html)
total = len(tags)
divs = sum(1 for t in tags if t == '<div')
print(f"HTML: {len(html):,} bytes")
print(f"Total tags: {total} (divs: {divs})")
print(f"data-framer attrs: {len(re.findall(r'data-framer-', html))}")
print(f"Inline styles: {len(re.findall(r'style="', html))}")
print(f"<style> blocks: {len(re.findall(r'<style', html))}")
print(f"Script tags: {len(re.findall(r'<script', html))}")
print(f"Framer classes: {len(re.findall(r'framer-', html))}")
print(f"CSS size: {len(css):,} bytes")
print(f"CSS @media: {len(re.findall(r'@media', css))}")
print(f"CSS rules: {len(re.findall(r'}', css))}")
