import tkinter as tk
from PIL import Image
from comparador import canal, comparar_ssim
import numpy as np
import threading
import time

ip = "192.168.1.108"

labels_resultado = {}

def imagem_ta_preta(img_pil):
    img_np = np.array(img_pil.convert('L'))  # Converte para tons de cinza
    media = img_np.mean()
    return media < 20  # Considera imagem preta se for escura demais

def verificar_automaticamente():
    while True:
        for canal_id in range(1, 8):
            img = canal(ip, canal_id)
            if img is None:
                labels_resultado[canal_id].config(text="ERRO", fg="red")
                continue

            if imagem_ta_preta(img):
                labels_resultado[canal_id].config(text="SEM IMAGEM", fg="red")
            else:
                # Só muda para "Aguardando" se o texto atual for diferente (evita piscar desnecessário)
                if labels_resultado[canal_id].cget("text") != "Aguardando":
                    labels_resultado[canal_id].config(text="Aguardando", fg="black")
        time.sleep(1)  # Faz a verificação a cada 1,5 segundo

def mostrar_resultado(canal_escolhido):
    texto_atual = labels_resultado[canal_escolhido].cget("text")

    if texto_atual == "SEM IMAGEM" or texto_atual == "ERRO":
        return  # Não faz validação se estiver sem imagem

    img2 = canal(ip, canal_escolhido)
    if img2 is None:
        labels_resultado[canal_escolhido].config(text="ERRO", fg="red")
        return

    img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")
    ssim_score = comparar_ssim(img1, img2)

    if ssim_score > 0.80:
        resultado = "APROVADO"
        cor = "green"
    else:
        resultado = "REPROVADO"
        cor = "red"

    labels_resultado[canal_escolhido].config(text=resultado, fg=cor)

# Criar interface
janela = tk.Tk()
janela.title("Validação SSIM por Canal")

for i in range(1, 8):
    # Botão START
    botao = tk.Button(janela, text="START", font=("Arial", 14),
                      command=lambda c=i: mostrar_resultado(c))
    botao.grid(row=i - 1, column=3, padx=10, pady=10)

    # Label CH
    label_ch = tk.Label(janela, text=f"CH{i}", font=("Arial", 14),
                        borderwidth=2, relief="solid", padx=10, pady=5, width=3)
    label_ch.grid(row=i - 1, column=0, padx=10, pady=10)

    # Label de resultado
    label_resultado = tk.Label(janela, text="Aguardando", font=("Arial", 14),
                               borderwidth=2, relief="solid", padx=10, pady=5, width=12)
    label_resultado.grid(row=i - 1, column=1, padx=10, pady=10)

    entrada = tk.Entry(janela, font=("Arial", 14))
    entrada.grid(row=i - 1, column=2, padx=10, pady=10)

    labels_resultado[i] = label_resultado

# Iniciar verificação automática em thread separada
threading.Thread(target=verificar_automaticamente, daemon=True).start()

janela.mainloop()
