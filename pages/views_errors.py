from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.loader import get_template


def page_not_found(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def permission_denied(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def csrf_failure(request, reason=''):
    return render(request, 'errors/403.html', {'csrf': True}, status=403)


def server_error(request):
    lang = 'ru' if request.path.startswith('/ru/') else 'ua'
    html = get_template('errors/500.html').render({'lang': lang})
    return HttpResponseServerError(html)
