import models
import requests
import time
from sqlalchemy import *
from sqlalchemy.exc import OperationalError


session = models.SessionLocal()

def reset_database():
    models.Base.metadata.drop_all(bind=models.engine) 
    models.Base.metadata.create_all(bind=models.engine)
    print("Database reset and schema updated.")


def charles_said_let_there_be_data(session):
    reset_database()
    try:    
        load_races(session)
        load_subraces(session)
        load_spells(session)
        load_classes(session)
        load_subclasses(session)
        load_traits(session)
        load_equipment(session)
        load_features(session)
        load_conditions(session)
        load_damage_types(session)
        load_proficiencies(session)
        #oh lordy the big one
        load_monsters(session)
        session.commit()
        print("Database populated successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


API_BASE = "https://www.dnd5eapi.co/api"

def fetch_json(endpoint):
    url = f"{API_BASE}/{endpoint}"
    retries = 5
    delay = 5
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"❌ Failed to fetch {endpoint} after {retries} attempts.")


def load_races(session):
    models.Race.__table__.drop(models.engine, checkfirst=True)
    models.Base.metadata.create_all(models.engine, tables=[models.Race.__table__])
    data = fetch_json("races")["results"]
    for item in data:
        race_data = fetch_json(f"races/{item['index']}")
        race = models.Race(
            index=race_data['index'],
            name=race_data["name"],
            asi=str(race_data.get("ability_bonuses", [])),
            speed = race_data['speed'],
            alignment = race_data['alignment'],
            age = race_data['age'],
            size = race_data['size'],
            size_description = race_data['size_description'],
            starting_proficiencies = race_data['starting_proficiencies'],
            languages =race_data['languages'],
            language_description = race_data['language_desc'],
            traits=str([t["name"] for t in race_data.get("traits", [])]),
            url = race_data['url']
        )
        session.merge(race)
    session.commit()



def load_subraces(session):
    models.Subrace.__table__.drop(models.engine, checkfirst=True)

    for attempt in range(5):
        try:
            models.Base.metadata.create_all(models.engine, tables=[models.Subrace.__table__])
            break
        except OperationalError as e:
            if "database is locked" in str(e):
                print("Database is locked. Retrying...")
                time.sleep(1)
            else:
                raise

    data = fetch_json("subraces")["results"]
    for item in data:
        subrace_data = fetch_json(f"subraces/{item['index']}")
        race_index = subrace_data["race"]["index"]
        race_obj = session.query(models.Race).filter_by(index=race_index).first()
        if race_obj is None:
            raise ValueError(f"Race with index '{race_index}' not found.")

        subrace = models.Subrace(
            index=subrace_data["index"],
            name=subrace_data["name"],
            desc=subrace_data.get("desc", ""),
            ability_bonuses=subrace_data.get("ability_bonuses", []),
            racial_traits=subrace_data.get("racial_traits", []),
            languages=subrace_data.get("languages", []),
            starting_proficiencies=subrace_data.get("starting_proficiencies", []),
            url=subrace_data["url"],
            race_index=race_index
        )
        session.merge(subrace)
    session.commit()



def load_spells(session):
    data = fetch_json("spells")["results"]
    for item in data:
        spell_data = fetch_json(f"spells/{item['index']}")
        spell = models.Spell(
            index=spell_data["index"],
            name=spell_data["name"],
            desc=spell_data.get("desc", []),
            higher_level=spell_data.get("higher_level", []),
            range=spell_data.get("range", ""),
            components=spell_data.get("components", []),
            material=spell_data.get("material", ""),
            duration=spell_data.get("duration", ""),
            concentration=spell_data.get("concentration", False),
            casting_time=spell_data.get("casting_time", ""),
            level=spell_data.get("level", 0),
            attack_type=spell_data.get("attack_type", ""),
            damage=spell_data.get("damage", {}),
            damage_at_slot_level=spell_data.get("damage_at_slot_level", {}),
            school=spell_data.get("school", {}),
            classes=spell_data.get("classes", []),
            subclasses=spell_data.get("subclasses", []),
            url=spell_data['url']
        )
        session.merge(spell)

def load_classes(session):
    models.Class.__table__.drop(models.engine, checkfirst=True)
    models.Base.metadata.create_all(models.engine, tables=[models.Class.__table__])

    data = fetch_json("classes")["results"]
    for item in data:
        class_data = fetch_json(f"classes/{item['index']}")
        class_obj = models.Class(
            index=class_data["index"],
            name=class_data["name"],
            hit_die=class_data.get("hit_die", 0),
            proficiency_choices=class_data.get("proficiency_choices", []),
            proficiencies=class_data.get("proficiencies", []),
            saving_throws=class_data.get("saving_throws", []),
            starting_equipment=class_data.get("starting_equipment", []),
            starting_equipment_options=class_data.get("starting_equipment_options", []),
            multi_classing=class_data.get("multi_classing", {}),
            spellcasting=class_data.get("spellcasting", {}),
            url=class_data["url"]
        )
        session.merge(class_obj)

    session.commit()


def load_subclasses(session):
    models.Subclass.__table__.drop(models.engine, checkfirst=True)
    models.Base.metadata.create_all(models.engine, tables=[models.Subclass.__table__])

    data = fetch_json("subclasses")["results"]
    for item in data:
        subclass_data = fetch_json(f"subclasses/{item['index']}")
        class_index = subclass_data["class"]["index"]
        parent_class = session.query(models.Class).filter_by(index=class_index).first()

        if parent_class is None:
            print(f"Class '{class_index}' not found for subclass '{subclass_data['index']}'. Skipping.")
            continue

        subclass_obj = models.Subclass(
            index=subclass_data["index"],
            name=subclass_data["name"],
            url=subclass_data["url"],
            parent_class=parent_class 
        )
        session.merge(subclass_obj)

    session.commit()


def load_traits(session):
    data = fetch_json("traits")["results"]
    for item in data:
        trait_data = fetch_json(f"traits/{item['index']}")
        trait_obj = models.Trait(
            index=trait_data["index"],
            name=trait_data["name"],
            desc="\n".join(trait_data.get("desc", [])),
            races=trait_data.get("races", []),
            subraces=trait_data.get("subraces", []),
            url=trait_data["url"]
        )
        session.merge(trait_obj)

def load_equipment(session):
    data = fetch_json("equipment")["results"]
    for item in data:
        eq_data = fetch_json(f"equipment/{item['index']}")
        equipment = models.Equipment(
            index=eq_data["index"],
            name=eq_data["name"],
            equipment_category=eq_data["equipment_category"]["name"],
            url=eq_data["url"],
            weight=eq_data.get("weight"),
            cost_quantity=eq_data.get("cost", {}).get("quantity"),
            cost_unit=eq_data.get("cost", {}).get("unit"),
            desc=eq_data.get("desc", []),
            special=eq_data.get("special", [])
        )
        session.merge(equipment)

        # Armor
        if "armor_category" in eq_data:
            armor = models.Armor(
                equipment_index=eq_data["index"],
                armor_category=eq_data["armor_category"],
                base_ac=eq_data["armor_class"].get("base"),
                dex_bonus=eq_data["armor_class"].get("dex_bonus", False),
                str_minimum=eq_data.get("str_minimum", 0),
                stealth_disadvantage=eq_data.get("stealth_disadvantage", False)
            )
            session.merge(armor)

        # Weapon
        if "weapon_category" in eq_data:
            weapon = models.Weapon(
                equipment_index=eq_data["index"],
                weapon_category=eq_data["weapon_category"],
                weapon_range=eq_data.get("weapon_range"),
                category_range=eq_data.get("category_range"),
                damage_dice=eq_data.get("damage", {}).get("damage_dice"),
                damage_type=eq_data.get("damage", {}).get("damage_type", {}).get("name"),
                range_normal=eq_data.get("range", {}).get("normal"),
                throw_range_normal=eq_data.get("throw_range", {}).get("normal"),
                throw_range_long=eq_data.get("throw_range", {}).get("long")
            )
            session.merge(weapon)

        # Tool
        if eq_data["equipment_category"]["name"].lower() == "tools":
            tool = models.Tool(
                equipment_index=eq_data["index"],
                tool_type=eq_data.get("tool_category", "Generic")
            )
            session.merge(tool)

        # Equipment Properties
        for prop in eq_data.get("properties", []):
            existing_prop = session.query(models.EquipmentProperty).filter_by(index=prop["index"]).first()
            if not existing_prop:
                prop_obj = models.EquipmentProperty(
                    index=prop["index"],
                    name=prop["name"],
                    url=prop["url"]
                )
                session.add(prop_obj)

            # Always add the link (even if the property already exists)
            link = models.EquipmentPropertyLink(
                equipment_index=eq_data["index"],
                property_index=prop["index"]
            )
            session.merge(link)


def load_features(session):
    data = fetch_json("features")["results"]
    for item in data:
        feat_data = fetch_json(f"features/{item['index']}")
        feature = models.Feature(
            index=feat_data["index"],
            name=feat_data["name"],
            class_index=feat_data.get("class", {}).get("index"),
            subclass_index=feat_data.get("subclass", {}).get("index"),
            optional_feat=feat_data.get("optional", False),
            level=feat_data.get("level", 0),
            desc="\n".join(feat_data.get("desc", [])),
            url=feat_data["url"]
        )
        session.merge(feature)

def load_conditions(session):
    data = fetch_json("conditions")["results"]
    for item in data:
        cond_data = fetch_json(f"conditions/{item['index']}")
        condition = models.Condition(
            index=cond_data["index"],
            name=cond_data["name"],
            desc="\n".join(cond_data.get("desc", [])),
            url=cond_data["url"]
        )
        session.merge(condition)

def load_damage_types(session):
    data = fetch_json("damage-types")["results"]
    for item in data:
        dmg_data = fetch_json(f"damage-types/{item['index']}")
        damage_type = models.DamageType(
            index=dmg_data["index"],
            name=dmg_data["name"],
            desc="\n".join(dmg_data.get("desc", [])),
            url=dmg_data["url"]
        )
        session.merge(damage_type)

def load_proficiencies(session):
    data = fetch_json("proficiencies")["results"]
    for item in data:
        prof_data = fetch_json(f"proficiencies/{item['index']}")
        proficiency = models.Proficiency(
            name=prof_data["name"],
            type=prof_data.get("type", "unknown"),
            target_index=prof_data.get("index")
        )
        session.merge(proficiency)

def load_monsters(session):
    data = fetch_json("monsters")["results"]
    for item in data:
        mon_data = fetch_json(f"monsters/{item['index']}")

        monster = models.Monster(
            index=mon_data["index"],
            name=mon_data["name"],
            size=mon_data.get("size"),
            type=mon_data.get("type"),
            alignment=mon_data.get("alignment"),
            armor_class=mon_data.get("armor_class", []),
            hit_points=mon_data.get("hit_points"),
            hit_dice=mon_data.get("hit_dice"),
            hit_points_roll=mon_data.get("hit_points_roll"),
            speed=mon_data.get("speed", {}),
            strength=mon_data.get("strength"),
            dexterity=mon_data.get("dexterity"),
            constitution=mon_data.get("constitution"),
            intelligence=mon_data.get("intelligence"),
            wisdom=mon_data.get("wisdom"),
            charisma=mon_data.get("charisma"),
            damage_vulnerabilities=mon_data.get("damage_vulnerabilities", []),
            damage_resistances=mon_data.get("damage_resistances", []),
            damage_immunities=mon_data.get("damage_immunities", []),
            condition_immunities=mon_data.get("condition_immunities", []),
            senses=mon_data.get("senses", {}),
            languages=mon_data.get("languages"),
            challenge_rating=mon_data.get("challenge_rating"),
            proficiency_bonus=mon_data.get("proficiency_bonus"),
            xp=mon_data.get("xp"),
            image=mon_data.get("image"),
            url=mon_data.get("url"),
        )
        session.merge(monster)

        # Proficiencies
        for prof in mon_data.get("proficiencies", []):
            prof_obj = models.MonsterProficiency(
                monster_index=mon_data["index"],
                proficiency_index=prof["proficiency"]["index"],
                proficiency_name=prof["proficiency"]["name"],
                value=prof.get("value")
            )
            session.merge(prof_obj)

        # Actions
        for act in mon_data.get("actions", []):
            action = models.MonsterAction(
                monster_index=mon_data["index"],
                name=act.get("name"),
                desc=act.get("desc"),
                attack_bonus=act.get("attack_bonus"),
                damage=act.get("damage", []),
                dc=act.get("dc"),
                usage=act.get("usage"),
                multiattack_type=act.get("multiattack_type"),
                subactions=act.get("actions", [])
            )
            session.merge(action)

        # Legendary Actions
        for leg in mon_data.get("legendary_actions", []):
            legendary = models.MonsterLegendaryAction(
                monster_index=mon_data["index"],
                name=leg.get("name"),
                desc=leg.get("desc"),
                damage=leg.get("damage", []),
                dc=leg.get("dc")
            )
            session.merge(legendary)

        # Special Abilities
        for special in mon_data.get("special_abilities", []):
            ability = models.MonsterSpecialAbility(
                monster_index=mon_data["index"],
                name=special.get("name"),
                desc=special.get("desc"),
                usage=special.get("usage"),
                damage=special.get("damage", [])
            )
            session.merge(ability)
