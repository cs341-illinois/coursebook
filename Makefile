# Find all tex files one directory down
TEX=$(shell find . -path "./.git*" -prune -o -type f -iname "*.tex" -print)
MAIN_TEX=main_wrapper.tex
MAIN_TEX_SOURCE=main.tex
PDF_TEX=$(patsubst %.tex,%.pdf,$(MAIN_TEX))
MAIN_OUT=main.pdf
MAIN_EPUB=main.epub
BASE=$(patsubst %.tex,%,$(MAIN_TEX))
OTHER_FILES=$(addprefix $(BASE),.aux .log .synctex.gz .toc .out .blg .bbl .glg .gls .ist .glo)
BIBS=$(shell find . -maxdepth 2 -mindepth 2 -path "./.git*" -prune -o -type f -iname "*.bib" -print)
OTHER=$$(find . -iname *aux) $$(find . -iname *bbl) $$(find . -iname *blg)
ORDER_TEX=order.tex
ORDER_TEX_DEP=order.yaml

TEX_ORDER=$(shell sh -c "cat order.yaml | sed 's/^- //'")
CHAPTER_PDF=$(patsubst %,%.pdf,$(TEX_ORDER))

.PHONY: all
all: pdf epub
	-@latexmk -c
	-@rm *aux *bbl *glg *glo *gls *ist *latexmk *fls
	-@rm **/*aux **/*bbl **/*glg **/*glo **/*gls **/*ist **/*latexmk **/*fls

.PHONY: pdf
pdf: $(MAIN_OUT) chapters

.PHONY: chapters
chapters: $(CHAPTER_PDF)

.PHONY: debug
debug: $(PDF_TEX)-debug

.PHONY: epub
epub: $(MAIN_EPUB)

$(MAIN_EPUB): $(ORDER_TEX) $(MAIN_TEX_SOURCE)
	pandoc --toc -s -f latex -t epub --filter pandoc-citeproc --filter _scripts/pandoc_epub_filter.py -M link-citations=true --epub-cover-image _images/cover.png -M author="B. Venkatesh, L. Angrave, et Al." -o $(MAIN_EPUB) $(MAIN_TEX_SOURCE);

$(ORDER_TEX): $(ORDER_TEX_DEP)
	python3 _scripts/gen_order.py $^ > $@

$(CHAPTER_PDF): %.pdf: %.tex
	echo '\\let\\cleardoublepage\\clearpage' > $@.tmp
	echo "\includeonly{$(basename $^)}\input{$(MAIN_TEX)}" >> $@.tmp
	@latexmk -interaction=nonstopmode -quiet -pdflatex=lualatex -pdf -jobname="$@" $@.tmp \
		|| { echo "*** latexmk failed for $@"; grep -n -A3 '^! ' $@.log 2>/dev/null; rm -f $@.tmp; false; }
	@mv $@.pdf $@
	@ls $@ > /dev/null
	-@rm $@.tmp

$(MAIN_OUT): $(TEX) $(MAIN_TEX) $(BIBS) Makefile $(ORDER_TEX)
	@latexmk -quiet -pdflatex=lualatex -interaction=nonstopmode -pdf $(MAIN_TEX) \
		|| { echo "*** latexmk failed"; grep -n -A3 '^! ' $(basename $(MAIN_TEX)).log 2>/dev/null; false; }
	@ls $(PDF_TEX) > /dev/null
	@mv $(PDF_TEX) $(MAIN_OUT)
	@echo "Finished"

$(PDF_TEX)-debug: $(TEX) $(MAIN_TEX) $(BIBS) Makefile
	-@latexmk -interaction=nonstopmode -f -pdf $(MAIN_TEX) > latexmk.out
	@mv $(PDF_TEX)-debug $(MAIN_OUT)

.PHONY: clean
clean:
	-@rm $(PDF_TEX) $(OTHER_FILES) $(OTHER)



