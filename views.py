import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from models import ProjectSchema

class AppView(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.title("Architecture Project Manager")
        self.geometry("1100x700")
        self.controller = controller
        self._setup_nav()
        self._show_home()

    def _setup_nav(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        menubar.add_command(label="Home", command=self._show_home)
        menubar.add_command(label="Projects", command=self._show_projects)
        menubar.add_command(label="Contacts", command=self._show_contacts)

    def _clear_main(self):
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

    def _show_home(self):
        self._clear_main()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        tk.Label(self.main_frame, text="Welcome to Architecture Project Manager", font=("Arial", 20, "bold")).pack(pady=40)
        tk.Label(self.main_frame, text="Use the menu to manage projects and contacts.", font=("Arial", 14)).pack(pady=10)

    # --- Project List View ---
    def _show_projects(self):
        self._clear_main()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        top = tk.Frame(self.main_frame)
        top.pack(fill='x', pady=5)
        tk.Label(top, text="Projects", font=("Arial", 16, "bold")).pack(side='left', padx=10)
        self.project_search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.project_search_var, width=30).pack(side='left', padx=5)
        tk.Button(top, text="Search", command=self._refresh_projects).pack(side='left')
        self.active_only_var = tk.BooleanVar()
        tk.Checkbutton(top, text="Active Only", variable=self.active_only_var, command=self._refresh_projects).pack(side='left', padx=10)
        tk.Button(top, text="Add Project", command=self._add_project_dialog).pack(side='right', padx=10)
        # Table columns driven by schema
        columns = ["id", "Project Name"] + [label for label, _ in ProjectSchema.FIELDS]
        style = ttk.Style()
        style.configure("Bold.Treeview.Heading", font=("Arial", 10, "bold"))
        self.project_tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', style="Bold.Treeview")
        for col in columns:
            self.project_tree.heading(col, text=col, command=lambda c=col: self._sort_project_tree(c, False), anchor='w')
            self.project_tree.column(col, width=120, anchor='w')
        self.project_tree.pack(fill='both', expand=True, pady=10)
        self.project_tree.bind('<Double-1>', self._on_project_double_click)
        self._refresh_projects()

    def _sort_project_tree(self, col, reverse):
        l = [(self.project_tree.set(k, col), k) for k in self.project_tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.project_tree.move(k, '', index)
        self.project_tree.heading(col, command=lambda: self._sort_project_tree(col, not reverse))

    def _refresh_projects(self):
        for row in self.project_tree.get_children():
            self.project_tree.delete(row)
        search = self.project_search_var.get()
        active_only = self.active_only_var.get()
        projects = self.controller.list_projects(search, active_only)
        for p in projects:
            schema = self.controller.get_project_schema(p.id)
            if not schema:
                continue
            row = [
                schema.id,
                self._auto_project_name(schema)
            ]
            for label, attr in ProjectSchema.FIELDS:
                value = getattr(schema, attr)
                if label == "Active":
                    value = 'Yes' if value else 'No'
                row.append(value if value is not None else "")
            self.project_tree.insert('', 'end', values=tuple(row))

    def _auto_project_name(self, project_schema):
        # Use roles and location from schema
        customers = [project_schema.roles.get(label, "") for label in ["Customer 1", "Customer 2"] if project_schema.roles.get(label, "")]
        if customers:
            names = ', '.join(customers)
            return f"{names} - {project_schema.location}"
        return f"Project {project_schema.id} - {project_schema.location}"

    def _on_project_double_click(self, event):
        item = self.project_tree.selection()
        if item:
            project_id = int(self.project_tree.item(item[0])['values'][0])
            self._show_project_detail(project_id)

    # --- Project Detail View ---
    def _show_project_detail(self, project_id):
        project_schema = self.controller.get_project_schema(project_id)
        if not project_schema:
            messagebox.showerror("Error", "Project not found.")
            return
        self._clear_main()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        top = tk.Frame(self.main_frame)
        top.pack(fill='x', pady=5)
        title = tk.Label(top, text=f"Project: {self._auto_project_name(project_schema)}", font=("Arial", 16, "bold"))
        title.pack(side='top', pady=10, anchor='center', expand=True)
        form = tk.Frame(self.main_frame)
        form.pack(fill='x', pady=10)
        contacts = self.controller.list_contacts()
        contact_names = [f"{c.first_name} {c.last_name}" for c in contacts]
        self.role_vars = {}
        self.project_detail_vars = {}
        row_idx = 0
        # Role dropdowns (schema-driven)
        for label in project_schema.ROLE_LABELS:
            tk.Label(form, text=label, font=("Arial", 12, "bold")).grid(row=row_idx, column=0, sticky='e', padx=5, pady=4)
            var = tk.StringVar(value=project_schema.roles.get(label, ""))
            om = ttk.Combobox(form, textvariable=var, values=contact_names, state='readonly')
            om.grid(row=row_idx, column=1, sticky='w')
            self.role_vars[label] = var
            row_idx += 1
        # Project fields (schema-driven)
        self._end_date_entry = None
        for label, attr in project_schema.FIELDS:
            tk.Label(form, text=label, font=("Arial", 12, "bold")).grid(row=row_idx, column=0, sticky='e', padx=5, pady=4)
            value = getattr(project_schema, attr)
            if label == "Active":
                var = tk.BooleanVar(value=value)
                cb = tk.Checkbutton(form, variable=var, command=self._on_active_toggle)
                cb.grid(row=row_idx, column=1, sticky='w')
                self.project_detail_vars[label] = var
            elif label == "Stage":
                stages = self.controller.list_stages()
                stage_names = [s.name for s in stages]
                var = tk.StringVar(value=value)
                om = ttk.Combobox(form, textvariable=var, values=stage_names, state='readonly')
                om.grid(row=row_idx, column=1, sticky='w')
                om.bind('<<ComboboxSelected>>', lambda e: self._reload_stage_tasks(project_schema))
                self.project_detail_vars[label] = var
            elif label == "End Date":
                var = tk.StringVar(value=value if value else "")
                entry = tk.Entry(form, textvariable=var, width=22)
                entry.grid(row=row_idx, column=1, sticky='w')
                self.project_detail_vars[label] = var
                self._end_date_entry = entry
            elif label == "Document Path":
                var = tk.StringVar(value=value)
                entry = tk.Entry(form, textvariable=var, width=40)
                entry.grid(row=row_idx, column=1, sticky='w')
                btn = tk.Button(form, text="Browse", command=lambda v=var: self._browse_file(v))
                btn.grid(row=row_idx, column=2, sticky='w')
                self.project_detail_vars[label] = var
            else:
                var = tk.StringVar(value=value)
                tk.Entry(form, textvariable=var, width=30).grid(row=row_idx, column=1, sticky='w')
                self.project_detail_vars[label] = var
            row_idx += 1
        tk.Label(self.main_frame, text="Stage Tasks", font=("Arial", 13, "bold"), anchor='w', justify='left').pack(anchor='w', pady=8, padx=10)
        self._show_project_stage_tasks(project_schema)
        self._update_end_date_state()
        btns = tk.Frame(self.main_frame)
        btns.pack(side='bottom', pady=20)
        save_btn = tk.Button(btns, text="Save", width=12, command=lambda: self._save_project_detail(project_schema))
        delete_btn = tk.Button(btns, text="Delete", width=12, command=lambda pid=project_schema.id: self._delete_project(pid))
        close_btn = tk.Button(btns, text="Close", width=12, command=self._show_projects)
        save_btn.pack(side='left', padx=5)
        delete_btn.pack(side='left', padx=5)
        close_btn.pack(side='left', padx=5)

    def _show_project_stage_tasks(self, project_schema):
        if hasattr(self, '_stage_task_frame') and self._stage_task_frame:
            self._stage_task_frame.destroy()
        self._stage_task_frame = tk.Frame(self.main_frame)
        self._stage_task_frame.pack(fill='x', pady=2)
        stage_name = self.project_detail_vars["Stage"].get() if "Stage" in self.project_detail_vars else None
        stage_id = None
        for s in self.controller.list_stages():
            if s.name == stage_name:
                stage_id = s.id
                break
        task_schemas = self.controller.get_task_schemas_for_project_stage(project_schema.id, stage_id) if stage_id else []
        for t in task_schemas:
            var = tk.BooleanVar(value=t.is_done)
            cb = tk.Checkbutton(self._stage_task_frame, text=t.description, variable=var, command=lambda tid=t.id, v=var: self._toggle_task_done(project_schema.id, tid, v))
            cb.pack(anchor='w', padx=10)

    def _on_active_toggle(self):
        self._update_end_date_state()

    def _update_end_date_state(self):
        active = self.project_detail_vars["Active"].get()
        if self._end_date_entry:
            if active:
                self.project_detail_vars["End Date"].set("")
                self._end_date_entry.config(state='disabled')
            else:
                self._end_date_entry.config(state='normal')

    def _save_project_detail(self, project_schema):
        try:
            # Use schema field keys for mapping
            field_map = dict(ProjectSchema.FIELDS)
            location = self.project_detail_vars.get("Location", tk.StringVar()).get()
            start_date = self.project_detail_vars.get("Start Date", tk.StringVar()).get()
            active = self.project_detail_vars.get("Active", tk.BooleanVar()).get()
            stage_name = self.project_detail_vars.get("Stage", tk.StringVar()).get()
            document_path = self.project_detail_vars.get("Document Path", tk.StringVar()).get()
            stage_id = next((s.id for s in self.controller.list_stages() if s.name == stage_name), None)
            end_date = self.project_detail_vars.get("End Date", tk.StringVar()).get() if not active else None
            updated = self.controller.get_project(project_schema.id)
            updated.location = location
            updated.start_date = start_date
            updated.end_date = end_date
            updated.active = active
            updated.stage_id = stage_id
            updated.document_path = document_path
            self.controller.update_project(updated)
            self.controller.project_role_model.db.execute_query("DELETE FROM project_roles WHERE project_id=?", (project_schema.id,))
            contacts = self.controller.list_contacts()
            role_map = {label: (label if label not in ["Customer 1", "Customer 2"] else "Customer") for label in ProjectSchema.ROLE_LABELS}
            for label, var in self.role_vars.items():
                name = var.get()
                if name:
                    contact = next((c for c in contacts if f"{c.first_name} {c.last_name}" == name), None)
                    if contact:
                        self.controller.add_project_role(project_schema.id, contact.id, role_map[label])
            messagebox.showinfo("Saved", "Project updated successfully.")
            self._show_projects()
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"{e}\n\n{traceback.format_exc()}")

    def _delete_project(self, project_id):
        if messagebox.askyesno("Confirm", "Delete this project?"):
            self.controller.delete_project(project_id)
            self._show_projects()

    def _reload_stage_tasks(self, project):
        self._show_project_stage_tasks(project)

    def _toggle_task_done(self, project_id, task_id, var):
        # Find or create project_stage_task
        tasks = self.controller.list_project_stage_tasks(project_id)
        pst = next((t for t in tasks if t.task_id == task_id), None)
        if pst:
            self.controller.set_project_stage_task_done(pst.id, var.get())
        else:
            # Create new project_stage_task
            self.controller.project_stage_task_model.db.execute_query(
                "INSERT INTO project_stage_tasks (project_id, task_id, is_done) VALUES (?, ?, ?)",
                (project_id, task_id, int(var.get()))
            )
        # Optionally refresh view

    def _add_project_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Project")
        dialog.geometry("400x500")
        contacts = self.controller.list_contacts()
        contact_names = [f"{c.first_name} {c.last_name}" for c in contacts]
        cust_labels = ProjectSchema.ROLE_LABELS
        customer_vars = {}
        for j, cust_label in enumerate(cust_labels):
            tk.Label(dialog, text=cust_label).grid(row=j, column=0, sticky='e', padx=5, pady=4)
            var = tk.StringVar()
            om = ttk.Combobox(dialog, textvariable=var, values=contact_names, state='readonly')
            om.grid(row=j, column=1, sticky='w')
            customer_vars[cust_label] = var
        fields = [label for label, _ in ProjectSchema.FIELDS]
        vars = {}
        end_date_entry = None
        for i, label in enumerate(fields):
            row_idx = i + len(cust_labels)
            tk.Label(dialog, text=label).grid(row=row_idx, column=0, sticky='e', padx=5, pady=4)
            if label == "Active":
                var = tk.BooleanVar(value=True)
                cb = tk.Checkbutton(dialog, variable=var, command=lambda: update_end_date_state())
                cb.grid(row=row_idx, column=1, sticky='w')
                vars[label] = var
            elif label == "Stage":
                stages = self.controller.list_stages()
                stage_names = [s.name for s in stages]
                var = tk.StringVar(value=stage_names[0] if stage_names else "")
                om = ttk.Combobox(dialog, textvariable=var, values=stage_names, state='readonly')
                om.grid(row=row_idx, column=1, sticky='w')
                vars[label] = var
            elif label == "End Date":
                var = tk.StringVar()
                entry = tk.Entry(dialog, textvariable=var, width=22)
                entry.grid(row=row_idx, column=1, sticky='w')
                vars[label] = var
                end_date_entry = entry
            elif label == "Document Path":
                var = tk.StringVar()
                entry = tk.Entry(dialog, textvariable=var, width=40)
                entry.grid(row=row_idx, column=1, sticky='w')
                btn = tk.Button(dialog, text="Browse", command=lambda v=var: self._browse_file(v))
                btn.grid(row=row_idx, column=2, sticky='w')
                vars[label] = var
            else:
                var = tk.StringVar()
                tk.Entry(dialog, textvariable=var, width=30).grid(row=row_idx, column=1, sticky='w')
                vars[label] = var
        def update_end_date_state():
            if vars["Active"].get():
                vars["End Date"].set("")
                if end_date_entry:
                    end_date_entry.config(state='disabled')
            else:
                if end_date_entry:
                    end_date_entry.config(state='normal')
        update_end_date_state()
        def add():
            try:
                # Use schema field keys for mapping
                field_map = dict(ProjectSchema.FIELDS)
                location = vars.get("Location", tk.StringVar()).get()
                start_date = vars.get("Start Date", tk.StringVar()).get()
                active = vars.get("Active", tk.BooleanVar()).get()
                stage_name = vars.get("Stage", tk.StringVar()).get()
                document_path = vars.get("Document Path", tk.StringVar()).get()
                stage_id = next((s.id for s in self.controller.list_stages() if s.name == stage_name), None)
                end_date = vars.get("End Date", tk.StringVar()).get() if not active else None
                project_id = self.controller.create_project(location, start_date, end_date, active, stage_id, document_path)
                if not project_id:
                    last_row = self.controller.project_model.db.execute_query("SELECT id FROM projects ORDER BY id DESC LIMIT 1", fetchone=True)
                    if last_row:
                        project_id = last_row[0]
                if not project_id:
                    raise Exception("Failed to create project. Project ID not found.")
                for cust_label in cust_labels:
                    name = customer_vars[cust_label].get()
                    if name:
                        contact = next((c for c in contacts if f"{c.first_name} {c.last_name}" == name), None)
                        if contact:
                            self.controller.add_project_role(project_id, contact.id, cust_label if cust_label not in ["Customer 1", "Customer 2"] else "Customer")
                dialog.destroy()
                self._refresh_projects()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=len(fields)+len(cust_labels), column=0, columnspan=2, pady=10)
        save_btn = tk.Button(btn_frame, text="Save", command=add, width=12)
        save_btn.pack(side='left', padx=8)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12)
        cancel_btn.pack(side='left', padx=8)

    def _save_project_role(self, project, label):
        contacts = self.controller.list_contacts()
        name = self.role_vars[label].get()
        if name:
            contact = next((c for c in contacts if f"{c.first_name} {c.last_name}" == name), None)
            if contact:
                # Remove existing role for this label (Customer 1 or 2)
                project_roles = self.controller.list_project_roles(project.id)
                idx = 0 if label == "Customer 1" else 1
                matches = [r for r in project_roles if r.role == "Customer"]
                if len(matches) > idx:
                    self.controller.remove_project_role(matches[idx].id)
                self.controller.add_project_role(project.id, contact.id, "Customer")
                messagebox.showinfo("Saved", f"{label} updated.")

    def _remove_project_role(self, project, label):
        project_roles = self.controller.list_project_roles(project.id)
        idx = 0 if label == "Customer 1" else 1
        matches = [r for r in project_roles if r.role == "Customer"]
        if len(matches) > idx:
            self.controller.remove_project_role(matches[idx].id)
            self.role_vars[label].set("")
            messagebox.showinfo("Removed", f"{label} removed.")

    # --- Contact List View ---
    def _show_contacts(self):
        self._clear_main()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        top = tk.Frame(self.main_frame)
        top.pack(fill='x', pady=5)
        tk.Label(top, text="Contacts", font=("Arial", 16, "bold")).pack(side='left', padx=10)
        self.contact_search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.contact_search_var, width=30).pack(side='left', padx=5)
        tk.Button(top, text="Search", command=self._refresh_contacts).pack(side='left')
        tk.Button(top, text="Add Contact", command=self._add_contact_dialog).pack(side='right', padx=10)
        # Table
        columns = ["id", "first_name", "last_name", "phone", "email", "address"]
        style = ttk.Style()
        style.configure("Bold.Treeview.Heading", font=("Arial", 10, "bold"))
        self.contact_tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', style="Bold.Treeview")
        for col in columns:
            self.contact_tree.heading(col, text=col, command=lambda c=col: self._sort_contact_tree(c, False), anchor='w')
            self.contact_tree.column(col, width=120, anchor='w')
        self.contact_tree.pack(fill='both', expand=True, pady=10)
        self.contact_tree.bind('<Double-1>', self._on_contact_double_click)
        self._refresh_contacts()

    def _sort_contact_tree(self, col, reverse):
        l = [(self.contact_tree.set(k, col), k) for k in self.contact_tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.contact_tree.move(k, '', index)
        self.contact_tree.heading(col, command=lambda: self._sort_contact_tree(col, not reverse))

    def _refresh_contacts(self):
        for row in self.contact_tree.get_children():
            self.contact_tree.delete(row)
        search = self.contact_search_var.get()
        contacts = self.controller.list_contacts(search)
        for c in contacts:
            self.contact_tree.insert('', 'end', values=(c.id, c.first_name, c.last_name, c.phone, c.email, c.address))

    def _on_contact_double_click(self, event):
        item = self.contact_tree.selection()
        if item:
            contact_id = int(self.contact_tree.item(item[0])['values'][0])
            self._show_contact_detail(contact_id)

    # --- Contact Detail View ---
    def _show_contact_detail(self, contact_id):
        contact = self.controller.get_contact(contact_id)
        if not contact:
            messagebox.showerror("Error", "Contact not found.")
            return
        self._clear_main()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        top = tk.Frame(self.main_frame)
        top.pack(fill='x', pady=5)
        tk.Label(top, text=f"Contact Detail: {contact.first_name} {contact.last_name}", font=("Arial", 16, "bold")).pack(side='top', padx=10, anchor='center')
        # Fields
        form = tk.Frame(self.main_frame)
        form.pack(fill='x', pady=10)
        fields = [
            ("First Name", contact.first_name),
            ("Last Name", contact.last_name),
            ("Phone", contact.phone),
            ("Email", contact.email),
            ("Address", contact.address)
        ]
        self.contact_detail_vars = {}
        for i, (label, value) in enumerate(fields):
            tk.Label(form, text=label, font=("Arial", 12, "bold")).grid(row=i, column=0, sticky='e', padx=5, pady=4)
            var = tk.StringVar(value=value)
            tk.Entry(form, textvariable=var, width=30).grid(row=i, column=1, sticky='w')
            self.contact_detail_vars[label] = var
        # Linked Projects section
        lp_frame = tk.Frame(self.main_frame)
        lp_frame.pack(fill='x', padx=30, pady=8, anchor='w')
        tk.Label(lp_frame, text="Linked Projects", font=("Arial", 13, "bold"), anchor='w', justify='left').pack(anchor='w', pady=(0, 4))
        tree_frame = tk.Frame(lp_frame)
        tree_frame.pack(fill='x', anchor='w')
        columns = ["project", "role"]
        style = ttk.Style()
        style.configure("Bold.Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Treeview.Heading", anchor='w')
        style.configure("Treeview", rowheight=28, font=("Arial", 10), padding=6)
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', style="Bold.Treeview")
        for col in columns:
            tree.heading(col, text=col, anchor='w')
            tree.column(col, width=180, anchor='w')
        projects = []
        for p in self.controller.list_projects():
            for r in self.controller.list_project_roles(p.id):
                if r.contact_id == contact.id:
                    projects.append((p, r.role))
        for p, role in projects:
            tree.insert('', 'end', values=(self._auto_project_name(p), role), tags=(str(p.id),))
        tree.pack(fill='x', anchor='w', padx=8, pady=4)
        def on_linked_project_double_click(event):
            item = tree.selection()
            if item:
                tags = tree.item(item[0], 'tags')
                if tags:
                    project_id = int(tags[0])
                    self._show_project_detail(project_id)
        tree.bind('<Double-1>', on_linked_project_double_click)
        # Save/Delete/Close buttons at the bottom, center-aligned and adjacent
        btns = tk.Frame(self.main_frame)
        btns.pack(side='bottom', pady=20)
        save_btn = tk.Button(btns, text="Save", width=12, command=lambda: self._save_contact_detail(contact))
        delete_btn = tk.Button(btns, text="Delete", width=12, command=lambda: self._delete_contact(contact.id))
        close_btn = tk.Button(btns, text="Close", width=12, command=self._show_contacts)
        # Center the button group and keep them adjacent
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)
        btns.grid_columnconfigure(2, weight=1)
        save_btn.grid(row=0, column=0, padx=10)
        delete_btn.grid(row=0, column=1, padx=10)
        close_btn.grid(row=0, column=2, padx=10)

    def _save_contact_detail(self, contact):
        try:
            first_name = self.contact_detail_vars["First Name"].get()
            last_name = self.contact_detail_vars["Last Name"].get()
            phone = self.contact_detail_vars["Phone"].get()
            email = self.contact_detail_vars["Email"].get()
            address = self.contact_detail_vars["Address"].get()
            contact.first_name = first_name
            contact.last_name = last_name
            contact.phone = phone
            contact.email = email
            contact.address = address
            self.controller.update_contact(contact)
            messagebox.showinfo("Saved", "Contact updated successfully.")
            self._show_contacts()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_contact(self, contact_id):
        if messagebox.askyesno("Confirm", "Delete this contact?"):
            self.controller.delete_contact(contact_id)
            self._show_contacts()

    def _show_contact_projects(self, contact):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill='x', pady=2)
        # Find all project_roles for this contact
        # (This is a simplified version; you may want to optimize with a join)
        projects = []
        for p in self.controller.list_projects():
            for r in self.controller.list_project_roles(p.id):
                if r.contact_id == contact.id:
                    projects.append((p, r.role))
        tree = ttk.Treeview(frame, columns=["project", "role"], show='headings', height=4)
        for col in ["project", "role"]:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        for p, role in projects:
            tree.insert('', 'end', values=(self._auto_project_name(p), role))
        tree.pack(side='left', fill='x', expand=True)

    def _add_contact_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Contact")
        dialog.geometry("400x350")
        fields = ["First Name", "Last Name", "Phone", "Email", "Address"]
        vars = {}
        for i, label in enumerate(fields):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=4)
            var = tk.StringVar()
            tk.Entry(dialog, textvariable=var, width=25).grid(row=i, column=1, sticky='w')
            vars[label] = var
        def add():
            try:
                self.controller.create_contact(
                    vars["First Name"].get(),
                    vars["Last Name"].get(),
                    vars["Phone"].get(),
                    vars["Email"].get(),
                    vars["Address"].get()
                )
                dialog.destroy()
                self._refresh_contacts()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        # Add Save and Cancel buttons next to each other at the bottom
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        save_btn = tk.Button(btn_frame, text="Save", command=add, width=12)
        save_btn.pack(side='left', padx=8)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12)
        cancel_btn.pack(side='left', padx=8)
