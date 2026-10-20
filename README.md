# Site — Daniela Clemente, Advogada

Site institucional estático, gerado a partir de arquivos de dados.
Direito Previdenciário e Inventários e Sucessões.

## Estado

**Em revisão.** O site está publicado apenas para apresentação e aprovação.
Enquanto `em_revisao` estiver como `true` em `data/site.json`, todas as páginas saem com
`noindex` e o `robots.txt` bloqueia os buscadores — um site com campos ainda em branco não
deve aparecer no Google no nome da advogada.

Os campos pendentes aparecem **destacados em amarelo** dentro do site. A lista completa
está no [LEIA-ME.md](LEIA-ME.md).

## Rodar localmente

```bash
python3 -m pip install pillow
python3 build.py
cd build/dist && python3 -m http.server 8000
```

Abra `http://localhost:8000`.

Para revisar sem servidor, abra `build/preview.html` — arquivo único, com as imagens
embutidas, que navega entre todas as páginas.

## Publicação

Cada push na branch `main` dispara o workflow em `.github/workflows/deploy.yml`, que gera
o site e publica no GitHub Pages. O prefixo de caminho é ajustado automaticamente conforme
o nome do repositório.

## Estrutura

```
data/          Conteúdo editável (site, áreas, artigos)
src/           CSS, JavaScript e imagens otimizadas
build.py       Gerador estático
LEIA-ME.md     Documentação completa e pendências
```

Para alterar textos, edite os arquivos em `data/` e rode `python3 build.py`.
Nenhum conteúdo precisa ser editado diretamente no HTML.
