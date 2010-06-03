from django.conf import settings

def media(request):
    return {
        'STATICFILES_URL': settings.STATICFILES_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
