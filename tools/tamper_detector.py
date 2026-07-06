import json
import os
import cv2
import numpy as np
from cryptography.hazmat.primitives import hashes

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "tamper_detector",
    "description": "Verifica se uma imagem foi adulterada usando Error Level Analysis (ELA) com OpenCV para buscar inconsistências de pixels e texturas. Também gera um Hash criptográfico seguro (SHA-256) da imagem para garantir sua integridade.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "O caminho (absoluto ou relativo) da imagem a ser analisada contra adulterações."
            }
        },
        "required": ["image_path"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    1. Lê a imagem crua e usa Cryptography (SHA-256) para criar um registro de integridade.
    2. Utiliza ELA (Error Level Analysis) via OpenCV para comparar artefatos de compressão.
    3. Analisa as texturas e inconsistências nas bordas (Laplacian variance) para detectar adulterações.
    """
    image_path = kwargs.get("image_path")
    
    if not image_path:
        return json.dumps({"status": "error", "message": "O parâmetro 'image_path' é obrigatório."})
        
    try:
        target_in = os.path.abspath(image_path)
        
        if not os.path.exists(target_in):
            return json.dumps({"status": "error", "message": f"Arquivo de entrada não encontrado: {image_path}"})
            
        # ==========================================
        # 1. HASH CRIPTOGRÁFICO (INTEGRIDADE)
        # ==========================================
        # Lê os bytes brutos para o hash
        with open(target_in, "rb") as f:
            image_bytes = f.read()
            
        # Gera SHA-256 com Cryptography
        digest = hashes.Hash(hashes.SHA256())
        digest.update(image_bytes)
        image_hash = digest.finalize().hex()
        
        # ==========================================
        # 2. DETECÇÃO DE ADULTERAÇÃO (OPENCV ELA)
        # ==========================================
        cv_img = cv2.imread(target_in)
        if cv_img is None:
            return json.dumps({"status": "error", "message": "Falha ao ler a imagem com o OpenCV. Formato pode não ser suportado."})
            
        # ELA (Error Level Analysis): Salva a imagem em memória recomprimida em 90%
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, encimg = cv2.imencode('.jpg', cv_img, encode_param)
        
        if not result:
            return json.dumps({"status": "error", "message": "Falha ao recomprimir a imagem em memória."})
            
        # Decodifica de volta
        recompressed = cv2.imdecode(encimg, 1)
        
        # Compara a imagem original com a recomprimida
        # Áreas manipuladas tendem a reagir diferente à compressão do que as áreas originais.
        diff = cv2.absdiff(cv_img, recompressed)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Normaliza a diferença (0 a 255) para destacar anomalias de pixel
        cv2.normalize(diff_gray, diff_gray, 0, 255, cv2.NORM_MINMAX)
        
        # Analisa a variância da diferença. 
        # Um desvio padrão muito alto significa que partes da imagem têm compressões inconsistentes (montagem).
        ela_mean = np.mean(diff_gray)
        ela_std = np.std(diff_gray)
        
        # ==========================================
        # 3. ANÁLISE DE BORDAS E TEXTURA
        # ==========================================
        # Laplacian Variance avalia a "focagem" (nitidez/blur). 
        # Áreas muito borradas artificialmente perto de áreas muito nítidas podem ser recortes.
        gray_original = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray_original, cv2.CV_64F).var()
        
        # ==========================================
        # RESULTADO HEURÍSTICO DO MVP
        # ==========================================
        tamper_risk = "Baixo"
        # Limiares de MVP para anomalias em JPG
        if ela_std > 50 or ela_mean > 45:
            tamper_risk = "Alto (Montagem Provável)"
        elif ela_std > 35:
            tamper_risk = "Médio (Possível Edição)"
            
        return json.dumps({
            "status": "success",
            "data": {
                "message": "Detecção de adulteração finalizada.",
                "image_sha256_hash": image_hash,
                "tamper_risk": tamper_risk,
                "metrics": {
                    "ela_pixel_inconsistency_std": round(float(ela_std), 2),
                    "ela_pixel_inconsistency_mean": round(float(ela_mean), 2),
                    "texture_sharpness_score": round(float(laplacian_var), 2)
                },
                "explanation": "O risco foi baseado no método ELA. Uma variância/desvio (std) alta significa que diferentes partes da imagem foram salvas com diferentes níveis de compressão (típico de colagens)."
            }
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Falha ao realizar a detecção de adulteração: {str(e)}"
        })
