# design_diff — render & compare E-com design vs Django site
Dev tooling, no deps (Node >= 22, system Chrome, Pillow from .venv for pairs).

    # reference (design served over HTTP)
    node tools/design_diff/render.mjs --serve E-com --url "{SERVE}/Product.dc.html" --out ../Замки_context/ref --name product
    # site (runserver on :8000 must be up)
    node tools/design_diff/render.mjs --url http://127.0.0.1:8000/product/<slug>/ --out ../Замки_context/site --name product
    # states: --click "Доставка" --click "35×35"
    node tools/design_diff/compare.mjs ../Замки_context/ref/product_1440.json ../Замки_context/site/product_1440.json
    .venv/bin/python tools/design_diff/pair.py ref.png site.png pair.png

Thresholds: page height ±3%, matched element w/h ±2px, identical font family/size/weight/line-height.
Always: hard timeout, Chrome + http.server killed on exit.
