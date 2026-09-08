import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

application = get_wsgi_application()
from whitenoise import WhiteNoise
application = WhiteNoise(application, root=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"), prefix="static/")
