from PIL import Image, ImageChops
import numpy as np

def comparacao(im1, im2):
    im1 = im1.convert("RGB")
    im2 = im2.convert("RGB")

    if im1.size != im2.size:
        im2 = im2.resize(im1.size)

    diff = ImageChops.difference(im1, im2)
    diff.show()
    diff_array = np.array(diff, dtype=np.int32)

    max_diff_por_pixel = 255 * 3

    media_diff = np.mean(diff_array.sum(axis=2))

    return media_diff

img1 = Image.open(r"C:\Users\lu063249\Pictures\WhatsApp Image 2025-07-21 at 22.38.34 (2).jpeg")
img2 = str(input('Foto: ')).strip().strip('"')
img2 = Image.open(img2)

media_diff = comparacao(img1, img2)

print(f"As imagens têm {media_diff} de similaridade.")

if media_diff < 20:
    print("APROVADO")
else:
    print("REPROVADO")

