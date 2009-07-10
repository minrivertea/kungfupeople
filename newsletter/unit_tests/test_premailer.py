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
        
        
        
        