"""
Módulo de resumo usando Hugging Face Transformers
Com fallback para resumidor local em caso de erro
"""
from transformers import pipeline
import logging
from typing import List, Dict, Optional
from fallback_summarizer import FallbackSummarizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISummarizer:
    """Classe para gerar resumos usando IA (Hugging Face) com fallback local"""
    
    def __init__(self):
        """Inicializa o resumidor com modelo Hugging Face"""
        self.model_name = "facebook/bart-large-cnn"
        self.summarizer = None
        self.fallback = FallbackSummarizer()
        self.use_fallback = False
        
        # Tentar carregar modelo Hugging Face
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo Hugging Face"""
        try:
            logger.info(f"Carregando modelo {self.model_name}...")
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=-1  # CPU (-1), use 0 para GPU
            )
            logger.info("Modelo carregado com sucesso!")
            self.use_fallback = False
        except Exception as e:
            logger.warning(f"Não foi possível carregar modelo Hugging Face: {str(e)}")
            logger.info("Usando resumidor fallback local")
            self.use_fallback = True
    
    def summarize_text(
        self, 
        text: str, 
        max_length: int = 150, 
        min_length: int = 50
    ) -> Dict[str, any]:
        """
        Gera resumo do texto usando IA ou fallback
        
        Args:
            text: Texto a ser resumido
            max_length: Comprimento máximo do resumo
            min_length: Comprimento mínimo do resumo
            
        Returns:
            Dict contendo:
                - summary: Resumo do texto
                - bullet_points: Lista de pontos-chave
                - method: Método usado ('ai' ou 'fallback')
                - success: Se a operação foi bem-sucedida
                - error: Mensagem de erro (se houver)
        """
        try:
            # Validar entrada
            if not text or len(text.strip()) < 50:
                return {
                    "summary": "",
                    "bullet_points": [],
                    "method": "none",
                    "success": False,
                    "error": "Texto muito curto. Mínimo de 50 caracteres."
                }
            
            # Limitar tamanho do texto (modelos têm limite de tokens)
            max_input_length = 1024
            if len(text) > max_input_length:
                logger.info(f"Texto truncado de {len(text)} para {max_input_length} caracteres")
                text = text[:max_input_length]
            
            # Tentar usar modelo Hugging Face
            if not self.use_fallback and self.summarizer:
                try:
                    summary = self._summarize_with_ai(text, max_length, min_length)
                    bullet_points = self._generate_bullet_points_ai(text)
                    
                    return {
                        "summary": summary,
                        "bullet_points": bullet_points,
                        "method": "ai",
                        "success": True,
                        "error": None
                    }
                except Exception as e:
                    logger.warning(f"Erro ao usar IA, mudando para fallback: {str(e)}")
                    self.use_fallback = True
            
            # Usar fallback local
            summary = self.fallback.summarize(text, max_sentences=5)
            bullet_points = self.fallback.generate_bullet_points(text, num_points=5)
            
            return {
                "summary": summary,
                "bullet_points": bullet_points,
                "method": "fallback",
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}")
            return {
                "summary": "",
                "bullet_points": [],
                "method": "none",
                "success": False,
                "error": f"Erro ao processar texto: {str(e)}"
            }
    
    def _summarize_with_ai(
        self, 
        text: str, 
        max_length: int, 
        min_length: int
    ) -> str:
        """
        Gera resumo usando modelo Hugging Face
        
        Args:
            text: Texto a ser resumido
            max_length: Comprimento máximo do resumo
            min_length: Comprimento mínimo do resumo
            
        Returns:
            str: Resumo gerado
        """
        logger.info("Gerando resumo com IA...")
        
        # Gerar resumo
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,
            truncation=True
        )
        
        summary = result[0]['summary_text']
        logger.info(f"Resumo IA gerado: {len(summary)} caracteres")
        
        return summary
    
    def _generate_bullet_points_ai(self, text: str, num_points: int = 5) -> List[str]:
        """
        Gera bullet points usando IA
        Para BART, vamos usar o resumo e dividir em pontos
        
        Args:
            text: Texto original
            num_points: Número de bullet points desejados
            
        Returns:
            List[str]: Lista de bullet points
        """
        try:
            # Gerar um resumo mais longo para extrair pontos
            result = self.summarizer(
                text,
                max_length=200,
                min_length=100,
                do_sample=False,
                truncation=True
            )
            
            summary = result[0]['summary_text']
            
            # Dividir resumo em sentenças para criar bullet points
            sentences = [s.strip() for s in summary.split('.') if s.strip()]
            
            # Limitar número de bullet points
            bullet_points = sentences[:min(num_points, len(sentences))]
            
            # Se não temos pontos suficientes, usar fallback
            if len(bullet_points) < 3:
                return self.fallback.generate_bullet_points(text, num_points)
            
            logger.info(f"Bullet points IA gerados: {len(bullet_points)}")
            return bullet_points
            
        except Exception as e:
            logger.warning(f"Erro ao gerar bullet points com IA: {str(e)}")
            return self.fallback.generate_bullet_points(text, num_points)
    
    def get_status(self) -> Dict[str, any]:
        """
        Retorna status do resumidor
        
        Returns:
            Dict com informações de status
        """
        return {
            "model_loaded": self.summarizer is not None,
            "model_name": self.model_name,
            "using_fallback": self.use_fallback,
            "fallback_available": True
        }
    
    def force_fallback(self, use_fallback: bool = True):
        """
        Força uso do fallback (útil para testes)
        
        Args:
            use_fallback: Se deve usar fallback
        """
        self.use_fallback = use_fallback
        logger.info(f"Fallback {'ativado' if use_fallback else 'desativado'} manualmente")


# Instância global do resumidor
ai_summarizer = AISummarizer()


def get_summarizer() -> AISummarizer:
    """
    Retorna instância do resumidor
    
    Returns:
        AISummarizer: Instância do resumidor
    """
    return ai_summarizer

# Made with Bob
