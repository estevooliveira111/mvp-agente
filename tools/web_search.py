import json
import requests

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "web_search",
    "description": "Busca informações externas na web. Uso: qualquer pergunta fora do conhecimento interno.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "O termo, frase ou pergunta a ser pesquisada na web."
            }
        },
        "required": ["query"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Realiza uma busca na web e retorna uma lista estruturada de resultados.
    """
    query = kwargs.get("query")
    
    if not query:
        return json.dumps({"status": "error", "message": "O parâmetro 'query' é obrigatório."})
        
    try:
        # Para o MVP, usaremos a API pública do DuckDuckGo (Instant Answer API)
        # Ela é gratuita e não exige chave, sendo ideal para um MVP inicial.
        # Caso precise de buscas avançadas depois, você pode trocar por SerpApi, Google Custom Search ou Tavily.
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        resultados = []
        
        # 1. Tenta pegar a resposta direta (Abstract)
        if data.get("AbstractText"):
            resultados.append({
                "title": data.get("Heading", "Resumo Direto"),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("AbstractText")
            })
            
        # 2. Pega os tópicos relacionados
        for topic in data.get("RelatedTopics", []):
            # O DuckDuckGo às vezes retorna sub-tópicos aninhados, filtramos apenas os que têm "Text"
            if "Text" in topic and "FirstURL" in topic:
                # Separa o título do snippet se possível
                texto_completo = topic.get("Text")
                partes = texto_completo.split(" - ", 1)
                
                titulo = partes[0] if len(partes) > 1 else "Resultado Relacionado"
                snippet = partes[1] if len(partes) > 1 else texto_completo
                
                resultados.append({
                    "title": titulo,
                    "url": topic.get("FirstURL"),
                    "snippet": snippet
                })
                
        # Limitamos aos 5 primeiros resultados para não sobrecarregar o contexto da IA
        resultados = resultados[:5]
        
        if not resultados:
            return json.dumps({
                "status": "success",
                "data": f"Nenhuma informação estruturada encontrada diretamente para '{query}'. Pode ser necessário usar sinônimos ou uma busca mais genérica."
            })

        return json.dumps({
            "status": "success",
            "data": resultados
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro ao realizar a busca web: {str(e)}"
        })
