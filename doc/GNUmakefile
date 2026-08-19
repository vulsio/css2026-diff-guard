IMAGE = paperist/alpine-texlive-ja:latest
MAIN = css2026-diff-guard.tex

# ワンショットビルド(CI・確認用)
build:
	docker run --rm --volume $(PWD):/workdir $(IMAGE) latexmk $(MAIN)

clean:
	docker run --rm --volume $(PWD):/workdir $(IMAGE) latexmk -C $(MAIN)

# 継続ビルド(執筆時。css2026-data と同じ構成)
run:
	docker run --rm -itd --name texlive --volume $(PWD):/workdir $(IMAGE) sh -c "latexmk -pvc $(MAIN)"

attach:
	docker exec -it texlive /bin/sh

stop:
	docker stop texlive
