from models import Database
from controller import Controller
from views import AppView

if __name__ == "__main__":
    db = Database()
    controller = Controller(db)
    app = AppView(controller)
    app.mainloop()
