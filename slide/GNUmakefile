# Marp slide build (docker image bundles chromium + Noto CJK)
MARP = docker run --rm --init -e MARP_USER=$(shell id -u):$(shell id -g) -v $(CURDIR):/home/marp/app -e LANG=ja_JP.UTF-8 marpteam/marp-cli
SRC = slide.md
THEME = theme.css

.PHONY: build html pdf clean
build: html pdf

html: $(SRC) $(THEME)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.html

pdf: $(SRC) $(THEME)
	$(MARP) --theme $(THEME) --allow-local-files $(SRC) -o slide.pdf

clean:
	rm -f slide.html slide.pdf
