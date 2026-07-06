import json
import os
import cv2
from PIL import Image, ImageFilter
from cryptography.fernet import Fernet

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "face_anonymizer",
    "description": "Pipeline avançado: Detecta rostos (OpenCV), aplica blur seletivo (Pillow) para anonimização e criptografa a imagem original (Fernet) como backup seguro antes da exportação.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Caminho da imagem original a ser processada."
            },
            "output_path": {
                "type": "string",
                "description": "Caminho onde a imagem com os rostos borrados (anonimizada) será salva."
            },
            "encryption_key": {
                "type": "string",
                "description": "(Opcional) Chave Fernet em Base64. Se não for passada, a ferramenta gerará uma nova automaticamente."
            },
            "delete_original": {
                "type": "boolean",
                "description": "(Opcional) Se verdadeiro, apaga a imagem original após gerar o backup criptografado. Padrão: false."
            }
        },
        "required": ["input_path", "output_path"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    1. Criptografa a imagem original (salva como .enc).
    2. Lê a imagem e usa Haar Cascades do OpenCV para achar as coordenadas dos rostos.
    3. Passa para o Pillow recortar, borrar (Gaussian Blur) e colar de volta os rostos.
    4. Salva a versão segura e, opcionalmente, apaga a original.
    """
    input_path = kwargs.get("input_path")
    output_path = kwargs.get("output_path")
    encryption_key = kwargs.get("encryption_key")
    delete_original = kwargs.get("delete_original", False)
    
    if not input_path or not output_path:
        return json.dumps({"status": "error", "message": "Parâmetros 'input_path' e 'output_path' são obrigatórios."})
        
    try:
        target_in = os.path.abspath(input_path)
        target_out = os.path.abspath(output_path)
        
        if not os.path.exists(target_in):
            return json.dumps({"status": "error", "message": f"Arquivo de entrada não encontrado: {input_path}"})
            
        # ==========================================
        # 1. PROTEÇÃO (CRYPTOGRAPHY)
        # ==========================================
        # Lê os bytes brutos da imagem original
        with open(target_in, "rb") as f:
            original_bytes = f.read()
            
        # Prepara a chave
        if not encryption_key:
            encryption_key = Fernet.generate_key().decode('utf-8')
            
        fernet = Fernet(encryption_key.encode('utf-8'))
        
        # Criptografa e salva o backup (.enc)
        encrypted_bytes = fernet.encrypt(original_bytes)
        enc_path = target_in + ".enc"
        
        with open(enc_path, "wb") as f:
            f.write(encrypted_bytes)
            
        # ==========================================
        # 2. DETECÇÃO (OPENCV)
        # ==========================================
        cv_img = cv2.imread(target_in)
        if cv_img is None:
            return json.dumps({"status": "error", "message": "Falha ao ler a imagem original com o OpenCV."})
            
        # Converte para escala de cinza para melhorar a detecção
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Carrega o modelo pré-treinado Haar Cascade padrão do OpenCV
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Detecta rostos (retorna lista de coordenadas: x, y, largura, altura)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # ==========================================
        # 3. ANONIMIZAÇÃO (PILLOW)
        # ==========================================
        # Converte para RGB (padrão Pillow)
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        
        for (x, y, w, h) in faces:
            # Define a caixa delimitadora do rosto
            box = (x, y, x + w, y + h)
            
            # Recorta apenas o rosto
            face_region = pil_img.crop(box)
            
            # Calcula um raio de blur dinâmico baseado no tamanho do rosto (para borrar bem)
            blur_radius = max(w, h) // 8
            
            # Aplica o blur forte
            blurred_face = face_region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            # Cola o rosto borrado de volta na imagem inteira
            pil_img.paste(blurred_face, box)
            
        # Salva o resultado final anonimizado
        pil_img.save(target_out)
        
        # ==========================================
        # 4. LIMPEZA (OPCIONAL)
        # ==========================================
        if delete_original:
            os.remove(target_in)
            
        return json.dumps({
            "status": "success",
            "data": {
                "message": "Pipeline executado com sucesso.",
                "faces_detected": len(faces),
                "anonymized_image": output_path,
                "encrypted_original": enc_path,
                "encryption_key": encryption_key,
                "original_deleted": delete_original
            }
        })
        
    except ValueError:
        return json.dumps({"status": "error", "message": "Chave de criptografia inválida fornecida."})
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro durante o pipeline de anonimização: {str(e)}"
        })
