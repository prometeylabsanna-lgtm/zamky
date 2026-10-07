"""Side-by-side pair: python pair.py REF.png SITE.png OUT.png  (ref left, site right, magenta gutter)."""
import sys
from PIL import Image
a, b = (Image.open(p).convert('RGB') for p in sys.argv[1:3])
o = Image.new('RGB', (a.width + b.width + 20, max(a.height, b.height)), (255, 0, 255))
o.paste(a, (0, 0)); o.paste(b, (a.width + 20, 0)); o.save(sys.argv[3])
