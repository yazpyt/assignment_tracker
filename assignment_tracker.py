"""
assignment_tracker.py
Efficient assignment tracker with local JSON storage
"""

import json
import os
from datetime import datetime
import PySimpleGUI as sg

JSON_PATH = "assignments.json"
DATE_FORMAT = "%Y-%m-%d"

def load_data():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return []
    
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_subject_dialog():
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    layout = [
        [sg.Text("Add New Subject", font=("Helvetica", 14, "bold"))],
        [sg.Text("Subject Name:"), sg.Input(key="-NAME-")],
        [sg.Text("Exam Date:"), sg.Input(key="-EXAM-"), sg.CalendarButton("Choose", target="-EXAM-", format=DATE_FORMAT)],
        [sg.Text("Total Assignments:"), sg.Input(key="-TOTAL-")],
        [sg.Text("Delivered:"), sg.Input("0", key="-DELIVERED-")],
        [sg.Text("Deadline:"), sg.Input(key="-DEADLINE-"), sg.CalendarButton("Choose", target="-DEADLINE-", format=DATE_FORMAT)],
        [sg.Text("Study Day:"), sg.Combo(days_of_week, default_value="Monday", key="-DAY-")],
        [sg.Button("Add"), sg.Button("Cancel")]
    ]
    
    window = sg.Window("Add New Subject", layout, modal=True)
    
    event, values = window.read()
    window.close()
    
    if event != "Add":
        return None
    
    # Validate inputs
    name = values["-NAME-"].strip()
    exam = values["-EXAM-"].strip()
    total = values["-TOTAL-"].strip()
    delivered = values["-DELIVERED-"].strip() or "0"
    deadline = values["-DEADLINE-"].strip()
    day = values["-DAY-"]
    
    errors = []
    if not name: errors.append("Subject name is required")
    
    for date_str, field_name in [(exam, "Exam date"), (deadline, "Deadline")]:
        if not date_str: 
            errors.append(f"{field_name} is required")
        else:
            try:
                datetime.strptime(date_str, DATE_FORMAT)
            except ValueError:
                errors.append(f"{field_name} must be in YYYY-MM-DD format")
    
    for num_str, field_name in [(total, "Total assignments"), (delivered, "Delivered assignments")]:
        try:
            num = int(num_str)
            if num < 0: errors.append(f"{field_name} cannot be negative")
            if field_name == "Total assignments" and num <= 0: errors.append("Total assignments must be positive")
        except ValueError:
            errors.append(f"{field_name} must be a number")
    
    if errors:
        sg.popup_error("Please fix errors:\n" + "\n".join(errors))
        return None
    
    return {
        "subject_name": name,
        "exam_date": exam,
        "total_assignments": int(total),
        "delivered_assignments": int(delivered),
        "deadline": deadline,
        "study_day": day
    }

def build_window(subjects):
    sg.theme("LightGrey4")
    
    # Sort by deadline
    subjects.sort(key=lambda s: s.get('deadline', '9999-12-31'))
    
    header = [
        sg.Text("Subject", size=18),
        sg.Text("Exam Date", size=12),
        sg.Text("Total", size=6),
        sg.Text("Delivered", size=10),
        sg.Text("Progress", size=20),
        sg.Text("Deadline", size=12),
        sg.Text("Study Day", size=10),
    ]
    
    rows = []
    for i, s in enumerate(subjects):
        row = [
            sg.Input(s.get("subject_name", ""), key=f"-SUB-{i}-", size=18),
            sg.Input(s.get("exam_date", ""), key=f"-EXAM-{i}-", size=12),
            sg.Input(str(s.get("total_assignments", 0)), key=f"-TOT-{i}-", size=6),
            sg.Input(str(s.get("delivered_assignments", 0)), key=f"-DELIV-{i}-", size=10),
            sg.ProgressBar(s.get('total_assignments', 1), orientation='h', size=(15, 20), key=f"-PROG-{i}-"),
            sg.Input(s.get("deadline", ""), key=f"-DL-{i}-", size=12),
            sg.Input(s.get("study_day", ""), key=f"-DAY-{i}-", size=10),
        ]
        rows.append(row)
    
    layout = [
        [sg.Text("Assignment Tracker - Edit fields and click Save")],
        header,
        *rows,
        [sg.Button("Add Subject"), sg.Button("Save"), sg.Button("Exit")],
    ]
    
    window = sg.Window("Assignment Tracker", layout, finalize=True, resizable=True)
    
    # Initialize progress bars
    for i, s in enumerate(subjects):
        window[f"-PROG-{i}-"].update(current_count=s.get("delivered_assignments", 0))
    
    return window

def main():
    subjects = load_data()
    window = build_window(subjects)
    
    while True:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Exit"):
            break
        
        if event == "Add Subject":
            new_subject = add_subject_dialog()
            if new_subject:
                subjects.append(new_subject)
                save_data(subjects)
                window.close()
                window = build_window(subjects)
        
        elif event == "Save":
            errors = []
            for i, s in enumerate(subjects):
                # Update all fields
                s["subject_name"] = values[f"-SUB-{i}-"].strip()
                s["exam_date"] = values[f"-EXAM-{i}-"].strip()
                s["deadline"] = values[f"-DL-{i}-"].strip()
                s["study_day"] = values[f"-DAY-{i}-"].strip()
                
                # Validate dates
                for date_str, field_name in [(s["exam_date"], "Exam date"), (s["deadline"], "Deadline")]:
                    try:
                        datetime.strptime(date_str, DATE_FORMAT)
                    except ValueError:
                        errors.append(f"Row {i+1}: {field_name} format invalid")
                
                # Validate numbers
                try:
                    s["total_assignments"] = int(values[f"-TOT-{i}-"])
                    if s["total_assignments"] <= 0:
                        errors.append(f"Row {i+1}: Total must be positive")
                except ValueError:
                    errors.append(f"Row {i+1}: Total must be a number")
                
                try:
                    s["delivered_assignments"] = int(values[f"-DELIV-{i}-"])
                    if s["delivered_assignments"] < 0:
                        errors.append(f"Row {i+1}: Delivered cannot be negative")
                except ValueError:
                    errors.append(f"Row {i+1}: Delivered must be a number")
            
            if errors:
                sg.popup_error("Errors:\n" + "\n".join(errors))
            else:
                save_data(subjects)
                window.close()
                window = build_window(subjects)
                sg.popup("Saved!")
    
    window.close()

if __name__ == "__main__":
    main()