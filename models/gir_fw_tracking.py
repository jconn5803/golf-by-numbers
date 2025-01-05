from . import db
from .shot import Shot
from .round import Round, HoleStats
from .course import Hole

def update_gir_fairway(roundID, holes):
    for hole in holes:
        hole_shots = Shot.query.filter_by(roundID=roundID, holeID=hole.holeID).order_by(Shot.shotID).all()
        if not hole_shots:
            continue

        # Compute fairway_hit
        fairway_hit = None # This captures the par 3 case
        if hole.par in [4, 5] and len(hole_shots) > 0:
            first_shot = hole_shots[0]
            if first_shot.lie_before == "Tee" and first_shot.lie_after == "Fairway":
                fairway_hit = True
            else:
                fairway_hit = False

        # Compute GIR
        gir = False
        strokes_to_green = None
        for i, shot in enumerate(hole_shots, start=1):
            if shot.lie_after == "Green" or shot.lie_after == "In the Hole":
                strokes_to_green = i
                break
        if strokes_to_green:
            if hole.par == 3 and strokes_to_green <= 1:
                gir = True
            elif hole.par == 4 and strokes_to_green <= 2:
                gir = True
            elif hole.par == 5 and strokes_to_green <= 3:
                gir = True

        # Upsert HoleStats
        hole_stat = HoleStats.query.filter_by(roundID=roundID, holeID=hole.holeID).first()
        if not hole_stat:
            hole_stat = HoleStats(roundID=roundID, holeID=hole.holeID)
            db.session.add(hole_stat)

        hole_stat.fairway_hit = fairway_hit
        hole_stat.gir = gir

    db.session.commit()