import tkinter as tk
from tkinter import messagebox
import re
import json
import os
import subprocess
import sys

root = tk.Tk()
root.title("Smart Resume Builder")
root.geometry("700x700")   # fixed visible window size; content scrolls inside it

# --- Scrollable canvas setup ---
# A Canvas + Scrollbar wrap a Frame (main_frame). All form widgets go inside
# main_frame instead of directly inside root, so the form can grow taller
# than the visible window and the user scrolls to see the rest.
canvas = tk.Canvas(root, borderwidth=0)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
main_frame = tk.Frame(canvas)

main_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=main_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Let the mouse wheel scroll the canvas when hovering over the form
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)          # Windows/macOS
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down

# --- Mandatory Fields ---
tk.Label(main_frame, text="Full Name *").grid(row=0, column=0, sticky="w", padx=10, pady=5)
name_entry = tk.Entry(main_frame, width=40)
name_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(main_frame, text="Email *").grid(row=1, column=0, sticky="w", padx=10, pady=5)
email_entry = tk.Entry(main_frame, width=40)
email_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(main_frame, text="Contact Number *").grid(row=2, column=0, sticky="w", padx=10, pady=5)
contact_entry = tk.Entry(main_frame, width=40)
contact_entry.grid(row=2, column=1, padx=10, pady=5)

# --- Section: Objective ---
objective_var = tk.IntVar()

def toggle_objective():
    if objective_var.get():
        objective_frame.grid()
    else:
        objective_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Objective", variable=objective_var, command=toggle_objective
).grid(row=3, column=0, sticky="w", padx=10, pady=(15, 0))

objective_frame = tk.Frame(main_frame)
objective_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=10)
tk.Label(objective_frame, text="Objective:").grid(row=0, column=0, sticky="nw")
objective_entry = tk.Text(objective_frame, width=45, height=3)
objective_entry.grid(row=0, column=1)
objective_frame.grid_remove()  # hidden by default

# --- Section: Education ---
education_var = tk.IntVar()

def toggle_education():
    if education_var.get():
        education_frame.grid()
    else:
        education_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Education", variable=education_var, command=toggle_education
).grid(row=5, column=0, sticky="w", padx=10, pady=(15, 0))

education_frame = tk.Frame(main_frame)
education_frame.grid(row=6, column=0, columnspan=2, sticky="w", padx=10)

tk.Label(education_frame, text="Degree:").grid(row=0, column=0, sticky="w")
degree_entry = tk.Entry(education_frame, width=35)
degree_entry.grid(row=0, column=1)

tk.Label(education_frame, text="Institution:").grid(row=1, column=0, sticky="w")
institution_entry = tk.Entry(education_frame, width=35)
institution_entry.grid(row=1, column=1)

tk.Label(education_frame, text="Year:").grid(row=2, column=0, sticky="w")
year_entry = tk.Entry(education_frame, width=35)
year_entry.grid(row=2, column=1)

education_frame.grid_remove()  # hidden by default

# --- Section: Skills (dynamic, one row by default, "Add" for more) ---
skills_var = tk.IntVar()
skill_entries = []  # list of dicts: {"name": Entry, "desc": Entry, "row_frame": Frame}

def toggle_skills():
    if skills_var.get():
        skills_frame.grid()
        if not skill_entries:          # show one skill row by default the first time
            add_skill_row()
    else:
        skills_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Skills", variable=skills_var, command=toggle_skills
).grid(row=7, column=0, sticky="w", padx=10, pady=(15, 0))

skills_frame = tk.Frame(main_frame)
skills_frame.grid(row=8, column=0, columnspan=2, sticky="w", padx=10)

skills_container = tk.Frame(skills_frame)   # holds all dynamically added skill rows
skills_container.pack(fill="x")

def add_skill_row():
    row_frame = tk.Frame(skills_container, bd=1, relief="solid", padx=5, pady=5)
    row_frame.pack(fill="x", pady=4)

    index = len(skill_entries) + 1
    tk.Label(row_frame, text=f"Skill {index}:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(row_frame, width=30)
    name_entry.grid(row=0, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Description (optional):").grid(row=1, column=0, sticky="w")
    desc_entry = tk.Entry(row_frame, width=40)
    desc_entry.grid(row=1, column=1, padx=5, sticky="w")

    skill_entries.append({"name": name_entry, "desc": desc_entry, "row_frame": row_frame})

tk.Button(
    skills_frame, text="+ Add Another Skill", command=add_skill_row
).pack(pady=(5, 0))

skills_frame.grid_remove()  # hidden by default

# --- Section: Experience (dynamic, one entry by default, "Add" for more) ---
experience_var = tk.IntVar()
experience_entries = []  # list of dicts: {"role", "company", "duration", "desc", "row_frame"}

def toggle_experience():
    if experience_var.get():
        experience_frame.grid()
        if not experience_entries:     # show one experience card by default the first time
            add_experience_row()
    else:
        experience_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Experience / Internships", variable=experience_var, command=toggle_experience
).grid(row=9, column=0, sticky="w", padx=10, pady=(15, 0))

experience_frame = tk.Frame(main_frame)
experience_frame.grid(row=10, column=0, columnspan=2, sticky="w", padx=10)

experience_container = tk.Frame(experience_frame)   # holds all dynamically added experience rows
experience_container.pack(fill="x")

def add_experience_row():
    row_frame = tk.Frame(experience_container, bd=1, relief="solid", padx=5, pady=5)
    row_frame.pack(fill="x", pady=4)

    index = len(experience_entries) + 1
    tk.Label(row_frame, text=f"Experience {index}", font=("TkDefaultFont", 9, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w"
    )

    tk.Label(row_frame, text="Role/Title:").grid(row=1, column=0, sticky="w")
    role_entry = tk.Entry(row_frame, width=35)
    role_entry.grid(row=1, column=1, padx=5)

    tk.Label(row_frame, text="Company:").grid(row=2, column=0, sticky="w")
    company_entry = tk.Entry(row_frame, width=35)
    company_entry.grid(row=2, column=1, padx=5)

    tk.Label(row_frame, text="Duration:").grid(row=3, column=0, sticky="w")
    duration_entry = tk.Entry(row_frame, width=35)
    duration_entry.grid(row=3, column=1, padx=5)

    tk.Label(row_frame, text="Description:").grid(row=4, column=0, sticky="nw")
    desc_entry = tk.Text(row_frame, width=35, height=3)
    desc_entry.grid(row=4, column=1, padx=5)

    experience_entries.append({
        "role": role_entry,
        "company": company_entry,
        "duration": duration_entry,
        "desc": desc_entry,
        "row_frame": row_frame,
    })

tk.Button(
    experience_frame, text="+ Add Another Experience", command=add_experience_row
).pack(pady=(5, 0))

experience_frame.grid_remove()  # hidden by default

# --- Section: Achievements / Activities (dynamic, one entry by default, "Add" for more) ---
achievements_var = tk.IntVar()
achievement_entries = []  # list of dicts: {"entry": Entry, "row_frame": Frame}

def toggle_achievements():
    if achievements_var.get():
        achievements_frame.grid()
        if not achievement_entries:    # show one achievement box by default the first time
            add_achievement_row()
    else:
        achievements_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Achievements / Activities", variable=achievements_var, command=toggle_achievements
).grid(row=11, column=0, sticky="w", padx=10, pady=(15, 0))

achievements_frame = tk.Frame(main_frame)
achievements_frame.grid(row=12, column=0, columnspan=2, sticky="w", padx=10)

achievements_container = tk.Frame(achievements_frame)  # holds all dynamically added achievement rows
achievements_container.pack(fill="x")

def add_achievement_row():
    row_frame = tk.Frame(achievements_container, pady=2)
    row_frame.pack(fill="x")

    index = len(achievement_entries) + 1
    tk.Label(row_frame, text=f"Achievement {index}:").grid(row=0, column=0, sticky="w")
    entry = tk.Entry(row_frame, width=45)
    entry.grid(row=0, column=1, padx=5)

    achievement_entries.append({"entry": entry, "row_frame": row_frame})

tk.Button(
    achievements_frame, text="+ Add Another Achievement", command=add_achievement_row
).pack(pady=(5, 0))

achievements_frame.grid_remove()  # hidden by default

# --- Section: Projects (dynamic, one card by default, "Add" for more) ---
projects_var = tk.IntVar()
project_entries = []  # list of dicts: {"title", "subtitle", "desc", "link", "row_frame"}

def toggle_projects():
    if projects_var.get():
        projects_frame.grid()
        if not project_entries:        # show one project card by default the first time
            add_project_row()
    else:
        projects_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Projects", variable=projects_var, command=toggle_projects
).grid(row=13, column=0, sticky="w", padx=10, pady=(15, 0))

projects_frame = tk.Frame(main_frame)
projects_frame.grid(row=14, column=0, columnspan=2, sticky="w", padx=10)

projects_container = tk.Frame(projects_frame)   # holds all dynamically added project cards
projects_container.pack(fill="x")

def add_project_row():
    row_frame = tk.Frame(projects_container, bd=1, relief="solid", padx=5, pady=5)
    row_frame.pack(fill="x", pady=4)

    index = len(project_entries) + 1
    tk.Label(row_frame, text=f"Project {index}", font=("TkDefaultFont", 9, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w"
    )

    tk.Label(row_frame, text="Title:").grid(row=1, column=0, sticky="w")
    title_entry = tk.Entry(row_frame, width=40)
    title_entry.grid(row=1, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Subtitle:").grid(row=2, column=0, sticky="w")
    subtitle_entry = tk.Entry(row_frame, width=40)
    subtitle_entry.grid(row=2, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Description:").grid(row=3, column=0, sticky="nw")
    desc_entry = tk.Text(row_frame, width=40, height=3)
    desc_entry.grid(row=3, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Link URL (GitHub/Video/Doc):").grid(row=4, column=0, sticky="w")
    link_entry = tk.Entry(row_frame, width=40)
    link_entry.grid(row=4, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Link Display Text (optional):").grid(row=5, column=0, sticky="w")
    link_text_entry = tk.Entry(row_frame, width=40)
    link_text_entry.grid(row=5, column=1, padx=5, sticky="w")

    project_entries.append({
        "title": title_entry,
        "subtitle": subtitle_entry,
        "desc": desc_entry,
        "link": link_entry,
        "link_text": link_text_entry,
        "row_frame": row_frame,
    })

tk.Button(
    projects_frame, text="+ Add Another Project", command=add_project_row
).pack(pady=(5, 0))

projects_frame.grid_remove()  # hidden by default

# --- Submit ---
def submit():
    name = name_entry.get().strip()
    email = email_entry.get().strip()
    contact = contact_entry.get().strip()

    if not name or not email or not contact:
        messagebox.showerror("Missing Info", "Name, Email, and Contact are required.")
        return

    email_pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        messagebox.showerror("Invalid Email", "Please enter a valid email address (e.g. name@example.com).")
        return

    # --- Build the data dictionary (matches the JSON structure from the spec) ---
    data = {
        "name": name,
        "email": email,
        "contact": contact,
        "objective": "",
        "skills": [],
        "education": [],
        "projects": [],
        "experience": [],
        "activities": [],
    }

    # Objective
    if objective_var.get():
        objective_text = objective_entry.get("1.0", "end").strip()
        if objective_text:
            data["objective"] = objective_text

    # Education (single entry, stored as a list per the spec's schema)
    if education_var.get():
        degree = degree_entry.get().strip()
        institution = institution_entry.get().strip()
        year = year_entry.get().strip()

        education_data = {}
        if degree:
            education_data["degree"] = degree
        if institution:
            education_data["institution"] = institution
        if year:
            education_data["year"] = year

        if education_data:
            data["education"].append(education_data)

    # Skills
    if skills_var.get():
        for entry in skill_entries:
            skill_name = entry["name"].get().strip()
            skill_desc = entry["desc"].get().strip()

            if not skill_name:      # skip rows where the skill name itself is empty
                continue

            skill_data = {"name": skill_name}
            if skill_desc:
                skill_data["description"] = skill_desc

            data["skills"].append(skill_data)

    # Experience
    if experience_var.get():
        for entry in experience_entries:
            role = entry["role"].get().strip()
            company = entry["company"].get().strip()
            duration = entry["duration"].get().strip()
            exp_description = entry["desc"].get("1.0", "end").strip()

            experience_data = {}
            if role:
                experience_data["role"] = role
            if company:
                experience_data["company"] = company
            if duration:
                experience_data["duration"] = duration
            if exp_description:
                experience_data["description"] = exp_description

            if experience_data:   # skip fully-empty cards
                data["experience"].append(experience_data)

    # Achievements / Activities
    if achievements_var.get():
        for entry in achievement_entries:
            achievement_text = entry["entry"].get().strip()
            if achievement_text:   # skip empty rows
                data["activities"].append(achievement_text)

    # Projects
    if projects_var.get():
        for entry in project_entries:
            title = entry["title"].get().strip()
            subtitle = entry["subtitle"].get().strip()
            desc = entry["desc"].get("1.0", "end").strip()
            link_url = entry["link"].get().strip()
            link_text = entry["link_text"].get().strip()

            project_data = {}
            if title:
                project_data["title"] = title
            if subtitle:
                project_data["subtitle"] = subtitle
            if desc:
                project_data["description"] = desc
            if link_url:
                project_data["link"] = {
                    "url": link_url,
                    "text": link_text if link_text else link_url,
                }

            if project_data:   # skip fully-empty cards
                data["projects"].append(project_data)

    # --- Confirmation before saving ---
    if not messagebox.askyesno("Confirm", "Is all the information correct?"):
        return   # user chose "No" — let them go back and edit before re-submitting

    # --- Write to data/resume_data.json ---
    try:
        os.makedirs("data", exist_ok=True)
        json_path = os.path.join("data", "resume_data.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        messagebox.showerror("Save Failed", f"Could not write JSON file:\n{e}")
        return

    # --- Auto-trigger generator.py to build the PDF ---
    # sys.executable ensures we use the same Python interpreter (and venv)
    # that's currently running gui.py, rather than whatever "python3" resolves
    # to on the system PATH.
    try:
        result = subprocess.run(
            [sys.executable, "generator.py"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        messagebox.showerror(
            "Generator Not Found",
            "Could not find generator.py. Make sure it's in the same folder as gui.py."
        )
        return

    if result.returncode != 0:
        # Show the last part of the error so the user has something to act on,
        # without dumping the entire LaTeX log into a popup.
        error_tail = result.stdout[-800:] if result.stdout else result.stderr[-800:]
        messagebox.showerror(
            "PDF Generation Failed",
            f"resume_data.json was saved, but PDF generation failed.\n\n"
            f"Details:\n{error_tail}\n\n"
            f"Check output/resume.log for the full LaTeX log."
        )
        return

    messagebox.showinfo("Success", "Resume generated at output/resume.pdf")

tk.Button(main_frame, text="Submit", command=submit).grid(row=15, column=0, columnspan=2, pady=25)

root.mainloop()