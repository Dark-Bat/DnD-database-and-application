import models
import api
from sqlalchemy import *
from sqlalchemy.orm import *
import requests
import time


#Utility
def slug(text):
    return text.lower().replace(" ", "-")

#Functions of the program
def get_race(race_name, session):
    #Calling race from API
    api_url = f"https://www.dnd5eapi.co/api/races/{slug(race_name)}"
    response = requests.get(api_url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch race '{race_name} : {response.status_code}")

    race_data = response.json()
    name = race_data["name"]
    asi = ", ".join([f"{a['ability_score']['name']}+{a['bonus']}" for a in race_data["ability_bonuses"]])
    traits = ", ".join([t["name"] for t in race_data["traits"]])

    #Logging the race to database
    existing = session.query(models.Race).filter_by(name=name).first()
    if existing:
        print(f"Race '{name}' already exists")
        return existing
    
    new_race = models.Race(name=name, asi=asi, traits=traits)
    session.add(new_race)
    session.commit()
    print(f"Logged race: {new_race.name}")
    return new_race

def get_class(session, class_name):
    # get the class from the API
    api_url = f"https://www.dnd5eapi.co/api/classes/{slug(class_name)}"
    response = requests.get(api_url, verify=False)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch class '{class_name}' : {response.status_code}")
    
    class_data = response.json()
    name = class_data["name"]
    hit_die = f"d{class_data['hit_die']}"

    #Get the class in the database
    existing = session.query(models.Class).filter_by(name=name).first()
    if existing:
        print(f"Class '{name}' already exists")
        return existing
    new_class = models.Class(name=name, hit_die=hit_die)
    session.add(new_class)
    session.commit()
    print(f"Logged class: {new_class.name}")
    return new_class

def get_skill(skill_name, session):
    #Calling skill from API
    api_url = f"https://www.dnd5eapi.co/api/proficiencies/skill-{slug(skill_name)}"
    response = requests.get(api_url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch skill '{skill_name} : {response.status_code}")

    skill_data = response.json()
    name = skill_data["name"]

    #Logging the race to database
    existing = session.query(models.Proficiency).filter_by(name=name).first()
    if existing:
        print(f"Race '{name}' already exists")
        return existing
    
    new_skill = models.Proficiency(name=name, type="skill")
    session.add(new_skill)
    session.commit()
    print(f"Logged skill: {new_skill.name}")
    return new_skill

def gimme(item_name, item_type, session):
    # Map item_type to model and API endpoint
    type_map = {
        "skill": {
            "model": models.Proficiency,
            "endpoint": lambda name: f"/proficiencies/skill-{slug(name)}",
            "db_filter": lambda q, name: q.filter_by(name=name)
        },
        "race": {
            "model": models.Race,
            "endpoint": lambda name: f"/races/{slug(name)}",
            "db_filter": lambda q, name: q.filter_by(name=name)
        },
        "class": {
            "model": models.Class,
            "endpoint": lambda name: f"/classes/{slug(name)}",
            "db_filter": lambda q, name: q.filter_by(name=name)
        },
        "spell": {
            "model": models.Spell,
            "endpoint": lambda name: f"/spells/{slug(name)}",
            "db_filter": lambda q, name: q.filter_by(name=name)
        },
        "subclass": {
            "model": models.Subclass,
            "endpoint": lambda name: f"/subclasses/{slug(name)}",
            "db_filter": lambda q, name: q.filter_by(name=name)
        }
        # Add more types as needed
    }

    if item_type not in type_map:
        raise ValueError(f"Unsupported item type: {item_type}")

    model = type_map[item_type]["model"]
    endpoint = type_map[item_type]["endpoint"](item_name)
    db_filter = type_map[item_type]["db_filter"]

    # Check database
    query = session.query(model)
    existing = db_filter(query, item_name).first()
    if existing:
        print(f"{item_type.capitalize()} '{item_name}' found in database.")
        return existing

    # Fetch from API
    api_url = f"https://www.dnd5eapi.co/api{endpoint}"
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {item_type} '{item_name}': {response.status_code}")

    data = response.json()

    # Create new object — customize per type
    if item_type == "skill":
        new_item = model(name=data["name"], type="skill")
    elif item_type == "race":
        new_item = model(
            name=data["name"],
            asi=str(data.get("ability_bonuses")),
            traits=str(data.get("traits"))
        )
    elif item_type == "class":
        new_item = model(
            name=data["name"],
            hit_die=data.get("hit_die")
        )
    elif item_type == "subclass":
        new_item = model(
            name=data["name"],
            index=data["index"],
            class_index=data["class"]["index"],
            subclass_flavor=data.get("subclass_flavor"),
            desc="\n".join(data.get("desc", [])),
            features=data.get("features"),
            url=data.get("url")
        )
    else:
        new_item = model(name=data["name"])  # fallback

    session.add(new_item)
    session.commit()
    print(f"Logged {item_type}: {new_item.name}")
    return new_item





