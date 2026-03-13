import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

_django_app = get_wsgi_application()


def app(environ, start_response):
    """WSGI app with temporary debug endpoint"""
    path = environ.get('PATH_INFO', '')
    if path == '/_debug/files':
        import json
        result = {}
        base = '/var/task'
        templates_dir = os.path.join(base, 'templates')
        result['cwd'] = os.getcwd()
        result['base_dir_contents'] = sorted(os.listdir(base)) if os.path.isdir(base) else 'NOT FOUND'
        result['templates_exists'] = os.path.isdir(templates_dir)

        if os.path.isdir(templates_dir):
            all_files = []
            for root, dirs, files in os.walk(templates_dir):
                for f in files:
                    all_files.append(os.path.relpath(os.path.join(root, f), base))
            result['template_files'] = sorted(all_files)
        else:
            result['template_files'] = []

        body = json.dumps(result, indent=2).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [body]
    return _django_app(environ, start_response)
