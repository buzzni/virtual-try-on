def assemble_model_prompt(*, type: str):
    front_prompt = """
        Generate a photorealistic image of a young woman wearing the outfit exactly as shown in the provided Source Image.
        The entire clothing provided in the Source Image must be fully visible within the frame. No part of the clothing should be cropped, cut off, or out of view.
        The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
        Create a model who matches this description: a young woman with a loose updo hairstyle and soft bangs, natural makeup with soft pink lips.
        Maintain realistic body proportions, gentle facial expression, and soft, even lighting that matches the clothing's visual tone.
        Place her in a minimalist, plain light gray background with no props, patterns, or textures.
        Lighting should be even and diffused, matching the direction implied by the outfit photo.
        Ensure the clothing drapes naturally on the model's body with realistic folds and contact shadows.
        Preserve accurate color balance and texture detail; avoid seams, blur, or artificial effects.
        Output a single high-resolution, full-body image in neutral, editorial style.
        """
    
    back_prompt = """
        Generate a photorealistic image of a young woman wearing the outfit exactly as shown in the provided Source Image.
        The clothing's design, pattern, color, fabric texture, and fit must be perfectly replicated with no alteration.
        The model must be shown from behind.
        Her entire back — from head to toe — must face the camera.
        Do **not** show her face, eyes, or any part of the front of her body.
        This image must be a **true back view** with the model completely turned away from the viewer, as if walking or standing with her back to the camera.
        A side or front angle is strictly prohibited.
        Create a model who matches this description: a young woman with a loose updo hairstyle and soft bangs visible from behind, natural makeup (not visible in this view), and soft pink lips (also not visible due to angle).
        Maintain realistic body proportions, soft posture, and even lighting that matches the outfit's visual tone.
        Ensure that the lighting direction is consistent with the Source Image and that shadows, folds, and fabric contact points look natural on the body.
        The background should be plain, minimalist, and light gray with no textures or props.
        The final image must be high-resolution and editorial in tone, with no artificial artifacts, blur, or face visible.
        """

    if type == "front":
        return front_prompt
    elif type == "back":
        return back_prompt
    else:
        raise ValueError(f"Invalid type: {type}")
    