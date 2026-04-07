"""
Módulo de resumo local/simulado (fallback)
Usado quando o modelo Hugging Face não está disponível
"""
import re
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FallbackSummarizer:
    """Resumidor local baseado em extração de sentenças importantes"""
    
    def __init__(self):
        """Inicializa o resumidor fallback"""
        self.min_sentence_length = 20
        self.max_sentence_length = 200
        
    def summarize(self, text: str, max_sentences: int = 5) -> str:
        """
        Gera um resumo extraindo as sentenças mais importantes
        
        Args:
            text: Texto a ser resumido
            max_sentences: Número máximo de sentenças no resumo
            
        Returns:
            str: Resumo do texto
        """
        try:
            logger.info("Usando resumidor fallback local")
            
            # Dividir texto em sentenças
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                return "Não foi possível gerar resumo: texto muito curto ou inválido."
            
            # Se o texto já é curto, retornar como está
            if len(sentences) <= max_sentences:
                return " ".join(sentences)
            
            # Pontuar sentenças por importância
            scored_sentences = self._score_sentences(sentences, text)
            
            # Ordenar por pontuação e pegar as top N
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = scored_sentences[:max_sentences]
            
            # Reordenar pela posição original no texto
            top_sentences.sort(key=lambda x: x[2])
            
            # Extrair apenas as sentenças
            summary_sentences = [sent for sent, score, pos in top_sentences]
            
            summary = " ".join(summary_sentences)
            logger.info(f"Resumo fallback gerado: {len(summary)} caracteres")
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo fallback: {str(e)}")
            return "Erro ao gerar resumo. Por favor, tente novamente."
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Divide o texto em sentenças
        
        Args:
            text: Texto a ser dividido
            
        Returns:
            List[str]: Lista de sentenças
        """
        # Padrão para dividir em sentenças (pontos, exclamações, interrogações)
        sentence_pattern = r'[.!?]+\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Filtrar sentenças muito curtas ou muito longas
        filtered_sentences = [
            sent.strip() 
            for sent in sentences 
            if self.min_sentence_length <= len(sent.strip()) <= self.max_sentence_length
        ]
        
        return filtered_sentences
    
    def _score_sentences(self, sentences: List[str], full_text: str) -> List[Tuple[str, float, int]]:
        """
        Pontua sentenças baseado em vários critérios
        
        Args:
            sentences: Lista de sentenças
            full_text: Texto completo original
            
        Returns:
            List[Tuple[str, float, int]]: Lista de (sentença, pontuação, posição)
        """
        scored = []
        
        # Palavras-chave que indicam importância
        keywords = self._extract_keywords(full_text)
        
        for idx, sentence in enumerate(sentences):
            score = 0.0
            
            # 1. Posição no texto (primeiras e últimas sentenças são mais importantes)
            position_score = self._calculate_position_score(idx, len(sentences))
            score += position_score * 2.0
            
            # 2. Comprimento da sentença (sentenças médias são preferidas)
            length_score = self._calculate_length_score(len(sentence))
            score += length_score * 1.0
            
            # 3. Presença de palavras-chave
            keyword_score = self._calculate_keyword_score(sentence, keywords)
            score += keyword_score * 3.0
            
            # 4. Presença de números (podem indicar dados importantes)
            if re.search(r'\d+', sentence):
                score += 0.5
            
            scored.append((sentence, score, idx))
        
        return scored
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extrai palavras-chave do texto
        
        Args:
            text: Texto para extrair palavras-chave
            top_n: Número de palavras-chave a extrair
            
        Returns:
            List[str]: Lista de palavras-chave
        """
        # Remover pontuação e converter para minúsculas
        words = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', text.lower())
        
        # Palavras comuns a ignorar (stop words básicas em português)
        stop_words = {
            'para', 'com', 'por', 'que', 'uma', 'como', 'mais', 'dos', 'das',
            'este', 'esta', 'esse', 'essa', 'seu', 'sua', 'seus', 'suas',
            'pelo', 'pela', 'pelos', 'pelas', 'sobre', 'entre', 'quando',
            'onde', 'qual', 'quais', 'muito', 'muita', 'muitos', 'muitas',
            'todo', 'toda', 'todos', 'todas', 'outro', 'outra', 'outros', 'outras'
        }
        
        # Filtrar stop words
        filtered_words = [word for word in words if word not in stop_words]
        
        # Contar frequência
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Ordenar por frequência e pegar top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:top_n]]
        
        return keywords
    
    def _calculate_position_score(self, position: int, total: int) -> float:
        """
        Calcula pontuação baseada na posição da sentença
        Primeiras e últimas sentenças recebem pontuação maior
        
        Args:
            position: Posição da sentença (0-indexed)
            total: Total de sentenças
            
        Returns:
            float: Pontuação de posição (0-1)
        """
        if position < 3:  # Primeiras 3 sentenças
            return 1.0
        elif position >= total - 2:  # Últimas 2 sentenças
            return 0.8
        else:
            return 0.3
    
    def _calculate_length_score(self, length: int) -> float:
        """
        Calcula pontuação baseada no comprimento da sentença
        Sentenças de tamanho médio são preferidas
        
        Args:
            length: Comprimento da sentença
            
        Returns:
            float: Pontuação de comprimento (0-1)
        """
        ideal_length = 100
        diff = abs(length - ideal_length)
        
        if diff < 20:
            return 1.0
        elif diff < 50:
            return 0.7
        else:
            return 0.4
    
    def _calculate_keyword_score(self, sentence: str, keywords: List[str]) -> float:
        """
        Calcula pontuação baseada na presença de palavras-chave
        
        Args:
            sentence: Sentença a ser pontuada
            keywords: Lista de palavras-chave
            
        Returns:
            float: Pontuação de palavras-chave
        """
        sentence_lower = sentence.lower()
        keyword_count = sum(1 for keyword in keywords if keyword in sentence_lower)
        
        # Normalizar pela quantidade de palavras-chave
        if keywords:
            return keyword_count / len(keywords)
        return 0.0
    
    def generate_bullet_points(self, text: str, num_points: int = 5) -> List[str]:
        """
        Gera bullet points a partir do texto
        
        Args:
            text: Texto para gerar bullet points
            num_points: Número de bullet points desejados
            
        Returns:
            List[str]: Lista de bullet points
        """
        try:
            # Dividir em sentenças
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                return ["Texto muito curto para gerar pontos-chave"]
            
            # Pontuar sentenças
            scored_sentences = self._score_sentences(sentences, text)
            
            # Ordenar por pontuação
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Pegar top N sentenças
            top_sentences = scored_sentences[:min(num_points, len(scored_sentences))]
            
            # Criar bullet points (encurtar se necessário)
            bullet_points = []
            for sentence, score, pos in top_sentences:
                # Limitar tamanho do bullet point
                if len(sentence) > 150:
                    sentence = sentence[:147] + "..."
                bullet_points.append(sentence)
            
            logger.info(f"Gerados {len(bullet_points)} bullet points")
            return bullet_points
            
        except Exception as e:
            logger.error(f"Erro ao gerar bullet points: {str(e)}")
            return ["Erro ao gerar pontos-chave"]

# Made with Bob
