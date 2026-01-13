# =========================
# TABLE GENERATION
# =========================

def table_creation(div, working_days, no_of_period):
    # Changed to lists to support multiple assignments per cell (e.g., batches)
    table = [[[] for _ in range(working_days + 1)]
             for _ in range(no_of_period + 1)]

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][:working_days]

    table[0][0] = f"Div-{div}"
    for j in range(1, working_days + 1):
        table[0][j] = days[j - 1]

    for i in range(1, no_of_period + 1):
        table[i][0] = f"P{i}"

    return table


def timegen(no_of_div, working_days, no_of_period):
    return [
        table_creation(div, working_days, no_of_period)
        for div in range(1, no_of_div + 1)
    ]


# =========================
# HOURS → PERIODS
# =========================

def convert_hours_to_periods(subjects, lecture_duration, practical_duration):
    for s in subjects:
        total_lecture_hours = (
            s.get("theory_hours", 0) +
            s.get("tutorial_hours", 0)
        )

        s["theory_per_week"] = (total_lecture_hours * 60) // lecture_duration
        s["practical_per_week"] = (s.get("practical_hours", 0) * 60) // practical_duration


# =========================
# PRACTICAL CHECK
# =========================

def can_place_practical(table, day, period, no_of_period):
    return (
        period < no_of_period and  # Cannot start in last period
        len(table[period][day]) == 0 and  # No assignments yet in this block
        len(table[period + 1][day]) == 0
    )


# =========================
# FACULTY STATE HELPERS
# =========================

def can_use_faculty(faculty, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=False):
    # Check cooldown
    if faculty_cooldown.get(faculty, 0) > 0:
        return False
    
    # Check continuous limit
    state = faculty_state.get(faculty, {"continuous": 0})
    if state["continuous"] >= 2:
        return False
    
    # Check global availability (cross-division clash)
    occupied = faculty_availability.get(faculty, {}).get(day, set())
    if is_practical:
        if period in occupied or (period + 1) in occupied:
            return False
    else:
        if period in occupied:
            return False
    
    return True


def update_faculty_state(faculty, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=False):
    state = faculty_state.setdefault(faculty, {"continuous": 0})
    state["continuous"] += 1
    
    # Update global availability
    avail = faculty_availability.setdefault(faculty, {})
    day_occ = avail.setdefault(day, set())
    day_occ.add(period)
    if is_practical:
        day_occ.add(period + 1)
    
    # Trigger cooldown after 2 continuous (or after practical)
    if state["continuous"] == 2 or is_practical:
        faculty_cooldown[faculty] = 1  # 1 period break
        state["continuous"] = 0


def tick_cooldowns(faculty_cooldown):
    for f in list(faculty_cooldown):
        faculty_cooldown[f] -= 1
        if faculty_cooldown[f] <= 0:
            del faculty_cooldown[f]


# =========================
# ASSIGNMENT HELPERS
# =========================

def assign_theory(table, div, day, period, subject, faculty):
    table[period][day].append({  # Append to list
        "division": div,
        "subject": subject["subject"],
        "faculty": faculty,
        "type": "theory"
    })


def assign_practical(table, div, day, period, subject, faculty, lab):
    for p in (period, period + 1):
        table[p][day].append({  # Append to list
            "division": div,
            "subject": subject["subject"],
            "faculty": faculty,
            "type": "practical",
            "lab": lab
        })


# =========================
# CORE ASSIGNMENT LOGIC
# =========================

def assign_faculty(
    table,
    div,
    day,
    period,
    subjects,
    labs,
    lab_usage,
    no_of_period,
    faculty_state,
    faculty_cooldown,
    faculty_availability,
    division_subject_faculty,
    subject_count_per_day,  # Soft constraint: track subjects per day
    practical_batches  # New: Max batches per practical block
):
    for subject in subjects:
        if not subject.get("faculty"):
            continue

        key = (div, subject["subject"])
        allowed_faculty = (
            [division_subject_faculty[key]]
            if key in division_subject_faculty
            else subject["faculty"]
        )

        # Soft constraint: Avoid >2 of same subject per day
        current_count = subject_count_per_day.get((div, day, subject["subject"]), 0)
        if current_count >= 2:
            continue  # Skip if already 2+ today (soft, so allow if no choice)

        # THEORY
        if subject["theory_per_week"] > 0 and len(table[period][day]) == 0:  # Check if empty
            for fac in allowed_faculty:
                if can_use_faculty(fac, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=False):
                    division_subject_faculty[key] = fac
                    assign_theory(table, div, day, period, subject, fac)
                    update_faculty_state(fac, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=False)
                    subject["theory_per_week"] -= 1
                    subject_count_per_day[(div, day, subject["subject"])] = current_count + 1
                    return

        # PRACTICAL
        if subject["practical_per_week"] > 0 and can_place_practical(table, day, period, no_of_period):
            assigned_batches = 0
            used_labs = set()  # Track labs used in this block
            used_faculty = set()  # Track faculty used in this block (to allow reuse if needed, but prefer different)
            
            for _ in range(practical_batches):  # Try to assign up to practical_batches
                if subject["practical_per_week"] <= 0:
                    break  # No more needed
                
                lab_assigned = None
                fac_assigned = None
                
                # Find available lab
                for lab in labs:
                    lab_occ = lab_usage.get(lab, {}).get(day, set())
                    if period not in lab_occ and (period + 1) not in lab_occ and lab not in used_labs:
                        lab_assigned = lab
                        break
                
                if not lab_assigned:
                    break  # No free lab
                
                # Find available faculty (prefer unused in this block)
                for fac in allowed_faculty:
                    if fac not in used_faculty and can_use_faculty(fac, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=True):
                        fac_assigned = fac
                        break
                
                if not fac_assigned:
                    break  # No free faculty
                
                # Assign
                division_subject_faculty[key] = fac_assigned
                assign_practical(table, div, day, period, subject, fac_assigned, lab_assigned)
                update_faculty_state(fac_assigned, faculty_state, faculty_cooldown, faculty_availability, day, period, is_practical=True)
                lab_usage.setdefault(lab_assigned, {}).setdefault(day, set()).update({period, period + 1})
                subject["practical_per_week"] -= 1
                assigned_batches += 1
                used_labs.add(lab_assigned)
                used_faculty.add(fac_assigned)
                subject_count_per_day[(div, day, subject["subject"])] = current_count + 1  # Counts as 1 for the day
            
            if assigned_batches > 0:
                return  # Assigned at least one batch


# =========================
# ASSIGN ALL DIVISIONS
# =========================

import copy

def assign_all_faculty(tables, working_days, no_of_period, subjects, lab_count, practical_batches):
    labs = [f"Lab-{i}" for i in range(1, lab_count + 1)]
    
    # Global state (shared across divisions)
    faculty_state = {}  # Per faculty
    faculty_cooldown = {}  # Per faculty
    faculty_availability = {}  # faculty -> day -> set of periods
    lab_usage = {}  # lab -> day -> set of periods
    
    for div, table in enumerate(tables, start=1):
        subs = copy.deepcopy(subjects)
        division_subject_faculty = {}
        subject_count_per_day = {}  # (div, day, subject) -> count (for soft constraint)
        
        for day in range(1, working_days + 1):
            for period in range(1, no_of_period + 1):
                assign_faculty(
                    table,
                    div,
                    day,
                    period,
                    subs,
                    labs,
                    lab_usage,
                    no_of_period,
                    faculty_state,
                    faculty_cooldown,
                    faculty_availability,
                    division_subject_faculty,
                    subject_count_per_day,
                    practical_batches  # New param
                )
                tick_cooldowns(faculty_cooldown)
        
        # Failure check: Ensure all subjects are fully scheduled
        for sub in subs:
            if sub.get("theory_per_week", 0) > 0 or sub.get("practical_per_week", 0) > 0:
                raise ValueError(f"No valid timetable possible for Division {div}: Subject '{sub['subject']}' not fully scheduled (theory left: {sub.get('theory_per_week', 0)}, practical left: {sub.get('practical_per_week', 0)}).")


# =========================
# FACULTY INITIALS
# =========================

def faculty_initials(name):
    return "".join(p[0].upper() for p in name.split() if p)


# =========================
# DEBUG PRINT
# =========================

def pretty_print_tables(tables):
    for d, table in enumerate(tables, start=1):
        print(f"\n========== Division {d} ==========")
        for row in table:
            out = []
            for cell in row:
                if isinstance(cell, list):
                    if not cell:
                        out.append("")
                    else:
                        # Show all assignments in the cell
                        cell_strs = []
                        for item in cell:
                            fac = faculty_initials(item["faculty"])
                            lab_str = f"({item.get('lab', '')})" if item.get('lab') else ""
                            cell_strs.append(f"{item['subject']}[{fac}]{lab_str}({item['type'][0].upper()})")
                        out.append(", ".join(cell_strs))
                else:
                    out.append(str(cell))
            print("\t".join(out))