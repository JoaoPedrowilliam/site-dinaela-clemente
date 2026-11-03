# Site institucional — Daniela Clemente, Advogada

Site estático de 8 páginas, gerado por um script Python a partir de arquivos de dados.
Publicado no GitHub Pages. Sem framework, sem dependência de runtime: o navegador recebe
HTML, um CSS e um JS.

**No ar:** https://joaopedrowilliam.github.io/site-dinaela-clemente/
(o nome do repositório tem um erro de digitação — `dinaela`. Renomear é seguro: os
caminhos internos são relativos de propósito.)

---

## Como mexer

```bash
pip install pillow opencv-python-headless playwright
python3 -m playwright install chromium

python3 build.py                  # gera build/dist e build/preview.html
python3 ferramentas/testes.py     # 291 verificações; sai 1 se falhar
```

**Conteúdo fica em `data/`, nunca no HTML.** Editou `data/*.json`, rode `build.py`.

| Arquivo | O quê |
|---|---|
| `data/site.json` | Nome, OAB, contatos, domínio, `em_revisao`, variante do hero |
| `data/areas.json` | As duas áreas: textos, assuntos atendidos, FAQ |
| `data/artigos.json` | Artigos. `"rascunho": true` esconde do site |
| `build.py` | Gerador. Uma função por página, `p_home()`, `p_sobre()`… |
| `src/style.css` | Todo o CSS. Tokens no topo |
| `src/main.js` | Menu, acordeão, revelações, parallax, formulário |
| `ferramentas/imagens.py` | Gera as variantes responsivas das fotos |
| `ferramentas/testes.py` | Verificação do site gerado |
| `fotos-originais/` | Originais; `src/img/` é tudo derivado daqui |

`build/` é gerado e está no `.gitignore` — mas o site publicado mora na **raiz** do
repositório (ver "Publicação").

---

## Armadilhas que já custaram caro

Cada uma destas quebrou o site em produção. Há teste para todas.

**1. `img[width][height]` tem especificidade (0,2,1).** Dois seletores de atributo. Isso
é mais que `.marca img`, que é (0,1,1). Uma regra dessas venceu a altura do logotipo, que
passou a renderizar em tamanho natural — 196px de altura — esticou o cabeçalho e quebrou
o menu em três linhas. A regra hoje usa `:where()`, que zera a especificidade. **Não tire
o `:where()`.**

**2. Os atributos `width`/`height` do HTML anulam o `aspect-ratio` do CSS.** Eles entram
como dica de apresentação e fixam a altura em pixels. Uma foto renderizou a 456×1955 em
vez de 456×608. O `:where(img[width][height]) { height: auto }` resolve e mantém os
atributos reservando espaço contra deslocamento de layout.

**3. Não aplique máscara de nitidez nas fotografias.** Nas fotos escuras dela ela endurece
a pele e realça os blocos de compressão do original. A variância do laplaciano sobe e
parece ganho, mas numa imagem com 77% dos pixels abaixo de luminância 40 essa métrica mede
sobretudo artefato em área lisa. **Avalie olhando o recorte no tamanho de exibição.**

**4. O `sizes` declarando a largura exata da caixa entrega resolução de menos.** O
navegador escolhe o menor arquivo que serve, e numa foto escura isso fica visivelmente
pobre. Os retratos declaram um degrau acima, em pixels:
`(min-width: 1200px) 1100px, (min-width: 900px) 760px, …`

**5. O `srcset` é montado a partir dos arquivos que existem**, com a largura real de cada
um (`build.py`, função `img()`). Uma foto de origem mais estreita não gera os degraus
maiores. Não volte a listar larguras fixas: daria 404.

---

## Publicação

O Pages serve da **branch `main`, pasta raiz** — não via Actions. Por isso o site gerado
fica commitado na raiz do repositório, junto com o código-fonte.

```bash
python3 build.py
python3 ferramentas/testes.py
cp -r build/dist/. .          # leva o site gerado para a raiz
git add -A && git commit -m "..." && git push
```

O `.github/workflows/deploy.yml` existe e funciona, mas **não está no repositório
publicado**: ele deploya via Actions, o que conflita com o Pages servindo da branch. Para
usar o Actions, suba o workflow e mude **Settings → Pages → Source** para GitHub Actions.

---

## Modo de revisão

`"em_revisao": true` em `data/site.json` faz todas as páginas saírem com
`noindex, nofollow` e o `robots.txt` bloquear os buscadores.

**Está ligado de propósito.** Um site de advogada com campos em branco indexado no nome
dela é pior que site nenhum. Só desligue quando as pendências abaixo estiverem resolvidas.

---

## Pendências antes de publicar de verdade

- [ ] **Confirmar a lista de assuntos de cada área, item a item, com a cliente.** Os itens
      em `data/areas.json` vieram dos exemplos do briefing original, não de algo que ela
      disse que atende. Anunciar serviço que ela não presta é problema perante a OAB.
      Em Sucessões, só estes vieram dela: pactos antenupciais, doações, cessão de direitos
      hereditários e constituição de holding.
- [ ] **Razão social e CNPJ** — exigidos pela LGPD na política de privacidade
- [ ] **Endereço** — o campo some sozinho enquanto vazio, mas a política precisa dele
- [ ] **Prazo de retenção de dados e cookies** na política de privacidade
- [ ] `em_revisao: false` e `dominio` definitivo

---

## Regras de conteúdo

**Não invente informação sobre a advogada.** Nome, OAB, formação, experiência, endereço:
só o que ela forneceu. Campo sem informação vira marcador entre colchetes, que renderiza
destacado em amarelo (função `ph()` em `build.py`) — e há teste garantindo que marcador
não vaza para o site publicado.

**Publicidade na advocacia:** sem promessa de resultado, comparação com outros
profissionais, depoimento de cliente ou número de processos. O rodapé traz o aviso de
caráter informativo.

**Direito de Família saiu do escopo** em outubro. Já sobrou resíduo em metadados depois da
remoção; há teste procurando por isso.

**A página de Conteúdos é condicional:** não existe enquanto `data/artigos.json` não tiver
um artigo fora de rascunho. Ela some do menu, do rodapé e do sitemap, e volta sozinha.

---

## Identidade visual

Derivada do cartão de visita e do logotipo, não escolhida do zero.

| Papel | Hex | Origem |
|---|---|---|
| Grafite | `#5f6467` | fundo do cartão de visita |
| Grafite profundo | `#2e3234` | derivado, seções escuras |
| Greige | `#d9d8d5` | fundo do logotipo circular |
| Papel | `#f1f0ed` | fundo principal |
| Bronze | `#8c6e3e` / `#a98b57` | degradê do monograma |
| Champagne | `#e5d3a8` | monograma, detalhes |
| Bordô | `#5c2334` | guarda-roupa dela nas fotos |

Tipografia: **Playfair Display** nos títulos, **Inter** no texto.

O dourado entra só em fios de 1px, numeração e hover — nunca em bloco. O elemento de
assinatura é a coluna de "D" fantasma nas seções escuras (`.monograma-faixa`), eco da
marca d'água lateral do cartão.
