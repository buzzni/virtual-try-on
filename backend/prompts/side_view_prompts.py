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
    
    if side == "left" or side == "right":
        prompt = f"""Rotate the person in the image approximately 30 degrees to the {side}, so that the camera sees {her_him} front-{side} side.  
Keep {her_his} body shape, hairstyle, facial features, and clothing consistent with the original.  
The new image should show {her_him} from a slightly turned front-{side} angle, with natural lighting and realistic perspective.
Preserve the details of the garment using the second image.
"""
    else:
        prompt = f"""Rotate the person in the image 180 degrees, so that the camera sees {her_him} back side.  
Keep {her_his} body shape, hairstyle, facial features, and clothing consistent with the original.  
The new image should show {her_him} from a completely turned back angle, with natural lighting and realistic perspective.
Use the second image to create a realistic back view of the model.
"""
    return prompt