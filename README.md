
https://bitbucket.org/jurko/suds/issue/89/suds-does-not-double-encode-when-necessary
```
virtualenv .
. bin/activate
pip install -r requirements.txt
sed -i 's/(?!(amp|lt|gt|quot|apos);)//' lib/python2.7/site-packages/suds/sax/enc.py

nodeenv -p --node=0.12.7 --npm=3.2.0 # slow, compiles node
cd js_ui
npm install
./node_modules/.bin/flow check src/
./node_modules/.bin/browserify src/zenrox_ui.jsx -t [ reactify --es6 --strip-types ] -o ../static/zenrox_bundle.js
cp node_modules/fixed-data-table/dist/fixed-data-table.min.css ../static/
```
