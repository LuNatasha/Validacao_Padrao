import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
import time
from comparador import canal, comparar_ssim


class SistemaValidacaoSSIM:
    def __init__(self):
        self.ip = "192.168.1.108"

        # Cores do tema
        self.COR_FUNDO = "#000000"
        self.COR_FONTE = "#ffffff"
        self.COR_LABEL = "#2b2b3d"
        self.COR_STATUS_BG = "#3d3d5c"
        self.COR_BOTAO = "#4caf50"
        self.logo_image = None
        # Cores de status
        self.COR_STATUS_AGUARDANDO = "#FFC107"  # Amarelo
        self.COR_STATUS_OK = "#4CAF50"  # Verde
        self.COR_STATUS_NOK = "#F44336"  # Vermelho
        self.COR_STATUS_SEMIMAGEM = "#0000FF"  #azul

        self.labels_resultado = {}
        self.entradas_canais = {}

        self.setup_interface()
        self.varificacao()

    def carregar_logo(self):
        """Carrega e redimensiona o logo"""
        try:
            # Substitua pelo caminho da sua imagem
            img = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\logo2.png")
            # Redimensiona para ficar proporcional (largura máxima 200px)
            img.thumbnail((200, 100), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            return True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            return False

    def imagem_ta_preta(self, img_pil):
       #nivel da imagem escura
        img_np = np.array(img_pil.convert('L'))  # Converte para tons de cinza
        media = img_np.mean()
        return media < 17

    def verificar_automaticamente(self):
        #verifica os status do canal
        while True:
            for canal_id in range(1, 9):
                img = canal(self.ip, canal_id)
                if img is None:
                    self.labels_resultado[canal_id].config(text="ERRO", fg="red")
                    continue

                if self.imagem_ta_preta(img):
                    self.labels_resultado[canal_id].config(text="SEM IMAGEM", fg="white", bg = self.COR_STATUS_SEMIMAGEM)
                    self.entradas_canais[canal_id].delete(0, tk.END)

                else:
                    texto_atual = self.labels_resultado[canal_id].cget("text")
                    if texto_atual in ["SEM IMAGEM", "ERRO"]:
                        self.labels_resultado[canal_id].config(text="AGUARDANDO", fg="black", bg = self.COR_STATUS_AGUARDANDO)

            time.sleep(1)

    def mostrar_resultado(self, canal_escolhido):

        #validação por canal
        valor_entrada = self.entradas_canais[canal_escolhido].get()
        if valor_entrada.strip():
            texto_atual = self.labels_resultado[canal_escolhido].cget("text")

            if texto_atual in ["SEM IMAGEM", "ERRO"]:
                messagebox.showerror("Erro", "Produto ainda não foi inicializado!")
                self.entradas_canais[canal_escolhido].delete(0, tk.END)
                return

            img2 = canal(self.ip, canal_escolhido)
            if img2 is None:
                self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red")
                return

            img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")
            ssim_score = comparar_ssim(img1, img2)

            if ssim_score > 0.80:
                resultado = "APROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_OK
            else:
                resultado = "REPROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_NOK

            self.labels_resultado[canal_escolhido].config(text=resultado,fg = cor_txt, bg = cor_bg)
        else:
            messagebox.showerror("Erro", "Por favor, preencha o campo!")

    def setup_interface(self):

        # Janela principal
        self.janela = tk.Tk()
        self.janela.title("INTELBRAS")
        self.janela.geometry("1000x800")
        self.janela.configure(bg=self.COR_FUNDO)

        if self.carregar_logo():
            logo_label = tk.Label(self.janela, image=self.logo_image, bg=self.COR_FUNDO)
            logo_label.pack(pady=10)

        # Título
        titulo = tk.Label(self.janela, text="INTELBRAS",
                          font=("Segoe UI", 22, "bold"),
                          bg=self.COR_FUNDO, fg=self.COR_FONTE)
        titulo.pack(pady=20)

        # Frame principal
        frame = tk.Frame(self.janela, bg=self.COR_LABEL, bd=2, relief="ridge")
        frame.pack(pady=10, padx=20)

        self.cabecalho(frame)
        self.canais(frame)

    def cabecalho(self, frame):

        headers = ["Canal", "Status", "NS/MAC1/MAC2", "Ação"]
        widths = [8, 15, 20, 10]

        for col, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=header, font=("Segoe UI", 12, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=width).grid(
                row=0, column=col, padx=10, pady=10)

    def canais(self, frame):

        for i in range(1, 9):
            canal_nome = f"CH{i:02d}"

            # Nome do canal
            tk.Label(frame, text=canal_nome, font=("Segoe UI", 11),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=8).grid(
                row=i, column=0, padx=10, pady=5)

            # Label de status
            status_label = tk.Label(frame, text="AGUARDANDO", font=("Segoe UI", 11),
                                    bg=self.COR_STATUS_AGUARDANDO, fg="black",
                                    width=15, relief="groove")
            status_label.grid(row=i, column=1, padx=10, pady=5)
            self.labels_resultado[i] = status_label

            # Entrada SSIM
            entrada = tk.Entry(frame, font=("Segoe UI", 11), width=60)
            entrada.grid(row=i, column=2, padx=10, pady=5)
            self.entradas_canais[i] = entrada

            # Botão START
            botao = tk.Button(frame, text="START", font=("Segoe UI", 11, "bold"),
                              bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                              command=lambda c=i: self.mostrar_resultado(c))
            botao.grid(row=i, column=3, padx=10, pady=5)

    def varificacao(self):

        threading.Thread(target=self.verificar_automaticamente, daemon=True).start()

    def executar(self):

        self.janela.mainloop()


if __name__ == "__main__":
    app = SistemaValidacaoSSIM()
    app.executar()