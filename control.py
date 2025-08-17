import models
import ui
import db
import and_on_the_first_day
from sqlalchemy.orm import Session
from PySide6.QtWidgets import QApplication

models.Base.metadata.create_all(bind=models.engine)
session = models.SessionLocal()



# Run user interface
app = QApplication([])
window = ui.MainUI()
window.show()
app.exec()