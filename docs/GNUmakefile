IMAGE = paperist/alpine-texlive-ja:latest

# ワンショットビルド(CI・確認用)
build:
	docker run --rm --volume $(PWD):/workdir $(IMAGE) latexmk css.tex

clean:
	docker run --rm --volume $(PWD):/workdir $(IMAGE) latexmk -C css.tex

# 継続ビルド(執筆時。css2026-data と同じ構成)
run:
	docker run --rm -itd --name texlive --volume $(PWD):/workdir $(IMAGE) sh -c "latexmk -pvc css.tex"

attach:
	docker exec -it texlive /bin/sh

stop:
	docker stop texlive
