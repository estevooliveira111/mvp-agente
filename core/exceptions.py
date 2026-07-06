class MVPBaseException(Exception):
    """Classe base fundamental para todas as exceções personalizadas do sistema."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigurationException(MVPBaseException):
    """
    Lançada quando o sistema falha em inicializar devido a configurações ausentes ou inválidas 
    (ex: variáveis do .env faltando, portas não configuradas).
    """
    pass


class ToolExecutionException(MVPBaseException):
    """
    Lançada quando ocorre uma falha irrecuperável dentro de uma das ferramentas (pasta tools/).
    """
    pass


class ChannelIntegrationException(MVPBaseException):
    """
    Lançada quando a camada de Gateway (channels/) falha ao processar uma mensagem,
    autenticar na API do canal ou traduzir o Payload Normalizado.
    """
    pass


class SecurityException(MVPBaseException):
    """
    Lançada quando violações de segurança ocorrem, como chaves de criptografia inválidas, 
    falha de autenticação ou adulterações detectadas (Tamper/Forense).
    """
    pass
