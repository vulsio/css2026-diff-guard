# Marp slide build (docker image bundles chromium + Noto CJK)
# fonts/ はコンテナのフォントディレクトリにも載せる(<img> で読む SVG 図は @font-face が効かず fontconfig 経由になるため)
MARP = docker run --rm --init -e MARP_USER=$(shell id -u):$(shell id -g) -v $(CURDIR):/home/marp/app -v $(CURDIR)/fonts:/usr/share/fonts/slide:ro -e LANG=ja_JP.UTF-8 marpteam/marp-cli
SRC = slide.md
THEME = theme.css

.PHONY: build html pdf fonts clean
build: html pdf

# 本文フォント(Noto Sans JP 可変フォント)。docker image に日本語フォントが無いので同梱する
FONT = fonts/NotoSansJP.ttf fonts/NotoSansMonoCJKjp-Regular.otf fonts/NotoSansMonoCJKjp-Bold.otf
FONT_URL_NotoSansJP = https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf
# 等幅(コードブロック・アーキ名)。docker image の等幅は WenQuanYi のみで Bold が無く、
# 日本語を含む行の桁を揃えるには半角:全角 = 1:2 の CJK 等幅が要る
FONT_URL_NotoSansMonoCJKjp-Regular = https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKjp-Regular.otf
FONT_URL_NotoSansMonoCJKjp-Bold = https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKjp-Bold.otf
fonts: $(FONT)
fonts/%.ttf fonts/%.otf:
	mkdir -p fonts
	curl -sSL -o $@ '$(FONT_URL_$*)'

html: $(SRC) $(THEME) $(FONT)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.html

pdf: $(SRC) $(THEME) $(FONT)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.pdf

clean:
	rm -f slide.html slide.pdf
