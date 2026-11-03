#!/usr/bin/env python3
"""
Verificação do site gerado.

    python3 build.py && python3 ferramentas/testes.py

Sobe um servidor local sobre build/dist, abre as páginas num Chromium e
verifica. Sai com código 1 se algo falhar, então serve em CI.

Precisa de:  pip install playwright && python3 -m playwright install chromium

Cada bloco aqui nasceu de um defeito que passou despercebido uma vez.
Antes de remover uma verificação, leia o comentário dela.
"""
import contextlib
import functools
import http.server
import re
import socket
import socketserver
import sys
import threading
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
DIST = RAIZ / "build" / "dist"

ok: list[str] = []
falhas: list[str] = []


def ck(condicao, mensagem: str) -> None:
    (ok if condicao else falhas).append(mensagem)


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def servidor(pasta: Path):
    if not pasta.exists():
        raise SystemExit(f"{pasta} não existe — rode 'python3 build.py' antes")
    porta = porta_livre()

    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # o servidor não precisa narrar cada GET
            pass

    handler = functools.partial(Silencioso, directory=str(pasta))
    httpd = socketserver.TCPServer(("127.0.0.1", porta), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{porta}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def rotas() -> list[str]:
    sm = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    saida = []
    for u in re.findall(r"<loc>(.*?)</loc>", sm):
        # tira o domínio e, se houver, o prefixo do repositório
        r = re.sub(r"^https?://[^/]+(/[^/]+)?", "", u) or "/"
        saida.append(r if r.startswith("/") else "/" + r)
    return saida


def executar(base: str) -> None:
    ROTAS = rotas()
    print(f"{len(ROTAS)} páginas no sitemap")

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        erros: list[str] = []
        d = navegador.new_context(viewport={"width": 1440, "height": 900}).new_page()
        d.on("pageerror", lambda e: erros.append(str(e)))
        d.on(
            "console",
            lambda m: erros.append(m.text)
            if (m.type == "error" and "Failed to load resource" not in m.text)
            else None,
        )

        for r in ROTAS:
            resp = d.goto(base + r, wait_until="networkidle")
            ck(resp.status == 200, f"{r} responde 200")
            ck(d.evaluate("document.querySelectorAll('h1').length") == 1, f"{r} um H1")
            ck(
                "Playfair"
                in d.evaluate("getComputedStyle(document.querySelector('h1')).fontFamily"),
                f"{r} CSS aplicado",
            )
            ck(d.evaluate("!!document.querySelector('link[rel=canonical]')"), f"{r} canônica")
            ck(
                d.evaluate("Array.from(document.images).filter(i=>!i.alt).length") == 0,
                f"{r} imagens com alt",
            )
            d.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            d.wait_for_timeout(1200)
            ck(
                d.evaluate(
                    "Array.from(document.images)"
                    ".filter(i=>!i.complete||i.naturalWidth===0).length"
                )
                == 0,
                f"{r} sem imagem quebrada",
            )
            ck(
                d.evaluate(
                    "document.documentElement.scrollWidth"
                    "-document.documentElement.clientWidth"
                )
                <= 0,
                f"{r} sem rolagem horizontal",
            )

            texto = d.evaluate("document.body.innerText")
            # Direito de Família saiu do escopo; já sobrou resíduo em
            # metadados e textos depois da remoção.
            ck("Direito de Família" not in texto, f"{r} sem a área removida")
            # Marcadores pendentes não podem vazar para o site publicado.
            ck("ENDEREÇO" not in texto, f"{r} sem marcador de endereço")
            ck(
                d.evaluate("document.querySelector('meta[name=robots]')?.content")
                == ("noindex, nofollow" if EM_REVISAO else "index, follow"),
                f"{r} meta robots coerente com em_revisao",
            )

            # Links internos precisam resolver de verdade.
            ruins = []
            alvos = d.evaluate(
                """Array.from(document.querySelectorAll(
                     'a:not([href^="http"]):not([href^="mailto"]):not([href^="tel"])'
                   )).map(a=>a.href)"""
            )
            for l in set(alvos):
                try:
                    urllib.request.urlopen(l, timeout=5)
                except Exception:
                    ruins.append(l.replace(base, ""))
            ck(not ruins, f"{r} links internos resolvem ({ruins[:2]})")

            # Os atributos width/height do HTML já anularam o aspect-ratio do
            # CSS e deixaram uma foto renderizando a 456x1955.
            deformadas = d.evaluate(
                """Array.from(document.images)
                   .filter(i=>{const b=i.getBoundingClientRect();
                               return b.width>0 &&
                                 (b.width/b.height<0.3 || b.width/b.height>4);})
                   .map(i=>(i.currentSrc||i.src).split('/').pop())"""
            )
            ck(not deformadas, f"{r} sem imagem deformada ({deformadas[:2]})")

        # --- Cabeçalho em toda a faixa de larguras.
        # Uma regra com especificidade alta demais (img[width][height]) já
        # venceu .marca img e fez o logotipo renderizar em tamanho natural,
        # esticando o cabeçalho e quebrando o menu em três linhas.
        for w in (360, 390, 414, 768, 900, 1024, 1100, 1280, 1440, 1920):
            ctx = navegador.new_context(viewport={"width": w, "height": 800})
            pw = ctx.new_page()
            pw.goto(base + "/", wait_until="networkidle")
            pw.wait_for_timeout(300)
            m = pw.evaluate(
                """(()=>{
                  const c=document.querySelector('.cabecalho__interno');
                  const l=document.querySelector('.marca img');
                  const nav=document.querySelector('.nav');
                  const linhas=e=>{const r=document.createRange();
                                   r.selectNodeContents(e);
                                   return r.getClientRects().length;};
                  const multi=Array.from(
                      document.querySelectorAll('.nav__link, .cabecalho__acao'))
                    .filter(e=>e.offsetParent!==null && linhas(e)>1)
                    .map(e=>e.textContent.trim().slice(0,18));
                  return {cab:Math.round(c.getBoundingClientRect().height),
                          logo:Math.round(l.getBoundingClientRect().height),
                          navVisivel:getComputedStyle(nav).display!=='none',
                          multi,
                          over:document.documentElement.scrollWidth
                               -document.documentElement.clientWidth};})()"""
            )
            ck(m["cab"] <= 110, f'{w}px: cabeçalho com altura sã ({m["cab"]}px)')
            ck(30 <= m["logo"] <= 70, f'{w}px: logotipo dimensionado ({m["logo"]}px)')
            ck(not m["multi"], f'{w}px: nada quebra em duas linhas ({m["multi"][:2]})')
            ck(m["over"] <= 0, f"{w}px: sem rolagem horizontal")
            ck(m["navVisivel"] == (w >= 1024), f"{w}px: menu certo para a largura")
            ctx.close()

        # --- Responsividade das páginas inteiras.
        for w in (320, 414, 768, 1024, 1440, 1920):
            ctx = navegador.new_context(
                viewport={"width": w, "height": 800}, is_mobile=w < 768
            )
            pm = ctx.new_page()
            for r in ROTAS:
                pm.goto(base + r, wait_until="networkidle")
                pm.wait_for_timeout(150)
                res = pm.evaluate(
                    """(()=>{const vw=document.documentElement.clientWidth;
                      // o link "pular para o conteúdo" fica fora da tela de
                      // propósito até receber foco
                      const vaza=Array.from(document.querySelectorAll('body *'))
                        .filter(e=>{
                          if(e.classList.contains('pular-para-conteudo')) return false;
                          const b=e.getBoundingClientRect();
                          return b.width>0 && (b.right>vw+1 || b.left<-1);})
                        .slice(0,2)
                        .map(e=>e.tagName+'.'+(e.className?String(e.className).split(' ')[0]:''));
                      const alvos=Array.from(document.querySelectorAll(
                          'a.btn,button,.canal,.hamburguer'))
                        .filter(e=>e.offsetParent &&
                                   e.getBoundingClientRect().height<44).length;
                      return {over:document.documentElement.scrollWidth-vw,
                              vaza, alvos};})()"""
                )
                ck(res["over"] <= 0, f"{w}px {r}: sem rolagem horizontal")
                ck(not res["vaza"], f'{w}px {r}: nada vaza a lateral ({res["vaza"]})')
                ck(res["alvos"] == 0, f"{w}px {r}: alvos de toque ≥ 44px")
            ctx.close()

        ck(not erros, f"sem erros de JavaScript ({erros[:2]})")
        navegador.close()


if __name__ == "__main__":
    import json

    EM_REVISAO = json.loads(
        (RAIZ / "data" / "site.json").read_text(encoding="utf-8")
    ).get("em_revisao", False)
    print(f"em_revisao = {EM_REVISAO}")
    with servidor(DIST) as base:
        executar(base)
    print(f"\n{len(ok)} verificações passaram.")
    if falhas:
        print("FALHAS:")
        for f in falhas:
            print("  x", f)
    else:
        print("Nenhuma falha.")
    sys.exit(1 if falhas else 0)
