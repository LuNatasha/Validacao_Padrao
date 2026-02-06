from PIL import Image
from math import log2
import numpy as np
import requests
from io import BytesIO
from requests.auth import HTTPDigestAuth
from skimage.metrics import structural_similarity as ssim
import cv2


def canal(ip, x):

    url = f"http://{ip}/cgi-bin/snapshot.cgi?channel={x}&type=0"
    auth = HTTPDigestAuth('admin', 'admin123')

    try:
        response = requests.get(url, auth=auth, timeout=10)

        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            print(f"Erro ao acessar DVR no canal {x}: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão no canal {x}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado no canal {x}: {e}")
        return None


def comparar_ssim(im1, im2):

    try:
        # Converte para escala de cinza
        im1 = im1.convert("L")
        im2 = im2.convert("L")

        # Converte para arrays numpy
        im1_array = np.array(im1)
        im2_array = np.array(im2)

        # Ajusta o tamanho se necessário
        if im1_array.shape != im2_array.shape:
            im2_array = cv2.resize(im2_array, (im1_array.shape[1], im1_array.shape[0]))

        # Calcula SSIM
        score, _ = ssim(im1_array, im2_array, full=True)
        return score

    except Exception as e:
        print(f"Erro ao comparar imagens: {e}")
        return 0.0


def validar_conexao_dvr(ip):

    try:
        # Testa conexão com o canal 1
        teste_img = canal(ip, 1)
        return teste_img is not None
    except:
        return False


def obter_info_imagem(img):

    if img is None:
        return None

    return {
        'tamanho': img.size,
        'modo': img.mode,
        'formato': img.format,
        'brilho_medio': np.array(img.convert('L')).mean()
    }

def calcular_entropia(img):
    if img is None:
        return 0.0
    gray = img.convert('L')  # Converte para escala de cinza
    arr = np.array(gray)

    # Calcula histograma e normaliza para obter probabilidades
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    total_pixels = hist.sum()
    if total_pixels == 0:
        return 0.0

    probs = hist / total_pixels

    # Calcula entropia com a fórmula correta
    entropia = -np.sum([p * log2(p) for p in probs if p > 0])

    return entropia