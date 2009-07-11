import re
from unittest import TestCase

from newsletter.premailer import Premailer, etree

class PremailerTest(TestCase):
    
    def test_basic_html(self):
        """test the simplest case"""
        if not etree:
            # can't test it
            return
        
        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
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
        
        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:red">Hi!</h1>
        <p><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""
        
        p = Premailer(html)
        result_html = p.transform()
        
        whitespace_between_tags = re.compile('>\s*<',)
        
        expect_html = whitespace_between_tags.sub('><', expect_html).strip()
        result_html = whitespace_between_tags.sub('><', result_html).strip()
        
        self.assertEqual(expect_html, result_html)
        
        
    def test_parse_style_rules(self):
        
        p = Premailer('html') # won't need the html
        func = p._parse_style_rules
        rules = func("""
        h1, h2 { color:red; }
        /* ignore
          this */
        strong { 
          text-decoration:none
          }
        ul li {  list-style: 2px; }
        """)
        
        self.assertTrue('h1' in rules)
        self.assertTrue('h2' in rules)
        self.assertTrue('strong' in rules)
        self.assertTrue('ul li' in rules)
        
        self.assertEqual(rules['h1'], 'color:red')
        self.assertEqual(rules['h2'], 'color:red')
        self.assertEqual(rules['strong'], 'text-decoration:none')
        self.assertEqual(rules['ul li'], 'list-style:2px')
        
        
    def test_base_url_fixer(self):
        """if you leave some URLS as /foo and set base_url to 
        'http://www.google.com' the URLS become 'http://www.google.com/foo'
        """
        if not etree:
            # can't test it
            return
        
        html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="/images/foo.jpg"/>
        <img src="/images/bar.gif"/>
        <img src="http://www.googe.com/photos/foo.jpg">
        <a href="/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="subpage">Subpage</a>
        </body>
        </html>"""
        
        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="http://kungfupeople.com/images/foo.jpg"/>
        <img src="http://kungfupeople.com/images/bar.gif"/>
        <img src="http://www.googe.com/photos/foo.jpg"/>
        <a href="http://kungfupeople.com/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="http://kungfupeople.com/subpage">Subpage</a>
        </body>
        </html>"""
        
        p = Premailer(html, base_url='http://kungfupeople.com')
        result_html = p.transform()
        
        whitespace_between_tags = re.compile('>\s*<',)
        
        expect_html = whitespace_between_tags.sub('><', expect_html).strip()
        result_html = whitespace_between_tags.sub('><', result_html).strip()
        
        self.assertEqual(expect_html, result_html)
        
        