import json
from datetime import datetime
from typing import Dict, List, Optional
from core.logger import logger
from agents.prompts import SYSTEM_PROMPT_PLANNER

class PlannerAgent:
    """
    Sub-agente analítico. Em um padrão LangChain/CrewAI, ele é a etapa de 'Reasoning' (Pensamento).
    Recebe o pedido e o catálogo de ferramentas, e responde com um plano passo-a-passo no formato JSON.
    """
    def __init__(self, llm_client):
        # Cliente do LLM injetado via construtor (ex: google-generativeai)
        self.llm = llm_client
        
    def create_plan(
        self,
        objective: str,
        available_tools_metadata: list,
        raw_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> dict:
        """
        Pede ao LLM para estruturar como resolver o objetivo usando as ferramentas fornecidas.
        Recebe também a mensagem original e o histórico: o objetivo é um resumo e perde
        detalhes (destinatários, termos de busca, referências a mensagens anteriores).
        As lembranças (memória de longo prazo) trazem trocas antigas do mesmo usuário.
        Retorna um dicionário (JSON parseado).
        """
        logger.info(f"[Planner Agent] Criando plano para o objetivo: {objective}")
        
        # 1. Empacota todos os manuais de instrução das ferramentas num grande JSON
        tools_str = json.dumps(available_tools_metadata, indent=2, ensure_ascii=False)
        history_str = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])) or "(sem histórico)"
        memories_str = "\n".join(memories or []) or "(nenhuma)"
        # Sem a data atual, o LLM não resolve 'ontem', 'amanhã', 'semana passada'.
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        
        # 2. Monta o Prompt de Raciocínio (Chain of Thought focado em JSON)
        prompt = f"""
        DATA E HORA ATUAIS: {now_str}

        HISTÓRICO RECENTE DA CONVERSA:
        {history_str}

        LEMBRANÇAS DE CONVERSAS ANTERIORES:
        {memories_str}

        MENSAGEM ORIGINAL DO USUÁRIO: "{raw_message or objective}"

        OBJETIVO DO USUÁRIO: "{objective}"
        
        FERRAMENTAS DISPONÍVEIS:
        {tools_str}
        
        INSTRUÇÕES VITAIS:
        Pense em quais dessas ferramentas devem ser usadas para atingir o objetivo.
        Sua única resposta deve ser um objeto JSON estritamente válido e nada mais, contendo:
        {{
            "objective": "resumo do objetivo em 1 frase",
            "estimated_complexity": "Baixa/Media/Alta",
            "steps": [
                {{
                    "step_number": 1,
                    "action": "descrição do que será feito",
                    "tool": "nome_da_tool (exato como consta no campo name dos metadados)",
                    "arguments": {{"nome_do_arg": "valor gerado ou inferido"}}
                }}
            ]
        }}
        Se o objetivo for apenas conversar ou algo que não exige as ferramentas listadas, retorne a lista "steps" VAZIA.
        """
        
        # 3. Dispara para o LLM gerar a estrutura rígida de dados
        try:
            plan = self.llm.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT_PLANNER)
            logger.debug(f"[Planner Agent] Plano final finalizado com {len(plan.get('steps', []))} passos táticos.")
            return plan
        except Exception as e:
            logger.error(f"[Planner Agent] Falha ao gerar plano estratégico no LLM: {e}")
            return {"steps": []}
