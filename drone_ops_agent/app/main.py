from fastapi import FastAPI
from app.sheets_client import SheetsClient
from datetime import datetime

app = FastAPI()

# 🔹 Google Sheet ID
SHEET_ID = "1jLqcJSNg4i4cIXjwU3LfMk-bvRig-tsIp_iDgBvZJQ4"
sheets = SheetsClient(SHEET_ID)


# --------------------------------------------------
# Root
# --------------------------------------------------
@app.get("/")
def root():
    return {"status": "Drone Ops Agent running"}


# --------------------------------------------------
# Read APIs
# --------------------------------------------------
@app.get("/pilots")
def get_pilots():
    return sheets.read_sheet("pilot_roster!A1:Z").to_dict(orient="records")


@app.get("/drones")
def get_drones():
    return sheets.read_sheet("drone_fleet!A1:Z").to_dict(orient="records")


@app.get("/missions")
def get_missions():
    return sheets.read_sheet("missions!A1:Z").to_dict(orient="records")


# --------------------------------------------------
# Update Pilot Status (2-way sync)
# --------------------------------------------------
@app.post("/pilot/{row}/status")
def update_pilot_status(row: int, status: str):
    # Column G = status (as per template)
    sheets.update_cell(f"pilot_roster!G{row}", status)
    return {"message": "Pilot status updated successfully"}


# --------------------------------------------------
# Conflict Detection
# --------------------------------------------------
@app.get("/conflicts")
def detect_conflicts():
    pilots = sheets.read_sheet("pilot_roster!A1:Z").to_dict(orient="records")
    drones = sheets.read_sheet("drone_fleet!A1:Z").to_dict(orient="records")
    missions = sheets.read_sheet("missions!A1:Z").to_dict(orient="records")

    conflicts = []

    mission_map = {m["project_id"].strip(): m for m in missions}
    drone_map = {d["drone_id"].strip(): d for d in drones}

    for pilot in pilots:
        assignment = pilot.get("current_assignment", "").strip()

        # Skip unassigned pilots
        if assignment in ["", "-", "–"]:
            continue

        if assignment not in mission_map:
            continue

        mission = mission_map[assignment]

        # -------------------------
        # Skill mismatch
        # -------------------------
        required_skills = set(mission["required_skills"].split(", "))
        pilot_skills = set(pilot["skills"].split(", "))

        if not required_skills.issubset(pilot_skills):
            conflicts.append({
                "type": "Skill Mismatch",
                "pilot": pilot["name"],
                "mission": assignment
            })

        # -------------------------
        # Certification mismatch
        # -------------------------
        required_certs = set(mission["required_certs"].split(", "))
        pilot_certs = set(pilot["certifications"].split(", "))

        if not required_certs.issubset(pilot_certs):
            conflicts.append({
                "type": "Certification Mismatch",
                "pilot": pilot["name"],
                "mission": assignment
            })

        # -------------------------
        # Double booking risk
        # -------------------------
        end_date = datetime.fromisoformat(mission["end_date"])
        if pilot["status"] == "Assigned" and datetime.now() < end_date:
            conflicts.append({
                "type": "Double Booking Risk",
                "pilot": pilot["name"],
                "mission": assignment
            })

        # -------------------------
        # Drone maintenance + location
        # (No assigned_drone in missions → use pilot assignment only)
        # -------------------------
        for drone in drones:
            if drone["current_assignment"].strip() == assignment:
                if drone["status"] == "Maintenance":
                    conflicts.append({
                        "type": "Drone Maintenance Conflict",
                        "drone": drone["drone_id"],
                        "mission": assignment
                    })

                if drone["location"] != pilot["location"]:
                    conflicts.append({
                        "type": "Location Mismatch",
                        "pilot": pilot["name"],
                        "drone": drone["drone_id"]
                    })

    return {"conflicts": conflicts}


# --------------------------------------------------
# AI-style Pilot Recommendation (Urgent Reassignment)
# --------------------------------------------------
@app.get("/suggest-pilot/{project_id}")
def suggest_pilot(project_id: str):
    pilots = sheets.read_sheet("pilot_roster!A1:Z").to_dict(orient="records")
    missions = sheets.read_sheet("missions!A1:Z").to_dict(orient="records")

    mission = next(
        (m for m in missions if m["project_id"].strip() == project_id.strip()),
        None
    )

    if not mission:
        return {"error": "Mission not found"}

    required_skills = set(mission["required_skills"].split(", "))
    required_certs = set(mission["required_certs"].split(", "))
    mission_location = mission["location"]
    priority = mission["priority"]

    ranked_pilots = []

    for pilot in pilots:
        if pilot["status"] != "Available":
            continue

        pilot_skills = set(pilot["skills"].split(", "))
        pilot_certs = set(pilot["certifications"].split(", "))

        score = 0

        # Skill & cert match
        score += len(required_skills & pilot_skills) * 2
        score += len(required_certs & pilot_certs) * 3

        # Location match
        if pilot["location"] == mission_location:
            score += 5

        # Urgent missions → prefer same city
        if priority == "Urgent" and pilot["location"] == mission_location:
            score += 5

        if score > 0:
            ranked_pilots.append({
                "pilot": pilot["name"],
                "score": score,
                "location": pilot["location"]
            })

    ranked_pilots.sort(key=lambda x: x["score"], reverse=True)

    return {
        "project_id": project_id,
        "recommended_pilot": ranked_pilots[0] if ranked_pilots else None,
        "all_matches": ranked_pilots
    }
