## Various templatetags for misc stuff
##

from django import template

register = template.Library()

def uniqify(seq, idfun=None): 
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        ##if marker in seen: continue
        if seen.has_key(marker): continue
        seen[marker] = 1
        result.append(item)
    return result



@register.filter()
def uniqify_on(list_, on):
    return uniqify(list_, lambda x: getattr(x, on))
