# http://www.peterbe.com/plog/premailer.py
import re
from cStringIO import StringIO
try:
    import lxml.html
    from lxml.cssselect import CSSSelector
    from lxml import etree
except ImportError:
    import warnings
    warnings.warn("lxml not installed! Can't use premailer")
    etree = None

__version__='0'

class PremailerError(Exception):
    pass

class Premailer(object):
    
    def __init__(self, html, base_url=None):
        self.html = html
        self.base_url = base_url
        
    def _parse_style_rules(self, css_body):
        rules = {}
        css_comments = re.compile(r'/\*.*?\*/', re.MULTILINE|re.DOTALL)
        css_body = css_comments.sub('', css_body)
        
        regex = re.compile('((.*?){(.*?)})', re.DOTALL|re.M)
        semicolon_regex = re.compile(';(\s+)')
        colon_regex = re.compile(':(\s+)')
        for each in regex.findall(css_body.strip()):
            __, selectors, bulk = each
            
            bulk = semicolon_regex.sub(';', bulk.strip())
            bulk = colon_regex.sub(':', bulk.strip())
            if bulk.endswith(';'):
                bulk = bulk[:-1]
            for selector in [x.strip() for x in selectors.split(',') if x.strip()]:
                rules[selector] = bulk
            
        return rules
        
    def transform(self, pretty_print=True):
        """change the self.html and return it with CSS turned into style
        attributes.
        """
        if etree is None:
            return self.html
        
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(self.html.strip().encode('utf8')), parser)
        page = tree.getroot()
        
        if page is None:
            print repr(self.html)
            raise PremailerError("Could not parse the html")
        assert page is not None
        rules = {}
        
        for style in CSSSelector('style')(page):
            css_body = etree.tostring(style)
            css_body = css_body.split('>')[1].split('</')[0]
            rules.update(self._parse_style_rules(css_body))
            parent_of_style = style.getparent()
            parent_of_style.remove(style)
            
        for selector, style in rules.items():
            sel = CSSSelector(selector)
            for item in sel(page):
                old_style = item.attrib.get('style','')
                if old_style:
                    old_style += ';'
                item.attrib['style'] = old_style + style
            
        return etree.tostring(page, pretty_print=pretty_print)
            
                    
        
        
        
if __name__=='__main__':
    html = """<html>
        <head>
        <title>Test</title>
        <style>
        h1, h2 { color:red; }
        strong { 
          text-decoration:none
          }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""
    p = Premailer(html)
    print p.transform()
    
    