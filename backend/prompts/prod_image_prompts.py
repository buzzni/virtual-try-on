DEFAULT_PROMPT = """Generate a high-resolution, studio-lit product photograph of the clothing from Image.
Transform the clothing into a perfectly smooth, wrinkle-free, and symmetrically flattened garment.
Place it neatly against a pure white, shadowless background. Remove any visible tags, labels, or price stickers and hangers from the garment.
The lighting should be soft, even, and professionally diffused, highlighting the fabric's texture and details like the buttons and collar with sharp focus.
"""

REMOVE_MANNEQUIN_PROMPT = """Generate a high-resolution, studio-lit product photograph of the clothing from Image.
Remove the mannequin completely, reconstructing any hidden parts of the garment so that only the clothing remains visible.
Transform the clothing into a perfectly smooth, wrinkle-free, and symmetrically flattened garment.
Place it neatly against a pure white, shadowless background.
Remove any visible tags, labels, or price stickers from the garment.
The lighting should be soft, even, and professionally diffused, highlighting the fabric’s texture and details like the buttons and collar with sharp focus.
"""

REMOVE_PERSON_PROMPT = """Generate a high-resolution, studio-lit product photograph of the clothing from Image.
Remove the person wearing the garment completely, reconstructing any hidden parts of the clothing so that only the garment remains visible.
Transform the clothing into a perfectly smooth, wrinkle-free, and symmetrically flattened garment.
Place it neatly against a pure white, shadowless background.
Remove any visible tags, labels, or price stickers from the garment.
The lighting should be soft, even, and professionally diffused, highlighting the fabric’s texture and details like the buttons and collar with sharp focus.
"""

def product_image_prompt(type: str):
    if type == "default":
        return DEFAULT_PROMPT
    elif type == "mannequin":
        return REMOVE_MANNEQUIN_PROMPT
    elif type == "person":
        return REMOVE_PERSON_PROMPT
    else:
        raise ValueError(f"Invalid type: {type}")