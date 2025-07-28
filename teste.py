import tkinter as tk

janela = tk.Tk()
janela.title("Validação SSIM por Canal")

# Criar os botões e labels lado a lado
for i in range(1, 8):
    # Botão Canal
    botao = tk.Button(janela, text="START", font=("Arial", 14),
                      command=lambda c=i: mostrar_resultado(c))
    botao.grid(row=i-1, column=3, padx=10, pady=10)

    # Label correspondente ao canal
    label2 = tk.Label(janela, text=f"CH{i}", font=("Arial", 14),
                     borderwidth=2, relief="solid", padx=10, pady=5, width=3)
    label2.grid(row=i - 1, column=0, padx=10, pady=10)

    label = tk.Label(janela, text="Aguardando", font=("Arial", 14),
                     borderwidth=2, relief="solid", padx=10, pady=5, width=12)
    label.grid(row=i-1, column=1, padx=10, pady=10)

    entrada = tk.Entry(janela, font=("Arial", 14))
    entrada.grid(row=i-1, column=2, padx=10, pady=10)

    # Salva a label no dicionário

janela.mainloop()