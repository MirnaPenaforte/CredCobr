from apps.companies.models import State


def navigation(request):
    if not request.user.is_authenticated:
        return {"navigation_states": []}
    return {"navigation_states": State.objects.all()}
