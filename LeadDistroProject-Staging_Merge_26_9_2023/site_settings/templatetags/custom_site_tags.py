from django import template
register = template.Library()

#todo: need to modify it further if found better solution
@register.filter
def auto_select_header(value, the_list):
    value = str(value).lower()
    list_ = the_list.split(',')
    for _ in list_:
        if str(_).strip() in value:
            return True
    return False 
