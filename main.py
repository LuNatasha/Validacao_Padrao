from comparador import canal, comparar_ssim
from PIL import Image

ip = "192.168.1.108"
x = int(input('Escolha o canal para realizar a validação\n'
              '1 - CH1\n'
              '2 - CH2\n'
              '3 - ch3\n'
              'Escolha a opção: '))
img2 = canal(ip, x)

if img2 is None:
    print("Não foi possível obter a imagem do DVR.")
    exit()

img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")
ssim_score = comparar_ssim(img1, img2)


