# Site — Daniela Clemente, Advogada

Site institucional estático, sem dependências externas além das fontes do Google Fonts.
Dez páginas, HTML gerado a partir de arquivos de dados.

---

## 1. Como abrir agora

**`preview.html`** — arquivo único, é só abrir no navegador. Navega entre todas as páginas,
funciona sem servidor e sem internet (as imagens estão embutidas). Serve para revisão e
aprovação, **não** para publicação.

**`dist/`** — o site de verdade, para hospedagem.

---

## 2. Estrutura do projeto

```
data/
  site.json          Nome, contatos, OAB, endereço, ano, variante do hero
  areas.json         As duas áreas: textos, listas de assuntos, perguntas frequentes
  artigos.json       Conteúdos publicados (traz um modelo em rascunho)
src/
  style.css          Sistema visual completo (tokens no topo do arquivo)
  main.js            Menu, acordeão, revelações, formulário
  img/               Imagens já otimizadas em WebP + JPG
build.py             Gera dist/ e preview.html
dist/                Saída pronta para publicar
```

Para alterar textos, edite os arquivos em `data/` e rode `python3 build.py`.
Nenhum texto precisa ser mexido diretamente no HTML.

---

## 3. Publicação

O site usa URLs limpas (`/sobre/` em vez de `/sobre.html`), então precisa de uma
hospedagem que sirva `index.html` dentro de pastas — o que inclui praticamente todas as
opções modernas.

**Netlify ou Vercel:** arraste a pasta `dist/` na interface. O `404.html` é reconhecido
automaticamente.

**Hospedagem tradicional (cPanel, Hostinger):** envie o conteúdo de `dist/` para
`public_html/`.

Depois de publicar, ajuste `dominio` em `data/site.json` para o endereço real e rode o
build de novo — esse valor alimenta as URLs canônicas, o Open Graph e o `sitemap.xml`.

---

## 4. Formulário de contato

Sem configuração, o formulário monta a mensagem e abre o WhatsApp já preenchido. Funciona
imediatamente, sem servidor.

Para receber por e-mail, crie um formulário no [Formspree](https://formspree.io) (plano
gratuito serve) e cole a URL em `form_endpoint` no `data/site.json`. O JavaScript passa a
enviar por lá, com mensagem de sucesso e de erro já tratadas.

---

## 5. Trocar a foto do hero

Em `data/site.json`:

```json
"hero_variante": "capa"      → foto "Capa" enviada pela cliente (padrão)
"hero_variante": "real"      → fotografia do ensaio anterior
"hero_variante": "estudio"   → imagem gerada por IA
```

Rode `python3 build.py` depois de alterar.

---

## 6. Publicar um artigo

O sistema de conteúdos está funcionando. Para publicar, edite `data/artigos.json` e rode
`python3 build.py`. Cada artigo gera uma página própria em `/conteudos/[slug]/`, entra na
listagem, respeita os filtros por área, aparece no `sitemap.xml` e recebe dados
estruturados `Article`.

O arquivo já traz um artigo-modelo com todos os tipos de bloco disponíveis. Ele está
marcado com `"rascunho": true` e por isso **não** aparece no site — copie a estrutura dele
para escrever os textos reais.

Campos de cada artigo:

| Campo | O que é |
|---|---|
| `slug` | Endereço da página. Só letras minúsculas e hífens. |
| `rascunho` | `true` esconde do site. Remova ou coloque `false` para publicar. |
| `titulo` | Vira o H1 e o título no Google. |
| `resumo` | Aparece na listagem e como meta description. |
| `categoria` | Um dos três slugs de área, para o filtro funcionar. |
| `data` | Formato `AAAA-MM-DD`. Ordena a listagem, mais recente primeiro. |
| `leitura` | Minutos estimados. |
| `corpo` | Lista de blocos. |

Tipos de bloco: `p` (parágrafo), `h2` (subtítulo), `lista` (com o campo `itens`) e
`destaque` (citação em serifa — no máximo um por texto).

Enquanto não houver nenhum artigo publicado, a página de conteúdos mostra um estado vazio
com convite para enviar uma dúvida, e o bloco de conteúdos some da home automaticamente.

---

## 7. Pendências — informações que faltam

Todos os campos abaixo aparecem no site **destacados em amarelo** para não passarem
despercebidos. Nenhum deles foi inventado.

### Precisa da cliente

- [ ] **Endereço do escritório** — hoje o campo está vazio em `data/site.json` e o site se
      ajusta sozinho: o endereço some do rodapé, da página de contato, da política de
      privacidade e dos dados estruturados. Basta preencher `endereco` e rodar o build
      para ele reaparecer nos quatro lugares.
- [ ] **Cidade / região de atuação**
- [ ] **Razão social e CNPJ** — para a política de privacidade
- [ ] **Prazo de retenção de dados** e **quais cookies** o site vai usar
- [ ] **LinkedIn** — informar ou remover do `site.json`

### Precisa de decisão

- [ ] **Lista de assuntos por área** — os itens em `areas.json` seguem os exemplos do
      briefing e **precisam ser confirmados ou riscados um a um**. Só devem permanecer
      os assuntos que ela efetivamente atende.

### Recomendado

- [ ] **Uma foto em alta resolução para a página do Previdenciário.** As cinco fotos novas
      (2,5 MP) cobrem hero, posicionamento, sobre, a advogada e sucessões. A página de
      Direito Previdenciário ainda usa uma imagem do lote antigo, de 896 px.
- [ ] **Coerência cromática do conjunto.** Ver a observação no fim deste arquivo.

---

## 8. Verificações já feitas

- Sem rolagem horizontal em nenhuma página, no desktop e no mobile
- Alvos de toque com no mínimo 46 px
- Um único H1 por página, hierarquia de headings correta
- Todas as imagens com texto alternativo
- Navegação por teclado funcional, incluindo o submenu de áreas
- `prefers-reduced-motion` respeitado — as animações são desligadas
- Foco visível em todos os elementos interativos
- Imagens responsivas com WebP e fallback JPG, carregamento adiado
- `sitemap.xml`, `robots.txt`, canônicas, Open Graph e dados estruturados `Attorney`
- Bordas brancas residuais removidas de todas as fotografias de origem
- Fundo branco removido do logotipo, com versão invertida para o rodapé
- Favicon, ícone de app e `site.webmanifest` gerados a partir do monograma
- 81 verificações automatizadas nas 11 páginas, em desktop e mobile, sem falhas

---

## 9. Observação sobre publicidade

O rodapé traz o aviso de caráter informativo. Os textos foram escritos evitando promessa
de resultado, comparação com outros profissionais, depoimentos e números de casos. Antes
de publicar, vale uma leitura da cliente com esse olhar — a responsabilidade pelo conteúdo
publicitário é dela perante a OAB.

---

## 10. Observação sobre o conjunto fotográfico

As cinco fotos novas resolvem a resolução, mas ampliam a variação de cor do conjunto: verde
oliva na foto "Sobre", rosa na "A advogada", azul claro na de Sucessões, azul royal na
"Capa". A paleta do site nasceu do cartão de visita — grafite quente, greige e bronze — e
essas cores puxam para fora dela.

Isso não quebra o site. Cada foto, isolada, funciona bem na sua página. Mas quem percorre
o site inteiro de uma vez percebe a troca de registro.

Dois caminhos, se a cliente quiser resolver:

1. **Tratamento unificador** — uma leve dessaturação seletiva nos fundos, preservando a
   pele e as roupas. Reduz a variação sem descaracterizar as fotos.
2. **Nova seleção** — escolher, dentro do ensaio completo, um conjunto com fundos mais
   próximos entre si.

Não apliquei nenhum dos dois: alterar fotos aprovadas pela cliente é decisão dela, não
minha.
