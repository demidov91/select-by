import base64


def get_username(request):
    if 'name' not in request.COOKIES:
        return None
    try:
        return base64.b64decode(request.COOKIES['name']).decode('utf-8')
    except Exception as e:
        return None
