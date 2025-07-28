from PIL import Image
import numpy as np
import requests
from io import BytesIO
from requests.auth import HTTPDigestAuth
from skimage.metrics import structural_similarity as ssim
import cv2


def canal(ip, x):
    url = f"http://{ip}/cgi-bin/snapshot.cgi?channel={x}&type=0"
    auth = HTTPDigestAuth('admin', 'admin123')
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        img2 = Image.open(BytesIO(response.content))
        return img2

    else:
        print(f"Erro ao acessar DVR: {response.status_code}")
        exit()

def comparar_ssim(im1, im2):
    im1 = im1.convert("L")  # Converte para escala de cinza
    im2 = im2.convert("L")

    im1_array = np.array(im1)
    im2_array = np.array(im2)

    if im1_array.shape != im2_array.shape:
        im2_array = cv2.resize(im2_array, (im1_array.shape[1], im1_array.shape[0]))

    score, _ = ssim(im1_array, im2_array, full=True)
    return score
