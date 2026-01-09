import requests
import urllib.parse

def generate_image(
    prompt: str,
    width: int,
    height: int,
    output_file: str = "generated_image.jpg",
    seed: int = 42,
    model: str = "flux",
):
    params = {
        "width": width,
        "height": height,
        "seed": seed,
        "model": model,
        "enhance": "true",
        "maxSideLength": max(width, height),
        "nologo": "true",
    }

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    response = requests.get(url, params=params, timeout=300)
    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    return output_file
