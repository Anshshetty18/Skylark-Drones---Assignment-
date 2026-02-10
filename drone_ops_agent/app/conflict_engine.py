def dates_overlap(start1, end1, start2, end2):
    return not (end1 < start2 or end2 < start1)

def drone_in_maintenance(drone):
    return drone["status"].lower() == "maintenance"
