
https://bitbucket.org/jurko/suds/issue/89/suds-does-not-double-encode-when-necessary
```
virtualenv .
. bin/activate
pip install -r requirements.txt
sed -i 's/(?!(amp|lt|gt|quot|apos);)//' lib/python2.7/site-packages/suds/sax/enc.py
```
