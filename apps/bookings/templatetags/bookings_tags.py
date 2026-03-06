from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """辞書からキーで値を取得するテンプレートフィルタ"""
    if isinstance(dictionary, dict):
        # テンプレートのforloop.counter0は整数だが念のため型変換を試みる
        result = dictionary.get(key)
        if result is None:
            try:
                result = dictionary.get(int(key))
            except (ValueError, TypeError):
                result = []
        return result if result is not None else []
    return []


@register.filter
def split(value, delimiter=','):
    """文字列を分割するテンプレートフィルタ"""
    return value.split(delimiter)
