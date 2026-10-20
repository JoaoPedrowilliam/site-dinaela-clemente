#!/usr/bin/env python3
"""
Build do site de Daniela Clemente — Advogada.

Gera duas saídas a partir da mesma fonte:
  build/dist/      site estático multipágina, com URLs limpas (para hospedagem)
  build/preview.html   arquivo único navegável, com imagens embutidas (para revisão)

Uso:  python3 build.py
"""

import json
import base64
import shutil
import os
import re
import html
from pathlib import Path

RAIZ = Path(__file__).parent
SRC = RAIZ / "src"
DIST = RAIZ / "build" / "dist"

SITE = json.loads((RAIZ / "data" / "site.json").read_text(encoding="utf-8"))
AREAS = json.loads((RAIZ / "data" / "areas.json").read_text(encoding="utf-8"))
ARTIGOS = [
    a for a in json.loads((RAIZ / "data" / "artigos.json").read_text(encoding="utf-8"))
    if not a.get("rascunho")
]
ARTIGOS.sort(key=lambda a: a.get("data", ""), reverse=True)

MODO = "dist"  # alternado durante o build

# Prefixo de caminho. Vazio quando o site está na raiz do domínio;
# "/nome-do-repo" quando publicado em github.io/nome-do-repo/.
BASE = SITE.get("base_path", "").rstrip("/")

# Caminhos relativos: o site funciona na raiz do domínio, em qualquer subpasta
# e sobrevive à renomeação do repositório, sem precisar reconstruir.
RELATIVO = bool(SITE.get("caminhos_relativos", False))

_PROFUNDIDADE = 0  # profundidade da página em geração, só no modo relativo


def prefixo():
    """No modo relativo: '' na raiz, '../' um nível abaixo, e assim por diante."""
    if not RELATIVO:
        return (BASE + "/") if BASE else "/"
    return "../" * _PROFUNDIDADE


def rel(caminho):
    """Converte um caminho absoluto do site em um caminho válido na página atual."""
    if not RELATIVO:
        return (BASE + caminho) if BASE else caminho
    if caminho == "/":
        return prefixo() + "index.html"
    return prefixo() + caminho.lstrip("/")

# Enquanto o site estiver em revisão, com campos ainda em branco, ele não deve
# ser indexado: um site incompleto no nome de uma advogada aparecendo no Google
# é pior do que site nenhum.
EM_REVISAO = bool(SITE.get("em_revisao", False))
ROBOTS_META = "noindex, nofollow" if EM_REVISAO else "index, follow"

# Endereço público completo, usado em canônicas, sitemap e Open Graph.
RAIZ_PUBLICA = SITE["dominio"].rstrip("/") + BASE

WHATS = "https://wa.me/{}?text={}".format(
    SITE["telefone_e164"],
    SITE["mensagem_whatsapp"].replace(" ", "%20").replace(",", "%2C").replace(".", "%2E"),
)


# ---------------------------------------------------------------- utilidades

def preenchido(valor):
    """Um campo só conta como preenchido se não estiver vazio nem for um marcador."""
    return bool(valor) and not str(valor).strip().startswith("[")


def ph(texto):
    """Marca visualmente um valor ainda não fornecido pela cliente."""
    if isinstance(texto, str) and texto.strip().startswith("["):
        return f'<span class="pendente">{html.escape(texto)}</span>'
    return html.escape(str(texto))


def url(caminho):
    """Resolve links conforme o modo de build."""
    if MODO == "preview":
        if caminho == "/":
            return "#/"
        return "#" + caminho.rstrip("/")
    return rel(caminho)


def ativo(atual, alvo):
    return ' aria-current="page"' if atual == alvo else ""


def img(nome, alt, classe="", sizes="100vw", eager=False, ratio=None):
    """<picture> responsivo. No preview, embute a imagem em base64."""
    alt_esc = html.escape(alt)
    cls = f' class="{classe}"' if classe else ""
    carregamento = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    dims = ""
    if ratio:
        dims = f' width="{ratio[0]}" height="{ratio[1]}"'

    if MODO == "preview":
        dado = base64.b64encode((SRC / "img" / f"{nome}-760.webp").read_bytes()).decode()
        return (
            f'<img{cls} src="data:image/webp;base64,{dado}" alt="{alt_esc}" '
            f'{carregamento} decoding="async"{dims}>'
        )

    return (
        "<picture>"
        f'<source type="image/webp" sizes="{sizes}" '
        f'srcset="{prefixo()}assets/img/{nome}-520.webp 520w, {prefixo()}assets/img/{nome}-760.webp 760w, {prefixo()}assets/img/{nome}-1100.webp 1100w">'
        f'<img{cls} src="{prefixo()}assets/img/{nome}-760.jpg" alt="{alt_esc}" '
        f'{carregamento} decoding="async"{dims}>'
        "</picture>"
    )


def logo(variante="escuro"):
    """variante 'escuro' = logotipo original, para fundos claros.
       variante 'claro'  = logotipo invertido, para fundos escuros."""
    arquivo = "logo.png" if variante == "escuro" else "logo-claro.png"
    if MODO == "preview":
        dado = base64.b64encode((SRC / "img" / arquivo).read_bytes()).decode()
        return (f'<img src="data:image/png;base64,{dado}" '
                f'alt="Daniela Clemente — Advogada" width="504" height="196">')
    return (f'<img src="{prefixo()}assets/img/{arquivo}" '
            f'alt="Daniela Clemente — Advogada" width="504" height="196">')


ICONES = {
    "whatsapp": '<svg class="canal__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.7-5.2A8.5 8.5 0 1 1 21 11.5Z"/><path d="M8.6 9.3c.3 2.6 2.6 4.9 5.2 5.2l1-1.4 2 .9-.3 1.7c-3.7.5-7.6-3.4-8.1-8.1l1.7-.3.9 2-1.4 1Z"/></svg>',
    "telefone": '<svg class="canal__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 3h3.5l1.8 4.4-2.2 1.3a12 12 0 0 0 5.2 5.2l1.3-2.2L19 13.5V17a2 2 0 0 1-2.2 2A15.8 15.8 0 0 1 3 5.2 2 2 0 0 1 5 3Z"/></svg>',
    "email": '<svg class="canal__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14"/><path d="m2.5 6.5 9.5 7 9.5-7"/></svg>',
    "instagram": '<svg class="canal__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1"/></svg>',
    "local": '<svg class="canal__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M12 21s7-5.7 7-11a7 7 0 1 0-14 0c0 5.3 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/></svg>',
}

SOCIAL_WHATS = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.7-5.2A8.5 8.5 0 1 1 21 11.5Z"/></svg>'
SOCIAL_INSTA = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1"/></svg>'


# --------------------------------------------------- ícones das áreas
# Desenhados a partir da geometria do monograma: arcos abertos e círculos
# que se sobrepõem. Sem balança, martelo, coluna ou prédio.

def _svg(interno):
    return (
        '<svg class="icone-area" viewBox="0 0 48 48" fill="none" '
        'stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" focusable="false">{interno}</svg>'
    )


ICONES_AREA = {
    # Previdenciário — o anel é a vida de trabalho inteira; o arco em bronze
    # é a parte dela que efetivamente conta como tempo de contribuição.
    "direito-previdenciario": _svg(
        '<circle cx="24" cy="24" r="14"/>'
        '<path class="icone-area__acento" d="M24 10A14 14 0 1 1 19.2 37.2"/>'
        '<circle class="icone-area__acento" cx="24" cy="10" r="2.2" fill="currentColor" stroke="none"/>'
    ),
    # Inventários e Sucessões — o que foi construído por um se divide
    # e passa adiante para os que ficam.
    "inventarios-e-sucessoes": _svg(
        '<circle class="icone-area__acento" cx="24" cy="12" r="6"/>'
        '<path d="M24 18v7"/>'
        '<path d="M12 25h24"/>'
        '<path d="M12 25v5"/><path d="M36 25v5"/>'
        '<circle cx="12" cy="36" r="6"/>'
        '<circle cx="36" cy="36" r="6"/>'
    ),
}


# ---------------------------------------------------------------- navegação

NAV = [
    ("Início", "/"),
    ("Sobre", "/sobre/"),
    ("Áreas de Atuação", "/areas-de-atuacao/"),
    ("A Advogada", "/a-advogada/"),
    ("Conteúdos", "/conteudos/"),
    ("Contato", "/contato/"),
]


def cabecalho(atual):
    itens = ""
    for rotulo, destino in NAV:
        if destino == "/areas-de-atuacao/":
            sub = "".join(
                f'<a href="{url("/areas-de-atuacao/" + a["slug"] + "/")}">{a["titulo"]}</a>'
                for a in AREAS
            )
            itens += (
                '<div class="nav__grupo">'
                f'<a class="nav__link" href="{url(destino)}"{ativo(atual, destino)}>{rotulo}</a>'
                f'<div class="nav__submenu">'
                f'<a href="{url(destino)}">Visão geral</a>{sub}</div></div>'
            )
        else:
            itens += f'<a class="nav__link" href="{url(destino)}"{ativo(atual, destino)}>{rotulo}</a>'

    moveis = ""
    for rotulo, destino in NAV:
        moveis += f'<a class="menu-mobile__item" href="{url(destino)}">{rotulo}</a>'
        if destino == "/areas-de-atuacao/":
            moveis += '<div class="menu-mobile__sub">' + "".join(
                f'<a href="{url("/areas-de-atuacao/" + a["slug"] + "/")}">{a["titulo"]}</a>'
                for a in AREAS
            ) + "</div>"

    return f"""
<a class="pular-para-conteudo" href="#conteudo">Pular para o conteúdo</a>
<header class="cabecalho">
  <div class="env cabecalho__interno">
    <a class="marca" href="{url('/')}" aria-label="Daniela Clemente — Advogada, página inicial">{logo()}</a>
    <nav class="nav" aria-label="Navegação principal">{itens}</nav>
    <a class="btn btn--solido cabecalho__acao" href="{WHATS}" target="_blank" rel="noopener">Agendar uma conversa</a>
    <button class="hamburguer" aria-expanded="false" aria-controls="menu-mobile" aria-label="Abrir menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="menu-mobile" id="menu-mobile">
  {moveis}
  <a class="btn btn--solido" href="{WHATS}" target="_blank" rel="noopener">Agendar uma conversa</a>
</div>"""


def rodape():
    linha_endereco_rodape = (
        f"          <li>{ph(SITE['endereco'])}</li>\n"
        if preenchido(SITE["endereco"]) else ""
    )
    links_areas = "".join(
        f'<li><a href="{url("/areas-de-atuacao/" + a["slug"] + "/")}">{a["titulo"]}</a></li>'
        for a in AREAS
    )
    return f"""
<footer class="rodape">
  <div class="env">
    <div class="rodape__grade">
      <div>
        <div class="rodape__marca">{logo("claro")}</div>
        <p>{SITE['profissao']} — {SITE['oab']}<br>{SITE['atendimento']}</p>
        <div class="rodape__sociais">
          <a href="{WHATS}" target="_blank" rel="noopener" aria-label="WhatsApp">{SOCIAL_WHATS}</a>
          <a href="{SITE['instagram_url']}" target="_blank" rel="noopener" aria-label="Instagram">{SOCIAL_INSTA}</a>
        </div>
      </div>
      <div>
        <p class="rodape__titulo">Áreas de atuação</p>
        <ul class="rodape__lista">{links_areas}</ul>
      </div>
      <div>
        <p class="rodape__titulo">Navegação</p>
        <ul class="rodape__lista">
          <li><a href="{url('/sobre/')}">Sobre</a></li>
          <li><a href="{url('/a-advogada/')}">A Advogada</a></li>
          <li><a href="{url('/conteudos/')}">Conteúdos</a></li>
          <li><a href="{url('/contato/')}">Contato</a></li>
          <li><a href="{url('/politica-de-privacidade/')}">Política de Privacidade</a></li>
        </ul>
      </div>
      <div>
        <p class="rodape__titulo">Contato</p>
        <ul class="rodape__lista">
          <li><a href="{WHATS}" target="_blank" rel="noopener">{SITE['telefone_exibicao']}</a></li>
          <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
          <li><a href="{SITE['instagram_url']}" target="_blank" rel="noopener">@{SITE['instagram_handle']}</a></li>
{linha_endereco_rodape}        </ul>
      </div>
    </div>

    <p class="rodape__aviso">
      Este site tem caráter meramente informativo e não constitui oferta, captação de clientela ou
      promessa de resultado, em observância ao Código de Ética e Disciplina e às normas da OAB sobre
      publicidade na advocacia. As informações aqui publicadas não substituem a análise individual
      de cada caso.
    </p>

    <div class="rodape__base">
      <span>© {SITE['ano']} {SITE['nome']} — Todos os direitos reservados.</span>
      <span>{SITE['oab']}</span>
    </div>
  </div>
</footer>
<a class="whats-flutuante" href="{WHATS}" target="_blank" rel="noopener" aria-label="Falar pelo WhatsApp">
  <svg viewBox="0 0 24 24" width="23" height="23" fill="none" stroke="currentColor"
       stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.7-5.2A8.5 8.5 0 1 1 21 11.5Z"/>
    <path d="M8.7 9.4c.35 2.6 2.6 4.85 5.2 5.2l1-1.4 2 .9-.3 1.7c-3.7.5-7.6-3.4-8.1-8.1l1.7-.3.9 2-1.4 1Z"/>
  </svg>
  <span class="whats-flutuante__texto">Falar pelo WhatsApp</span>
</a>"""


# ---------------------------------------------------------------- shell HTML

FONTES = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Playfair+Display:ital,wght@0,400;0,500;1,400&"
    'family=Inter:wght@300;400;500&display=swap">'
)


def dados_estruturados(pagina, artigo=None):
    if artigo:
        return json.dumps({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": artigo["titulo"],
            "description": artigo["resumo"],
            "datePublished": artigo["data"],
            "inLanguage": "pt-BR",
            "author": {"@type": "Person", "name": SITE["nome"], "jobTitle": SITE["profissao"]},
            "publisher": {"@type": "Organization", "name": SITE["nome"]},
            "mainEntityOfPage": RAIZ_PUBLICA + pagina,
        }, ensure_ascii=False, indent=2)
    base = {
        "@context": "https://schema.org",
        "@type": "Attorney",
        "name": SITE["nome"],
        "description": "Advocacia em Direito Previdenciário e em Inventários e Sucessões.",
        "url": RAIZ_PUBLICA,
        "telephone": "+" + SITE["telefone_e164"],
        "email": SITE["email"],
        "sameAs": [SITE["instagram_url"]],
        "areaServed": SITE["regiao_atuacao"],
        "knowsAbout": [a["titulo"] for a in AREAS],
    }
    if preenchido(SITE["endereco"]):
        base["address"] = {
            "@type": "PostalAddress",
            "streetAddress": SITE["endereco"],
        }
    return json.dumps(base, ensure_ascii=False, indent=2)


def pagina(slug, titulo_seo, descricao, corpo, atual=None, artigo=None):
    canonico = RAIZ_PUBLICA + slug
    estilos = prefixo() + "assets/style.css"
    script = prefixo() + "assets/main.js"
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo_seo)}</title>
<meta name="description" content="{html.escape(descricao)}">
<link rel="canonical" href="{canonico}">
<meta name="robots" content="{ROBOTS_META}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['nome']} — {SITE['profissao']}">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{html.escape(titulo_seo)}">
<meta property="og:description" content="{html.escape(descricao)}">
<meta property="og:url" content="{canonico}">
<meta property="og:image" content="{RAIZ_PUBLICA}/assets/img/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2e3234">
<link rel="icon" href="{prefixo()}assets/img/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="{prefixo()}assets/img/icone-512.png" sizes="512x512">
<link rel="apple-touch-icon" href="{prefixo()}assets/img/icone-180.png">
<link rel="manifest" href="{prefixo()}site.webmanifest">
{FONTES}
<link rel="stylesheet" href="{estilos}">
<script type="application/ld+json">
{dados_estruturados(slug, artigo)}
</script>
</head>
<body>
{cabecalho(atual or slug)}
<main id="conteudo">
{corpo}
</main>
{rodape()}
<script src="{script}" defer></script>
</body>
</html>"""


# ---------------------------------------------------------------- blocos

def topo_pagina(migalhas, titulo, lead):
    trilha = ""
    for i, (rotulo, destino) in enumerate(migalhas):
        if destino:
            trilha += f'<a href="{url(destino)}">{rotulo}</a>'
        else:
            trilha += rotulo
        if i < len(migalhas) - 1:
            trilha += "<span>/</span>"
    return f"""
<section class="pagina-topo">
  <div class="monograma-faixa"></div>
  <div class="env">
    <p class="migalhas">{trilha}</p>
    <h1 class="revelar">{titulo}</h1>
    <p class="lead revelar" data-atraso="1">{lead}</p>
  </div>
</section>"""


def cta_final(titulo, texto):
    return f"""
<section class="secao secao--greige">
  <div class="env env--estreito cta-final revelar">
    <span class="rotulo">Próximo passo</span>
    <h2>{titulo}</h2>
    <p class="lead">{texto}</p>
    <div class="grupo-btn">
      <a class="btn btn--solido" href="{WHATS}" target="_blank" rel="noopener">Falar pelo WhatsApp</a>
      <a class="btn btn--linha" href="{url('/contato/')}">Ver todas as formas de contato</a>
    </div>
  </div>
</section>"""


ETAPAS = [
    ("Primeiro contato", "Uma conversa inicial para entender o que está acontecendo e verificar se é mesmo uma questão jurídica — às vezes não é, e dizer isso também faz parte do trabalho."),
    ("Reunião e documentos", "Levantamento do que existe: documentos, prazos, histórico. É aqui que o caso ganha contorno real e deixa de ser apenas uma dúvida."),
    ("Análise jurídica", "Estudo da situação à luz da legislação e da jurisprudência aplicáveis, com identificação dos caminhos possíveis e dos riscos de cada um."),
    ("Definição da estratégia", "Apresentação das alternativas em linguagem clara, com honorários e prazos definidos por escrito antes de qualquer providência."),
    ("Condução e acompanhamento", "Execução do que foi combinado, com atualização periódica sobre o andamento — inclusive quando não há novidade."),
]


# ---------------------------------------------------------------- páginas

def bloco_conteudos_home():
    """Só aparece quando há artigos publicados."""
    if not ARTIGOS:
        return ""
    itens = "".join(
        f'<a class="relacionado" href="{url("/conteudos/" + a["slug"] + "/")}">'
        f'<span class="relacionado__cat">{nome_categoria(a["categoria"])}</span>'
        f'<span class="relacionado__titulo">{a["titulo"]}</span></a>'
        for a in ARTIGOS[:3]
    )
    return f"""
<section class="secao">
  <div class="env">
    <div class="revelar bloco-intro">
      <span class="rotulo rotulo--linha">Conteúdos</span>
      <h2 class="titulo-secao">Dúvidas frequentes, explicadas por escrito.</h2>
    </div>
    <div class="grade-relacionados revelar">{itens}</div>
    <div class="grupo-btn" style="margin-top: 2.5rem;">
      <a class="link-seta" href="{url('/conteudos/')}">Ver todos os textos<span aria-hidden="true">→</span></a>
    </div>
  </div>
</section>"""


def p_home():
    variante = SITE.get("hero_variante", "capa")
    variante = {"capa": "hero-capa", "real": "hero-real", "estudio": "hero-estudio"}.get(
        variante, "hero-capa"
    )

    blocos_areas = ""
    for a in AREAS:
        blocos_areas += f"""
    <article class="area-item revelar">
      <span class="numero" aria-hidden="true">{a['num']}</span>
      <div>
        <h3 class="area-item__titulo">{a['titulo']}</h3>
        <p class="area-item__texto">{a['resumo']}</p>
      </div>
      <a class="link-seta area-item__acao" href="{url('/areas-de-atuacao/' + a['slug'] + '/')}">
        Ver detalhes<span aria-hidden="true">→</span>
      </a>
    </article>"""

    etapas_html = ""
    for i, (t, d) in enumerate(ETAPAS, 1):
        etapas_html += f"""
      <div class="etapa revelar">
        <span class="etapa__num" aria-hidden="true">0{i}</span>
        <div>
          <h3 class="etapa__titulo">{t}</h3>
          <p class="etapa__texto">{d}</p>
        </div>
      </div>"""

    return f"""
<section class="hero">
  <div class="env hero__grade">
    <div>
      <span class="rotulo revelar">Aposentadoria e Sucessões</span>
      <h1 class="hero__titulo revelar" data-atraso="1">
        Aposentadoria e <em>patrimônio</em>.
      </h1>
      <p class="lead hero__sub revelar" data-atraso="2">
        Momentos em que entender o que está acontecendo e ser assistido
        faz toda a diferença.
      </p>
      <div class="grupo-btn hero__acoes revelar" data-atraso="3">
        <a class="btn btn--solido" href="{url('/areas-de-atuacao/')}">Conheça minha atuação</a>
        <a class="btn btn--linha" href="{WHATS}" target="_blank" rel="noopener">Fale comigo</a>
      </div>
    </div>
    <figure class="hero__figura revelar revelar--imagem" data-atraso="1">
      {img(variante, 'Daniela Clemente, advogada', sizes='(min-width: 900px) 45vw, 90vw', eager=True, ratio=(1299, 1952))}
      <figcaption class="hero__nota">{SITE['nome']} — {SITE['oab']}</figcaption>
    </figure>
  </div>
</section>

<section class="secao secao--clara manifesto">
  <div class="env manifesto__grade">
    <figure class="manifesto__figura revelar revelar--imagem" data-parallax="0.018">
      {img('posicionamento', 'Daniela Clemente, advogada', sizes='(min-width: 900px) 38vw, 90vw', ratio=(1299, 1955))}
    </figure>
    <div class="revelar" data-atraso="1">
      <span class="rotulo">Posicionamento</span>
      <p class="manifesto__citacao">Advocacia estratégica e comprometida.</p>
      <div class="prosa lead">
        <p>
          Uma aposentadoria negada depois de décadas de contribuição, uma perda familiar
          cujo patrimônio precisa ser partilhado, um imóvel que precisa ser regularizado.
          O que todos têm em comum?
        </p>
        <p>
          Minha atuação começa aí: compreender que cada caso exige mais que conhecimento
          técnico. Exige escuta, sensibilidade, profundo respeito e responsabilidade, sem
          perder de vista os impactos emocionais, sociais e patrimoniais que cada decisão
          pode gerar. Sempre pautada pela transparência na comunicação com meu cliente.
        </p>
        <p>
          Atuo de forma estratégica, buscando sempre o melhor caminho jurídico. Cada
          demanda é conduzida com análise técnica aprofundada, estratégia definida e
          acompanhamento contínuo, do fechamento do contrato até o encerramento do caso.
        </p>
      </div>
    </div>
  </div>
</section>

<section class="secao">
  <div class="env">
    <div class="revelar">
      <span class="rotulo rotulo--linha">Áreas de atuação</span>
      <h2 class="titulo-secao">
        Duas áreas, um mesmo cuidado com quem está do outro lado.
      </h2>
    </div>
    <div class="areas">{blocos_areas}</div>
  </div>
</section>

<section class="secao secao--clara">
  <div class="env retrato-bloco">
    <figure class="revelar revelar--imagem">
      {img('sobre', 'Daniela Clemente, advogada', sizes='(min-width: 900px) 42vw, 90vw', ratio=(1300, 1954))}
    </figure>
    <div class="revelar" data-atraso="1">
      <span class="rotulo">Sobre</span>
      <h2 class="titulo-secao titulo-secao--solto">
        Existe uma pessoa por trás de cada processo. Nos dois lados da mesa.
      </h2>
      <div class="prosa">
        <p>
          Atendimento direto, sem intermediários: quem analisa o caso é quem conversa com
          você e quem conduz o processo até o fim.
        </p>
        <p>
          Isso muda a forma de trabalhar. Significa menos volume e mais atenção a cada
          situação, retorno sobre o andamento mesmo quando não há novidade, e explicações
          que dispensam tradução.
        </p>
      </div>
      <div class="grupo-btn" style="margin-top: 2.2rem;">
        <a class="link-seta" href="{url('/sobre/')}">Como eu trabalho<span aria-hidden="true">→</span></a>
      </div>
    </div>
  </div>
</section>

<section class="secao secao--escura">
  <div class="monograma-faixa"></div>
  <div class="env">
    <div class="revelar bloco-intro">
      <span class="rotulo rotulo--linha">Como funciona o atendimento</span>
      <h2 class="titulo-secao">
        Um caminho previsível, do primeiro contato ao desfecho.
      </h2>
    </div>
    <div class="etapas">{etapas_html}</div>
  </div>
</section>

{bloco_conteudos_home()}
{cta_final(
    "Vamos conversar sobre o seu caso.",
    "A primeira conversa serve para entender a situação e esclarecer se há mesmo uma "
    "questão jurídica a tratar. Sem compromisso de contratação."
)}"""


def p_sobre():
    if preenchido(SITE["endereco"]):
        paragrafo_atendimento = (
            f"<p>O atendimento presencial acontece em {ph(SITE['endereco'])}, mediante "
            f"agendamento prévio. O atendimento online, por videochamada, atende clientes "
            f"em {ph(SITE['regiao_atuacao'])} e em outras localidades, com a mesma "
            f"estrutura de acompanhamento e envio de documentos de forma digital.</p>"
        )
    else:
        paragrafo_atendimento = (
            "<p>O atendimento presencial acontece mediante agendamento prévio. O "
            "atendimento online, por videochamada, tem a mesma estrutura de "
            "acompanhamento, com envio de documentos de forma digital.</p>"
        )

    principios = [
        ("Explicar antes de propor", "Nenhuma estratégia é apresentada antes de você entender o que está em jogo. Direito é técnico, mas a explicação não precisa ser."),
        ("Dizer o que não é possível", "Nem todo caso tem solução jurídica, e nem toda solução vale o desgaste. Ouvir isso logo no começo custa menos do que descobrir no meio do caminho."),
        ("Um único interlocutor", "Você conversa sempre com a mesma pessoa — a mesma que analisa os documentos e conduz o processo."),
        ("Discrição como padrão", "Questões de família e de patrimônio são assuntos privados. Nada é exposto, comentado ou usado como exemplo."),
    ]
    blocos = "".join(
        f'<div class="principio revelar" data-atraso="{i % 4}">'
        f'<h3 class="principio__titulo">{t}</h3>'
        f'<p class="principio__texto">{d}</p></div>'
        for i, (t, d) in enumerate(principios)
    )

    etapas_html = ""
    for i, (t, d) in enumerate(ETAPAS, 1):
        etapas_html += f"""
      <div class="etapa revelar">
        <span class="etapa__num" aria-hidden="true">0{i}</span>
        <div>
          <h3 class="etapa__titulo">{t}</h3>
          <p class="etapa__texto">{d}</p>
        </div>
      </div>"""

    return topo_pagina(
        [("Início", "/"), ("Sobre", None)],
        "Uma advocacia de proximidade, para assuntos que não admitem pressa.",
        "Como o atendimento funciona, o que orienta as decisões e o que você pode esperar "
        "desde a primeira conversa.",
    ) + f"""
<section class="secao">
  <div class="env retrato-bloco retrato-bloco--inverso">
    <div class="revelar">
      <span class="rotulo">A forma de trabalhar</span>
      <div class="prosa lead">
        <p>
          Previdenciário e sucessões são áreas muito diferentes entre si, mas compartilham
          uma característica: chegam até o escritório em momentos de transição. A
          aposentadoria que encerra uma vida de trabalho. A perda que obriga uma família a
          lidar com patrimônio e com luto ao mesmo tempo.
        </p>
        <p>
          Casos assim não se resolvem apenas com peça processual bem escrita. Exigem
          alguém que consiga traduzir o que está acontecendo, apontar as alternativas
          reais e sustentar a decisão que for tomada.
        </p>
      </div>
    </div>
    <figure class="revelar revelar--imagem" data-atraso="1">
      {img('areas', 'Daniela Clemente', sizes='(min-width: 900px) 42vw, 90vw', ratio=(896, 1348))}
    </figure>
  </div>
</section>

<section class="secao secao--clara">
  <div class="env">
    <div class="revelar bloco-intro">
      <span class="rotulo rotulo--linha">O que orienta o atendimento</span>
      <h2 class="titulo-secao">Quatro compromissos que valem para qualquer caso.</h2>
    </div>
    <div class="grade-principios">{blocos}</div>
  </div>
</section>

<section class="secao secao--escura">
  <div class="monograma-faixa"></div>
  <div class="env">
    <div class="revelar bloco-intro">
      <span class="rotulo rotulo--linha">Como funciona</span>
      <h2 class="titulo-secao">
        Do primeiro contato ao acompanhamento.
      </h2>
    </div>
    <div class="etapas">{etapas_html}</div>
  </div>
</section>

<section class="secao">
  <div class="env env--estreito revelar">
    <span class="rotulo">Atendimento</span>
    <h2 style="font-size: var(--t-h2); margin-bottom: 1.5rem;">Presencial e online.</h2>
    <div class="prosa">
      {paragrafo_atendimento}
    </div>
  </div>
</section>

{cta_final(
    "Comece por uma conversa.",
    "Descreva a situação em poucas linhas. A partir daí definimos se o caso pede uma reunião."
)}"""


def p_areas_hub():
    cartoes = ""
    for a in AREAS:
        cartoes += f"""
    <a class="cartao-area revelar" href="{url('/areas-de-atuacao/' + a['slug'] + '/')}">
      <div class="cartao-area__topo">
        {ICONES_AREA[a['slug']]}
        <span class="cartao-area__num" aria-hidden="true">{a['num']}</span>
      </div>
      <div class="cartao-area__corpo">
        <h2 class="cartao-area__titulo">{a['titulo']}</h2>
        <p class="cartao-area__texto">{a['resumo']}</p>
        <span class="link-seta">Ver área<span aria-hidden="true">→</span></span>
      </div>
    </a>"""

    return topo_pagina(
        [("Início", "/"), ("Áreas de Atuação", None)],
        "Áreas de atuação",
        "Duas áreas de trabalho que se encontram nas transições importantes da vida: "
        "a aposentadoria que encerra uma trajetória e o patrimônio que precisa passar adiante.",
    ) + f"""
<section class="secao">
  <div class="env">
    <div class="grade-areas">{cartoes}</div>
  </div>
</section>

<section class="secao secao--clara">
  <div class="env env--estreito revelar">
    <span class="rotulo">Não encontrou seu assunto?</span>
    <h2 style="font-size: var(--t-h2); margin-bottom: 1.3rem;">
      Nem toda situação se encaixa numa lista.
    </h2>
    <p class="lead">
      Se o seu caso não aparece acima, vale a conversa mesmo assim. Se não for uma questão
      que eu atenda, indico o caminho ou o profissional adequado.
    </p>
    <div class="grupo-btn" style="margin-top: 2rem;">
      <a class="btn btn--linha" href="{url('/contato/')}">Falar sobre o meu caso</a>
    </div>
  </div>
</section>

{cta_final(
    "Vamos conversar sobre o seu caso.",
    "A primeira conversa serve para entender a situação e esclarecer os caminhos possíveis."
)}"""


def p_area(a):
    corpo = "".join(f"<p>{p}</p>" for p in a["corpo"])
    servicos = "".join(f"<li>{s['nome']}</li>" for s in a["servicos"])

    faq_html = ""
    if a.get("faq"):
        itens = ""
        for i, q in enumerate(a["faq"]):
            pid = f"faq-{a['slug']}-{i}"
            itens += f"""
      <div class="faq__item">
        <h3>
          <button class="faq__botao" aria-expanded="false" aria-controls="{pid}">
            <span>{q['p']}</span><span class="faq__sinal" aria-hidden="true"></span>
          </button>
        </h3>
        <div class="faq__resposta" id="{pid}"><div>{q['r']}</div></div>
      </div>"""
        faq_html = f"""
<section class="secao secao--clara">
  <div class="env env--estreito">
    <div class="revelar bloco-intro">
      <span class="rotulo rotulo--linha">Perguntas frequentes</span>
      <h2 class="titulo-secao">O que costuma gerar dúvida.</h2>
    </div>
    <div class="faq revelar">{itens}</div>
  </div>
</section>"""

    return topo_pagina(
        [("Início", "/"), ("Áreas de Atuação", "/areas-de-atuacao/"), (a["titulo"], None)],
        a["titulo"],
        a["resumo"],
    ) + f"""
<section class="secao">
  <div class="env retrato-bloco retrato-bloco--inverso">
    <div class="revelar">
      <span class="rotulo">{a['eyebrow']}</span>
      <h2 style="font-size: var(--t-h2); margin-bottom: 1.8rem; max-width: 22ch;">{a['abertura']}</h2>
      <div class="prosa">{corpo}</div>
    </div>
    <figure class="revelar revelar--imagem" data-atraso="1">
      {img(a['img'], a['titulo'], sizes='(min-width: 900px) 42vw, 90vw', ratio=(896, 1372))}
    </figure>
  </div>
</section>

<section class="secao secao--greige">
  <div class="env env--estreito revelar">
    <span class="rotulo rotulo--linha">{a['servicos_titulo']}</span>
    <ul class="lista-servicos">{servicos}</ul>
    <p style="margin-top: 1.8rem; font-size: 0.92rem; color: var(--tinta-suave);">
      Esta lista reúne os assuntos mais frequentes e não esgota as possibilidades de atuação
      na área.
    </p>
  </div>
</section>
{faq_html}
{cta_final(
    "Tem uma dúvida sobre " + a['titulo'].lower() + "?",
    "Descreva sua situação em poucas linhas. O retorno costuma acontecer em até um dia útil."
)}"""


def p_advogada():
    return topo_pagina(
        [("Início", "/"), ("A Advogada", None)],
        SITE["nome"],
        f"{SITE['profissao']} — {SITE['oab']}. Atuação em Direito Previdenciário, "
        "Inventários e Sucessões.",
    ) + f"""
<section class="secao">
  <div class="env retrato-bloco retrato-bloco--integral">
    <figure class="revelar revelar--imagem">
      {img('advogada', 'Retrato profissional de Daniela Clemente', sizes='(min-width: 900px) 44vw, 90vw', ratio=(1300, 1951))}
    </figure>
    <div class="revelar" data-atraso="1">
      <span class="rotulo">Trajetória</span>
      <div class="prosa lead">
        <p>
          Advogada especializada na área previdenciária, com atuação prática em sucessões
          e inventários.
        </p>
        <p>
          A escolha dessas áreas foi pautada no desejo de oferecer aos clientes
          previdenciários a consolidação de um direito — muitos deles de caráter
          alimentar.
        </p>
        <p>
          Quanto à atuação em sucessões e inventários, a escolha veio do desejo de
          esclarecer e direcionar quem enfrenta questões complexas, muitas vezes
          familiares, no momento da discussão de heranças e dos demais instrumentos de
          regulamentação patrimonial.
        </p>
      </div>
    </div>
  </div>
</section>

{cta_final(
    "Vamos conversar.",
    "Atendimento presencial mediante agendamento e atendimento online por videochamada."
)}"""


def nome_categoria(slug):
    for a in AREAS:
        if a["slug"] == slug:
            return a["titulo"]
    return slug


def data_extenso(iso):
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
    try:
        ano, mes, dia = iso.split("-")
        return f"{int(dia)} de {meses[int(mes) - 1]} de {ano}"
    except Exception:
        return iso


def p_conteudos():
    filtros = '<button class="filtro" data-categoria="todos" aria-pressed="true">Todos</button>'
    for a in AREAS:
        filtros += f'<button class="filtro" data-categoria="{a["slug"]}" aria-pressed="false">{a["titulo"]}</button>'

    if ARTIGOS:
        cartoes = ""
        for art in ARTIGOS:
            cartoes += f"""
      <article class="artigo-card revelar" data-artigo="{art['categoria']}">
        <p class="artigo-card__meta">
          <span>{nome_categoria(art['categoria'])}</span>
          <span aria-hidden="true">·</span>
          <time datetime="{art['data']}">{data_extenso(art['data'])}</time>
          <span aria-hidden="true">·</span>
          <span>{art.get('leitura', 3)} min de leitura</span>
        </p>
        <h2 class="artigo-card__titulo">
          <a href="{url('/conteudos/' + art['slug'] + '/')}">{art['titulo']}</a>
        </h2>
        <p class="artigo-card__resumo">{art['resumo']}</p>
        <a class="link-seta" href="{url('/conteudos/' + art['slug'] + '/')}">
          Ler o texto<span aria-hidden="true">→</span>
        </a>
      </article>"""
        listagem = f'<div class="lista-artigos">{cartoes}</div>'
    else:
        listagem = f"""
    <div class="vazio revelar">
      <p class="vazio__titulo">Os primeiros textos estão sendo escritos.</p>
      <p class="vazio__texto">
        Enquanto isso, se você tem uma dúvida específica sobre aposentadoria, guarda,
        pensão ou inventário, ela pode ser respondida diretamente — e talvez vire o
        próximo texto publicado aqui.
      </p>
      <div class="grupo-btn" style="justify-content: center; margin-top: 2rem;">
        <a class="btn btn--linha" href="{WHATS}" target="_blank" rel="noopener">Enviar uma dúvida</a>
      </div>
    </div>"""

    return topo_pagina(
        [("Início", "/"), ("Conteúdos", None)],
        "Conteúdos",
        "Textos sobre direito previdenciário, inventários e sucessões, escritos para quem não é "
        "da área — para esclarecer dúvidas antes mesmo de existir um caso.",
    ) + f"""
<section class="secao">
  <div class="env">
    <div class="filtros revelar">{filtros}</div>
    {listagem}
  </div>
</section>

<section class="secao secao--clara">
  <div class="env env--estreito revelar">
    <span class="rotulo">Nota</span>
    <p class="lead">
      Os conteúdos publicados aqui têm finalidade informativa e não substituem a análise
      individual de cada caso. Situações semelhantes podem ter desfechos diferentes conforme
      os documentos, os prazos e a legislação aplicável.
    </p>
  </div>
</section>"""


def p_artigo(art):
    corpo = ""
    for bloco in art["corpo"]:
        t = bloco.get("tipo")
        if t == "h2":
            corpo += f'<h2 class="artigo__h2">{bloco["texto"]}</h2>'
        elif t == "lista":
            itens = "".join(f"<li>{i}</li>" for i in bloco["itens"])
            corpo += f'<ul class="artigo__lista">{itens}</ul>'
        elif t == "destaque":
            corpo += f'<blockquote class="artigo__destaque">{bloco["texto"]}</blockquote>'
        else:
            corpo += f"<p>{bloco['texto']}</p>"

    relacionados = [a for a in ARTIGOS if a["slug"] != art["slug"]][:2]
    bloco_rel = ""
    if relacionados:
        itens = "".join(
            f'<a class="relacionado" href="{url("/conteudos/" + r["slug"] + "/")}">'
            f'<span class="relacionado__cat">{nome_categoria(r["categoria"])}</span>'
            f'<span class="relacionado__titulo">{r["titulo"]}</span></a>'
            for r in relacionados
        )
        bloco_rel = f"""
<section class="secao secao--clara">
  <div class="env env--estreito revelar">
    <span class="rotulo rotulo--linha">Continue lendo</span>
    <div class="grade-relacionados">{itens}</div>
  </div>
</section>"""

    area = next((a for a in AREAS if a["slug"] == art["categoria"]), None)
    link_area = ""
    if area:
        link_area = (
            f'<a class="link-seta" href="{url("/areas-de-atuacao/" + area["slug"] + "/")}">'
            f'Ver atuação em {area["titulo"]}<span aria-hidden="true">→</span></a>'
        )

    return topo_pagina(
        [("Início", "/"), ("Conteúdos", "/conteudos/"), (nome_categoria(art["categoria"]), None)],
        art["titulo"],
        art["resumo"],
    ) + f"""
<section class="secao">
  <div class="env env--estreito">
    <p class="artigo__meta revelar">
      <time datetime="{art['data']}">{data_extenso(art['data'])}</time>
      <span aria-hidden="true">·</span>
      <span>{art.get('leitura', 3)} min de leitura</span>
    </p>
    <div class="artigo prosa revelar">{corpo}</div>
    <div class="artigo__rodape revelar">
      {link_area}
    </div>
  </div>
</section>
{bloco_rel}
{cta_final(
    "Ficou com uma dúvida sobre o seu caso?",
    "Este texto é geral. Cada situação depende de documentos, prazos e detalhes próprios."
)}"""


def p_contato():
    valor_atendimento = (
        f"{ph(SITE['endereco'])}<br>{SITE['atendimento']}"
        if preenchido(SITE["endereco"]) else SITE["atendimento"]
    )
    canais = f"""
    <a class="canal" href="{WHATS}" target="_blank" rel="noopener">
      {ICONES['whatsapp']}
      <span><span class="canal__rotulo">WhatsApp</span>
      <span class="canal__valor">{SITE['telefone_exibicao']}</span></span>
    </a>
    <a class="canal" href="tel:+{SITE['telefone_e164']}">
      {ICONES['telefone']}
      <span><span class="canal__rotulo">Telefone</span>
      <span class="canal__valor">{SITE['telefone_exibicao']}</span></span>
    </a>
    <a class="canal" href="mailto:{SITE['email']}">
      {ICONES['email']}
      <span><span class="canal__rotulo">E-mail</span>
      <span class="canal__valor">{SITE['email']}</span></span>
    </a>
    <a class="canal" href="{SITE['instagram_url']}" target="_blank" rel="noopener">
      {ICONES['instagram']}
      <span><span class="canal__rotulo">Instagram</span>
      <span class="canal__valor">@{SITE['instagram_handle']}</span></span>
    </a>
    <div class="canal">
      {ICONES['local']}
      <span><span class="canal__rotulo">Atendimento</span>
      <span class="canal__valor">{valor_atendimento}</span></span>
    </div>"""

    opcoes = "".join(f'<option value="{a["titulo"]}">{a["titulo"]}</option>' for a in AREAS)

    return topo_pagina(
        [("Início", "/"), ("Contato", None)],
        "Fale comigo",
        "WhatsApp, telefone, e-mail ou formulário. Escolha o canal mais confortável para você.",
    ) + f"""
<section class="secao">
  <div class="env contato__grade">
    <div class="revelar">
      <span class="rotulo rotulo--linha">Canais diretos</span>
      <div class="canais">{canais}</div>
    </div>

    <div class="revelar" data-atraso="1">
      <span class="rotulo rotulo--linha">Enviar uma mensagem</span>
      <form class="form" data-endpoint="{SITE['form_endpoint']}" data-whatsapp="{SITE['telefone_e164']}" novalidate>
        <div class="campo">
          <label for="nome">Nome</label>
          <input type="text" id="nome" name="nome" required autocomplete="name">
        </div>
        <div class="campo">
          <label for="email">E-mail</label>
          <input type="email" id="email" name="email" required autocomplete="email">
        </div>
        <div class="campo">
          <label for="telefone">Telefone ou WhatsApp</label>
          <input type="tel" id="telefone" name="telefone" autocomplete="tel">
        </div>
        <div class="campo campo--select">
          <label for="assunto">Assunto</label>
          <select id="assunto" name="assunto">
            <option value="">Selecione</option>
            {opcoes}
            <option value="Outro assunto">Outro assunto</option>
          </select>
        </div>
        <div class="campo">
          <label for="mensagem">Como posso ajudar?</label>
          <textarea id="mensagem" name="mensagem" rows="4" required
            placeholder="Descreva a situação em poucas linhas."></textarea>
        </div>
        <label class="form__consentimento">
          <input type="checkbox" name="consentimento" required>
          <span>Autorizo o contato por e-mail, telefone ou WhatsApp e o tratamento dos meus
          dados para essa finalidade, conforme a
          <a href="{url('/politica-de-privacidade/')}" style="border-bottom:1px solid currentColor;">Política de Privacidade</a>.</span>
        </label>
        <p class="form__retorno" role="status" aria-live="polite"></p>
        <div class="grupo-btn">
          <button type="submit" class="btn btn--solido">Enviar mensagem</button>
        </div>
        <p style="font-size: 0.82rem; color: var(--tinta-suave);">
          Evite enviar documentos ou dados sensíveis por este formulário. Eles serão
          solicitados de forma segura durante o atendimento.
        </p>
      </form>
    </div>
  </div>
</section>

<section class="secao secao--escura">
  <div class="monograma-faixa"></div>
  <div class="env env--estreito revelar">
    <span class="rotulo">Antes de escrever</span>
    <h2 style="font-size: var(--t-h2); color: var(--papel); margin-bottom: 1.3rem;">
      O que ajuda a agilizar o primeiro retorno.
    </h2>
    <p class="lead">
      Diga em poucas linhas o que aconteceu, desde quando, e se já existe algum processo,
      protocolo ou decisão em andamento. Com essas três informações já é possível dizer se
      o caso pede uma reunião e o que levar para ela.
    </p>
  </div>
</section>"""


def p_privacidade():
    # A identificação do controlador exige endereço. Enquanto ele não existir,
    # o trecho é omitido em vez de gerar uma frase truncada.
    trecho_endereco = (
        f", com endereço em {ph(SITE['endereco'])}" if preenchido(SITE["endereco"]) else ""
    )
    return topo_pagina(
        [("Início", "/"), ("Política de Privacidade", None)],
        "Política de Privacidade",
        "Como os dados enviados por este site são tratados, armazenados e protegidos.",
    ) + f"""
<section class="secao">
  <div class="env env--estreito prosa">
    <p class="lead" style="margin-bottom: 2.5rem;">
      Esta política descreve como os dados pessoais informados neste site são tratados, em
      conformidade com a Lei nº 13.709/2018 (Lei Geral de Proteção de Dados).
    </p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Quem trata os dados</h2>
    <p>{ph(SITE['razao_social'])}, inscrita no CNPJ {ph(SITE['cnpj'])}{trecho_endereco},
    representada por {SITE['nome']}, {SITE['oab']}.</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Quais dados são coletados</h2>
    <p>Apenas os dados que você informa voluntariamente no formulário de contato: nome,
    e-mail, telefone, assunto e o conteúdo da mensagem. O site não coleta dados sensíveis
    e não exige cadastro.</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Para que são usados</h2>
    <p>Exclusivamente para responder ao seu contato e, se houver interesse mútuo, dar
    andamento a um eventual atendimento jurídico. Os dados não são vendidos, cedidos nem
    compartilhados com terceiros para fins comerciais.</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Sigilo profissional</h2>
    <p>As informações compartilhadas em contato com advogado estão protegidas pelo sigilo
    profissional previsto no Estatuto da Advocacia e no Código de Ética e Disciplina da OAB,
    independentemente de o atendimento ser efetivamente contratado.</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Por quanto tempo são guardados</h2>
    <p>{ph('[PRAZO DE RETENÇÃO — definir, por exemplo: mensagens não convertidas em atendimento são eliminadas em até 12 meses.]')}</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Seus direitos</h2>
    <p>Você pode solicitar a qualquer momento a confirmação do tratamento, o acesso, a
    correção, a portabilidade ou a eliminação dos seus dados, bem como revogar o
    consentimento. Basta escrever para
    <a href="mailto:{SITE['email']}" style="border-bottom:1px solid currentColor;">{SITE['email']}</a>.</p>

    <h2 style="font-size: var(--t-h3); margin: 2.5rem 0 1rem;">Cookies</h2>
    <p>{ph('[COOKIES — descrever conforme as ferramentas efetivamente instaladas, como Google Analytics ou Meta Pixel. Se nenhuma for usada, informar que o site não utiliza cookies de rastreamento.]')}</p>

    <p style="margin-top: 3rem; font-size: 0.88rem; color: var(--tinta-suave);">
      Última atualização: {ph('[DATA]')}
    </p>
  </div>
</section>"""


def p_404():
    return f"""
<section class="secao" style="padding-block: clamp(6rem, 12vw, 11rem); text-align: center;">
  <div class="env env--estreito">
    <span class="rotulo" style="text-align:center;">Erro 404</span>
    <h1 style="font-size: var(--t-h1); margin-bottom: 1.3rem;">Esta página não existe.</h1>
    <p class="lead" style="margin-inline:auto;">
      O endereço pode ter mudado ou o link pode estar incompleto. Use o menu para continuar
      navegando ou volte ao início.
    </p>
    <div class="grupo-btn" style="justify-content:center; margin-top:2.4rem;">
      <a class="btn btn--solido" href="{url('/')}">Voltar ao início</a>
      <a class="btn btn--linha" href="{url('/contato/')}">Falar comigo</a>
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------- registro

def registro():
    paginas = [
        ("/", "Daniela Clemente — Advogada | Previdenciário, Inventários e Sucessões",
         "Advocacia em Direito Previdenciário e em Inventários e Sucessões. "
         "Atendimento presencial e online. OAB/SP 511.615.", p_home, 1.0),
        ("/sobre/", "Sobre a atuação | Daniela Clemente — Advogada",
         "Como funciona o atendimento, o que orienta as decisões e o que esperar desde a "
         "primeira conversa.", p_sobre, 0.8),
        ("/areas-de-atuacao/", "Áreas de atuação | Daniela Clemente — Advogada",
         "Direito Previdenciário e Inventários e Sucessões.",
         p_areas_hub, 0.9),
        ("/a-advogada/", f"{SITE['nome']} | Advogada — {SITE['oab']}",
         f"{SITE['profissao']} — {SITE['oab']}. Trajetória, formação e forma de atendimento.",
         p_advogada, 0.8),
        ("/conteudos/", "Conteúdos | Daniela Clemente — Advogada",
         "Textos sobre direito previdenciário, inventários e sucessões, escritos em linguagem "
         "acessível.", p_conteudos, 0.6),
        ("/contato/", "Contato | Daniela Clemente — Advogada",
         "WhatsApp, telefone, e-mail e formulário. Atendimento presencial e online.",
         p_contato, 0.9),
        ("/politica-de-privacidade/", "Política de Privacidade | Daniela Clemente — Advogada",
         "Como os dados enviados por este site são tratados, conforme a LGPD.",
         p_privacidade, 0.3),
    ]
    for art in ARTIGOS:
        paginas.append((
            f"/conteudos/{art['slug']}/",
            f"{art['titulo']} | Daniela Clemente — Advogada",
            art["resumo"],
            (lambda artigo=art: p_artigo(artigo)),
            0.6,
            art,
        ))
    for a in AREAS:
        paginas.insert(
            3 + AREAS.index(a),
            (
                f"/areas-de-atuacao/{a['slug']}/",
                f"{a['seo_title']} | Daniela Clemente — Advogada",
                a["seo_desc"],
                (lambda area=a: p_area(area)),
                0.85,
            ),
        )
    return paginas


# ---------------------------------------------------------------- execução

def build_dist():
    global MODO
    MODO = "dist"

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets" / "img").mkdir(parents=True)

    shutil.copy(SRC / "style.css", DIST / "assets" / "style.css")
    shutil.copy(SRC / "main.js", DIST / "assets" / "main.js")
    for f in (SRC / "img").iterdir():
        shutil.copy(f, DIST / "assets" / "img" / f.name)

    # imagem Open Graph (1200x630) a partir do hero
    try:
        from PIL import Image
        base = Image.open(SRC / "img" / "hero-real-1100.webp").convert("RGB")
        og = Image.new("RGB", (1200, 630), "#2e3234")
        prop = base.copy()
        prop.thumbnail((520, 630))
        og.paste(prop, (660, (630 - prop.height) // 2))
        og.save(DIST / "assets" / "img" / "og.jpg", quality=84)
    except Exception as e:
        print("  aviso: og.jpg não gerado —", e)

    urls = []
    global _PROFUNDIDADE
    for entrada in registro():
        slug, titulo, desc, fn, prio = entrada[:5]
        art = entrada[5] if len(entrada) > 5 else None
        destino = DIST / slug.strip("/") / "index.html" if slug != "/" else DIST / "index.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        # /sobre/ fica um nível abaixo, /areas-de-atuacao/x/ dois, e assim por diante
        _PROFUNDIDADE = len([p for p in slug.strip("/").split("/") if p])
        destino.write_text(
            pagina(slug, titulo, desc, fn(), atual=slug, artigo=art), encoding="utf-8"
        )
        urls.append((slug, prio))
        print(f"  ✓ {slug}")

    _PROFUNDIDADE = 0  # o 404 é servido a partir da raiz
    (DIST / "404.html").write_text(
        pagina("/404", "Página não encontrada | Daniela Clemente — Advogada",
               "A página que você procura não existe.", p_404(), atual="/"),
        encoding="utf-8",
    )

    itens = "".join(
        f"\n  <url><loc>{RAIZ_PUBLICA}{u}</loc><priority>{p}</priority>"
        f"<changefreq>monthly</changefreq></url>"
        for u, p in urls
    )
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{itens}\n</urlset>\n",
        encoding="utf-8",
    )

    (DIST / "site.webmanifest").write_text(
        json.dumps({
            "name": f"{SITE['nome']} — {SITE['profissao']}",
            "short_name": SITE["nome"].split()[0],
            "icons": [
                {"src": prefixo() + "assets/img/icone-180.png", "sizes": "180x180", "type": "image/png"},
                {"src": prefixo() + "assets/img/icone-512.png", "sizes": "512x512", "type": "image/png"},
            ],
            "theme_color": "#2e3234",
            "background_color": "#f1f0ed",
            "display": "standalone",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if EM_REVISAO:
        (DIST / "robots.txt").write_text(
            "# Site em revisão — não indexar.\nUser-agent: *\nDisallow: /\n",
            encoding="utf-8",
        )
    else:
        (DIST / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {RAIZ_PUBLICA}/sitemap.xml\n",
            encoding="utf-8",
        )

    # O GitHub Pages ignora o Jekyll na presença deste arquivo.
    (DIST / ".nojekyll").write_text("", encoding="utf-8")


def favicon_embutido():
    """O arquivo único não tem ativos ao lado, então o ícone vai embutido."""
    return base64.b64encode((SRC / "img" / "favicon.ico").read_bytes()).decode()


def build_preview():
    """Arquivo único navegável, para revisão sem servidor."""
    global MODO, _PROFUNDIDADE
    MODO = "preview"
    _PROFUNDIDADE = 0

    secoes = ""
    for entrada in registro():
        slug, titulo, desc, fn = entrada[:4]
        rota = "/" if slug == "/" else slug.rstrip("/")
        secoes += f'<div class="rota" data-rota="{rota}" hidden>{fn()}</div>'

    css = (SRC / "style.css").read_text(encoding="utf-8")
    js = (SRC / "main.js").read_text(encoding="utf-8")

    roteador = """
    function rota() {
      var r = location.hash.replace(/^#/, '') || '/';
      var ativa = null;
      document.querySelectorAll('.rota').forEach(function (s) {
        var eh = s.getAttribute('data-rota') === r;
        s.hidden = !eh;
        if (eh) ativa = s;
      });
      if (!ativa) {
        ativa = document.querySelector('.rota[data-rota="/"]');
        if (ativa) ativa.hidden = false;
      }
      document.querySelectorAll('.nav__link, .menu-mobile__item').forEach(function (a) {
        var alvo = a.getAttribute('href').replace(/^#/, '') || '/';
        if (alvo === r) { a.setAttribute('aria-current', 'page'); }
        else { a.removeAttribute('aria-current'); }
      });
      window.scrollTo(0, 0);
      // Reanima a página recém-aberta, em vez de marcar tudo como já revelado.
      if (window.__revelacoes && ativa) {
        window.__revelacoes.reiniciar(ativa);
        requestAnimationFrame(function () { window.__revelacoes.observar(); });
      }
    }
    window.addEventListener('hashchange', rota);
    rota();
    """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="{ROBOTS_META}">
<title>{SITE['nome']} — {SITE['profissao']}</title>
<link rel="icon" href="data:image/x-icon;base64,{favicon_embutido()}">
{FONTES}
<style>{css}
.rota[hidden] {{ display: none; }}
</style>
</head>
<body>
{cabecalho('/')}
<main id="conteudo">{secoes}</main>
{rodape()}
<script>{js}
{roteador}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Gerando site estático…")
    build_dist()
    print("Gerando prévia de arquivo único…")
    (RAIZ / "build" / "preview.html").write_text(build_preview(), encoding="utf-8")
    print("Pronto.")
