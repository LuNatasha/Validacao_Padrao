from datetime import datetime
import logging

canal = "CH01"  # valor da variável

nome_arquivo_log = f"{canal}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename=nome_arquivo_log
)

logging.info("Log criado para o canal.")