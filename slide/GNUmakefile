# Marp slide build (docker image bundles chromium + Noto CJK)
# fonts/ はコンテナのフォントディレクトリにも載せる(<img> で読む SVG 図は @font-face が効かず fontconfig 経由になるため)
MARP = docker run --rm --init -e MARP_USER=$(shell id -u):$(shell id -g) -v $(CURDIR):/home/marp/app -v $(CURDIR)/fonts:/usr/share/fonts/slide:ro -e LANG=ja_JP.UTF-8 marpteam/marp-cli
SRC = slide.md
THEME = theme.css

.PHONY: build html pdf fonts clean
build: html pdf

# 本文フォント(Noto Sans JP 可変フォント)。docker image に日本語フォントが無いので同梱する
FONT = fonts/NotoSansJP.ttf
FONT_URL = https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf
fonts: $(FONT)
$(FONT):
	mkdir -p fonts
	curl -sSL -o $@ '$(FONT_URL)'

html: $(SRC) $(THEME) $(FONT)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.html

pdf: $(SRC) $(THEME) $(FONT)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.pdf

clean:
	rm -f slide.html slide.pdf
