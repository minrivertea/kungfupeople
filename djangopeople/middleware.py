from django.http import HttpResponseRedirect, get_host, HttpResponsePermanentRedirect
import re

from django.conf import settings
from djangopeople.models import AutoLoginKey, User

multislash_re = re.compile('/{2,}')

class NoDoubleSlashes:
    """
    123-reg redirects djangopeople.com/blah to djangopeople.net//blah - this
    middleware eliminates multiple slashes from incoming requests.
    """
    def process_request(self, request):
        if '//' in request.path:
            new_path = multislash_re.sub('/', request.path)
            return HttpResponseRedirect(new_path)
        else:
            return None

class RemoveWWW(object):
    def process_request(self, request):
        host = get_host(request)
        if host and host.startswith('www.'):
            newurl = "%s://%s%s" % (request.is_secure() and 'https' or 'http', host[len('www.'):], request.path)
            if request.GET:
                newurl += '?' + request.GET.urlencode()
            return HttpResponsePermanentRedirect(newurl)
        else:
            return None

class AutoLogin(object):
    def process_request(self, request):
        if request.GET.get('alu'):
            uuid = request.GET.get('alu')
            user = AutoLoginKey.find_user_by_uuid(uuid)
            if user:
                # "forcibly" log in as this user
                from django.contrib.auth import load_backend, login
                for backend in settings.AUTHENTICATION_BACKENDS:
                    if user == load_backend(backend).get_user(user.pk):
                        user.backend = backend
                if hasattr(user, 'backend'):
                    login(request, user)
            new_full_path = request.get_full_path().replace('alu=%s' % uuid, '')
            new_full_path = new_full_path.replace('?&','?').replace('&&','&')
            return HttpResponsePermanentRedirect(new_full_path)

        return None

class Recruitment(object):
    def process_request(self, request):
        if request.GET.get('rc') and request.GET.get('rc').isdigit():
            try:
                recruiter = User.objects.get(pk=request.GET.get('rc'))
                request.session['recruiter'] = recruiter.id
            except User.DoesNotExist:
                pass

        return None


class SWFUploadFileMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST':
            if 'Filename' in request.POST:
                # Not terribly secure but works
                # See http://code.google.com/p/django-filebrowser/issues/detail?id=222
                # for a possibly more sustainable solution
                request._dont_enforce_csrf_checks = True

        return None
