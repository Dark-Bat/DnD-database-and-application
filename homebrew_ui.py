# homebrew_ui.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QMessageBox, QCheckBox
)
from sqlalchemy.orm import Session
from models import (
    Spell, Race, Subrace, Subclass,
    Equipment, Monster, MagicItem, Weapon, Feature, Trait
)

class HomebrewWindow(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Add Homebrew Entry")
        self.setMinimumSize(400, 350)

        # Main form widgets
        self.type_selector = QComboBox()
        self.type_selector.addItems([
            "Spell", "Race", "Subrace", "Class", "Subclass",
            "Equipment", "Monster", "Magic Item", "Weapon",
            "Feature", "Trait",
        ])
        self.name_input   = QLineEdit()
        self.desc_input   = QTextEdit()
        # type-specific inputs
        self.level_input  = QLineEdit()
        self.school_input = QLineEdit()
        self.concentration_bool = QCheckBox()
        self.material_input = QLineEdit()
        self.duration = QLineEdit()
        self.casting_time = QLineEdit()
        # (you’ll add more fields for races, classes, etc.)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("What is it?"))
        layout.addWidget(self.type_selector)
        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.desc_input)

        # Spell-only fields
        layout.addWidget(QLabel("Level"))
        layout.addWidget(self.level_input)
        layout.addWidget(QLabel("School"))
        layout.addWidget(self.school_input)
        #Race only field

        #Class only field

        #Subrace only

        #Subclass only

        #Equipment

        #Monster

        #Magic Item

        #Weapon

        #Feature

        #Trait

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_entry)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        # Show/hide fields when type changes
        self.type_selector.currentTextChanged.connect(self.update_fields)
        self.update_fields(self.type_selector.currentText())

    def update_fields(self, entry_type: str):
        is_spell = entry_type == "Spell"
        self.level_input.setVisible(is_spell)
        self.school_input.setVisible(is_spell)

        is_race = entry_type == "Race"

        is_class = entry_type == "Class"

        is_subrace = entry_type == "Subrace"

        is_subclass = entry_type == "Subclass"

        is_equipment = entry_type == "Equipment"

        is_monster = entry_type == "Monster"

        is_magic_item = entry_type == "Magic Item"

        is_weapon = entry_type == "Weapon"

        is_feature = entry_type == "Feature"

        is_trait = entry_type == "Trait"
        # Add similar show/hide for Race, Class, etc.
        # e.g. self.traits_input.setVisible(entry_type in ["Race","Subrace"])

    def save_entry(self):
        entry_type = self.type_selector.currentText()
        name = self.name_input.text().strip()
        desc = [self.desc_input.toPlainText().strip()]

        if not name:
            QMessageBox.warning(self, "Error", "Name is required.")
            return

        try:
            if entry_type == "Spell":
                self._save_spell(name, desc)

            elif entry_type == "Race":
                self._save_race(name, desc)

            elif entry_type == "Class":
                self._save_class(name, desc)

            # … handle Subrace, Subclass, Equipment, Monster, etc.

            else:
                raise NotImplementedError(f"Saving {entry_type} not implemented")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))
            return

        QMessageBox.information(self, "Success", f"{entry_type} '{name}' added!")
        self.close()

    # --- Type-specific save routines ----------------------------------
    def _save_spell(self, name, desc):
        level = int(self.level_input.text().strip() or 0)
        school = {"name": self.school_input.text().strip()}
        new_spell = Spell(
            index=name.lower().replace(" ", "-"),
            name=name,
            level=level,
            school=school,
            desc=desc,
            range="Self",
            components=["V", "S"],
            material="",
            duration="Instantaneous",
            concentration=False,
            casting_time="1 action",
            attack_type="",
            damage={},
            damage_at_slot_level={},
            classes=[],
            subclasses=[],
            higher_level=[],
            url=""
        )
        self.session.add(new_spell)
        self.session.commit()

    def _save_race(self, name, desc):
        # assume Race model takes index,name,desc,traits,ability_bonuses
        from models import Race
        traits = []            # collect from your race‐specific fields
        bonuses = {}           # e.g. {"STR": 2, "DEX": 1}
        new_race = Race(
            index=name.lower().replace(" ", "-"),
            name=name,
            desc=desc,
            traits=traits,
            ability_bonuses=bonuses
        )
        self.session.add(new_race)
        self.session.commit()

    def _save_class(self, name, desc):
        from models import CharacterClass
        hit_die = 10           # pull from a QLineEdit you’ll add
        proficiencies = []     # collect list
        new_class = CharacterClass(
            index=name.lower().replace(" ", "-"),
            name=name,
            desc=desc,
            hit_die=hit_die,
            proficiencies=proficiencies
        )
        self.session.add(new_class)
        self.session.commit()