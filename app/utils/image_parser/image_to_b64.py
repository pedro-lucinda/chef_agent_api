import base64

def image_to_b64(image_path: str) -> bytes:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        raise Exception(f"Error converting image to base64: {e}")
    

