# homebrew_ui.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QStackedWidget, QMessageBox
)
from sqlalchemy.orm import Session
from models import (
    Spell, Race, Subrace, Class, Subclass,
    Equipment, Monster, MagicItem, Weapon, Feature, Trait
)

class HomebrewWindow(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Add Homebrew Entry")
        self.setMinimumSize(500, 400)

        main_layout = QVBoxLayout(self)

        # 1) Type selector
        self.type_selector = QComboBox()
        types = [
            "Spell", "Race", "Subrace", "Class", "Subclass",
            "Equipment", "Monster", "Magic Item", "Weapon",
            "Feature", "Trait", "Background"
        ]
        self.type_selector.addItems(types)
        main_layout.addWidget(self.type_selector)

        # 2) StackedWidget to hold one form per type
        self.stacked = QStackedWidget()
        main_layout.addWidget(self.stacked, 1)

        # 3) Define which fields each form needs
        #    key = combo-box text, value = list of (label, widget-class)
        self.field_defs = {
            "Spell": [
                ("Name", QLineEdit),
                ("Level", QLineEdit),
                ("School", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Race": [
                ("Name", QLineEdit),
                ("Ability Score Increases (JSON)", QLineEdit),
                ("Traits (comma)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Subrace": [
                ("Name", QLineEdit),
                ("Parent Race (index)", QLineEdit),
                ("Ability Score Increases (JSON)", QLineEdit),
                ("Traits (comma)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Class": [
                ("Name", QLineEdit),
                ("Hit Die", QLineEdit),
                ("Proficiencies (JSON)", QLineEdit),
                ("Saving Throws (JSON)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Subclass": [
                ("Name", QLineEdit),
                ("Parent Class (index)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Equipment": [
                ("Name", QLineEdit),
                ("Category", QLineEdit),
                ("Weight", QLineEdit),
                ("Cost Quantity", QLineEdit),
                ("Cost Unit", QLineEdit),
                ("Description (JSON)", QLineEdit),
            ],
            "Monster": [
                ("Name", QLineEdit),
                ("Size", QLineEdit),
                ("Type", QLineEdit),
                ("Alignment", QLineEdit),
                ("HP", QLineEdit),
                ("Hit Dice", QLineEdit),
                ("Armor Class (JSON)", QLineEdit),
                ("Speed (JSON)", QLineEdit),
                ("Stats (JSON)", QLineEdit),
                ("Damage Vulnerabilities (JSON)", QLineEdit),
                ("Immunities (JSON)", QLineEdit),
                ("Resistances (JSON)", QLineEdit),
                ("Condition Immunities (JSON)", QLineEdit),
                ("Senses (JSON)", QLineEdit),
                ("Languages", QLineEdit),
                ("CR", QLineEdit),
                ("XP", QLineEdit),
            ],
            "Magic Item": [
                ("Name", QLineEdit),
                ("Category", QLineEdit),
                ("Rarity", QLineEdit),
                ("Requires Attunement (True/False)", QLineEdit),
                ("Unattunable (True/False)", QLineEdit),
                ("Description (JSON)", QLineEdit),
            ],
            "Weapon": [
                ("Name", QLineEdit),
                ("Category", QLineEdit),
                ("Range", QLineEdit),
                ("Damage Dice", QLineEdit),
                ("Damage Type", QLineEdit),
                ("Normal Range", QLineEdit),
                ("Thrown Range", QLineEdit),
            ],
            "Feature": [
                ("Name", QLineEdit),
                ("Class Index", QLineEdit),
                ("Subclass Index", QLineEdit),
                ("Level", QLineEdit),
                ("Optional (True/False)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Trait": [
                ("Name", QLineEdit),
                ("Races (comma)", QLineEdit),
                ("Subraces (comma)", QLineEdit),
                ("Description", QTextEdit),
            ],
            "Background": [
                ("Name", QLineEdit),
                ("Description", QTextEdit)
            ]
        }

        # 4) Build each form dynamically and keep its inputs in a dict
        self.inputs = {}  # e.g. self.inputs["Spell"]["Level"] -> QLineEdit
        for entry_type, fields in self.field_defs.items():
            page = QWidget()
            form = QFormLayout(page)
            widget_map = {}
            for label, wcls in fields:
                w = wcls()
                form.addRow(label, w)
                widget_map[label] = w
            self.inputs[entry_type] = widget_map
            self.stacked.addWidget(page)

        # 5) Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_entry)
        main_layout.addWidget(self.save_button)

        # 6) Wire type‐switching
        self.type_selector.currentIndexChanged.connect(self.stacked.setCurrentIndex)
        # initialize
        self.stacked.setCurrentIndex(0)

    def save_entry(self):
        entry_type = self.type_selector.currentText()
        widgets = self.inputs[entry_type]

        name = widgets["Name"].text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required.")
            return

        # gather common description
        desc_widget = widgets.get("Description") or widgets.get("Description (JSON)")
        desc_val = desc_widget.toPlainText().strip() if isinstance(desc_widget, QTextEdit) else desc_widget.text().strip()

        # now branch
        if entry_type == "Spell":
            from models import Spell
            new = Spell(
                index=name.lower().replace(" ", "-"),
                name=name,
                level=int(widgets["Level"].text()),
                school={"name": widgets["School"].text().strip()},
                desc=[desc_val],
                # fill in the rest with defaults or more inputs...
                range="Self", components=["V", "S"], material="",
                duration="Instantaneous", concentration=False,
                casting_time="1 action", attack_type="", damage={},
                damage_at_slot_level={}, classes=[], subclasses=[],
                higher_level=[], url=""
            )

        elif entry_type == "Race":
            from models import Race
            abilities = widgets["Ability Score Increases (JSON)"].text().strip()
            traits   = widgets["Traits (comma)"].text().split(",")
            new = Race(
                index=name.lower().replace(" ", "-"),
                name=name,
                asi=abilities,
                traits=",".join(t.strip() for t in traits),
                url=""
            )

        # …similar elif blocks for Subrace, Class, Monster, etc…

        else:
            QMessageBox.critical(self, "Oops", f"Saving for {entry_type} not implemented")
            return

        # commit
        self.session.add(new)
        self.session.commit()
        QMessageBox.information(self, "Success", f"{entry_type} '{name}' added!")
        self.close()