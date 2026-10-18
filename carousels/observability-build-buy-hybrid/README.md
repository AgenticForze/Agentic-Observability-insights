# Carousel: Own the signal, rent the screen

- `observability-own-the-signal.pdf`: the file to upload to LinkedIn as a document post (10 slides, 1080x1350).
- `source.html`: slide source. `render.py` rebuilds the PDF and slide PNGs.
- `qr.svg`: QR code for https://agenticforze.github.io/Agentic-Observability-insights/

To rebuild, install the fonts next to the render script and run it:

```bash
npm i @fontsource/bricolage-grotesque@5.1.0 @fontsource/source-sans-3@5.1.0 @fontsource/jetbrains-mono@5.1.0
cp source.html carousel.html && sed -i 's#../../node_modules/#node_modules/#' carousel.html
pip install playwright && python render.py
```

Copy for the post (caption and first comment) is in `../observability-build-buy-hybrid.yaml`.
