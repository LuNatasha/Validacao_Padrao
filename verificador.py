from comparador import canal, comparar_ssim, calcular_entropia
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
from datetime import datetime
import time
import tkinter as tk
import logging
import os
import uuid
from tkinter import ttk
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed


class SistemaValidacaoSSIM:
    def __init__(self):
        self.after_ids = {}
        self.ip = "192.168.1.108"
        
        self.logs_dir = "logs_validacao"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        self.lock_logger = Lock()
        self.contador_logs = 0

        self.COR_FUNDO = "#000000"
        self.COR_FONTE = "#ffffff"
        self.COR_LABEL = "#000000"
        self.COR_STATUS_BG = "#3d3d5c"
        self.COR_BOTAO = "#00B140"
        self.logo_image = None

  
        self.COR_STATUS_AGUARDANDO = "#FFC107"  
        self.COR_STATUS_OK = "#4CAF50"
        self.COR_STATUS_NOK = "#F44336" 
        self.COR_STATUS_SEMIMAGEM = "#0000FF"  

        self.labels_resultado = {}
        self.entradas_canais = {}
        self.valores_processados = {}
        self.canais_processando = {}
        self.loggers_individuais = {}

        self.imagens_referencia = {
            "4140031 - 4K": r"C:\Users\linha.izzy\Documents\TesteValidacao\fotos\4K.png",
            "4140032 - STICK": r"C:\Users\linha.izzy\Documents\TesteValidacao\fotos\Stick.png",
            "4140033 - FULL HD": r"C:\Users\linha.izzy\Documents\TesteValidacao\fotos\FullHD.png",
            "4140040 - DONGLE 4k": r"C:\Users\linha.izzy\Documents\TesteValidacao\fotos\Dongle4k.png"
        }

        # Executor para análise simultânea
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.setup_interface()
        self.varificacao()

    
    def criar_logger_individual(self, ns, canal_id):
        """Versão otimizada com lock e identificador único"""
        with self.lock_logger:
            ns = ns.strip()
            if not ns:
                raise ValueError("NS inválido: vazio.")

            ns_limpo = "".join(c for c in ns if c.isalnum() or c in ('-', '_')).rstrip()
            ns_limpo = ns_limpo[2:15] if len(ns_limpo) > 2 else ns_limpo

            data_hoje = datetime.now().strftime("%Y-%m-%d")
            pasta_dia = os.path.join(self.logs_dir, data_hoje)
            if not os.path.exists(pasta_dia):
                os.makedirs(pasta_dia)

            timestamp = datetime.now().strftime("%H-%M-%S-%f")[:-3]
            self.contador_logs += 1

            nome_arquivo = f"{ns_limpo}_CH{canal_id:02d}_{timestamp}_{self.contador_logs}.log"
            caminho_arquivo = os.path.join(pasta_dia, nome_arquivo)

            logger_id = f"logger_{ns}_{canal_id}_{self.contador_logs}_{uuid.uuid4().hex[:8]}"
            logger = logging.getLogger(logger_id)
            logger.setLevel(logging.INFO)

            if logger.handlers:
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)

            handler = logging.FileHandler(
                caminho_arquivo,
                mode='w',
                encoding='utf-8',
                delay=False
            )
            handler.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False

            logger.info(f"Iniciando validação para NS: {ns}")
            logger.info(f"Canal: CH{canal_id:02d}")
            logger.info(f"Arquivo de log: {nome_arquivo}")

            handler.flush()

            self.loggers_individuais[f"{ns}_{canal_id}"] = logger
            return logger

    
    def carregar_logo(self):
        try:
            img = Image.open(r"C:\Users\linha.izzy\Documents\TesteValidacao\fotos\logo.png")
            img.thumbnail((600, 500), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            return True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            return False

    
    def imagem_ta_preta(self, img_pil, canal_id):
        img_np = np.array(img_pil.convert('L'))
        media = img_np.mean()
        entropia = calcular_entropia(img_pil)
        return media < 18.50 and entropia < 1.02

    def analisar_canal(self, canal_id):
        img = canal(self.ip, canal_id)
        if img is None:
            return canal_id, "ERRO"
        if self.imagem_ta_preta(img, canal_id):
            return canal_id, "SEM IMAGEM"
        return canal_id, "AGUARDANDO"


    def verificar_automaticamente(self):
        while True:
            futures = {self.executor.submit(self.analisar_canal, canal_id): canal_id for canal_id in range(1, 11)}
            for future in as_completed(futures):
                canal_id, status = future.result()
                label = self.labels_resultado[canal_id]
                entrada = self.entradas_canais[canal_id]

                if status == "ERRO":
                    label.config(text="ERRO", fg="red", bg=self.COR_FUNDO)

                elif status == "SEM IMAGEM":
                    label.config(text=status, fg="white", bg=self.COR_STATUS_SEMIMAGEM)
                    entrada.config(state="normal")
                    entrada.delete(0, tk.END)

                    if canal_id in self.valores_processados:
                        del self.valores_processados[canal_id]
                    self.canais_processando[canal_id] = False

                elif status == "AGUARDANDO":
                    texto_atual = label.cget("text")
                    if texto_atual in ["SEM IMAGEM", "ERRO"]:
                        label.config(text=status, fg="black", bg=self.COR_STATUS_AGUARDANDO)

                    entrada.config(state="normal")

                    ns_atual = entrada.get().strip()
                    if ns_atual and canal_id not in self.canais_processando:
                        self.valores_processados[canal_id] = ns_atual
                        self.iniciar_processo(canal_id, automatico=True)

                elif status in ["APROVADO", "REPROVADO"]:
                    entrada.config(state="disabled")

            time.sleep(0.005)

    # PROCESSAMENTO AUTOMATICO
    def callback_entrada(self, var_name, index, mode, canal):
        if canal in self.after_ids:
            self.janela.after_cancel(self.after_ids[canal])

        self.after_ids[canal] = self.janela.after(300, lambda: self.processar_entrada(canal))

    def processar_entrada(self, canal):
        texto_atual = self.vars_canais[canal].get().strip()
        if not texto_atual:
            if canal in self.valores_processados:
                del self.valores_processados[canal]
            return
        if self.canais_processando.get(canal, False):
            return
        if canal in self.valores_processados and self.valores_processados[canal] == texto_atual:
            return
        status_atual = self.labels_resultado[canal].cget("text")
        if status_atual == "AGUARDANDO":
            self.valores_processados[canal] = texto_atual
            self.iniciar_processo(canal, automatico=True)
        elif status_atual in ["SEM IMAGEM", "ERRO"]:
            messagebox.showerror("Erro", "Aguarde o produto ser inicializado!")
            self.entradas_canais[canal].delete(0, tk.END)
            if canal in self.valores_processados:
                del self.valores_processados[canal]
            return
        else:
            self.valores_processados[canal] = texto_atual

  
    def iniciar_processo(self, canal_escolhido, automatico=False):
        ns = self.entradas_canais[canal_escolhido].get().strip()
        if not ns:
            if not automatico:
                messagebox.showerror("Erro", "Por favor, preencha o campo NS!")
            return

        texto_status = self.labels_resultado[canal_escolhido].cget("text")
        if texto_status in ["APROVADO", "REPROVADO"]:
            if not automatico:
                messagebox.showwarning("Aviso", f"Campo bloqueado! Status atual: {texto_status}")
            return

        if self.canais_processando.get(canal_escolhido, False):
            return

        self.canais_processando[canal_escolhido] = True

      
        if self.modelo_selecionado not in self.imagens_referencia:
            messagebox.showerror("Erro", f"Modelo '{self.modelo_selecionado}' não configurado!")
            self.canais_processando[canal_escolhido] = False
            self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red", bg=self.COR_FUNDO)
            self.entradas_canais[canal_escolhido].config(state="normal")
            return

       
        self.mostrar_resultado(canal_escolhido)

    
    def mostrar_resultado(self, canal_escolhido):
        """Mostra resultado imediatamente após bipagem"""
        valor_entrada = self.entradas_canais[canal_escolhido].get()
        if not valor_entrada.strip():
            messagebox.showerror("Erro", "Por favor, preencha o campo!")
            self.canais_processando[canal_escolhido] = False
            self.entradas_canais[canal_escolhido].config(state="normal")
            return

        img2 = canal(self.ip, canal_escolhido)
        if img2 is None:
            self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red")
            self.canais_processando[canal_escolhido] = False
            self.entradas_canais[canal_escolhido].config(state="normal")
            return

        caminho_imagem_ref = self.imagens_referencia.get(self.modelo_selecionado)

        if not caminho_imagem_ref or not os.path.exists(caminho_imagem_ref):
            messagebox.showerror("Erro",
                                 f"Imagem de referência não encontrada para o modelo: {self.modelo_selecionado}")
            self.canais_processando[canal_escolhido] = False
            self.labels_resultado[canal_escolhido].config(text="ERRO", fg="red", bg=self.COR_FUNDO)
            self.entradas_canais[canal_escolhido].config(state="normal")
            return

        img1 = Image.open(caminho_imagem_ref)
        ssim_score = comparar_ssim(img1, img2)
        ns = self.entradas_canais[canal_escolhido].get().strip()

        if ssim_score > 0.75:
            resultado = "APROVADO"
            cor_txt = "white"
            cor_bg = self.COR_STATUS_OK
            print(f"\n\nRESULTADO CH{canal_escolhido:02d} - {ssim_score:.4f}\n")
        else:
            resultado = "REPROVADO"
            cor_txt = "white"
            cor_bg = self.COR_STATUS_NOK
            print(f"\n\nRESULTADO CH{canal_escolhido:02d} - {ssim_score:.4f}\n")

       
        try:
            logger = self.criar_logger_individual(ns, canal_escolhido)
            logger.info(f"Canal: CH{canal_escolhido:02d}")
            logger.info(f"Imagem de referência: {caminho_imagem_ref}")
            logger.info(f"SSIM: {ssim_score:.4f}")
            logger.info(f"Resultado: {resultado}")

            for handler in logger.handlers:
                handler.flush()
                handler.close()

        except Exception as e:
            print(f"Erro ao criar log para canal {canal_escolhido}: {e}")

        self.labels_resultado[canal_escolhido].config(text=resultado, fg=cor_txt, bg=cor_bg)
        self.canais_processando[canal_escolhido] = False

        # Bloqueia a entrada após resultado final
        if resultado in ["APROVADO", "REPROVADO"]:
            self.entradas_canais[canal_escolhido].config(state="disabled")
        else:
            self.entradas_canais[canal_escolhido].config(state="normal")

 
    def setup_interface(self):
        self.janela = tk.Tk()
        self.janela.title("TESTE DE VERIFICAÇÃO")
        self.janela.geometry("1000x780")
        self.janela.configure(bg=self.COR_FUNDO)

        if self.carregar_logo():
            logo_label = tk.Label(self.janela, image=self.logo_image, bg=self.COR_FUNDO)
            logo_label.place(x=200, y=645)

        titulo = tk.Label(self.janela, text="TESTE DE VERIFICAÇÃO", font=("Segoe UI", 22, "bold"),
                          bg=self.COR_FUNDO, fg=self.COR_FONTE)
        titulo.pack(pady=20)

        # Seletor de modelo
        frame_modelo = tk.Frame(self.janela, bg=self.COR_FUNDO)
        frame_modelo.pack(pady=(0, 15))

        tk.Label(frame_modelo, text="MODELO:", bg=self.COR_FUNDO, fg=self.COR_FONTE,
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=5)

        self.combobox_modelos = ttk.Combobox(frame_modelo, state="readonly")
        self.combobox_modelos['values'] = ["4140031 - 4K", "4140032 - STICK", "4140033 - FULL HD",
                                           "4140040 - DONGLE 4k"]
        self.combobox_modelos.current(0)
        self.combobox_modelos.pack(side=tk.LEFT, padx=5)
        self.modelo_selecionado = self.combobox_modelos.get()

        botao_atualizar = tk.Button(frame_modelo, text="ATUALIZAR", font=("Segoe UI", 11, "bold"),
                                    bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                                    command=self.atualizar_modelo)
        botao_atualizar.pack(side=tk.LEFT, padx=5)

        # Frame principal
        frame = tk.Frame(self.janela, bg=self.COR_LABEL, bd=0, relief="ridge")
        frame.pack(pady=10, padx=20)

        self.cabecalho(frame)
        self.canais(frame)

    def atualizar_modelo(self):
        self.modelo_selecionado = self.combobox_modelos.get()
        messagebox.showinfo("Atualizado", f"Modelo selecionado: {self.modelo_selecionado}")

    def cabecalho(self, frame):
        headers = ["CANAL", "STATUS", "NS/MAC1/MAC2", "EXECUTAR"]
        widths = [8, 15, 20, 10]
        for col, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=header, font=("Segoe UI", 12, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=width).grid(row=0, column=col, padx=10, pady=10)

    def canais(self, frame):
        self.vars_canais = {}
        self.callback_ids = {}
        for i in range(1, 11):
            canal_nome = f"CH{i:02d}"
            tk.Label(frame, text=canal_nome, font=("Segoe UI", 11, "bold"),
                     bg=self.COR_LABEL, fg=self.COR_FONTE, width=8).grid(row=i, column=0, padx=10, pady=5)
            status_label = tk.Label(frame, text="AGUARDANDO", font=("Segoe UI", 11),
                                    bg=self.COR_STATUS_AGUARDANDO, fg="black", width=15, relief="groove")
            status_label.grid(row=i, column=1, padx=10, pady=5)
            self.labels_resultado[i] = status_label

            var = tk.StringVar()
            entrada = tk.Entry(frame, font=("Segoe UI", 11), width=60, textvariable=var)
            entrada.grid(row=i, column=2, padx=10, pady=5)
            self.entradas_canais[i] = entrada
            self.vars_canais[i] = var

            callback_id = var.trace_add('write', lambda var_name, index, mode, canal=i:
            self.callback_entrada(var_name, index, mode, canal))
            self.callback_ids[i] = callback_id

            botao = tk.Button(frame, text="START", font=("Segoe UI", 11, "bold"),
                              bg=self.COR_BOTAO, fg="white", activebackground="#45a049",
                              command=lambda c=i: self.iniciar_processo(c, automatico=False))
            botao.grid(row=i, column=3, padx=10, pady=5)

    def varificacao(self):
        threading.Thread(target=self.verificar_automaticamente, daemon=True).start()

    def executar(self):
        """Execução otimizada com limpeza de recursos"""
        try:
            self.janela.mainloop()
        finally:
            for logger_key, logger in list(self.loggers_individuais.items()):
                for handler in logger.handlers[:]:
                    try:
                        handler.flush()
                        handler.close()
                        logger.removeHandler(handler)
                    except Exception as e:
                        print(f"Erro ao fechar handler: {e}")

            self.executor.shutdown(wait=False)


if __name__ == "__main__":
    app = SistemaValidacaoSSIM()
    app.executar()
