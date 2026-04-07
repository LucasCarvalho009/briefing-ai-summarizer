"""
API FastAPI para resumo de texto com IA
Suporta upload de PDF/TXT e texto direto
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import io

from pdf_extractor import PDFExtractor
from summarizer import get_summarizer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Text Summarizer API",
    description="API para resumo de texto usando IA com fallback local",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class TextRequest(BaseModel):
    """Modelo para requisição de texto direto"""
    text: str

class SummaryResponse(BaseModel):
    """Modelo para resposta de resumo"""
    summary: str
    bullet_points: list[str]
    method: str
    success: bool
    error: Optional[str] = None

# Constantes
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 50000


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Text Summarizer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize (POST)"
        }
    }


@app.get("/health")
async def health_check():
    """
    Verifica status da API e do modelo de IA
    """
    summarizer = get_summarizer()
    status = summarizer.get_status()
    
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "model_status": status
    }


@app.post("/summarize", response_model=SummaryResponse)
async def summarize(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Gera resumo de texto
    
    Aceita:
    - text: Texto direto via form data
    - file: Arquivo PDF ou TXT
    
    Retorna:
    - summary: Resumo do texto
    - bullet_points: Lista de pontos-chave
    - method: Método usado ('ai' ou 'fallback')
    - success: Status da operação
    - error: Mensagem de erro (se houver)
    """
    try:
        # Validar que pelo menos um input foi fornecido
        if not text and not file:
            raise HTTPException(
                status_code=400,
                detail="Forneça texto ou arquivo para resumir"
            )
        
        # Processar arquivo se fornecido
        if file:
            logger.info(f"Processando arquivo: {file.filename}")
            
            # Validar extensão do arquivo
            file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            if f'.{file_ext}' not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato não suportado. Use: {', '.join(ALLOWED_EXTENSIONS)}"
                )
            
            # Ler conteúdo do arquivo
            file_content = await file.read()
            
            # Validar tamanho do arquivo
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE / (1024*1024)}MB"
                )
            
            # Extrair texto baseado no tipo de arquivo
            if file_ext == 'pdf':
                pdf_file = io.BytesIO(file_content)
                text = PDFExtractor.extract_text(pdf_file)
                
                if not text:
                    raise HTTPException(
                        status_code=400,
                        detail="Não foi possível extrair texto do PDF. Verifique se o arquivo não está corrompido."
                    )
            
            elif file_ext == 'txt':
                try:
                    text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = file_content.decode('latin-1')
                    except Exception:
                        raise HTTPException(
                            status_code=400,
                            detail="Não foi possível decodificar arquivo TXT. Use UTF-8 ou Latin-1."
                        )
        
        # Validar texto
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Texto vazio ou inválido"
            )
        
        text = text.strip()
        
        # Validar comprimento do texto
        if len(text) < MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Texto muito curto. Mínimo: {MIN_TEXT_LENGTH} caracteres"
            )
        
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"Texto truncado de {len(text)} para {MAX_TEXT_LENGTH} caracteres")
            text = text[:MAX_TEXT_LENGTH]
        
        logger.info(f"Processando texto: {len(text)} caracteres")
        
        # Gerar resumo
        summarizer = get_summarizer()
        result = summarizer.summarize_text(text)
        
        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Erro ao gerar resumo')
            )
        
        logger.info(f"Resumo gerado com sucesso usando método: {result['method']}")
        
        return SummaryResponse(
            summary=result['summary'],
            bullet_points=result['bullet_points'],
            method=result['method'],
            success=True,
            error=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@app.post("/summarize/text", response_model=SummaryResponse)
async def summarize_text_only(request: TextRequest):
    """
    Endpoint alternativo para resumir apenas texto (JSON)
    
    Body:
    {
        "text": "Seu texto aqui..."
    }
    """
    try:
        text = request.text.strip()
        
        if len(text) < MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Texto muito curto. Mínimo: {MIN_TEXT_LENGTH} caracteres"
            )
        
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        
        summarizer = get_summarizer()
        result = summarizer.summarize_text(text)
        
        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Erro ao gerar resumo')
            )
        
        return SummaryResponse(
            summary=result['summary'],
            bullet_points=result['bullet_points'],
            method=result['method'],
            success=True,
            error=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


# Tratamento de erros global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "summary": "",
            "bullet_points": [],
            "method": "none",
            "success": False,
            "error": "Erro interno do servidor"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
