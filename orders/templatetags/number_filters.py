from django import template

register = template.Library()


@register.filter
def custom_intcomma(value):
    """將數字轉換為帶千分位逗點的格式，不受語言設定影響"""
    if value is None or value == '':
        return ''

    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    orig = str(value)
    # 處理小數點，分離整數和小數
    if '.' in orig:
        integer_part = orig.split('.')[0]
    else:
        integer_part = orig

    # 加千分位逗點
    result = ""
    for i, char in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            result = ',' + result
        result = char + result

    return result
