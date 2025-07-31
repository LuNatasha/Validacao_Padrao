from comparador import canal, comparar_ssim
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
import time
import tkinter as tk
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='validacao.log'
)


class SistemaValidacaoSSIM:
    def __init__(self):
        self.ip = "192.168.1.108"

        # Cores do tema
        self.COR_FUNDO = "#000000"
        self.COR_FONTE = "#ffffff"
        self.COR_LABEL = "#000000"
        self.COR_STATUS_BG = "#3d3d5c"
        self.COR_BOTAO = "#00B140"
        self.logo_image = None
        # Cores de status
        self.COR_STATUS_AGUARDANDO = "#FFC107"  # Amarelo
        self.COR_STATUS_OK = "#4CAF50"  # Verde
        self.COR_STATUS_NOK = "#F44336"  # Vermelho
        self.COR_STATUS_SEMIMAGEM = "#0000FF"  # azul

        self.labels_resultado = {}
        self.entradas_canais = {}

        # Controle para evitar múltiplas execuções
        self.valores_processados = {}  # Armazena último valor processado por canal
        self.canais_processando = {}  # Flag para saber se canal está processando

        self.setup_interface()
        self.varificacao()

    def carregar_logo(self):
        try:
            img = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\logo.png")
            img.thumbnail((600, 500), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            return True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            return False

    def imagem_ta_preta(self, img_pil):
        # nivel da imagem escura
        img_np = np.array(img_pil.convert('L'))  # Converte para tons de cinza
        media = img_np.mean()
        return media < 17

    def verificar_automaticamente(self):
        # verifica os status do canal
        while True:
            for canal_id in range(1, 9):
                img = canal(self.ip, canal_id)
                if img is None:
                    self.labels_resultado[canal_id].config(text="ERRO", fg="red")
                    continue

                if self.imagem_ta_preta(img):
                    self.labels_resultado[canal_id].config(text="SEM IMAGEM", fg="white", bg=self.COR_STATUS_SEMIMAGEM)
                    self.entradas_canais[canal_id].delete(0, tk.END)
                    # Limpa controles quando deleta entrada
                    if canal_id in self.valores_processados:
                        del self.valores_processados[canal_id]
                    self.canais_processando[canal_id] = False

                else:
                    texto_atual = self.labels_resultado[canal_id].cget("text")
                    if texto_atual in ["SEM IMAGEM", "ERRO"]:
                        self.labels_resultado[canal_id].config(text="AGUARDANDO", fg="black",
                                                               bg=self.COR_STATUS_AGUARDANDO)

            time.sleep(1)

    def callback_entrada(self, var_name, index, mode, canal):
        """Callback que é chamado a cada mudança no campo de entrada"""
        texto_atual = self.vars_canais[canal].get().strip()

        # Se o campo está vazio, limpa o controle
        if not texto_atual:
            if canal in self.valores_processados:
                del self.valores_processados[canal]
            return

        # Verifica se já está processando este canal
        if self.canais_processando.get(canal, False):
            return

        # Verifica se este valor já foi processado
        if canal in self.valores_processados and self.valores_processados[canal] == texto_atual:
            return

        # Se chegou até aqui, é um valor novo - processa
        self.valores_processados[canal] = texto_atual
        self.iniciar_processo(canal)

    def iniciar_processo(self, canal_escolhido):
        # Marca que este canal está processando
        self.canais_processando[canal_escolhido] = True

        # Atualiza o label para 'PROCESSANDO...'
        self.labels_resultado[canal_escolhido].config(text="PROCESSANDO...", fg="white", bg="orange")

        # Agenda a execução da mostrar_resultado depois de 50 segundos (50000 ms)
        self.janela.after(50000, lambda: self.mostrar_resultado(canal_escolhido))

    def mostrar_resultado(self, canal_escolhido):
        # validação por canal
        valor_entrada = self.entradas_canais[canal_escolhido].get()
        if valor_entrada.strip():
            texto_atual = self.labels_resultado[canal_escolhido].cget("text")

            if texto_atual in ["SEM IMAGEM", "ERRO"]:
                messagebox.showerror("Erro", "Produto ainda não foi inicializado!")
                self.entradas_canais[canal_escolhido].delete(0, tk.END)
                # Libera o canal para novo processamento
                self.canais_processando[canal_escolhido] = False
                return

            img2 = canal(self.ip, canal_escolhido)
            if img2 is None:
                self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red")
                # Libera o canal para novo processamento
                self.canais_processando[canal_escolhido] = False
                return

            img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")

            ssim_score = comparar_ssim(img1, img2)

            if ssim_score > 0.80:
                resultado = "APROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_OK
                ns = self.entradas_canais[canal_escolhido].get()
                logging.info(f"{ns} - VALOR = {ssim_score} - APROVADO")
            else:
                resultado = "REPROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_NOK
                ns = self.entradas_canais[canal_escolhido].get()
                logging.info(f"{ns} - VALOR = {ssim_score} - REPROVADO")

            self.labels_resultado[canal_escolhido].config(text=resultado, fg=cor_txt, bg=cor_bg)
        else:
            messagebox.showerror("Erro", "Por favor, preencha o campo!")

        # Libera o canal para novo processamento
        self.canais_processando[canal_escolhido] = False

    def setup_interface(self):
        # Janela principal
        self.janela = tk.Tk()
        self.janela.title("TESTE DE VERIFICA")
        self.janela.geometry("1000x720")
        self.janela.configure(bg=self.COR_FUNDO)

        if self.carregar_logo():
            logo_label = tk.Label(self.janela, image=self.logo_image, bg=self.COR_FUNDO)
            logo_label.place(x=200, y=560)

        # Título
        titulo = tk.Label(self.janela, text="TESTE DE VERIFICAÇÃO",
                          font=("Segoe UI", 22, "bold"),
                          bg=self.COR_FUNDO, fg=self.COR_FONTE)
        titulo.pack(pady=20)

        # Frame principal
        frame = tk.Frame(self.janela, bg=self.COR_LABEL, bd=0, relief="ridge")
        frame.pack(pady=10, padx=20)

        self.cabecalho(frame)
        self.canais(frame)

    def cabecalho(self, frame):
        headers = ["CANAL", "STATUS", "NS/MAC1/MAC2", "EXECUTAR"]
        widths = [8, 15, 20, 10]

        for col, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=header, font=("Segoe UI", 12, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=width, borderwidth=0, relief="flat").grid(
                row=0, column=col, padx=10, pady=10)

    def canais(self, frame):
        self.vars_canais = {}

        for i in range(1, 9):
            canal_nome = f"CH{i:02d}"

            # Nome do canal
            tk.Label(frame, text=canal_nome, font=("Segoe UI", 11, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=8).grid(
                row=i, column=0, padx=10, pady=5)

            # Label de status
            status_label = tk.Label(frame, text="AGUARDANDO", font=("Segoe UI", 11),
                                    bg=self.COR_STATUS_AGUARDANDO, fg="black",
                                    width=15, relief="groove")
            status_label.grid(row=i, column=1, padx=10, pady=5)
            self.labels_resultado[i] = status_label

            # Entrada SSIM
            var = tk.StringVar()
            entrada = tk.Entry(frame, font=("Segoe UI", 11), width=60, textvariable=var)
            entrada.grid(row=i, column=2, padx=10, pady=5)
            self.entradas_canais[i] = entrada
            self.vars_canais[i] = var

            # Callback modificado - agora com delay
            var.trace_add('write', lambda var_name, index, mode, canal=i:
            self.callback_entrada(var_name, index, mode, canal))

            # Botão START
            botao = tk.Button(frame, text="START", font=("Segoe UI", 11, "bold"),
                              bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                              command=lambda c=i: self.iniciar_processo(c))
            botao.grid(row=i, column=3, padx=10, pady=5)

    def varificacao(self):
        threading.Thread(target=self.verificar_automaticamente, daemon=True).start()

    def executar(self):
        self.janela.mainloop()


if __name__ == "__main__":
    app = SistemaValidacaoSSIM()
    app.executar()