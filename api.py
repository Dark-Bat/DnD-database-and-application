import requests
from models import (
    SessionLocal, Class, Spell, Race, Monster, Equipment,
    Feature, Subclass
)

BASE_URL = 'https://www.dnd5eapi.co/api'
ENDPOINTS = [
    'classes',
    'spells',
    'races',
    'monsters',
    'equipment',
    'features',
    'subclasses',
    'backgrounds'
]
#Utility
def slug(text):
    return text.lower().replace(" ", "-")

#Functions for API
def search():
    session = SessionLocal()
    all_items = []

    def add_items(queryset, category):
        for item in queryset:
            all_items.append({
                'name': item.name,
                'index': item.index,
                'category': category
            })

    add_items(session.query(Class).all(), 'classes')
    add_items(session.query(Spell).all(), 'spells')
    add_items(session.query(Race).all(), 'races')
    add_items(session.query(Monster).all(), 'monsters')
    add_items(session.query(Equipment).all(), 'equipment')
    add_items(session.query(Feature).all(), 'features')
    add_items(session.query(Subclass).all(), 'subclasses')

    session.close()
    return all_items


def search_items(all_items, query):
    query = query.lower()
    exact_matches = [
        item for item in all_items
        if item['name'].lower() == query or item['index'].lower() == query
    ]
    if exact_matches:
        return exact_matches

    return [
        item for item in all_items
        if query in item['name'].lower() or query in item['index'].lower()
    ]

def get_item_by_index(category, index):
    session = SessionLocal()
    model_map = {
        'classes': Class,
        'spells': Spell,
        'races': Race,
        'monsters': Monster,
        'equipment': Equipment,
        'features': Feature,
        'subclasses': Subclass
    }

    model = model_map.get(category)
    if not model:
        session.close()
        return None

    item = session.query(model).filter_by(index=index).first()
    session.close()
    return item


def rank_search_term(item, query):
    name = item['name'].lower()
    index = item['index'].lower()
    query = query.lower()
    score = 0

    if name ==query or index == query:
        score +=100
        #This is an exact match
    elif name.startswith(query) or index.startswith(query):
        score += 50
    elif query in name or query in index:
        score += 20
    
    return score


