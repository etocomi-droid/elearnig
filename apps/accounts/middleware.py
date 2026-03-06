from apps.accounts.models import Project


class CurrentProjectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_project = None
        if request.user.is_authenticated:
            project_id = request.session.get('current_project_id')
            if project_id:
                try:
                    request.current_project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    del request.session['current_project_id']
        response = self.get_response(request)
        return response
