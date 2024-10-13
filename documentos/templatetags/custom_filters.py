from django import template

register = template.Library()

@register.filter
def format_currency(value):
	try:
		value = float(value)
		return f"R$: {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
	except (ValueError, TypeError):
		return value