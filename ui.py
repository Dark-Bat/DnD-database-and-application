from PySide6.QtWidgets import QListWidget, QListWidgetItem, QComboBox, QPushButton, QWidget, QCheckBox, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from models import SessionLocal
import models
import api
from sqlalchemy.orm.exc import DetachedInstanceError
import homebrew_ui
from homebrew_ui import HomebrewWindow

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.all_items = api.search()

        self.setWindowTitle("D&D Info")
        self.resize(800, 600)
        self.session = SessionLocal()
        
        skill_names = [
            "Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception",
            "History", "Insight", "Intimidation", "Investigation", "Medicine",
            "Nature", "Perception", "Performance", "Persuasion", "Religion",
            "Sleight of Hand", "Stealth", "Survival"
        ]

        self.FORMATTERS = {
        'races': self.format_race,
        'subraces': self.format_subrace,
        'spells': self.format_spell,
        'proficiencies': self.format_proficiency,
        'classes': self.format_class,
        'subclasses': self.format_subclass,
        'equipment': self.format_equipment,
        'armor': self.format_armor,
        'weapons': self.format_weapon,
        'magic_items': self.format_magic_item,
        'traits': self.format_trait,
        'features': self.format_feature,
        'conditions': self.format_condition,
        'monsters': self.format_monster
    }

        self.search_box = QLineEdit()
        self.info_label = QLabel("Search")
        self.info_label.setTextFormat(Qt.TextFormat.RichText); self.info_label.setWordWrap(True)
        self.prof_label = QLabel("Proficiencies")
        self.suggestion_list = QListWidget()

        self.layout1 = QVBoxLayout()
        self.layout1.addWidget(self.search_box)
        self.layout1.addWidget(self.suggestion_list)
        self.layout1.addWidget(self.info_label)

        layout2 = QVBoxLayout()
        layout2.addWidget(self.prof_label)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.Shape.HLine)
        h_line.setFrameShadow(QFrame.Shadow.Sunken)
        layout2.addWidget(h_line)

        self.save_button = QPushButton("Save Character")
        self.save_button.clicked.connect(self.save_character)

        self.new_window_button = QPushButton("Click to add new stuff")
        self.new_window_button.clicked.connect(self.open_custom_menu)

        self.class_dropdown = QComboBox()
        classes = self.session.query(models.Class).all()
        for cls in classes:
            self.class_dropdown.addItem(cls.name)

        self.race_dropdown = QComboBox()
        race = self.session.query(models.Race).all()
        for rce in race:
            self.race_dropdown.addItem(rce.name)

        layout2.addWidget(self.race_dropdown)
        layout2.addWidget(self.class_dropdown)
        layout2.addWidget(self.save_button)

        
        self.skill_boxes = []
        for name in skill_names:
            box = QCheckBox(name)
            self.skill_boxes.append(box)
            layout2.addWidget(box)
        
        layout3 = QHBoxLayout()
        layout3.addLayout(layout2)
        layout3.addLayout(self.layout1)
        self.setLayout(layout3)

        # Connect input box signal to internal handler
        self.search_box.textChanged.connect(self.handle_search_input)

        self.search_box.returnPressed.connect(self.handle_input)

        self.suggestion_list.itemClicked.connect(self.handle_suggestion_click)
    def open_custom_menu(self):
        self.homebrew_window = HomebrewWindow(self.session)
        self.homebrew_window.show()

    def oops_we_dont_have_that(self, query):
        self.info_label.setText(f"As of now our database doesn't have '{query}'\n check for spelling mistakes, typos or weird spaces that databases hate \n or if its not in D&D SRD, and you want to add it, click below")
        self.layout1.addWidget(self.new_window_button)
    def get_selected_proficiencies(self):
        return {
        box.text(): True
        for box in self.skill_boxes
        if box.isChecked()
        }

    def save_character(self):
        selected_skills = self.get_selected_proficiencies()
        chosen_class = self.class_dropdown.currentText()
        race_name = self.race_dropdown.currentText()

        # You can now use selected_skills, class, and race however you like
        print("Race:", race_name)
        print("Class:", chosen_class)
        print("Skills:", selected_skills)

        self.info_label.setText("Character saved successfully!")

    def handle_input(self):
        query = self.search_box.text().strip()

        if not query:
            self.info_label.setText("Type a race, class, or spell name.")
            return
  # Fetch all items from database
        results = api.search_items(self.all_items, query)

        if not results:
            self.oops_we_dont_have_that(query)
            return

        # Just show the first match for now
        item = results[0]
        details = api.get_item_by_index(item['url'])

        if not details:
            self.info_label.setText("Error fetching item details.")
            self.oops_we_dont_have_that(query)
            return

        # Display based on category
        category = item['category']
        print(f"Category value: {category!r}")



    def handle_search_input(self):
        query = self.search_box.text().strip()
        if not query:
            self.clear_suggestions()
            return

        items = self.search_items(query)
        suggestions = self.autocomplete_search(items, query)
        self.update_suggestions_ui(suggestions)
        
    def update_suggestions_ui(self, suggestions):
        self.suggestion_list.clear()
        for item in suggestions:
            list_item = QListWidgetItem(f"{item['name']} ({item['index']})")
            list_item.setData(Qt.UserRole, item)
            self.suggestion_list.addItem(list_item)


    def clear_suggestions(self):
        self.suggestion_list.clear()

    def autocomplete_search(self, items, query, max_results=5):
        scored = [
            (item, api.rank_search_term(item, query))
            for item in items
        ]
        #sort the score by descending order from rank search term
        filtered = [item for item, score in scored if score >0]

        sorted_items = sorted(filtered, key=lambda x: api.rank_search_term(x, query), reverse=True)
        return sorted_items[:max_results]

    def search_items(self, query):
        query = query.lower()
        return[
            item for item in self.all_items
            if query in item['name'].lower() or query in item['index'].lower()
            ]

    
    #Clicking suggestions and giving information
    def handle_suggestion_click(self, list_item):
        print("clicked")
        item = list_item.data(Qt.UserRole)
        print("Item Data", item)
        category = item.get('category', '').lower()
        index = item.get('index')
        print(category, index)
        details = api.get_item_by_index(category, index)
        print("Details object:", details)
        if not details:
            self.info_label.setText("Error fetching item details")
            return

        formatter = self.FORMATTERS.get(category)

        if formatter:
            if category == "monsters":
                proficiencies = self.get_monster_related(self.session, models.MonsterProficiency, index)
                actions = self.get_monster_related(self.session, models.MonsterAction, index)
                legendary_actions = self.get_monster_related(self.session, models.MonsterLegendaryAction, index)
                special_abilities = self.get_monster_related(self.session, models.MonsterSpecialAbility, index)
                html = self.format_monster(details, proficiencies, actions, legendary_actions, special_abilities)
                self.info_label.setText(html)
                return
            else:
                html = formatter(details)
                print("formatted html", html)
                self.info_label.setText(html)
        else:
            print("Available formatter keys:", self.FORMATTERS.keys())
            self.info_label.setText(f"No formatter available for category: {category}")


    def format_race(self, race):
        return f"""<b>{race.name}</b><br>
        Index: {race.index}<br>
        ASI: {race.asi}<br>
        Traits: {race.traits}
        """
    def format_subrace(self, subrace):
        traits = ', '.join(subrace.racial_traits or [])
        langs = ', '.join(subrace.languages or [])
        profs = ', '.join(subrace.starting_proficiencies or [])
        asi = ', '.join([f"{ab['ability_score']['name']} +{ab['bonus']}" for ab in subrace.ability_bonuses or []])

        return f"""<b>{subrace.name}</b><br>
        Parent Race: {subrace.race}<br>
        ASI: {asi}<br>
        Traits: {traits}<br>
        Languages: {langs}<br>
        Proficiencies: {profs}<br>
        Description: {subrace.desc}
        """
    def format_spell(self, spell):
        desc = '<br>'.join(spell.desc or [])
        components = ', '.join(spell.components or [])
        damage = ', '.join(f"{k}: {v}" for k, v in (spell.damage or {}).items())

        return f"""<b>{spell.name}</b><br>
        Level: {spell.level}<br>
        School: {spell.school.get('name', 'Unknown')}<br>
        Casting Time: {spell.casting_time}<br>
        Range: {spell.range}<br>
        Duration: {spell.duration}<br>
        Components: {components}<br>
        Material: {spell.material}<br>
        Concentration: {'Yes' if spell.concentration else 'No'}<br>
        Attack Type: {spell.attack_type}<br>
        Damage: {damage}<br><br>
        {desc}
        """

    def format_proficiency(self, prof):
        return f"""<b>{prof.name}</b><br>
    Type: {prof.type}<br>
    Target Index: {prof.target_index}
    """

    def format_class(self, cls):
        # Extract names from dictionaries
        profs = ', '.join(p.get('name', 'Unknown') for p in cls.proficiencies or [])
        saves = ', '.join(s.get('name', 'Unknown') for s in cls.saving_throws or [])

        # Handle spellcasting ability
        spellcasting = cls.spellcasting.get('spellcasting_ability', {}).get('name', 'None') if cls.spellcasting else 'None'

        return f"""<b>{cls.name}</b><br>
        Hit Die: d{cls.hit_die}<br>
        Saving Throws: {saves}<br>
        Proficiencies: {profs}<br>
        Spellcasting Ability: {spellcasting}
        """


    def format_subclass(self, subcls):
        return f"""<b>{subcls.name}</b><br>
    Parent Class: {subcls.class_index}
    """

    def format_equipment(self, eq):
        desc = '<br>'.join(eq.desc or [])
        special = '<br>'.join(eq.special or [])

        return f"""<b>{eq.name}</b><br>
    Category: {eq.equipment_category}<br>
    Weight: {eq.weight} lb<br>
    Cost: {eq.cost_quantity} {eq.cost_unit}<br>
    {desc}<br>{special}
    """

    def format_armor(self, armor):
        return f"""<b>{armor.equipment.name}</b><br>
    Category: {armor.armor_category}<br>
    Base AC: {armor.base_ac}<br>
    Dex Bonus: {'Yes' if armor.dex_bonus else 'No'}<br>
    Strength Minimum: {armor.str_minimum}<br>
    Stealth Disadvantage: {'Yes' if armor.stealth_disadvantage else 'No'}
    """

    def format_weapon(self, weapon):
        return f"""<b>{weapon.equipment.name}</b><br>
    Category: {weapon.weapon_category}<br>
    Range: {weapon.weapon_range} ({weapon.category_range})<br>
    Damage: {weapon.damage_dice} {weapon.damage_type}<br>
    Normal Range: {weapon.range_normal}<br>
    Thrown Range: {weapon.throw_range_normal}–{weapon.throw_range_long}
    """

    def format_magic_item(self, item):
        desc = '<br>'.join(item.desc or [])
        special = '<br>'.join(item.special or [])

        return f"""<b>{item.name}</b><br>
    Category: {item.equipment_category}<br>
    Rarity: {item.rarity}<br>
    Requires Attunement: {'Yes' if item.requires_attunement else 'No'}<br>
    Unattunable: {'Yes' if item.unattunable else 'No'}<br>
    {desc}<br>{special}
    """

    def format_trait(self, trait):
        return f"""<b>{trait.name}</b><br>
    Races: {', '.join(trait.races or [])}<br>
    Subraces: {', '.join(trait.subraces or [])}<br>
    {trait.desc}
    """

    def format_feature(self, feature):
        return f"""<b>{feature.name}</b><br>
    Class: {feature.class_index}<br>
    Subclass: {feature.subclass_index}<br>
    Level: {feature.level}<br>
    Optional: {'Yes' if feature.optional_feat else 'No'}<br>
    {feature.desc}
    """

    def format_condition(self, cond):
        return f"""<b>{cond.name}</b><br>
    {cond.desc}
    """
    def format_monster(self, monster, proficiencies, actions, legendary_actions, special_abilities):
        # Basic stats
        stats = f"""
        STR: {monster.strength}, DEX: {monster.dexterity}, CON: {monster.constitution},<br>
        INT: {monster.intelligence}, WIS: {monster.wisdom}, CHA: {monster.charisma}
        """

        # Speed
        speed = ', '.join(f"{k}: {v}" for k, v in (monster.speed or {}).items())

        # Armor Class
        ac = ', '.join(str(a.get('value', '')) for a in (monster.armor_class or []))

        # Proficiencies
        profs = ', '.join(f"{p.proficiency_name} +{p.value}" for p in proficiencies)

        # Damage types
        dmg_vuln = ', '.join(monster.damage_vulnerabilities or [])
        dmg_resist = ', '.join(monster.damage_resistances or [])
        dmg_immune = ', '.join(monster.damage_immunities or [])
        cond_immune = ', '.join(ci['name'] for ci in monster.condition_immunities or [])

        # Senses
        senses = ', '.join(f"{k}: {v}" for k, v in (monster.senses or {}).items())

        # Abilities
        abilities = '<br>'.join(f"<b>{a.name}</b>: {a.desc}" for a in special_abilities)
        actions_html = '<br>'.join(f"<b>{a.name}</b>: {a.desc}" for a in actions)
        legendary_html = '<br>'.join(f"<b>{a.name}</b>: {a.desc}" for a in legendary_actions)

        return f"""<b>{monster.name}</b><br>
        Size: {monster.size}, Type: {monster.type}, Alignment: {monster.alignment}<br>
        HP: {monster.hit_points} ({monster.hit_dice}), AC: {ac}<br>
        Speed: {speed}<br>
        {stats}<br>
        Proficiencies: {profs}<br>
        Damage Vulnerabilities: {dmg_vuln}<br>
        Damage Resistances: {dmg_resist}<br>
        Damage Immunities: {dmg_immune}<br>
        Condition Immunities: {cond_immune}<br>
        Senses: {senses}<br>
        Languages: {monster.languages}<br>
        Challenge Rating: {monster.challenge_rating} (XP: {monster.xp})<br><br>
        <b>Special Abilities:</b><br>{abilities}<br><br>
        <b>Actions:</b><br>{actions_html}<br><br>
        <b>Legendary Actions:</b><br>{legendary_html}
        """

    def get_monster_related(self, session, model, monster_index):
        return session.query(model).filter_by(monster_index=monster_index).all()