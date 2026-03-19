from fastapi import HTTPException

def validate_sending_windows(sending_windows: dict):
    has_valid_slot = False

    for day, slots in sending_windows.items():
        for slot in slots:
            if slot.start and slot.end:
                has_valid_slot = True

                if slot.start>= slot.end:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid time range in {day}"
                    )

    if not has_valid_slot:
        raise HTTPException(
            status_code=400,
            detail="At least one valid sending window required"
        )