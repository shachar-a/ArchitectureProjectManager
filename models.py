import sqlite3
from dataclasses import dataclass
from typing import List, Optional

# --- Data Models ---
@dataclass
class Project:
    id: Optional[int]
    location: str
    start_date: str
    end_date: str
    active: bool
    stage_id: int
    document_path: str

@dataclass
class Contact:
    id: Optional[int]
    first_name: str
    last_name: str
    phone: str
    email: str
    address: str

@dataclass
class Stage:
    id: Optional[int]
    name: str

@dataclass
class Task:
    id: Optional[int]
    stage_id: int
    description: str

@dataclass
class ProjectRole:
    id: Optional[int]
    project_id: int
    contact_id: int
    role: str

@dataclass
class ProjectStageTask:
    id: Optional[int]
    project_id: int
    task_id: int
    is_done: bool

# --- Database and Model Layer ---
class Database:
    def __init__(self, db_name="projects.db"):
        self.db_name = db_name
        self.initialize_database()

    def initialize_database(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                location TEXT,
                start_date DATE,
                end_date DATE,
                active BOOLEAN,
                stage_id INTEGER,
                document_path TEXT,
                FOREIGN KEY (stage_id) REFERENCES stages(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                stage_id INTEGER,
                description TEXT NOT NULL,
                FOREIGN KEY (stage_id) REFERENCES stages(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_roles (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                contact_id INTEGER,
                role TEXT CHECK(role IN ('Customer', 'Inspector', 'Constructor', 'Consultant')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_stage_tasks (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                task_id INTEGER,
                is_done BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')
        # Prepopulate stages and tasks if empty
        cursor.execute("SELECT COUNT(*) FROM stages")
        if cursor.fetchone()[0] == 0:
            stages = [
                "Project Definition", "Planning Information", "Design", "Garmoshka",
                "Building approval pre-check", "Pikud Haoref", "Techen", "Final Approval"
            ]
            for s in stages:
                cursor.execute("INSERT INTO stages (name) VALUES (?)", (s,))
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            # Insert tasks according to mapping
            stage_task_map = {
                "Project Definition": ["Collects family needs"],
                "Planning Information": [
                    "צילום ת.ז", "כתובת למשלוח מכתבים", "פרטי המגרש", "חוזה מנהל", "מפת מדידה עדכנית",
                    "צילומי המגרש עם תאריך", "תשלום עבור פתיחת תיק המידע", "בדיקה האם קיימים עצים בוגרים במגרש"
                ],
                "Design": ["בניית תוכנית אדריכלית"],
                "Garmoshka": ["גרמושקה בסיסית", "חישוב שטחים", "גרמושקה ממוחשבת"],
                "Building approval pre-check": ["קונסטרוקטור נבחר", "יועץ סניטציה נבחר", "חוזה מנהל", "נסח טאבו"],
                "Pikud Haoref": ["תוכנית ממד"],
                "Techen": ["בחירת מכון"],
                "Final Approval": ["חישוב פסולת"]
            }
            cursor.execute("SELECT id, name FROM stages")
            stage_id_map = {name: id for id, name in cursor.fetchall()}
            for stage_name, tasks in stage_task_map.items():
                stage_id = stage_id_map.get(stage_name)
                if stage_id:
                    for desc in tasks:
                        cursor.execute("INSERT INTO tasks (stage_id, description) VALUES (?, ?)", (stage_id, desc))
        connection.commit()
        connection.close()

    def execute_query(self, query, params=(), fetchone=False, fetchall=False):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(query, params)
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        connection.commit()
        connection.close()
        return result

# Add model classes for CRUD and queries as needed (ProjectModel, ContactModel, etc.)
class ProjectModel:
    def __init__(self, db: Database):
        self.db = db

    def create(self, project: Project) -> int:
        query = """
            INSERT INTO projects (location, start_date, end_date, active, stage_id, document_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (project.location, project.start_date, project.end_date, int(project.active), project.stage_id, project.document_path)
        self.db.execute_query(query, params)
        return self.db.execute_query("SELECT last_insert_rowid()", fetchone=True)[0]

    def update(self, project: Project):
        query = """
            UPDATE projects SET location=?, start_date=?, end_date=?, active=?, stage_id=?, document_path=? WHERE id=?
        """
        params = (project.location, project.start_date, project.end_date, int(project.active), project.stage_id, project.document_path, project.id)
        self.db.execute_query(query, params)

    def delete(self, project_id: int):
        # Delete dependent rows first to avoid foreign key constraint errors
        self.db.execute_query("DELETE FROM project_roles WHERE project_id=?", (project_id,))
        self.db.execute_query("DELETE FROM project_stage_tasks WHERE project_id=?", (project_id,))
        self.db.execute_query("DELETE FROM projects WHERE id=?", (project_id,))

    def get(self, project_id: int) -> Optional[Project]:
        row = self.db.execute_query("SELECT * FROM projects WHERE id=?", (project_id,), fetchone=True)
        if row:
            return Project(*row)
        return None

    def list(self, search: str = "", active_only: bool = False) -> List[Project]:
        query = "SELECT * FROM projects"
        params = []
        if search:
            query += " WHERE location LIKE ?"
            params.append(f"%{search}%")
        if active_only:
            query += (" AND" if search else " WHERE") + " active=1"
        rows = self.db.execute_query(query, params, fetchall=True)
        return [Project(*row) for row in rows]

class ContactModel:
    def __init__(self, db: Database):
        self.db = db

    def create(self, contact: Contact) -> int:
        query = """
            INSERT INTO contacts (first_name, last_name, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (contact.first_name, contact.last_name, contact.phone, contact.email, contact.address)
        self.db.execute_query(query, params)
        return self.db.execute_query("SELECT last_insert_rowid()", fetchone=True)[0]

    def update(self, contact: Contact):
        query = """
            UPDATE contacts SET first_name=?, last_name=?, phone=?, email=?, address=? WHERE id=?
        """
        params = (contact.first_name, contact.last_name, contact.phone, contact.email, contact.address, contact.id)
        self.db.execute_query(query, params)

    def delete(self, contact_id: int):
        # Delete dependent rows in project_roles before deleting the contact
        self.db.execute_query("DELETE FROM project_roles WHERE contact_id=?", (contact_id,))
        self.db.execute_query("DELETE FROM contacts WHERE id=?", (contact_id,))

    def get(self, contact_id: int) -> Optional[Contact]:
        row = self.db.execute_query("SELECT * FROM contacts WHERE id=?", (contact_id,), fetchone=True)
        if row:
            return Contact(*row)
        return None

    def list(self, search: str = "") -> List[Contact]:
        query = "SELECT * FROM contacts"
        params = []
        if search:
            query += " WHERE first_name LIKE ? OR last_name LIKE ?"
            params.extend([f"%{search}%", f"%{search}%"])
        rows = self.db.execute_query(query, params, fetchall=True)
        return [Contact(*row) for row in rows]

class StageModel:
    def __init__(self, db: Database):
        self.db = db

    def list(self) -> List[Stage]:
        rows = self.db.execute_query("SELECT * FROM stages", fetchall=True)
        return [Stage(*row) for row in rows]

    def get(self, stage_id: int) -> Optional[Stage]:
        row = self.db.execute_query("SELECT * FROM stages WHERE id=?", (stage_id,), fetchone=True)
        if row:
            return Stage(*row)
        return None

class TaskModel:
    def __init__(self, db: Database):
        self.db = db

    def list_by_stage(self, stage_id: int) -> List[Task]:
        rows = self.db.execute_query("SELECT * FROM tasks WHERE stage_id=?", (stage_id,), fetchall=True)
        return [Task(*row) for row in rows]

    def get(self, task_id: int) -> Optional[Task]:
        row = self.db.execute_query("SELECT * FROM tasks WHERE id=?", (task_id,), fetchone=True)
        if row:
            return Task(*row)
        return None

class ProjectRoleModel:
    def __init__(self, db: Database):
        self.db = db

    def list_by_project(self, project_id: int) -> List[ProjectRole]:
        rows = self.db.execute_query("SELECT * FROM project_roles WHERE project_id=?", (project_id,), fetchall=True)
        return [ProjectRole(*row) for row in rows]

    def add(self, project_id: int, contact_id: int, role: str):
        self.db.execute_query(
            "INSERT INTO project_roles (project_id, contact_id, role) VALUES (?, ?, ?)",
            (project_id, contact_id, role)
        )

    def remove(self, project_role_id: int):
        self.db.execute_query("DELETE FROM project_roles WHERE id=?", (project_role_id,))

class ProjectStageTaskModel:
    def __init__(self, db: Database):
        self.db = db

    def list_by_project(self, project_id: int) -> List[ProjectStageTask]:
        rows = self.db.execute_query("SELECT * FROM project_stage_tasks WHERE project_id=?", (project_id,), fetchall=True)
        return [ProjectStageTask(*row) for row in rows]

    def set_done(self, project_stage_task_id: int, is_done: bool):
        self.db.execute_query(
            "UPDATE project_stage_tasks SET is_done=? WHERE id=?",
            (int(is_done), project_stage_task_id)
        )

# --- Schema Abstractions for GUI/View Layer ---
from typing import Dict, Any

class ProjectSchema:
    # Centralized field definitions for Project
    FIELDS = [
        ("Location", "location"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
        ("Active", "active"),
        ("Document Path", "document_path"),
        ("Stage", "stage_name"),
    ]
    ROLE_LABELS = ["Customer 1", "Customer 2", "Constructor", "Inspector", "Consultant"]

    def __init__(self, project: Project, stage_name: str, roles: Dict[str, str]):
        self.id = project.id
        self.location = project.location
        self.start_date = project.start_date
        self.end_date = project.end_date
        self.active = project.active
        self.stage_id = project.stage_id
        self.stage_name = stage_name
        self.document_path = project.document_path
        self.roles = roles  # Dict[label, contact_name]

    @classmethod
    def get_field_labels(cls):
        return [label for label, _ in cls.FIELDS]

    @classmethod
    def get_field_keys(cls):
        return [attr for _, attr in cls.FIELDS]

    def as_dict(self) -> Dict[str, Any]:
        d = {label: getattr(self, attr) for label, attr in self.FIELDS}
        d["id"] = self.id
        d["roles"] = self.roles
        return d

class ContactSchema:
    FIELDS = [
        ("First Name", "first_name"),
        ("Last Name", "last_name"),
        ("Phone", "phone"),
        ("Email", "email"),
        ("Address", "address"),
    ]

    def __init__(self, contact: Contact):
        self.id = contact.id
        self.first_name = contact.first_name
        self.last_name = contact.last_name
        self.phone = contact.phone
        self.email = contact.email
        self.address = contact.address

    def as_dict(self) -> Dict[str, Any]:
        d = {label: getattr(self, attr) for label, attr in self.FIELDS}
        d["id"] = self.id
        return d

class TaskSchema:
    FIELDS = [
        ("Description", "description"),
        ("Is Done", "is_done"),
    ]

    def __init__(self, task_id: int, description: str, is_done: bool):
        self.id = task_id
        self.description = description
        self.is_done = is_done

    def as_dict(self) -> Dict[str, Any]:
        d = {label: getattr(self, attr) for label, attr in self.FIELDS}
        d["id"] = self.id
        return d