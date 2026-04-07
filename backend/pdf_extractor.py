"""
Módulo para extração de texto de arquivos PDF
"""
import PyPDF2
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Classe para extrair texto de arquivos PDF"""
    
    @staticmethod
    def extract_text(pdf_file) -> Optional[str]:
        """
        Extrai texto de um arquivo PDF
        
        Args:
            pdf_file: Arquivo PDF (file-like object)
            
        Returns:
            str: Texto extraído do PDF ou None se houver erro
        """
        try:
            # Criar leitor de PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Verificar se o PDF tem páginas
            if len(pdf_reader.pages) == 0:
                logger.error("PDF não contém páginas")
                return None
            
            # Extrair texto de todas as páginas
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    logger.info(f"Página {page_num + 1} extraída com sucesso")
                except Exception as e:
                    logger.warning(f"Erro ao extrair página {page_num + 1}: {str(e)}")
                    continue
            
            # Verificar se algum texto foi extraído
            if not text.strip():
                logger.error("Nenhum texto foi extraído do PDF")
                return None
            
            # Limpar texto (remover espaços extras, quebras de linha múltiplas)
            text = PDFExtractor._clean_text(text)
            
            logger.info(f"Texto extraído com sucesso: {len(text)} caracteres")
            return text
            
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Erro ao ler PDF: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair texto do PDF: {str(e)}")
            return None
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Limpa o texto extraído removendo espaços extras e formatação desnecessária
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            str: Texto limpo
        """
        # Remover múltiplas quebras de linha
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
        
        # Remover múltiplos espaços
        text = " ".join(text.split())
        
        return text
    
    @staticmethod
    def validate_pdf(pdf_file) -> tuple[bool, str]:
        """
        Valida se o arquivo é um PDF válido
        
        Args:
            pdf_file: Arquivo para validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            if len(pdf_reader.pages) == 0:
                return False, "PDF não contém páginas"
            
            # Tentar extrair texto da primeira página para validar
            first_page = pdf_reader.pages[0]
            first_page.extract_text()
            
            return True, ""
            
        except PyPDF2.errors.PdfReadError:
            return False, "Arquivo PDF corrompido ou inválido"
        except Exception as e:
            return False, f"Erro ao validar PDF: {str(e)}"

# Made with Bob
