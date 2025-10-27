def side_view_prompt(side: str, gender: str = "none"):
    if gender == "man":
        her_him = "him"
        her_his = "his"
    elif gender == "woman":
        her_him = "her"
        her_his = "her"
    else:
        her_him = "their"
        her_his = "his"
    prompt = f"""Rotate the person in the image approximately 30 degrees to the {side}, so that the camera sees {her_him} front-{side} side.  
Keep {her_his} body shape, hairstyle, facial features, and clothing consistent with the original.  
The new image should show {her_him} from a slightly turned front-{side} angle, with natural lighting and realistic perspective.
"""
    return prompt