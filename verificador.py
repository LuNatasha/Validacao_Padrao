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
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple


class SistemaValidacaoSSIM:
    # Constantes da classe
    CORES = {
        'FUNDO': "#000000",
        'FONTE': "#ffffff",
        'LABEL': "#000000",
        'STATUS_BG': "#3d3d5c",
        'BOTAO': "#00B140",
        'AGUARDANDO': "#FFC107",
        'OK': "#4CAF50",
        'NOK': "#F44336",
        'SEM_IMAGEM': "#0000FF",
        'PROCESSANDO': "#FFA500"
    }

    MODELOS_CONFIG = {
        "4140031 - 4K": {
            'imagem': r"C:\Users\lu063249\projetos_luiza\TesteValidacao - Copia\fotos\FullHD_4K.png",
            'tempo_ms': 120000,
            'chars_ns': 54
        },
        "4140032 - STICK": {
            'imagem': r"C:\Users\lu063249\projetos_luiza\TesteValidacao - Copia\fotos\Stick.png",
            'tempo_ms': 120000,
            'chars_ns': 36
        },
        "4140033 - FULL HD": {
            'imagem': r"C:\Users\lu063249\projetos_luiza\TesteValidacao - Copia\fotos\FullHD_4K.png",
            'tempo_ms': 170000,
            'chars_ns': 54
        },
        "4140040 - DONGLE 4k": {
            'imagem': r"C:\Users\lu063249\projetos_luiza\TesteValidacao - Copia\fotos\Dongle.png",
            'tempo_ms': 90000,
            'chars_ns': 54
        }
    }

    def __init__(self):
        self.ip = "192.168.1.108"
        self.logs_dir = "logs_validacao"
        self.criar_diretorio_logs()

        # Estados dos canais
        self.estados_canais = {i: self.criar_estado_inicial() for i in range(1, 11)}

        # Interface
        self.labels_resultado = {}
        self.entradas_canais = {}
        self.vars_canais = {}
        self.loggers_individuais = {}
        self.logo_image = None

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.modelo_selecionado = "4140031 - 4K"
        self.setup_interface()
        self._iniciar_verificacao_automatica()

    def criar_estado_inicial(self) -> Dict:
        """Cria estado inicial para um canal"""
        return {
            'processando': False,
            'contagem_ativa': False,
            'tempo_inicio': None,
            'tempo_terminou': False,
            'ns_pendente': None,
            'after_id': None,
            'resultado_final': False  # NOVA FLAG PARA CONTROLAR SE JÁ PROCESSOU O RESULTADO FINAL
        }

    def criar_diretorio_logs(self):
        """Cria diretório de logs se não existir"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

    def get_config_modelo_atual(self) -> Dict:
        """Retorna configuração do modelo selecionado"""
        return self.MODELOS_CONFIG.get(self.modelo_selecionado, self.MODELOS_CONFIG["4140031 - 4K"])

    def criar_logger_individual(self, ns: str) -> logging.Logger:
        """Cria logger individual para um NS"""
        ns = ns.strip()
        if not ns:
            raise ValueError("NS inválido: vazio.")

        ns_limpo = "".join(c for c in ns if c.isalnum() or c in ('-', '_')).rstrip()
        ns_limpo = ns_limpo[2:15] if len(ns_limpo) > 15 else ns_limpo

        # Estrutura de diretórios por data
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        pasta_dia = os.path.join(self.logs_dir, data_hoje)
        if not os.path.exists(pasta_dia):
            os.makedirs(pasta_dia)

        timestamp = datetime.now().strftime("%H-%M-%S")
        nome_arquivo = f"{ns_limpo}_{timestamp}.log"
        caminho_arquivo = os.path.join(pasta_dia, nome_arquivo)

        # Configurar logger único
        logger_name = f"logger_{ns}_{timestamp}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Limpar handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        handler = logging.FileHandler(caminho_arquivo, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

        logger.info(f"Iniciando validação para NS: {ns}")
        logger.info(f"Modelo: {self.modelo_selecionado}")

        self.loggers_individuais[ns] = logger
        return logger

    def carregar_logo(self) -> bool:
        """Carrega logo da interface"""
        try:
            caminho_logo = r"C:\Users\lu063249\projetos_luiza\TesteValidacao - Copia\fotos\logo.png"
            img = Image.open(caminho_logo)
            img.thumbnail((600, 500), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            return True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            return False

    def validar_ns(self, ns: str) -> bool:
        """Valida formato do NS baseado no modelo"""
        config = self.get_config_modelo_atual()
        return len(ns.strip()) == config['chars_ns']

    def imagem_esta_preta(self, img_pil: Image.Image, canal_id: int) -> bool:
        """Detecta se imagem está preta"""
        img_np = np.array(img_pil.convert('L'))
        media = img_np.mean()
        entropia = calcular_entropia(img_pil)
        #print(f"Canal {canal_id:02d} - Brilho: {media:.2f} | Entropia: {entropia:.2f}")
        return media < 18.50 and entropia < 1.02

    def analisar_status_canal(self, canal_id: int) -> Tuple[int, str]:
        """Analisa status atual de um canal"""
        try:
            img = canal(self.ip, canal_id)
            if img is None:
                return canal_id, "ERRO"
            if self.imagem_esta_preta(img, canal_id):
                return canal_id, "SEM IMAGEM"
            return canal_id, "AGUARDANDO"
        except Exception as e:
            print(f"Erro ao analisar canal {canal_id}: {e}")
            return canal_id, "ERRO"

    def processar_ssim_canal(self, canal_id: int) -> Optional[Dict]:
        """Processa SSIM de um canal"""
        try:
            img2 = canal(self.ip, canal_id)
            if img2 is None:
                return None

            config = self.get_config_modelo_atual()
            caminho_img_padrao = config['imagem']

            if not os.path.exists(caminho_img_padrao):
                print(f"Imagem padrão não encontrada: {caminho_img_padrao}")
                return None

            img1 = Image.open(caminho_img_padrao)
            ssim_score = comparar_ssim(img1, img2)

            if ssim_score > 0.80:
                return {
                    "resultado": "APROVADO",
                    "ssim": ssim_score,
                    "cor_txt": "white",
                    "cor_bg": self.CORES['OK']
                }
            else:
                return {
                    "resultado": "REPROVADO",
                    "ssim": ssim_score,
                    "cor_txt": "white",
                    "cor_bg": self.CORES['NOK']
                }

        except Exception as e:
            print(f"Erro no processamento SSIM canal {canal_id}: {e}")
            return None

    def atualizar_interface_canal(self, canal_id: int, status: str, cor_bg: str = None, cor_fg: str = "black"):
        """Atualiza interface de um canal específico"""
        if cor_bg is None:
            cor_bg = {
                "AGUARDANDO": self.CORES['AGUARDANDO'],
                "SEM IMAGEM": self.CORES['SEM_IMAGEM'],
                "ERRO": self.CORES['FUNDO'],
                "PROCESSANDO": self.CORES['PROCESSANDO']
            }.get(status, self.CORES['FUNDO'])

        if status == "ERRO":
            cor_fg = "red"
        elif status == "SEM IMAGEM":
            cor_fg = "white"

        self.labels_resultado[canal_id].config(text=status, fg=cor_fg, bg=cor_bg)

    def limpar_estado_canal(self, canal_id: int):
        """Limpa estado de um canal"""
        estado = self.estados_canais[canal_id]

        # Cancelar timer ativo se existe
        if estado['after_id']:
            self.janela.after_cancel(estado['after_id'])

        estado.update({
            'processando': False,
            'contagem_ativa': False,
            'tempo_inicio': None,
            'tempo_terminou': False,
            'ns_pendente': None,
            'after_id': None,
            'resultado_final': False  # RESETAR A FLAG
        })

    def _iniciar_contagem_background(self, canal_id: int):
        """Inicia contagem em background quando canal fica AGUARDANDO"""
        estado = self.estados_canais[canal_id]
        print(f"[DEBUG] Chamando contagem para canal {canal_id}")
        # Se já está contando, não fazer nada
        if estado['contagem_ativa']:
            return

        # Limpar estado anterior
        if estado['after_id']:
            self.janela.after_cancel(estado['after_id'])

        # Iniciar contagem
        estado['contagem_ativa'] = True
        estado['tempo_inicio'] = time.time()
        estado['tempo_terminou'] = False
        estado['ns_pendente'] = None
        estado['resultado_final'] = False  # RESETAR A FLAG

        config = self.get_config_modelo_atual()
        tempo_processamento = config['tempo_ms']

        print(f"Canal {canal_id:02d}: Iniciando contagem de inicialização ({tempo_processamento}ms)")

        # Agendar fim da contagem
        estado['after_id'] = self.janela.after(tempo_processamento, lambda: self._marcar_tempo_terminado(canal_id))

    def _marcar_tempo_terminado(self, canal_id: int):
        """Marca que o tempo de inicialização terminou"""
        print(f"[DEBUG] Callback executado para canal {canal_id}")
        estado = self.estados_canais[canal_id]
        estado['tempo_terminou'] = True
        estado['after_id'] = None

        print(f"Canal {canal_id:02d}: Tempo de inicialização terminado")

        # Se já tem NS pendente, processar agora
        if estado['ns_pendente'] and not estado['resultado_final']:
            self._processar_com_ns(canal_id, estado['ns_pendente'])

    def _processar_com_ns(self, canal_id: int, ns: str):
        """Processa resultado quando NS é fornecido"""
        estado = self.estados_canais[canal_id]
        estado['ns_pendente'] = ns

        # Se o tempo já terminou e ainda não processou o resultado final, processar imediatamente
        if estado['tempo_terminou'] and not estado['resultado_final']:
            self._mostrar_resultado_final(canal_id, ns)
        elif not estado['tempo_terminou']:
            # Tempo ainda não terminou, mostrar processando
            estado['processando'] = True
            self.atualizar_interface_canal(canal_id, "PROCESSANDO", self.CORES['PROCESSANDO'], "white")
            print(f"Canal {canal_id:02d}: NS recebido, aguardando fim da inicialização...")

    def _mostrar_resultado_final(self, canal_id: int, ns: str):
        """Mostra resultado final após processamento"""
        estado = self.estados_canais[canal_id]

        # VERIFICAR SE JÁ PROCESSOU O RESULTADO FINAL
        if estado['resultado_final']:
            return

        print(f"Canal {canal_id:02d}: Processando SSIM para NS: {ns}")

        # Processar SSIM
        resultado_data = self.processar_ssim_canal(canal_id)

        if not resultado_data:
            self.atualizar_interface_canal(canal_id, "ERRO", cor_fg="red")
            estado['processando'] = False
            return

        # Gerar log
        try:
            logger = self.criar_logger_individual(ns)
            logger.info(f"Canal: {canal_id:02d}")
            logger.info(f"SSIM: {resultado_data['ssim']:.4f}")
            logger.info(f"Resultado: {resultado_data['resultado']}")
            tempo_total = time.time() - estado['tempo_inicio'] if estado['tempo_inicio'] else 0
            logger.info(f"Tempo total: {tempo_total:.2f}s")
        except Exception as e:
            print(f"Erro ao criar log: {e}")

        # Atualizar interface com resultado final
        self.labels_resultado[canal_id].config(
            text=resultado_data['resultado'],
            fg=resultado_data['cor_txt'],
            bg=resultado_data['cor_bg']
        )

        # MARCAR QUE O RESULTADO FINAL JÁ FOI PROCESSADO
        estado['resultado_final'] = True
        estado['processando'] = False
        estado['contagem_ativa'] = False

        print(f"Canal {canal_id:02d}: {resultado_data['resultado']} - SSIM: {resultado_data['ssim']:.4f}")

    def _verificar_automaticamente(self):
        """Loop principal de verificação automática"""
        while True:
            try:
                futures = {
                    self.executor.submit(self.analisar_status_canal, canal_id): canal_id
                    for canal_id in range(1, 11)
                }

                for future in as_completed(futures):
                    canal_id, status = future.result()
                    estado = self.estados_canais[canal_id]
                    texto_atual = self.labels_resultado[canal_id].cget("text")


                    print(f"DEBUG Canal {canal_id:02d}: Status={status}, Interface={texto_atual}, "
                          f"Contagem_ativa={estado['contagem_ativa']}, Processando={estado['processando']}, "
                          f"Tempo_terminou={estado['tempo_terminou']}, NS={estado['ns_pendente']}")

                    if status == "ERRO":
                        self.atualizar_interface_canal(canal_id, "ERRO", cor_fg="red")
                        self.limpar_estado_canal(canal_id)

                    elif status == "SEM IMAGEM":
                        self.atualizar_interface_canal(canal_id, "SEM IMAGEM")
                        self.limpar_estado_canal(canal_id)
                        self.entradas_canais[canal_id].delete(0, tk.END)

                    else:  # AGUARDANDO
                        # Se o status for AGUARDANDO e contagem ainda não ativa, iniciar contagem
                        if texto_atual == "AGUARDANDO" and not estado['contagem_ativa']:
                            print(f"DEBUG Canal {canal_id:02d}: Iniciando contagem agora")
                            self._iniciar_contagem_background(canal_id)

                        # Se já tem NS válido, tempo terminou e ainda não processou resultado final
                        elif (estado['tempo_terminou'] and estado['ns_pendente']
                              and not estado['processando'] and not estado['resultado_final']):
                            print(f"DEBUG Canal {canal_id:02d}: Processando NS pendente agora")
                            self._processar_com_ns(canal_id, estado['ns_pendente'])

                # Sempre dormir um pouquinho antes da próxima verificação
                time.sleep(0.5)

            except Exception as e:
                print(f"Erro no loop de verificação: {e}")
                time.sleep(1)

    def callback_entrada(self, var_name, index, mode, canal):
        """Callback para entrada de NS"""
        texto_atual = self.vars_canais[canal].get().strip()
        print(f"NS digitado no canal {canal:02d}: '{texto_atual}' (len={len(texto_atual)})")

        estado = self.estados_canais[canal]

        if not texto_atual:
            # Campo foi limpo - RESETAR ESTADO COMPLETAMENTE
            estado['ns_pendente'] = None
            estado['resultado_final'] = False  # PERMITIR NOVO PROCESSAMENTO
            if estado['processando']:
                estado['processando'] = False
                # Se ainda está na contagem, voltar para AGUARDANDO
                if estado['contagem_ativa'] and not estado['tempo_terminou']:
                    self.atualizar_interface_canal(canal, "AGUARDANDO")
            return

        status_atual = self.labels_resultado[canal].cget("text")

        # Validar estado do canal
        if status_atual == "SEM IMAGEM":
            self.entradas_canais[canal].delete(0, tk.END)
            messagebox.showerror("Erro", f"Canal {canal:02d} sem imagem! Aguarde inicialização.")
            return
        elif status_atual == "ERRO":
            self.entradas_canais[canal].delete(0, tk.END)
            messagebox.showerror("Erro", f"Canal {canal:02d} com erro! Verifique conexão.")
            return

        # Validar formato do NS quando atingir o tamanho esperado
        config = self.get_config_modelo_atual()
        if len(texto_atual) >= config['chars_ns']:
            if not self.validar_ns(texto_atual):
                self.entradas_canais[canal].delete(0, tk.END)
                messagebox.showerror("Erro", f"NS deve ter {config['chars_ns']} caracteres!")
                return

            # NS válido recebido - RESETAR FLAG PARA PERMITIR NOVO PROCESSAMENTO
            estado['resultado_final'] = False
            if status_atual in ["AGUARDANDO", "PROCESSANDO"]:
                self._processar_com_ns(canal, texto_atual)

    def iniciar_processo(self, canal_escolhido: int, automatico: bool = False):
        """Inicia processo de validação manual"""
        ns = self.entradas_canais[canal_escolhido].get().strip()
        if not ns:
            if not automatico:
                messagebox.showerror("Erro", "Por favor, preencha o campo NS!")
            return

        estado = self.estados_canais[canal_escolhido]

        if not automatico:
            texto_status = self.labels_resultado[canal_escolhido].cget("text")
            if texto_status in ["SEM IMAGEM", "ERRO"]:
                messagebox.showerror("Erro", f"Canal indisponível! Status: {texto_status}")
                return

        if not self.validar_ns(ns):
            config = self.get_config_modelo_atual()
            messagebox.showerror("Erro", f"NS deve ter {config['chars_ns']} caracteres!")
            return

        # RESETAR FLAG PARA PERMITIR NOVO PROCESSAMENTO
        estado['resultado_final'] = False
        self._processar_com_ns(canal_escolhido, ns)

    def atualizar_modelo(self):
        """Atualiza modelo selecionado"""
        novo_modelo = self.combobox_modelos.get()
        if novo_modelo != self.modelo_selecionado:
            self.modelo_selecionado = novo_modelo
            # Limpar estados dos canais ao mudar modelo
            for canal_id in range(1, 11):
                self.limpar_estado_canal(canal_id)
                self.atualizar_interface_canal(canal_id, "AGUARDANDO")
            messagebox.showinfo("Atualizado", f"Modelo: {self.modelo_selecionado}")

    def setup_interface(self):
        """Configura interface gráfica"""
        self.janela = tk.Tk()
        self.janela.title("TESTE DE VERIFICAÇÃO")
        self.janela.geometry("1000x780")
        self.janela.configure(bg=self.CORES['FUNDO'])

        # Logo
        if self.carregar_logo():
            logo_label = tk.Label(self.janela, image=self.logo_image, bg=self.CORES['FUNDO'])
            logo_label.place(x=200, y=645)

        # Título
        titulo = tk.Label(self.janela, text="TESTE DE VERIFICAÇÃO",
                          font=("Segoe UI", 22, "bold"),
                          bg=self.CORES['FUNDO'], fg=self.CORES['FONTE'])
        titulo.pack(pady=20)

        # Seletor de modelo
        self._criar_frame_modelo()

        # Frame principal
        frame = tk.Frame(self.janela, bg=self.CORES['LABEL'], bd=0, relief="ridge")
        frame.pack(pady=10, padx=20)

        self._criar_cabecalho(frame)
        self._criar_canais(frame)

    def _criar_frame_modelo(self):
        """Cria frame de seleção de modelo"""
        frame_modelo = tk.Frame(self.janela, bg=self.CORES['FUNDO'])
        frame_modelo.pack(pady=(0, 15))

        tk.Label(frame_modelo, text="MODELO:", bg=self.CORES['FUNDO'],
                 fg=self.CORES['FONTE'], font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=5)

        self.combobox_modelos = ttk.Combobox(frame_modelo, state="readonly")
        self.combobox_modelos['values'] = list(self.MODELOS_CONFIG.keys())
        self.combobox_modelos.current(0)
        self.combobox_modelos.pack(side=tk.LEFT, padx=5)

        botao_atualizar = tk.Button(frame_modelo, text="ATUALIZAR", font=("Segoe UI", 11, "bold"),
                                    bg=self.CORES['BOTAO'], fg="white", activebackground="#45a049",
                                    command=self.atualizar_modelo)
        botao_atualizar.pack(side=tk.LEFT, padx=5)

    def _criar_cabecalho(self, frame):
        """Cria cabeçalho da tabela"""
        headers = ["CANAL", "STATUS", "NS/MAC1/MAC2", "EXECUTAR"]
        widths = [8, 15, 20, 10]
        for col, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=header, font=("Segoe UI", 12, "bold"),
                     bg=self.CORES['LABEL'], fg=self.CORES['FONTE'], width=width).grid(
                row=0, column=col, padx=10, pady=10)

    def _criar_canais(self, frame):
        """Cria linhas dos canais"""
        for i in range(1, 11):
            canal_nome = f"CH{i:02d}"

            # Label do canal
            tk.Label(frame, text=canal_nome, font=("Segoe UI", 11, "bold"),
                     bg=self.CORES['LABEL'], fg=self.CORES['FONTE'], width=8).grid(
                row=i, column=0, padx=10, pady=5)

            # Label de status
            status_label = tk.Label(frame, text="AGUARDANDO", font=("Segoe UI", 11),
                                    bg=self.CORES['AGUARDANDO'], fg="black", width=15, relief="groove")
            status_label.grid(row=i, column=1, padx=10, pady=5)
            self.labels_resultado[i] = status_label

            # Campo de entrada
            var = tk.StringVar()
            entrada = tk.Entry(frame, font=("Segoe UI", 11), width=60, textvariable=var)
            entrada.grid(row=i, column=2, padx=10, pady=5)
            self.entradas_canais[i] = entrada
            self.vars_canais[i] = var

            # Callback para mudanças na entrada
            var.trace_add('write', lambda var_name, index, mode, canal=i:
            self.callback_entrada(var_name, index, mode, canal))

            # Botão de execução
            botao = tk.Button(frame, text="START", font=("Segoe UI", 11, "bold"),
                              bg=self.CORES['BOTAO'], fg="white", activebackground="#45a049",
                              command=lambda c=i: self.iniciar_processo(c, automatico=False))
            botao.grid(row=i, column=3, padx=10, pady=5)

    def _iniciar_verificacao_automatica(self):
        """Inicia thread de verificação automática"""
        threading.Thread(target=self._verificar_automaticamente, daemon=True).start()

    def executar(self):
        """Executa a aplicação"""
        try:
            self.janela.mainloop()
        finally:
            self.executor.shutdown(wait=False)
            for logger in self.loggers_individuais.values():
                for handler in logger.handlers:
                    handler.close()


if __name__ == "__main__":
    app = SistemaValidacaoSSIM()
    app.executar()