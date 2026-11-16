import unicodedata
from routes.models import City

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold().strip()) if not unicodedata.combining(c))

def find_city(name, state):
    state = state.upper()
    exact = City.objects.filter(state=state, name__iexact=name.strip()).first()
    if exact:
        return exact
    return next((c for c in City.objects.filter(state=state).iterator()
                 if normalize(c.name) == normalize(name)), None)
