from PIL import Image
import numpy as np
import requests
from io import BytesIO
from requests.auth import HTTPDigestAuth
from skimage.metrics import structural_similarity as ssim
import cv2


url = "http://192.168.1.108/cgi-bin/snapshot.cgi?channel=2&type=0"
auth = HTTPDigestAuth('admin', 'admin123')

response = requests.get(url, auth=auth)

if response.status_code == 200:
    img2 = Image.open(BytesIO(response.content))
else:
    print(f"Erro ao acessar DVR: {response.status_code}")
    exit()

# Função para comparar usando SSIM
def comparar_ssim(im1, im2):
    im1 = im1.convert("L")  # Converte para escala de cinza
    im2 = im2.convert("L")

    im1_array = np.array(im1)
    im2_array = np.array(im2)

    if im1_array.shape != im2_array.shape:
        im2_array = cv2.resize(im2_array, (im1_array.shape[1], im1_array.shape[0]))

    score, _ = ssim(im1_array, im2_array, full=True)
    return score

# Abre a imagem padrão
img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")

# Compara as imagens
ssim_score = comparar_ssim(img1, img2)

print(f"SSIM Score: {ssim_score:.4f}")

# Define o limite de aprovação
if ssim_score > 0.80:
    print("APROVADO")
else:
    print("REPROVADO")