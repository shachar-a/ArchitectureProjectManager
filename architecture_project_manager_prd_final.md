# Product Requirements Document (PRD): Architecture Project Manager

## 1. Overview / Purpose
This desktop-based software is designed for architecture firms to manage ongoing projects. It enables structured tracking of project stakeholders (customers, inspectors, constructors, consultants), statuses, stages, and associated documentation.

The solution includes:
- A **SQLite** database for local structured storage
- A **Python** application with a **TKInter** GUI

## 2. Goals
- Store and manage all architecture projects with relevant metadata
- Associate each project with multiple participants and roles
- Track current project stage and task completion
- Enable clear, responsive user interaction for editing and viewing project data

## 3. Functional Requirements
### 3.1 Project Management
- The **Active** field defaults to TRUE
- If Active is TRUE:
  - The End Date must be NULL and will be cleared in the UI
  - The End Date field will be grayed out and disabled
  - No validation is required for End Date relative to Start Date
- If Active is FALSE:
  - The End Date field becomes editable
  - The system must validate that End Date is not earlier than Start Date
- Users can **create, update, and delete projects**
- Projects store the following fields:
  - **Project Name**: Auto-generated from Customer’s full name and project location
  - **Location**: Text
  - **Start Date**: DATE
  - **End Date**: DATE
  - **Active**: BOOLEAN (GUI: checkbox)
  - **Stage**: Reference to a predefined stage
  - **Documents**: Path references
- Each project must be linked to the following roles (via contacts):
  - One or more: Customer, Inspector, Constructor, Consultant

### 3.2 Contact Management
- Users can **add, update, and delete contacts**
- Contact fields:
  - First Name
  - Last Name
  - Phone Number
  - Email Address
  - Address
- A contact can participate in multiple projects, in different roles

### 3.3 Stage & Task Management
- Stages are predefined (not editable via GUI):
  - Project Definition
  - Planning Information
  - Design
  - Garmoshka
  - Building approval pre-check
  - Pikud Haoref
  - Techen
  - Final Approval
- Each stage has a list of predefined tasks (1:N)
- Each task belongs to exactly one stage
- For each project, its current stage includes a list of task instances
  - Each task instance stores status: **is_done: BOOLEAN**

### 3.4 GUI Requirements (TKInter)
- In the Project Detail View, under the section 'Current Stage Tasks':
  - Display the list of tasks corresponding to the currently selected stage
  - If the stage is modified by the user, the application must reload and display the updated task list for that new stage
  - Each task must be displayed with a checkbox to represent its completion status (done/not done)
  - Task status must be stored and updated per project-stage combination
- The GUI must enforce the following interaction rules for Active and End Date:
  - If 'Active' is checked:
    - 'End Date' must be cleared and stored as NULL
    - The 'End Date' field must be grayed out and disabled
    - Validation is skipped for End Date relative to Start Date
  - If 'Active' is unchecked:
    - The 'End Date' field becomes editable
    - End Date must not be earlier than Start Date
- 'Active' should default to TRUE
- **Navigation:**
  - Home Screen
  - Project List View (with stage column, active status filter)
  - Contact List View
- **Detail Views:**
  - Project Detail View (view/edit fields, role-based contact links, document ref)
  - Contact Detail View (view/edit contact info, linked projects)
- **Stage View:**
  - Display list of tasks for the current project stage
  - Checkbox to mark each task as done/not done
- **Interactions:**
  - Double-click on a project/contact row opens the respective detail view
  - Select or add contacts via modal within project form
- **Search and Sort:**
  - Search for projects and contacts
  - Sort columns by clicking headers
- **Visual Enhancements:**
  - Use bold headers with click-to-sort
  - Add vertical padding to rows for clarity

## 4. Non-Functional Requirements
- Runs fully offline (local-only with SQLite)
- Fast and lightweight (desktop performance target)
- Input validation to prevent logical/data errors
- Error handling with user-friendly messages

## 5. Design Architecture
- Use **MVC pattern**:
  - **Models**: Database schema and data access layer
  - **Views**: TKInter-based UI components
  - **Controllers**: Business logic and event handling
- Use **central schema definitions** to prevent GUI/DB duplication
- Use **modular Python design** to separate responsibilities

## 6. Database Schema
### 6.1 Tables
#### `projects`
- id INTEGER PRIMARY KEY
- location TEXT
- start_date DATE
- end_date DATE
- active BOOLEAN
- stage_id INTEGER (FK → stages.id)
- document_path TEXT

#### `project_roles`
- id INTEGER PRIMARY KEY
- project_id INTEGER (FK → projects.id)
- contact_id INTEGER (FK → contacts.id)
- role TEXT CHECK(role IN ('Customer', 'Inspector', 'Constructor', 'Consultant'))

#### `contacts`
- id INTEGER PRIMARY KEY
- first_name TEXT NOT NULL
- last_name TEXT NOT NULL
- phone TEXT
- email TEXT
- address TEXT

#### `stages`
- id INTEGER PRIMARY KEY
- name TEXT UNIQUE NOT NULL

#### `tasks`
- id INTEGER PRIMARY KEY
- stage_id INTEGER (FK → stages.id)
- description TEXT NOT NULL

#### `project_stage_tasks`
- id INTEGER PRIMARY KEY
- project_id INTEGER (FK → projects.id)
- task_id INTEGER (FK → tasks.id)
- is_done BOOLEAN DEFAULT 0

### 6.2 Query Example
```sql
SELECT c.first_name, c.last_name, pr.role
FROM contacts c
JOIN project_roles pr ON c.id = pr.contact_id
WHERE pr.project_id = ?;
```

## 7. Milestones
- Week 1: Finalize PRD and database schema
- Week 2: Build data models and contact/project forms
- Week 3: Add project-stage-task tracking UI
- Week 4: Polish UX, test and deliver

## 8. Risks & Mitigations
- **User error**: Use input validation and confirmations
- **Data integrity**: Enforce via foreign keys and constraints
- **Growth**: Modular design allows for scaling and refactoring

## 9. Future Enhancements
- Improve visual usability:
  - Zebra striping for table rows
  - Row hover highlights
  - Column resizing and auto-fit
  - Icons/badges for role and stage
  - Task progress bar by stage
- Export to CSV/PDF
- Add user authentication
- Add calendar view integration
- Sync contacts with Outlook or external source
