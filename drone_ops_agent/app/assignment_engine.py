def match_pilots(pilots, mission):
    results = []
    for _, p in pilots.iterrows():
        if p["status"] != "Available":
            continue
        score = 0
        if p["location"] == mission["location"]:
            score += 2
        results.append((score, p["name"]))
    return sorted(results, reverse=True)
