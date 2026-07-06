import json
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "image_processor",
    "description": "Processa imagens de forma híbrida usando as bibliotecas Pillow e OpenCV. Converte formatos e aplica filtros (ex: grayscale, blur, edge_detect, resize).",
    "parameters": {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Caminho da imagem de entrada (ex: 'imagem.jpg')."
            },
            "output_path": {
                "type": "string",
                "description": "Caminho onde a imagem processada será salva. A extensão (.png, .jpg) define o formato de conversão."
            },
            "operation": {
                "type": "string",
                "description": "Operação a ser realizada: 'grayscale', 'blur', 'edge_detect' ou 'resize'."
            },
            "width": {
                "type": "integer",
                "description": "Largura em pixels (obrigatório somente se operation for 'resize')."
            },
            "height": {
                "type": "integer",
                "description": "Altura em pixels (obrigatório somente se operation for 'resize')."
            }
        },
        "required": ["input_path", "output_path", "operation"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Recebe instruções para processar uma imagem. Utiliza OpenCV para operações 
    como detecção de bordas ou cores, e Pillow para manipulações mais fáceis de formatos e filtros.
    """
    input_path = kwargs.get("input_path")
    output_path = kwargs.get("output_path")
    operation = kwargs.get("operation")
    width = kwargs.get("width")
    height = kwargs.get("height")
    
    if not all([input_path, output_path, operation]):
        return json.dumps({"status": "error", "message": "Os parâmetros 'input_path', 'output_path' e 'operation' são obrigatórios."})
        
    try:
        # Resolve caminhos relativos
        target_in = os.path.abspath(input_path)
        target_out = os.path.abspath(output_path)
        
        if not os.path.exists(target_in):
            return json.dumps({"status": "error", "message": f"Arquivo de entrada não encontrado: {input_path}"})
            
        # ==========================================
        # ABORDAGEM HÍBRIDA: LEITURA INICIAL (OPENCV)
        # ==========================================
        # Lê a imagem usando OpenCV (formato padrão é BGR)
        cv_img = cv2.imread(target_in)
        if cv_img is None:
            return json.dumps({"status": "error", "message": "Falha ao ler a imagem. Verifique se o formato é suportado e se o arquivo não está corrompido."})
            
        # ==========================================
        # PROCESSAMENTO
        # ==========================================
        if operation == "grayscale":
            # Usando OpenCV para conversão de cores
            processed_cv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            # Salvar com OpenCV
            cv2.imwrite(target_out, processed_cv)
            
        elif operation == "blur":
            # Usando Pillow para filtros de desfoque (fácil aplicação)
            # Converte de BGR (OpenCV) para RGB (Pillow)
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            blurred_img = pil_img.filter(ImageFilter.GaussianBlur(radius=5))
            # O Pillow deduz o formato de conversão pelo target_out (ex: .png)
            blurred_img.save(target_out)
            
        elif operation == "edge_detect":
            # Usando OpenCV para detecção de bordas (Algoritmo Canny)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            cv2.imwrite(target_out, edges)
            
        elif operation == "resize":
            if not width or not height:
                return json.dumps({"status": "error", "message": "Para a operação 'resize', 'width' e 'height' devem ser fornecidos."})
            # Usando Pillow para resize de alta qualidade (Lanczos)
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            # Resampling Lanczos para melhor qualidade possível
            resized_img = pil_img.resize((width, height), Image.Resampling.LANCZOS)
            resized_img.save(target_out)
            
        else:
            return json.dumps({"status": "error", "message": f"Operação '{operation}' não reconhecida."})
            
        return json.dumps({
            "status": "success",
            "data": f"Imagem processada usando operação '{operation}' e salva com sucesso em '{output_path}'."
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro durante o processamento híbrido da imagem: {str(e)}"
        })
