from django import template

register = template.Library()

@register.filter()
def item_module_name(item):
    return item._meta.module_name

from djangopeople.html2plaintext import html2plaintext as func_html2plaintext

@register.filter()
def html2plaintext(html):
    return func_html2plaintext(html, encoding='utf8')