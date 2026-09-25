from django.db.models import Q

HIDDEN_CUSTOMER_NAMES = ("REDE S.O.S EDUARDO", "REDE KEKA")

def is_hidden_customer_name(name: str) -> bool:
    normalized = " ".join(str(name or "").split()).casefold()
    return any(normalized == hidden.casefold() for hidden in HIDDEN_CUSTOMER_NAMES)

def exclude_hidden_customers(queryset, relation: str | None = "customer"):
    field = "name" if relation is None else f"{relation}__name"
    return queryset.exclude(Q(**{f"{field}__iexact": HIDDEN_CUSTOMER_NAMES[0]}) | Q(**{f"{field}__iexact": HIDDEN_CUSTOMER_NAMES[1]}))
