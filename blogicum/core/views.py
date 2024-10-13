from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView


# class PageNotFoundTemplateView(TemplateView):
#     template_name = 'pages/404.html'
#     status = 404

#     def get(self, request, *args: Any, **kwargs: Any):
#         response = super().get(request, *args, **kwargs)
#         response.status_code = self.status
#         return response


# class ServerErrorTemplateView(PageNotFoundTemplateView):
#     template_name = 'pages/500.html'
#     status = 500


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)
