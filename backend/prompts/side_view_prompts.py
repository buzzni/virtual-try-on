def side_view_prompt(side: str):
    prompt = f"""
    Rotate the person in the image approximately 30 degrees to the {side},
    as if the camera is viewing her from a front-side angle.
    Keep her body shape, hairstyle, facial features, and clothing consistent with the original.
    The new image should show her from a slightly turned angle, with natural lighting and realistic perspective.
    """
    return prompt