from PIL import Image, ImageChops
import numpy as np
import requests
from io import BytesIO
from requests.auth import HTTPDigestAuth

url = "http://192.168.1.108/cgi-bin/snapshot.cgi?channel=2&type=0"
auth = HTTPDigestAuth('admin', 'admin123')

response = requests.get(url, auth=auth)

if response.status_code == 200:
    img2 = Image.open(BytesIO(response.content))

else:
    print(f"Erro ao acessar DVR: {response.status_code}")


def comparacao(im1, im2):
    im1 = im1.convert("RGB")
    im2 = im2.convert("RGB")

    if im1.size != im2.size:
        im2 = im2.resize(im1.size)

    diff = ImageChops.difference(im1, im2)
    diff_array = np.array(diff, dtype=np.int32)

    # A diferença máxima por canal é 255, e temos 3 canais (RGB)
    max_diff_por_pixel = 255 * 3

    # Média da soma das diferenças por pixel (canal R+G+B)
    media_diff = np.mean(diff_array.sum(axis=2))

    return media_diff

img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")

media_diff = comparacao(img1, img2)

print(f"As imagens têm {media_diff} de similaridade.")

if media_diff < 45:
    print("APROVADO")
else:
    print("REPROVADO")