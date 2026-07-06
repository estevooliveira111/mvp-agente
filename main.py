import sys
from core.logger import logger
from core.config import settings
from llm.openai import OpenAILLM  # Troque por OllamaLLM para testar local!
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.manager import ManagerAgent

def get_tools_registry():
    """
    Simulação do carregamento das ferramentas da pasta tools/.
    Numa versão final, este método varre a pasta tools/ dinamicamente.
    """
    return {
        "web_search": lambda **kwargs: '{"status": "success", "data": "Resultado falso do DuckDuckGo"}',
        "email_sender": lambda **kwargs: '{"status": "success", "message": "Email enviado"}'
    }

def main():
    logger.info("Iniciando Interface CLI do MVP Agente...")
    
    # ==========================================
    # 1. Injeção de Dependências (Wiring)
    # ==========================================
    # O LLM escolhido
    llm = OpenAILLM() 
    
    # A memória (Curto prazo)
    memory = ConversationMemory()
    
    # Os Sub-Agentes
    planner = PlannerAgent(llm_client=llm)
    tools_registry = get_tools_registry()
    executor = ExecutorAgent(tools_registry=tools_registry)
    
    # O Orquestrador
    manager = ManagerAgent(
        llm_client=llm,
        memory=memory,
        planner=planner,
        executor=executor
    )
    
    session_id = "sessao_cli_local"
    user_id = "user_terminal"
    
    print("="*60)
    print("🤖 Agente Orquestrador Online (Digite 'sair' para encerrar)")
    print("="*60)
    
    # ==========================================
    # 2. Loop de Conversação (REPL)
    # ==========================================
    while True:
        try:
            user_input = input("\nVocê: ")
            
            if user_input.strip().lower() in ['sair', 'exit', 'quit']:
                print("\nEncerrando o agente...")
                break
                
            if not user_input.strip():
                continue
                
            # Delega tudo para o ManagerAgent processar
            response = manager.process_message(
                session_id=session_id,
                user_id=user_id,
                raw_message=user_input
            )
            
            print(f"\nAgente: {response}")
            
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            logger.error(f"Erro fatal no loop principal: {e}")
            print("\n⚠️ Ocorreu um erro interno. Verifique os logs.")

if __name__ == "__main__":
    main()
