"""
Provides the upload endpoint for the django storage backend.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from django.views.decorators.http import require_http_methods

# when the django backend is directly loaded from .backends.django_storage, 
# settings are not propertly initialized. It is therefore better to switch 
# to get_backend which loads settings and effectly arrives at the same provider.
from .backend import get_backend()

@login_required()
@require_http_methods(["PUT"])
def django_storage(request, key, content_type):
    """
    Upload files using django storage backend.
    """
    backend = get_backend()
    backend.upload_file(key, request.body, content_type)
    return HttpResponse()
