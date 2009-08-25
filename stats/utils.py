## Start stealing from django_extensions/management/commands/show_urls.py

from django.core.exceptions import ViewDoesNotExist

def extract_views_from_urlpatterns(urlpatterns, base=''):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a two-tuple: (view_func, regex)
    """
    views = []
    for p in urlpatterns:
        if hasattr(p, '_get_callback'):
            try:
                views.append((p._get_callback(), base + p.regex.pattern, p.name))
            except ViewDoesNotExist:
                continue
        elif hasattr(p, '_get_url_patterns'):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(extract_views_from_urlpatterns(patterns, base + p.regex.pattern))
        else:
            raise TypeError, _("%s does not appear to be a urlpattern object") % p
    return views

## End stealing