.PHONY: paper clean

paper:
	python3 scripts/make_paper_tables_figs.py --paper paper/assets/tefie_secure_paper.pdf --assets paper/assets --out output

clean:
	rm -rf output/tables output/figs
	mkdir -p output/tables output/figs
