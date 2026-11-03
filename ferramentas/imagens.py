#!/usr/bin/env python3
"""
Gera as variantes responsivas das fotografias a partir dos originais.

    python3 ferramentas/imagens.py            # todas
    python3 ferramentas/imagens.py sobre      # só uma

Lê de  fotos-originais/<nome>.<ext>
Grava em src/img/<nome>-<largura>.webp  (+ um .jpg de 760px como alternativa)

NÃO aplique máscara de nitidez aqui. Já foi tentado e o resultado foi pior:
nas fotografias escuras dela a máscara endurece a pele e realça os blocos de
compressão do arquivo original. A métrica que parecia confirmar o ganho
(variância do laplaciano) mede sobretudo artefato em área lisa quando a
imagem é majoritariamente sombra — numa das fotos, 77% dos pixels estão
abaixo de luminância 40. Avalie olhando o recorte no tamanho real de
exibição, não por número.
"""
import os
import sys
from pathlib import Path

import cv2
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGINAIS = RAIZ / "fotos-originais"
DESTINO = RAIZ / "src" / "img"

# Calibrado comparando o resultado na caixa de 547px, não por métrica.
QUALIDADE_WEBP = 90
QUALIDADE_JPG = 88

# Degraus do srcset. Um original mais estreito simplesmente não gera os
# maiores — build.py monta o srcset a partir dos arquivos que existem, com a
# largura real de cada um, então nada é anunciado sem existir.
DEGRAUS = (520, 760, 1100, 1300)


def gerar(origem: Path) -> None:
    nome = origem.stem
    src = cv2.imread(str(origem))
    if src is None:
        raise SystemExit(f"não consegui ler {origem}")
    altura, largura = src.shape[:2]

    # limpa variantes antigas para não deixar uma largura órfã no srcset
    for velho in DESTINO.glob(f"{nome}-*.webp"):
        velho.unlink()

    larguras = sorted({w for w in DEGRAUS if w < largura} | {largura})
    saidas = []
    for w in larguras:
        if w == largura:
            peq = src
        else:
            peq = cv2.resize(
                src, (w, round(altura * w / largura)), interpolation=cv2.INTER_LANCZOS4
            )
        pil = Image.fromarray(cv2.cvtColor(peq, cv2.COLOR_BGR2RGB))
        alvo = DESTINO / f"{nome}-{w}.webp"
        pil.save(alvo, "WEBP", quality=QUALIDADE_WEBP, method=6)
        saidas.append(f"{w}={alvo.stat().st_size // 1024}KB")
        if w == 760:
            pil.save(
                DESTINO / f"{nome}-760.jpg",
                "JPEG",
                quality=QUALIDADE_JPG,
                optimize=True,
                progressive=True,
            )
    print(f"{nome:16s} origem {largura}x{altura}  ->  " + "  ".join(saidas))


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    alvos = sys.argv[1:]
    arquivos = sorted(
        f for f in ORIGINAIS.iterdir()
        if f.suffix.lower() in {".jpg", ".jpeg", ".png"}
        and (not alvos or f.stem in alvos)
    )
    if not arquivos:
        raise SystemExit(f"nada para processar em {ORIGINAIS}")
    for f in arquivos:
        gerar(f)
    print("\nrode 'python3 build.py' em seguida para republicar o site")


if __name__ == "__main__":
    main()
