# import requests
# import urllib.parse
#
# ASPECT_RATIOS = {
#     "1:1": (1024, 1024),
#     "16:9": (1920, 1080),
#     "9:16": (1080, 1920),
#     "4:3": (1600, 1200),
#     "3:4": (1200, 1600),
#     "21:9": (2560, 1080),
#     "2:3": (1365, 2048),
#     "3:2": (2048, 1365),
# }
#
# def generate_image(
#     prompt: str,
#     aspect_ratio: str,
#     output_file: str = "generated_image.jpg",
#     seed: int = 42,
#     model: str = "flux",
# ):
#     if aspect_ratio not in ASPECT_RATIOS:
#         raise ValueError(
#             f"Invalid aspect_ratio. Allowed values: {list(ASPECT_RATIOS.keys())}"
#         )
#
#     width, height = ASPECT_RATIOS[aspect_ratio]
#
#     params = {
#         "width": width,
#         "height": height,
#         "seed": seed,
#         "model": model,
#         "enhance": "true",
#         "maxSideLength": max(width, height),
#         "nologo": "true",
#     }
#
#     encoded_prompt = urllib.parse.quote(prompt)
#     url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
#
#     response = requests.get(url, params=params, timeout=300)
#     response.raise_for_status()
#
#     with open(output_file, "wb") as f:
#         f.write(response.content)
#
#     return output_file



import requests
import urllib.parse

ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "4:3": (1600, 1200),
    "3:4": (1200, 1600),
    "21:9": (2560, 1080),
    "2:3": (1365, 2048),
    "3:2": (2048, 1365),
}

def generate_image(
    prompt: str,
    aspect_ratio: str,
    output_file: str = "generated_image.jpg",
    seed: int = 42,
    model: str = "flux",
):
    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(
            f"Invalid aspect_ratio. Allowed values: {list(ASPECT_RATIOS.keys())}"
        )

    width, height = ASPECT_RATIOS[aspect_ratio]

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
