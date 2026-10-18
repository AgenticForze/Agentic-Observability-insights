import asyncio, re, pathlib
from playwright.async_api import async_playwright

D = pathlib.Path(__file__).parent
qr = (D / "qr.svg").read_text()
qr = re.sub(r"<\?xml[^>]*\?>", "", qr)
qr = re.sub(r'width="[^"]*mm" height="[^"]*mm"', "", qr, count=1)
html = (D / "carousel.html").read_text().replace("__QR__", qr)
(D / "carousel_built.html").write_text(html)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.goto((D / "carousel_built.html").as_uri())
        await pg.evaluate("document.fonts.ready")
        fonts = await pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight)")
        print("fonts loaded:", fonts)
        # overflow check: content must stay above the footer
        issues = await pg.evaluate("""[...document.querySelectorAll('.slide')].map((s,i)=>{
          const foot=s.querySelector('.foot').getBoundingClientRect().top;
          let maxB=0; s.querySelectorAll(':scope > *:not(.foot)').forEach(e=>{maxB=Math.max(maxB,e.getBoundingClientRect().bottom)});
          return {slide:i+1, gap:Math.round(foot-maxB), overflowX: s.scrollWidth>1080};
        }).filter(r=>r.gap<24||r.overflowX)""")
        print("layout issues:", issues or "none")
        slides = await pg.query_selector_all(".slide")
        for i, s in enumerate(slides, 1):
            await s.screenshot(path=str(D / f"slide-{i:02d}.png"))
        await pg.pdf(path=str(D / "observability-own-the-signal.pdf"), width="1080px", height="1350px", print_background=True)
        await b.close()

asyncio.run(main())
