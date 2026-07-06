import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os

def setup_logger(name: str = "CoreLogger") -> logging.Logger:
    """
    Configura e retorna o logger padronizado do MVP.
    Os logs serão exibidos no console e salvos em um arquivo no diretório 'logs/'.
    """
    logger = logging.getLogger(name)
    
    # Impede que o logger acumule handlers se for importado múltiplas vezes
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Define o padrão visual do Log (Data | Nível | Módulo:Função | Mensagem)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. Output para o Console (Apenas INFO pra cima para manter a tela limpa)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. Output para Arquivo (Registra DEBUG e tudo para histórico completo)
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Usa TimedRotatingFileHandler para gerar um novo arquivo de log diariamente à meia-noite
        file_handler = TimedRotatingFileHandler(
            filename=f"{log_dir}/system.log",
            when="midnight",
            interval=1,
            backupCount=30, # Mantém histórico de 30 dias de logs
            encoding='utf-8'
        )
        file_handler.suffix = "%Y-%m-%d" # Renomeia o log do dia anterior usando a data
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Instância global do logger principal. Pode ser importada por outros arquivos:
# from core.logger import logger
logger = setup_logger()
