def choose_stance(facts, prior=None):
    if prior:
        return prior
    totals = {side: sum(f.score for f in facts if f.stance == side) for side in ("yes", "no")}
    return max(totals, key=totals.get)
