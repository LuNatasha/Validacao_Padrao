from comparador import canal, comparar_ssim
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
from datetime import datetime
import time
import tkinter as tk
import logging
import os
from tkinter import ttk

class SistemaValidacaoSSIM:
    def __init__(self):
        self.ip = "192.168.1.108"

        # Criar diretório para logs se não existir
        self.logs_dir = "logs_validacao"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

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

        self.valores_processados = {}
        self.canais_processando = {}

        # Dicionário para armazenar loggers individuais
        self.loggers_individuais = {}

        self.setup_interface()
        self.varificacao()

    def criar_logger_individual(self, ns):
        ns = ns.strip()
        if not ns:
            raise ValueError("NS inválido: vazio.")

        ns_limpo = "".join(c for c in ns if c.isalnum() or c in ('-', '_')).rstrip()
        ns_limpo = ns_limpo[2:15]

        # Criar subpasta com a data atual
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        pasta_dia = os.path.join(self.logs_dir, data_hoje)

        if not os.path.exists(pasta_dia):
            os.makedirs(pasta_dia)

        timestamp = datetime.now().strftime("%H-%M-%S")
        nome_arquivo = f"{ns_limpo}_{timestamp}.log"
        caminho_arquivo = os.path.join(pasta_dia, nome_arquivo)

        logger = logging.getLogger(f"logger_{ns}_{timestamp}")
        logger.setLevel(logging.INFO)

        # Limpa handlers anteriores, se existirem
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)

        handler = logging.FileHandler(caminho_arquivo, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.propagate = False

        logger.info(f"Iniciando validação para NS: {ns}")
        logger.info(f"Arquivo de log: {nome_arquivo}")

        return logger

    def carregar_logo(self):
        try:
            img = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\logo.png")
            img.thumbnail((600, 500), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            return True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            return False

    def imagem_ta_preta(self, img_pil, canal_id):
        img_np = np.array(img_pil.convert('L'))  # Converte para tons de cinza
        media = img_np.mean()
        print(f"Canal {canal_id:02d} - Média de brilho: {media:.2f}")
        return media < 18.50

    def verificar_automaticamente(self):
        while True:
            for canal_id in range(1, 11):
                img = canal(self.ip, canal_id)
                if img is None:
                    self.labels_resultado[canal_id].config(text="ERRO", fg="red", bg=self.COR_FUNDO)
                    continue

                if self.imagem_ta_preta(img, canal_id):  # <- Passa o canal_id aqui
                    self.labels_resultado[canal_id].config(text="SEM IMAGEM", fg="white", bg=self.COR_STATUS_SEMIMAGEM)

                    # Limpa controles quando perde imagem
                    if canal_id in self.valores_processados:
                        del self.valores_processados[canal_id]
                    self.canais_processando[canal_id] = False
                    self.entradas_canais[canal_id].delete(0, tk.END)

                else:
                    texto_atual = self.labels_resultado[canal_id].cget("text")
                    # Se estava sem imagem/erro e agora tem imagem, muda para AGUARDANDO
                    if texto_atual in ["SEM IMAGEM", "ERRO"]:
                        self.labels_resultado[canal_id].config(text="AGUARDANDO", fg="black",
                                                               bg=self.COR_STATUS_AGUARDANDO)

                        # Verifica se já tem NS digitado e inicia processamento automaticamente
                        ns_atual = self.entradas_canais[canal_id].get().strip()
                        if ns_atual and canal_id not in self.canais_processando:
                            self.valores_processados[canal_id] = ns_atual
                            self.iniciar_processo(canal_id, automatico=True)

            time.sleep(1)
    def callback_entrada(self, var_name, index, mode, canal):
        texto_atual = self.vars_canais[canal].get().strip()

        if not texto_atual:
            if canal in self.valores_processados:
                del self.valores_processados[canal]
            return

        if self.canais_processando.get(canal, False):
            return

        if canal in self.valores_processados and self.valores_processados[canal] == texto_atual:
            return

        # Verifica se o canal está em estado válido para processar
        status_atual = self.labels_resultado[canal].cget("text")
        if status_atual == "AGUARDANDO":
            self.valores_processados[canal] = texto_atual
            self.iniciar_processo(canal, automatico=True)  # Indica que é automático
        else:
            # Se não estiver pronto, apenas armazena o valor
            self.valores_processados[canal] = texto_atual

    def iniciar_processo(self, canal_escolhido, automatico=False):
        # Verificar se há texto na entrada
        ns = self.entradas_canais[canal_escolhido].get().strip()
        if not ns:
            if not automatico:  # Só mostra erro se for acionamento manual
                messagebox.showerror("Erro", "Por favor, preencha o campo NS!")
            return

        # Verificar se o canal não está em estado de erro ou sem imagem (só para manual)
        if not automatico:
            texto_status = self.labels_resultado[canal_escolhido].cget("text")
            if texto_status in ["SEM IMAGEM", "ERRO"]:
                messagebox.showerror("Erro", "Aguarde o produto ser inicializado! Status atual: " + texto_status)
                return

        # Verificar se já não está processando
        if self.canais_processando.get(canal_escolhido, False):
            return

        self.canais_processando[canal_escolhido] = True
        self.labels_resultado[canal_escolhido].config(text="PROCESSANDO...", fg="white", bg="orange")
        
        self.janela.after(200000, lambda: self.mostrar_resultado(canal_escolhido))

    def mostrar_resultado(self, canal_escolhido):
        valor_entrada = self.entradas_canais[canal_escolhido].get()
        if valor_entrada.strip():
            texto_atual = self.labels_resultado[canal_escolhido].cget("text")

            if texto_atual in ["SEM IMAGEM", "ERRO"]:
                messagebox.showerror("Erro", "Produto ainda não foi inicializado!")
                self.entradas_canais[canal_escolhido].delete(0, tk.END)
                self.canais_processando[canal_escolhido] = False
                return

            img2 = canal(self.ip, canal_escolhido)
            if img2 is None:
                self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red")
                self.canais_processando[canal_escolhido] = False
                return

            img1 = Image.open(r"C:\Users\lu063249\PythonProject\TesteValidacao\Imagem_padrao.jpeg")
            ssim_score = comparar_ssim(img1, img2)

            ns = self.entradas_canais[canal_escolhido].get().strip()
            if not ns:
                messagebox.showerror("Erro", "NS inválido. Campo vazio.")
                self.canais_processando[canal_escolhido] = False
                return

            if ssim_score > 0.80:
                resultado = "APROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_OK
                logger = self.criar_logger_individual(ns)
                logger.info(f"{canal_escolhido}")
                logger.info(f"{ssim_score:.4f}")
                logger.info(f"APROVADO")
            else:
                resultado = "REPROVADO"
                cor_txt = "white"
                cor_bg = self.COR_STATUS_NOK
                logger = self.criar_logger_individual(ns)
                logger.info(f"{canal_escolhido}")
                logger.info(f"{ssim_score:.4f}")
                logger.info(f"REPROVADO")

            self.labels_resultado[canal_escolhido].config(text=resultado, fg=cor_txt, bg=cor_bg)
            logger.info(f"Processamento concluído para NS: {ns}")

        else:
            messagebox.showerror("Erro", "Por favor, preencha o campo!")

        self.canais_processando[canal_escolhido] = False

    def setup_interface(self):
        self.janela = tk.Tk()
        self.janela.title("TESTE DE VERIFICA")
        self.janela.geometry("1000x780")
        self.janela.configure(bg=self.COR_FUNDO)

        if self.carregar_logo():
            logo_label = tk.Label(self.janela, image=self.logo_image, bg=self.COR_FUNDO)
            logo_label.place(x=200, y=610)

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

        frame_modelo = tk.Frame(self.janela, bg=self.COR_FUNDO)
        frame_modelo.place(x=10, y=100)  # 10 pixels da esquerda e 10 pixels do topo

        tk.Label(frame_modelo, text="MODELO:", bg=self.COR_FUNDO, fg=self.COR_FONTE,
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=5)

        # Cria o Combobox
        self.combobox_modelos = ttk.Combobox(frame_modelo, state="readonly")
        self.combobox_modelos['values'] = ["4140031 - 4K", "4140032 - STICK", "4140033 - FULL HD",
                                           "4140040 - DONGLE 4k"]
        self.combobox_modelos.current(0)
        self.combobox_modelos.pack(side=tk.LEFT, padx=5)

        # Variável que armazenará o modelo selecionado
        self.modelo_selecionado = self.combobox_modelos.get()

        # Botão para atualizar o modelo selecionado
        botao_atualizar = tk.Button(frame_modelo, text="ATUALIZAR", font=("Segoe UI", 11, "bold"),
                                    bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                                    command=self.atualizar_modelo)
        botao_atualizar.pack(side=tk.LEFT, padx=5)

    def atualizar_modelo(self):
        self.modelo_selecionado = self.combobox_modelos.get()
        messagebox.showinfo("Atualizado", f"Modelo selecionado: {self.modelo_selecionado}")

    def cabecalho(self, frame):
        headers = ["CANAL", "STATUS", "NS/MAC1/MAC2", "EXECUTAR"]
        widths = [8, 15, 20, 10]

        for col, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=header, font=("Segoe UI", 12, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=width, borderwidth=0, relief="flat").grid(
                row=0, column=col, padx=10, pady=10)

    def canais(self, frame):
        self.vars_canais = {}

        for i in range(1, 11):
            canal_nome = f"CH{i:02d}"

            tk.Label(frame, text=canal_nome, font=("Segoe UI", 11, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=8).grid(
                row=i, column=0, padx=10, pady=5)

            status_label = tk.Label(frame, text="AGUARDANDO", font=("Segoe UI", 11),
                                    bg=self.COR_STATUS_AGUARDANDO, fg="black",
                                    width=15, relief="groove")
            status_label.grid(row=i, column=1, padx=10, pady=5)
            self.labels_resultado[i] = status_label

            var = tk.StringVar()
            entrada = tk.Entry(frame, font=("Segoe UI", 11), width=60, textvariable=var)
            entrada.grid(row=i, column=2, padx=10, pady=5)
            self.entradas_canais[i] = entrada
            self.vars_canais[i] = var
            var.trace_add('write', lambda var_name, index, mode, canal=i:
            self.callback_entrada(var_name, index, mode, canal))

            botao = tk.Button(frame, text="START", font=("Segoe UI", 11, "bold"),
                              bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                              command=lambda c=i: self.iniciar_processo(c, automatico=False))
            botao.grid(row=i, column=3, padx=10, pady=5)

    def varificacao(self):
        threading.Thread(target=self.verificar_automaticamente, daemon=True).start()

    def executar(self):
        try:
            self.janela.mainloop()
        finally:
            # Fechar todos os loggers ao sair
            for logger in self.loggers_individuais.values():
                for handler in logger.handlers:
                    handler.close()


if __name__ == "__main__":
    app = SistemaValidacaoSSIM()
    app.executar()