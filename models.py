from sqlalchemy import *
from sqlalchemy.orm import *
import os
from passlib.hash import bcrypt

base_dir = os.path.dirname(__file__)
os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
db_path = os.path.join(base_dir, "data", "DnD.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

character_classes = Table(
    "character_classes",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id")),
    Column("class_id", Integer, ForeignKey("classes.id"))
)


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    alignment = Column(String)

    # Core information
    race_id = Column(Integer, ForeignKey("races.id"))
    race = relationship("Race")
    classes = relationship("Class", secondary="character_classes", backref="characters")
    background_id = Column(Integer, ForeignKey("backgrounds.id"))
    background = relationship("Background")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="characters")

    # Ability scores
    strength = Column(Integer)
    dexterity = Column(Integer)
    constitution = Column(Integer)
    intelligence = Column(Integer)
    wisdom = Column(Integer)
    charisma = Column(Integer)

    # Other importants
    inventory = Column(JSON)
    backstory = Column(Text)

    # Relationship to notes — one-to-many
    notes = relationship(
        "Notes",
        back_populates="character",
        foreign_keys="Notes.character_id"
    )


class Notes(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    category = Column(String)

    # Self-referential relationship
    parent_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    parent = relationship(
        "Notes",
        remote_side=[id],
        backref="children"
    )

    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    character = relationship(
        "Character",
        back_populates="notes",
        foreign_keys=[character_id]
    )
    user = relationship(
        "User",
        back_populates="notes",
        foreign_keys=[user_id]
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    characters = relationship("Character", back_populates="user")
    notes = relationship("Notes", back_populates="user")

    def set_password(self, password: str):
        self.hashed_password = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.hashed_password)


class Proficiency(Base):
    __tablename__ = "proficiencies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)
    target_index = Column(String)  # Links to skill, equipment, etc.
    url = Column(String, nullable=True)


class Race(Base):
    __tablename__ = "races"

    id                  = Column(Integer, primary_key=True)
    name                = Column(String,  nullable=False)
    index               = Column(String,  nullable=False, unique=True)
    speed               = Column(Integer)
    asi                 = Column(String)
    alignment           = Column(String)
    age                 = Column(String)
    size                = Column(String)
    size_description    = Column(String)
    starting_proficiencies = Column(JSON)
    languages           = Column(JSON)
    language_description  = Column(String)
    traits              = Column(JSON)
    url                 = Column(String, nullable=True)

    subraces = relationship(
        "Subrace",
        back_populates="race",
        cascade="all, delete-orphan"
    )

class Subrace(Base):
    __tablename__ = "subraces"

    id                      = Column(Integer, primary_key=True)
    index                   = Column(String,  nullable=False, unique=True)
    name                    = Column(String,  nullable=False)
    desc                    = Column(Text)
    ability_bonuses         = Column(JSON)
    racial_traits           = Column(JSON)
    languages               = Column(JSON)
    starting_proficiencies  = Column(JSON)
    url                     = Column(String, nullable=True)

    race_index              = Column(String, ForeignKey("races.index"), nullable=False)
    race                    = relationship("Race", backref="subraces_list")
    

class Spell(Base):
    __tablename__ = 'spells'

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    desc = Column(JSON, nullable=False)
    higher_level = Column(JSON)
    range = Column(String)
    components = Column(JSON)
    material = Column(String)
    duration = Column(String)
    concentration = Column(Boolean)
    casting_time = Column(String)
    level = Column(Integer)
    attack_type = Column(String)
    damage = Column(JSON)
    damage_at_slot_level = Column(JSON)
    school = Column(JSON)
    #Link these later to the proper table.
    classes = Column(JSON)
    subclasses = Column(JSON)
    url = Column(String, nullable=True)


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hit_die = Column(Integer)
    #More complex stuff
    proficiency_choices = Column(JSON)
    proficiencies = Column(JSON)
    saving_throws = Column(JSON)
    starting_equipment = Column(JSON)
    starting_equipment_options = Column(JSON)
    multi_classing = Column(JSON)
    spellcasting = Column(JSON)
    url = Column(String, nullable=True)

    subclasses = relationship("Subclass", back_populates="parent_class", cascade="all, delete-orphan")

class ClassLevel(Base):
    __tablename__ = "class_levels"
    id = Column(Integer, primary_key=True)
    class_index = Column(String, ForeignKey("classes.index"))
    level = Column(Integer)
    ability_score_bonuses = Column(Integer)
    prof_bonus = Column(Integer)
    features = Column(JSON)
    spellcasting = Column(JSON)
    class_specific = Column(JSON)
    url = Column(String, nullable=True)

class Subclass(Base):
    __tablename__ = "subclasses"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    class_index = Column(String, ForeignKey("classes.index"))
    url = Column(String, nullable=True)

    parent_class = relationship("Class", back_populates="subclasses")

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    equipment_category = Column(String)  
    url = Column(String, nullable=True)
    weight = Column(Float)
    cost_quantity = Column(Integer)
    cost_unit = Column(String)
    desc = Column(JSON)
    special = Column(JSON)
    
class Armor(Base):
    __tablename__ = "armor"

    id = Column(Integer, primary_key=True)
    equipment_index = Column(String, ForeignKey("equipment.index"), unique=True)
    armor_category = Column(String)  # Light, Medium, Heavy, Shield
    base_ac = Column(Integer)
    dex_bonus = Column(Boolean)
    str_minimum = Column(Integer)
    stealth_disadvantage = Column(Boolean)

    equipment = relationship("Equipment", backref="armor_stats")
    url = Column(String, nullable=True)

class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True)
    equipment_index = Column(String, ForeignKey("equipment.index"), unique=True)
    tool_type = Column(String)  # e.g. "Musical Instrument", "Artisan's Tool"
    url = Column(String, nullable=True)

class Weapon(Base):
    __tablename__ = "weapon"

    id = Column(Integer, primary_key=True)
    equipment_index = Column(String, ForeignKey("equipment.index"), unique=True)
    weapon_category = Column(String)  # Simple, Martial
    weapon_range = Column(String)     # Melee, Ranged
    category_range = Column(String)   # e.g. "Simple Melee"
    damage_dice = Column(String)
    damage_type = Column(String)
    range_normal = Column(Integer)
    throw_range_normal = Column(Integer)
    throw_range_long = Column(Integer)

    equipment = relationship("Equipment", backref="weapon_stats")
    url = Column(String, nullable=True)

class EquipmentProperty(Base):
    __tablename__ = "equipment_properties"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String)
    url = Column(String)

#Joining table between equipment and their properties. 
class EquipmentPropertyLink(Base):
    __tablename__ = "equipment_property_link"

    id = Column(Integer, primary_key=True)
    equipment_index = Column(String, ForeignKey("equipment.index"))
    property_index = Column(String, ForeignKey("equipment_properties.index"))
    
class MagicItem(Base):
    __tablename__ = "magic_items"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    equipment_category = Column(String)  # Often "Wondrous Item", "Potion", etc.
    rarity = Column(String)             # Common, Uncommon, Rare, etc.
    requires_attunement = Column(Boolean)
    unattunable = Column(Boolean)
    desc = Column(JSON)                 # Full description text
    special = Column(JSON)              # Optional special notes
    url = Column(String)

# A linking table between magic items and their potential ability to cast spells. 
class MagicItemSpell(Base):
    __tablename__ = "magic_item_spells"

    id = Column(Integer, primary_key=True)
    magic_item_index = Column(String, ForeignKey("magic_items.index"))
    spell_index = Column(String)  # Link to your spells table
    url = Column(String, nullable=True)

class MagicItemCharge(Base):
    __tablename__ = "magic_item_charges"

    id = Column(Integer, primary_key=True)
    magic_item_index = Column(String, ForeignKey("magic_items.index"))
    max_charges = Column(Integer)
    recharge_condition = Column(String)  # e.g. "at dawn", "on a long rest"
    url = Column(String, nullable=True)


class Trait(Base):
    __tablename__ = "traits"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String, nullable=False)
    desc = Column(Text)
    races = Column(JSON)        # List of race indexes
    subraces = Column(JSON)     # List of subrace indexes
    url = Column(String)

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String, nullable=False)
    class_index = Column(String)
    subclass_index = Column(String)
    optional_feat = Column(Boolean)
    level = Column(Integer)
    desc = Column(Text)
    url = Column(String, nullable=True)

class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String)
    desc = Column(Text)
    url = Column(String, nullable=True)


class DamageType(Base):
    __tablename__ = "damage_types"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String)
    desc = Column(Text)
    url = Column(String, nullable=True)

class Background(Base):
    __tablename__ = "backgrounds"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True)
    name = Column(String)
    description = Column(Text)
    starting_proficiencies = Column(Text)  # You can store as comma-separated or JSON
    starting_equipment = Column(Text)

class Monster(Base):
    __tablename__ = "monsters"

    id = Column(Integer, primary_key=True)
    index = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    size = Column(String)
    type = Column(String)
    alignment = Column(String)

    armor_class = Column(JSON)         # List of AC objects
    hit_points = Column(Integer)
    hit_dice = Column(String)
    hit_points_roll = Column(String)

    speed = Column(JSON)               # Walk, fly, swim, etc.

    strength = Column(Integer)
    dexterity = Column(Integer)
    constitution = Column(Integer)
    intelligence = Column(Integer)
    wisdom = Column(Integer)
    charisma = Column(Integer)

    damage_vulnerabilities = Column(JSON)
    damage_resistances = Column(JSON)
    damage_immunities = Column(JSON)
    condition_immunities = Column(JSON)

    senses = Column(JSON)
    languages = Column(String)

    challenge_rating = Column(Float)
    proficiency_bonus = Column(Integer)
    xp = Column(Integer)

    image = Column(String)
    url = Column(String, nullable=True)


class MonsterProficiency(Base):
    __tablename__ = "monster_proficiencies"

    id = Column(Integer, primary_key=True)
    monster_index = Column(String, ForeignKey("monsters.index"))
    proficiency_index = Column(String)
    proficiency_name = Column(String)
    value = Column(Integer)
    url = Column(String, nullable=True)

class MonsterAction(Base):
    __tablename__ = "monster_actions"

    id = Column(Integer, primary_key=True)
    monster_index = Column(String, ForeignKey("monsters.index"))
    name = Column(String)
    desc = Column(Text)
    attack_bonus = Column(Integer)
    damage = Column(JSON)
    dc = Column(JSON)
    usage = Column(JSON)
    multiattack_type = Column(String)
    subactions = Column(JSON)
    url = Column(String, nullable=True)

class MonsterLegendaryAction(Base):
    __tablename__ = "monster_legendary_actions"

    id = Column(Integer, primary_key=True)
    monster_index = Column(String, ForeignKey("monsters.index"))
    name = Column(String)
    desc = Column(Text)
    damage = Column(JSON)
    dc = Column(JSON)
    url = Column(String, nullable=True)

class MonsterSpecialAbility(Base):
    __tablename__ = "monster_special_abilities"

    id = Column(Integer, primary_key=True)
    monster_index = Column(String, ForeignKey("monsters.index"))
    name = Column(String)
    desc = Column(Text)
    usage = Column(JSON)
    damage = Column(JSON)
    url = Column(String, nullable=True)
