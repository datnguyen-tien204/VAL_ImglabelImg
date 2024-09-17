import requests
import os
url = "https://raw.githubusercontent.com/matlab-deep-learning/pretrained-yolo-v4/main/src/%2Bhelper/coco-classes.txt"
filename = "classes.txt"
def get_classestxt(original_root: str):
    filepath = os.path.join(original_root, filename)
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, "w") as file:
            file.write(response.text)
