import tkinter as tk
from tkinter import messagebox, colorchooser
import re
import json
import os
import subprocess
import sys

root = tk.Tk()
root.title("Smart Resume Builder")
root.geometry("700x700")   # fixed visible window size; content scrolls inside it

# Force the window to the front and give it keyboard/mouse focus on startup.
# On some Linux window managers, newly-opened Tk windows can appear without
# focus, making it seem like nothing responds to clicks.
root.lift()
root.attributes("-topmost", True)
root.after_idle(root.attributes, "-topmost", False)
root.focus_force()

# --- Scrollable canvas setup ---
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

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

# Row counter — incremented as we go, so inserting/removing sections later
# doesn't require manually renumbering every widget below it.
r = 0

# --- Mandatory Fields ---
tk.Label(main_frame, text="Full Name *").grid(row=r, column=0, sticky="w", padx=10, pady=5)
name_entry = tk.Entry(main_frame, width=40)
name_entry.grid(row=r, column=1, padx=10, pady=5)
r += 1

tk.Label(main_frame, text="Email *").grid(row=r, column=0, sticky="w", padx=10, pady=5)
email_entry = tk.Entry(main_frame, width=40)
email_entry.grid(row=r, column=1, padx=10, pady=5)
r += 1

tk.Label(main_frame, text="Contact Number *").grid(row=r, column=0, sticky="w", padx=10, pady=5)

# Live validation: only allow digits, and cap length at 10 characters as the
# user types. This blocks letters/symbols and prevents typing an 11th digit,
# but we still re-check "exactly 10 digits" at submit time in case the field
# is left short.
def validate_contact_input(proposed_value):
    if proposed_value == "":
        return True   # allow clearing the field
    return proposed_value.isdigit() and len(proposed_value) <= 10

vcmd_contact = (main_frame.register(validate_contact_input), "%P")
contact_entry = tk.Entry(main_frame, width=40, validate="key", validatecommand=vcmd_contact)
contact_entry.grid(row=r, column=1, padx=10, pady=5)
r += 1

# --- Heading Color Picker ---
# Lets the user choose the color used for section labels (Skills, Education,
# Projects, etc.) in the final PDF. Stored as a 6-digit hex string (no '#')
# since that's what LaTeX's \definecolor{...}{HTML}{...} expects.
heading_color_var = tk.StringVar(value="2454A6")   # default: the original accent blue

tk.Label(main_frame, text="Heading Color:").grid(row=r, column=0, sticky="w", padx=10, pady=(15, 5))

color_frame = tk.Frame(main_frame)
color_frame.grid(row=r, column=1, sticky="w", padx=10, pady=(15, 5))

color_preview = tk.Label(color_frame, text="  ", bg="#" + heading_color_var.get(), relief="sunken", width=3)
color_preview.pack(side="left", padx=(0, 10))

def set_heading_color(hex_no_hash):
    heading_color_var.set(hex_no_hash)
    color_preview.config(bg="#" + hex_no_hash)

def choose_custom_color():
    # Opens the OS's native color picker (a color wheel on most platforms).
    result = colorchooser.askcolor(title="Choose Heading Color")
    if result and result[1]:            # result = ((r,g,b), "#rrggbb") or (None, None) if cancelled
        hex_val = result[1].lstrip("#").upper()
        set_heading_color(hex_val)

tk.Button(
    color_frame, text="Light Blue", bg="#5DADE2",
    command=lambda: set_heading_color("5DADE2")
).pack(side="left", padx=2)

tk.Button(
    color_frame, text="Black", bg="#000000", fg="white",
    command=lambda: set_heading_color("000000")
).pack(side="left", padx=2)

tk.Button(
    color_frame, text="Dark Blue", bg="#1B3A6B", fg="white",
    command=lambda: set_heading_color("1B3A6B")
).pack(side="left", padx=2)

tk.Button(
    color_frame, text="Custom Color...", command=choose_custom_color
).pack(side="left", padx=2)

r += 1

# --- Section: Profiles / Social Links (dynamic, one card by default) ---
profiles_var = tk.IntVar()
profile_entries = []  # list of dicts: {"platform", "url", "text", "row_frame"}

def toggle_profiles():
    if profiles_var.get():
        profiles_frame.grid()
        if not profile_entries:
            add_profile_row()
    else:
        profiles_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Profiles / Social Links", variable=profiles_var, command=toggle_profiles
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

profiles_frame = tk.Frame(main_frame)
profiles_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

profiles_container = tk.Frame(profiles_frame)
profiles_container.pack(fill="x")

def add_profile_row():
    row_frame = tk.Frame(profiles_container, bd=1, relief="solid", padx=5, pady=5)
    row_frame.pack(fill="x", pady=4)

    index = len(profile_entries) + 1
    tk.Label(row_frame, text=f"Profile {index}", font=("TkDefaultFont", 9, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w"
    )

    tk.Label(row_frame, text="Platform (e.g. GitHub):").grid(row=1, column=0, sticky="w")
    platform_entry = tk.Entry(row_frame, width=30)
    platform_entry.grid(row=1, column=1, padx=5, sticky="w")

    tk.Label(row_frame, text="Profile URL:").grid(row=2, column=0, sticky="w")
    url_entry = tk.Entry(row_frame, width=40)
    url_entry.grid(row=2, column=1, padx=5, sticky="w")

    profile_entries.append({
        "platform": platform_entry,
        "url": url_entry,
        "row_frame": row_frame,
    })

tk.Button(
    profiles_frame, text="+ Add Another Profile", command=add_profile_row
).pack(pady=(5, 0))

profiles_frame.grid_remove()

# --- Section: Objective ---
objective_var = tk.IntVar()

def toggle_objective():
    if objective_var.get():
        objective_frame.grid()
    else:
        objective_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Objective", variable=objective_var, command=toggle_objective
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

objective_frame = tk.Frame(main_frame)
objective_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

tk.Label(objective_frame, text="Objective:").grid(row=0, column=0, sticky="nw")
objective_entry = tk.Text(objective_frame, width=45, height=3)
objective_entry.grid(row=0, column=1)
objective_frame.grid_remove()

# --- Section: Education (dynamic, one card by default, "Add" for more) ---
education_var = tk.IntVar()
education_entries = []  # list of dicts: {"degree", "institution", "year", "row_frame"}

def toggle_education():
    if education_var.get():
        education_frame.grid()
        if not education_entries:
            add_education_row()
    else:
        education_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Education", variable=education_var, command=toggle_education
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

education_frame = tk.Frame(main_frame)
education_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

education_container = tk.Frame(education_frame)
education_container.pack(fill="x")

def add_education_row():
    row_frame = tk.Frame(education_container, bd=1, relief="solid", padx=5, pady=5)
    row_frame.pack(fill="x", pady=4)

    index = len(education_entries) + 1
    tk.Label(row_frame, text=f"Education {index}", font=("TkDefaultFont", 9, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w"
    )

    tk.Label(row_frame, text="Degree:").grid(row=1, column=0, sticky="w")
    degree_entry = tk.Entry(row_frame, width=35)
    degree_entry.grid(row=1, column=1, padx=5)

    tk.Label(row_frame, text="Institution:").grid(row=2, column=0, sticky="w")
    institution_entry = tk.Entry(row_frame, width=35)
    institution_entry.grid(row=2, column=1, padx=5)

    tk.Label(row_frame, text="Year:").grid(row=3, column=0, sticky="w")
    year_entry = tk.Entry(row_frame, width=35)
    year_entry.grid(row=3, column=1, padx=5)

    education_entries.append({
        "degree": degree_entry,
        "institution": institution_entry,
        "year": year_entry,
        "row_frame": row_frame,
    })

tk.Button(
    education_frame, text="+ Add Another Education", command=add_education_row
).pack(pady=(5, 0))

education_frame.grid_remove()

# --- Section: Skills (dynamic, one row by default, "Add" for more) ---
skills_var = tk.IntVar()
skill_entries = []  # list of dicts: {"name": Entry, "desc": Entry, "row_frame": Frame}

def toggle_skills():
    if skills_var.get():
        skills_frame.grid()
        if not skill_entries:
            add_skill_row()
    else:
        skills_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Skills", variable=skills_var, command=toggle_skills
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

skills_frame = tk.Frame(main_frame)
skills_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

skills_container = tk.Frame(skills_frame)
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

skills_frame.grid_remove()

# --- Section: Experience (dynamic, one entry by default, "Add" for more) ---
experience_var = tk.IntVar()
experience_entries = []  # list of dicts: {"role", "company", "duration", "desc", "row_frame"}

def toggle_experience():
    if experience_var.get():
        experience_frame.grid()
        if not experience_entries:
            add_experience_row()
    else:
        experience_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Experience / Internships", variable=experience_var, command=toggle_experience
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

experience_frame = tk.Frame(main_frame)
experience_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

experience_container = tk.Frame(experience_frame)
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

experience_frame.grid_remove()

# --- Section: Achievements / Activities (dynamic, one entry by default) ---
achievements_var = tk.IntVar()
achievement_entries = []  # list of dicts: {"entry": Entry, "row_frame": Frame}

def toggle_achievements():
    if achievements_var.get():
        achievements_frame.grid()
        if not achievement_entries:
            add_achievement_row()
    else:
        achievements_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Achievements / Activities", variable=achievements_var, command=toggle_achievements
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

achievements_frame = tk.Frame(main_frame)
achievements_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

achievements_container = tk.Frame(achievements_frame)
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

achievements_frame.grid_remove()

# --- Section: Projects (dynamic, one card by default, "Add" for more) ---
projects_var = tk.IntVar()
project_entries = []  # list of dicts: {"title", "subtitle", "desc", "link", "link_text", "row_frame"}

def toggle_projects():
    if projects_var.get():
        projects_frame.grid()
        if not project_entries:
            add_project_row()
    else:
        projects_frame.grid_remove()

tk.Checkbutton(
    main_frame, text="Include Projects", variable=projects_var, command=toggle_projects
).grid(row=r, column=0, sticky="w", padx=10, pady=(15, 0))
r += 1

projects_frame = tk.Frame(main_frame)
projects_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=10)
r += 1

projects_container = tk.Frame(projects_frame)
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

projects_frame.grid_remove()

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

    if not (contact.isdigit() and len(contact) == 10):
        messagebox.showerror("Invalid Contact Number", "Contact number must be exactly 10 digits.")
        return

    # --- Build the data dictionary ---
    data = {
        "name": name,
        "email": email,
        "contact": contact,
        "heading_color": heading_color_var.get(),
        "profiles": [],
        "objective": "",
        "skills": [],
        "education": [],
        "projects": [],
        "experience": [],
        "activities": [],
    }

    # Profiles / Social Links
    if profiles_var.get():
        for entry in profile_entries:
            platform = entry["platform"].get().strip()
            url = entry["url"].get().strip()

            if not url:   # a profile with no URL has nothing to link to — skip it
                continue

            # Display text: platform name if given, otherwise fall back to the raw URL
            display_text = platform if platform else url

            data["profiles"].append({"url": url, "text": display_text})

    # Objective
    if objective_var.get():
        objective_text = objective_entry.get("1.0", "end").strip()
        if objective_text:
            data["objective"] = objective_text

    # Education
    if education_var.get():
        for entry in education_entries:
            degree = entry["degree"].get().strip()
            institution = entry["institution"].get().strip()
            year = entry["year"].get().strip()

            education_data = {}
            if degree:
                education_data["degree"] = degree
            if institution:
                education_data["institution"] = institution
            if year:
                education_data["year"] = year

            if education_data:   # skip fully-empty cards
                data["education"].append(education_data)

    # Skills
    if skills_var.get():
        for entry in skill_entries:
            skill_name = entry["name"].get().strip()
            skill_desc = entry["desc"].get().strip()

            if not skill_name:
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

            if experience_data:
                data["experience"].append(experience_data)

    # Achievements / Activities
    if achievements_var.get():
        for entry in achievement_entries:
            achievement_text = entry["entry"].get().strip()
            if achievement_text:
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

            if project_data:
                data["projects"].append(project_data)

    # --- Confirmation before saving ---
    if not messagebox.askyesno("Confirm", "Is all the information correct?"):
        return

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
        error_tail = result.stdout[-800:] if result.stdout else result.stderr[-800:]
        messagebox.showerror(
            "PDF Generation Failed",
            f"resume_data.json was saved, but PDF generation failed.\n\n"
            f"Details:\n{error_tail}\n\n"
            f"Check output/resume.log for the full LaTeX log."
        )
        return

    messagebox.showinfo("Success", "Resume generated at output/resume.pdf")

tk.Button(main_frame, text="Submit", command=submit).grid(row=r, column=0, columnspan=2, pady=25)

root.mainloop()