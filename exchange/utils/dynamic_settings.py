from exchange.models import DynamicSettings


def get_dynamic_setting(key: str) -> str:
    try:
        return DynamicSettings.objects.get(key=key).value
    except DynamicSettings.DoesNotExist:
        return None
