
def side_view_prompt(side: str):
    prompt = f"""Rotate the person in the image approximately 45 degrees to the {side}, so that the camera sees her front-{side} side.  
Keep her body shape, hairstyle, facial features, and clothing consistent with the original.  
The new image should show her from a slightly turned front-{side} angle, with natural lighting and realistic perspective.
"""
    return prompt