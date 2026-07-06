import json

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "prompt_builder",
    "description": "Gera prompts altamente estruturados e otimizados para orientar outras IAs. Ideal para uso em um pipeline de agentes.",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "A tarefa principal que a outra IA deve executar (ex: 'Extrair entidades deste texto', 'Gerar um roteiro')."
            },
            "context": {
                "type": "string",
                "description": "Contexto adicional, regras de negócio ou dados brutos necessários para a tarefa."
            },
            "output_format": {
                "type": "string",
                "description": "O formato de saída desejado da IA (ex: 'JSON com os campos X e Y', 'Markdown formatado', 'Tabela')."
            },
            "persona": {
                "type": "string",
                "description": "O tom, cargo ou a persona que a IA deve assumir (ex: 'Engenheiro de Software Sênior', 'Professor didático')."
            }
        },
        "required": ["task"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Recebe pedaços lógicos de intenção e constrói um prompt profissional, 
    utilizando boas práticas de engenharia de prompt (seções, delimitadores, etc).
    """
    task = kwargs.get("task")
    context = kwargs.get("context", "")
    output_format = kwargs.get("output_format", "")
    persona = kwargs.get("persona", "")
    
    if not task:
        return json.dumps({"status": "error", "message": "O parâmetro 'task' (tarefa) é obrigatório para construir o prompt."})
        
    try:
        prompt_parts = []
        
        # 1. Definição da Persona (System prompt behavior)
        if persona:
            prompt_parts.append(f"### 🎭 PERSONA E COMPORTAMENTO\nVocê atuará como: **{persona}**.\nSuma essa persona imediatamente e baseie todas as suas respostas nesse papel.")
            
        # 2. Tarefa (O objetivo central)
        prompt_parts.append(f"### 🎯 TAREFA PRINCIPAL\nSua tarefa fundamental é:\n{task}")
        
        # 3. Contexto e Dados (O que a IA vai usar para trabalhar)
        if context:
            prompt_parts.append(f"### 📚 CONTEXTO E DADOS DE APOIO\nUtilize as informações abaixo como base para realizar a tarefa:\n\n<context>\n{context}\n</context>")
            
        # 4. Formato de Saída (Garantir parseability no pipeline)
        if output_format:
            prompt_parts.append(f"### 📝 FORMATO DE SAÍDA EXIGIDO\nSua resposta DEVE seguir estritamente o formato abaixo. Não adicione textos extras:\n{output_format}")
            
        # 5. Regras de Segurança/Qualidade universais para Agentes
        prompt_parts.append(
            "### ⚠️ REGRAS GERAIS\n"
            "- Não inclua saudações, despedidas ou explicações genéricas no início ou no fim.\n"
            "- Se a tarefa for impossível com o contexto atual, retorne um aviso claro e estruturado indicando a falha.\n"
            "- Vá direto ao ponto."
        )
        
        prompt_final = "\n\n".join(prompt_parts)
        
        return json.dumps({
            "status": "success",
            "data": prompt_final
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro ao gerar o prompt: {str(e)}"
        })
