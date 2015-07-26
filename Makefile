.PHONY: server static prep

NODEMOD = $$(pwd)/js_ui/node_modules

bin/activate:
	virtualenv .

bin/nodeenv: bin/activate
	. bin/activate && pip install -r requirements.txt
	sed -i 's/(?!(amp|lt|gt|quot|apos);)//' lib/python2.7/site-packages/suds/sax/enc.py

bin/node: bin/nodeenv
	@echo "Please be patient, compiling nodejs"
	. bin/activate && nodeenv -p --node=0.12.7 --npm=3.2.0 # slow, compiles node

js_ui/node_modules: bin/node
	. bin/activate && npm install

prep: js_ui/node_modules

static/zenrox_bundle.js: js_ui/zenrox_ui.jsx | js_ui/node_modules
	mkdir -p static
	. bin/activate && export PATH=$(NODEMOD)/.bin:$$PATH && \
	    flow check $< && \
	    browserify $< -t [ reactify --es6 --strip-types ] -o $@

static/fixed-data-table.min.css: $(NODEMOD)/fixed-data-table/dist/fixed-data-table.min.css | js_ui/node_modules
	mkdir -p static
	cp $< $@

static: static/zenrox_bundle.js static/fixed-data-table.min.css

server: static
	. bin/activate && python zenrox_web.py
