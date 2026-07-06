import sys
from core.logger import logger
from core.config import settings
from llm.factory import get_active_llm
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.manager import ManagerAgent

from tools.registry import load_all_tools

def main():
    logger.info("Iniciando Interface CLI do MVP Agente...")
    
    # ==========================================
    # 1. Injeção de Dependências (Wiring)
    # ==========================================
    # Descobre e carrega automaticamente o LLM configurado no .env
    llm = get_active_llm() 
    
    # A memória (Curto prazo)
    memory = ConversationMemory()
    
    # Os Sub-Agentes
    planner = PlannerAgent(llm_client=llm)
    
    # CARREGAMENTO DINÂMICO DE FERRAMENTAS REAIS!
    tools_registry, tools_metadata = load_all_tools()
    executor = ExecutorAgent(tools_registry=tools_registry)
    
    # O Orquestrador
    manager = ManagerAgent(
        llm_client=llm,
        memory=memory,
        planner=planner,
        executor=executor,
        tools_metadata=tools_metadata
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
