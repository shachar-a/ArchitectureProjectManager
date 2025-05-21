from models import (
    ProjectModel, ContactModel, StageModel, TaskModel, ProjectRoleModel, ProjectStageTaskModel,
    Project, Contact
)

class Controller:
    def __init__(self, db):
        self.project_model = ProjectModel(db)
        self.contact_model = ContactModel(db)
        self.stage_model = StageModel(db)
        self.task_model = TaskModel(db)
        self.project_role_model = ProjectRoleModel(db)
        self.project_stage_task_model = ProjectStageTaskModel(db)

    # Project
    def create_project(self, location, start_date, end_date, active, stage_id, document_path):
        # Validation: End Date must not precede Start Date, but only if not active and end_date is set
        if not active and end_date:
            if end_date < start_date:
                raise ValueError("End Date must not precede Start Date.")
        project = Project(None, location, start_date, end_date, active, stage_id, document_path)
        return self.project_model.create(project)

    def update_project(self, project: Project):
        if not project.active and project.end_date:
            if project.end_date < project.start_date:
                raise ValueError("End Date must not precede Start Date.")
        self.project_model.update(project)

    def delete_project(self, project_id):
        self.project_model.delete(project_id)

    def get_project(self, project_id):
        return self.project_model.get(project_id)

    def list_projects(self, search="", active_only=False):
        return self.project_model.list(search, active_only)

    # Contact
    def create_contact(self, first_name, last_name, phone, email, address):
        contact = Contact(None, first_name, last_name, phone, email, address)
        return self.contact_model.create(contact)

    def update_contact(self, contact: Contact):
        self.contact_model.update(contact)

    def delete_contact(self, contact_id):
        self.contact_model.delete(contact_id)

    def get_contact(self, contact_id):
        return self.contact_model.get(contact_id)

    def list_contacts(self, search=""):
        return self.contact_model.list(search)

    # Stage
    def list_stages(self):
        return self.stage_model.list()

    def get_stage(self, stage_id):
        return self.stage_model.get(stage_id)

    # Task
    def list_tasks_by_stage(self, stage_id):
        return self.task_model.list_by_stage(stage_id)

    def get_task(self, task_id):
        return self.task_model.get(task_id)

    # Project Roles
    def list_project_roles(self, project_id):
        return self.project_role_model.list_by_project(project_id)

    def add_project_role(self, project_id, contact_id, role):
        self.project_role_model.add(project_id, contact_id, role)

    def remove_project_role(self, project_role_id):
        self.project_role_model.remove(project_role_id)

    # Project Stage Tasks
    def list_project_stage_tasks(self, project_id):
        return self.project_stage_task_model.list_by_project(project_id)

    def set_project_stage_task_done(self, project_stage_task_id, is_done):
        self.project_stage_task_model.set_done(project_stage_task_id, is_done)
