# text_processor.py
# Procesamiento de texto para análisis de estilos de citación

import re
import unicodedata
import logging
from typing import Dict, List, Tuple, Set, Optional, Any, Union
import string
from collections import Counter, defaultdict
import os
import json


class TextProcessor:
    """
    Clase para procesar y normalizar textos académicos para análisis de citas.
    
    Proporciona funcionalidades para limpiar, segmentar y manipular textos,
    con especial atención a las características relevantes para la detección
    de citas y referencias bibliográficas.
    """
    
    def __init__(self, 
                 remove_urls: bool = True,
                 normalize_whitespace: bool = True,
                 handle_encodings: bool = True,
                 language: str = 'en'):
        """
        Inicializa el procesador de texto.
        
        Args:
            remove_urls (bool): Si se deben eliminar URLs y correos electrónicos
            normalize_whitespace (bool): Si se deben normalizar espacios en blanco
            handle_encodings (bool): Si se debe manejar codificación de caracteres
            language (str): Idioma principal para procesamiento específico
        """
        self.logger = logging.getLogger('TextProcessor')
        self.remove_urls = remove_urls
        self.normalize_whitespace = normalize_whitespace
        self.handle_encodings = handle_encodings
        self.language = language
        
        # Cargar recursos específicos del idioma si están disponibles
        self._load_language_resources()
        
        # Compilar patrones de expresiones regulares comunes
        self._compile_common_patterns()
    
    def _load_language_resources(self):
        """
        Carga recursos específicos del idioma.
        """
        # Palabras vacías (stopwords) por idioma
        self.stopwords = {
            'en': {'the', 'and', 'of', 'to', 'a', 'in', 'is', 'that', 'for', 'it', 'as', 'was', 'with', 'be', 'by', 'on', 'not', 'he', 'this', 'are'},
            'es': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le'},
            'fr': {'le', 'la', 'de', 'et', 'à', 'les', 'des', 'un', 'une', 'du', 'en', 'est', 'que', 'qui', 'dans', 'pour', 'ce', 'pas', 'au', 'sur'},
            'de': {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als'}
        }
        
        # Caracteres especiales y su normalización por idioma
        self.special_chars = {
            'en': {'"': '"', '"': '"', ''': "'", ''': "'", '—': '-', '–': '-'},
            'es': {'«': '"', '»': '"', '"': '"', '"': '"', ''': "'", ''': "'", '—': '-', '–': '-'},
            'fr': {'«': '"', '»': '"', '‹': "'", '›': "'", '—': '-', '–': '-'},
            'de': {'„': '"', '"': '"', '‚': "'", ''': "'", '—': '-', '–': '-'}
        }
        
        # Abreviaturas comunes por idioma
        self.abbreviations = {
            'en': {'ed.', 'eds.', 'vol.', 'vols.', 'p.', 'pp.', 'ch.', 'fig.', 'et al.', 'i.e.', 'e.g.', 'cf.', 'ibid.', 'et seq.'},
            'es': {'ed.', 'eds.', 'vol.', 'vols.', 'p.', 'pp.', 'cap.', 'fig.', 'et al.', 'i.e.', 'p. ej.', 'cf.', 'ibíd.', 'y sig.'},
            'fr': {'éd.', 'éds.', 'vol.', 'vols.', 'p.', 'pp.', 'ch.', 'fig.', 'et al.', 'c.-à-d.', 'p. ex.', 'cf.', 'ibid.', 'et suiv.'},
            'de': {'Hg.', 'Hrsg.', 'Bd.', 'Bde.', 'S.', 'Abb.', 'et al.', 'd. h.', 'z. B.', 'vgl.', 'ebd.', 'f.', 'ff.'}
        }
        
        # Usar conjunto predeterminado si el idioma no está disponible
        if self.language not in self.stopwords:
            self.stopwords[self.language] = self.stopwords['en']
        
        if self.language not in self.special_chars:
            self.special_chars[self.language] = self.special_chars['en']
        
        if self.language not in self.abbreviations:
            self.abbreviations[self.language] = self.abbreviations['en']
    
    def _compile_common_patterns(self):
        """
        Compila patrones de expresiones regulares de uso común.
        """
        # Patrones para limpieza de texto
        self.patterns = {
            'url': re.compile(r'https?://\S+|www\.\S+'),
            'email': re.compile(r'\S+@\S+\.\S+'),
            'whitespace': re.compile(r'\s+'),
            'multiple_spaces': re.compile(r' {2,}'),
            'line_breaks': re.compile(r'\n+'),
            'tabs': re.compile(r'\t+'),
            'punctuation': re.compile(r'[^\w\s]'),
            'digits': re.compile(r'\d+'),
            'non_ascii': re.compile(r'[^\x00-\x7F]+'),
            'citation_parentheses': re.compile(r'\([^()]*?\)'),
            'citation_brackets': re.compile(r'\[[^\[\]]*?\]'),
            'footnote_markers': re.compile(r'(?<!\w)(\d+)(?:\s*\[\s*(?:note|footnote)\s*\])?(?!\w)')
        }
        
        # Patrones para segmentación de texto
        self.segment_patterns = {
            'sentence': re.compile(r'(?<=[.!?])\s+(?=[A-Z])'),
            'paragraph': re.compile(r'\n\s*\n'),
            'section': re.compile(r'^(?:[A-Z][A-Za-z\s]+|\d+(?:\.\d+)*)\s*\n', re.MULTILINE),
            'bibliography': re.compile(r'^(?:References|Bibliography|Works Cited|Bibliografía|Referencias|Literaturverzeichnis)(?:\s*\n)', re.IGNORECASE | re.MULTILINE)
        }
    
    def clean_text(self, text: str, level: str = 'medium') -> str:
        """
        Limpia un texto según el nivel de limpieza especificado.
        
        Args:
            text (str): Texto a limpiar
            level (str): Nivel de limpieza ('light', 'medium', 'aggressive')
            
        Returns:
            str: Texto limpio
        """
        if not text:
            return ""
        
        # Limpieza básica para todos los niveles
        cleaned = text
        
        # Normalizar codificación de caracteres si se solicita
        if self.handle_encodings:
            cleaned = self._normalize_encodings(cleaned)
        
        # Eliminar URLs y correos electrónicos si se solicita
        if self.remove_urls:
            cleaned = self.patterns['url'].sub(' ', cleaned)
            cleaned = self.patterns['email'].sub(' ', cleaned)
        
        # Normalizar espacios en blanco si se solicita
        if self.normalize_whitespace:
            cleaned = self.patterns['multiple_spaces'].sub(' ', cleaned)
            cleaned = self.patterns['tabs'].sub(' ', cleaned)
            cleaned = self.patterns['whitespace'].sub(' ', cleaned)
        
        # Aplicar nivel de limpieza específico
        if level == 'light':
            # Limpieza ligera: mantener estructura y puntuación
            cleaned = cleaned.strip()
            
        elif level == 'medium':
            # Limpieza media: normalizar puntuación y espacios
            cleaned = self._normalize_punctuation(cleaned)
            cleaned = self.patterns['multiple_spaces'].sub(' ', cleaned)
            cleaned = cleaned.strip()
            
        elif level == 'aggressive':
            # Limpieza agresiva: eliminar puntuación y números
            cleaned = self.patterns['punctuation'].sub(' ', cleaned)
            cleaned = self.patterns['digits'].sub(' ', cleaned)
            cleaned = self.patterns['multiple_spaces'].sub(' ', cleaned)
            cleaned = cleaned.strip()
            cleaned = cleaned.lower()
            
            # Eliminar stopwords si están disponibles para el idioma
            if self.language in self.stopwords:
                words = cleaned.split()
                cleaned = ' '.join(word for word in words if word not in self.stopwords[self.language])
        
        return cleaned
    
    def _normalize_encodings(self, text: str) -> str:
        """
        Normaliza la codificación de caracteres en el texto.
        
        Args:
            text (str): Texto a normalizar
            
        Returns:
            str: Texto con codificación normalizada
        """
        # Intentar normalizar caracteres Unicode
        try:
            # Normalización NFKC: compatibilidad + composición canónica
            normalized = unicodedata.normalize('NFKC', text)
            
            # Reemplazar caracteres especiales según el idioma
            for special, replacement in self.special_chars.get(self.language, {}).items():
                normalized = normalized.replace(special, replacement)
            
            return normalized
        
        except Exception as e:
            self.logger.warning(f"Error al normalizar codificación: {e}")
            return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """
        Normaliza los signos de puntuación en el texto.
        
        Args:
            text (str): Texto a normalizar
            
        Returns:
            str: Texto con puntuación normalizada
        """
        # Normalizar espacios alrededor de signos de puntuación
        normalized = text
        
        # Eliminar espacios antes de puntuación
        normalized = re.sub(r'\s+([.,:;!?)])', r'\1', normalized)
        
        # Asegurar espacio después de puntuación
        normalized = re.sub(r'([.,:;!?(])\s*', r'\1 ', normalized)
        
        # Corregir espacios múltiples
        normalized = re.sub(r'\s{2,}', ' ', normalized)
        
        # Normalizar guiones
        normalized = re.sub(r'[-‐‑‒–—―]', '-', normalized)
        
        # Normalizar comillas
        normalized = re.sub(r'[""„«»]', '"', normalized)
        normalized = re.sub(r'[''‚‹›]', "'", normalized)
        
        # Preservar puntos en abreviaturas conocidas
        for abbr in self.abbreviations.get(self.language, []):
            # Reemplazar temporalmente abreviaturas para evitar separación incorrecta
            escaped_abbr = re.escape(abbr)
            pattern = re.compile(r'\b' + escaped_abbr)
            normalized = pattern.sub(abbr.replace('.', '_DOT_'), normalized)
        
        # Restaurar abreviaturas
        normalized = normalized.replace('_DOT_', '.')
        
        return normalized
    
    def segment_text(self, text: str, unit: str = 'paragraph') -> List[str]:
        """
        Segmenta el texto en unidades específicas.
        
        Args:
            text (str): Texto a segmentar
            unit (str): Unidad de segmentación ('sentence', 'paragraph', 'section')
            
        Returns:
            List[str]: Lista de segmentos
        """
        if not text:
            return []
        
        # Aplicar segmentación según la unidad solicitada
        if unit == 'sentence':
            # Preservar abreviaturas para evitar división incorrecta
            processed = text
            for abbr in self.abbreviations.get(self.language, []):
                escaped_abbr = re.escape(abbr)
                pattern = re.compile(r'\b' + escaped_abbr)
                processed = pattern.sub(abbr.replace('.', '_DOT_'), processed)
            
            # Dividir por oraciones
            segments = self.segment_patterns['sentence'].split(processed)
            
            # Restaurar abreviaturas
            segments = [segment.replace('_DOT_', '.') for segment in segments]
        
        elif unit == 'paragraph':
            # Dividir por párrafos (líneas en blanco)
            segments = self.segment_patterns['paragraph'].split(text)
        
        elif unit == 'section':
            # Dividir por secciones (encabezados)
            segments = []
            current_section = ""
            
            lines = text.split('\n')
            in_new_section = False
            
            for line in lines:
                if self.segment_patterns['section'].match(line) or not current_section:
                    if current_section:
                        segments.append(current_section.strip())
                    current_section = line + "\n"
                    in_new_section = True
                else:
                    current_section += line + "\n"
                    in_new_section = False
            
            if current_section:
                segments.append(current_section.strip())
        
        else:
            # Si no se reconoce la unidad, devolver el texto completo
            segments = [text]
        
        # Filtrar segmentos vacíos
        return [segment.strip() for segment in segments if segment.strip()]
    
    def extract_bibliography(self, text: str) -> Tuple[str, str]:
        """
        Separa la sección bibliográfica del texto principal.
        
        Args:
            text (str): Texto completo
            
        Returns:
            Tuple[str, str]: (texto_principal, bibliografía)
        """
        if not text:
            return ("", "")
        
        # Buscar encabezado de bibliografía
        bibliography_headers = [
            r'(?i)referencias', r'(?i)bibliograf[ií]a', r'(?i)obras citadas',
            r'(?i)references', r'(?i)bibliography', r'(?i)works cited',
            r'(?i)literaturverzeichnis', r'(?i)sources', r'(?i)fuentes',
            r'(?i)literature cited'
        ]
        
        # Buscar cada posible encabezado
        lowest_pos = len(text)
        for header in bibliography_headers:
            match = re.search(f"(?:^|\n)\\s*{header}\\s*(?:\n|$)", text, re.IGNORECASE)
            if match and match.start() < lowest_pos:
                lowest_pos = match.start()
        
        # Si se encontró bibliografía
        if lowest_pos < len(text):
            main_text = text[:lowest_pos].strip()
            bibliography = text[lowest_pos:].strip()
            return (main_text, bibliography)
        
        # Buscar entradas bibliográficas típicas al final del texto
        # APA: Apellido, I. (Año).
        # MLA: Apellido, Nombre.
        # IEEE: [1] I. Apellido,
        bib_patterns = [
            r'\n[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)\.',  # APA
            r'\n[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\.\s',  # MLA
            r'\n\[\d+\]\s[A-Z]\.\s[A-Za-zÀ-ÿ\-]+',  # IEEE
            r'\n\d+\.\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,3}'  # Vancouver
        ]
        
        for pattern in bib_patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                # Usar la primera coincidencia como inicio de bibliografía
                first_match = matches[0]
                # Buscar el inicio de línea
                bib_start = first_match.start()
                while bib_start > 0 and text[bib_start-1] != '\n':
                    bib_start -= 1
                
                # Verificar si hay línea en blanco antes
                prev_newline = text.rfind('\n', 0, bib_start)
                if prev_newline != -1 and bib_start - prev_newline > 1:
                    # Buscar línea en blanco anterior
                    prev_blank_line = text.rfind('\n\n', 0, bib_start)
                    if prev_blank_line != -1:
                        bib_start = prev_blank_line + 1
                
                main_text = text[:bib_start].strip()
                bibliography = text[bib_start:].strip()
                return (main_text, bibliography)
        
        # Si no se encuentra bibliografía
        return (text, "")
    
    def extract_citations(self, text: str, style: Optional[str] = None) -> List[str]:
        """
        Extrae citas en texto del texto principal.
        
        Args:
            text (str): Texto del que extraer citas
            style (str, optional): Estilo de citación ('APA', 'MLA', etc.)
            
        Returns:
            List[str]: Lista de citas extraídas
        """
        if not text:
            return []
        
        citations = []
        
        # Aplicar patrones según el estilo
        if style == 'APA':
            # (Autor, año) o (Autor, año, p. xx)
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,|\s&|\sy)\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\(\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    citations.append(match.group(0))
        
        elif style == 'MLA':
            # (Autor página)
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\d+(?:-\d+)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\(\d+(?:-\d+)?\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    citations.append(match.group(0))
        
        elif style == 'CHICAGO':
            # (Autor año, página) o notas al pie
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\d{4}(?:,\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\(\d{4}(?:,\s\d+(?:-\d+)?)?\)',
                r'^\d+\.\s.+$'  # Notas al pie (líneas que comienzan con número y punto)
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE)
                for match in matches:
                    citations.append(match.group(0))
        
        elif style == 'IEEE' or style == 'VANCOUVER':
            # [n] o (n)
            patterns = [
                r'\[\d+(?:,\s*\d+)*\]',
                r'\(\d+(?:,\s*\d+)*\)',
                r'(?<!\w)(\d+)(?:\s*\[\s*(?:ref|nota|footnote)\s*\])?(?!\w)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    citations.append(match.group(0))
        
        else:
            # Si no se especifica estilo, extraer todos los tipos comunes
            # Citas entre paréntesis
            parentheses_matches = self.patterns['citation_parentheses'].finditer(text)
            for match in parentheses_matches:
                citation = match.group(0)
                # Filtrar falsos positivos básicos
                if len(citation) > 4 and not citation.isdigit():
                    citations.append(citation)
            
            # Citas entre corchetes
            bracket_matches = self.patterns['citation_brackets'].finditer(text)
            for match in bracket_matches:
                citation = match.group(0)
                # Filtrar falsos positivos básicos
                if len(citation) > 2 and not citation.isdigit():
                    citations.append(citation)
            
            # Marcadores de notas al pie
            footnote_matches = self.patterns['footnote_markers'].finditer(text)
            for match in footnote_matches:
                citations.append(match.group(0))
        
        # Eliminar duplicados preservando el orden
        unique_citations = []
        seen = set()
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def extract_bibliography_entries(self, text: str, style: Optional[str] = None) -> List[str]:
        """
        Extrae entradas bibliográficas individuales de la sección de bibliografía.
        
        Args:
            text (str): Texto de la sección bibliográfica
            style (str, optional): Estilo de citación ('APA', 'MLA', etc.)
            
        Returns:
            List[str]: Lista de entradas bibliográficas
        """
        if not text:
            return []
        
        # Extraer sección de bibliografía si se proporciona texto completo
        if len(text) > 1000:  # Heurística para texto completo vs. solo bibliografía
            _, bibliography = self.extract_bibliography(text)
            if bibliography:
                text = bibliography
        
        # Eliminar el encabezado de bibliografía
        bibliography_headers = [
            r'(?i)referencias', r'(?i)bibliograf[ií]a', r'(?i)obras citadas',
            r'(?i)references', r'(?i)bibliography', r'(?i)works cited',
            r'(?i)literaturverzeichnis', r'(?i)sources', r'(?i)fuentes'
        ]
        
        for header in bibliography_headers:
            text = re.sub(f"^\\s*{header}\\s*\n", "", text, flags=re.IGNORECASE)
        
        entries = []
        
        # Aplicar diferentes estrategias según el estilo
        if style == 'APA':
            # Dividir por autor-año
            pattern = r'(?:^|\n)([A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?(?:(?:,|,?\s&)\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*\s\(\d{4}\)\..*?)(?=\n[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.|\Z)'
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                entry = match.group(1).strip()
                if entry:
                    entries.append(entry)
        
        elif style == 'MLA':
            # Dividir por autor nombre
            pattern = r'(?:^|\n)([A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\..*?)(?=\n[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\.|\Z)'
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                entry = match.group(1).strip()
                if entry:
                    entries.append(entry)
        
        elif style == 'CHICAGO':
            # Dividir por autor nombre (similar a MLA)
            pattern = r'(?:^|\n)([A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\..*?)(?=\n[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\.|\Z)'
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                entry = match.group(1).strip()
                if entry:
                    entries.append(entry)
        
        elif style == 'IEEE' or style == 'VANCOUVER':
            # Dividir por número
            pattern = r'(?:^|\n)(?:\[(\d+)\]|\d+\.)\s.*?(?=\n(?:\[\d+\]|\d+\.)\s|\Z)'
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                entry = match.group(0).strip()
                if entry:
                    entries.append(entry)
        
        else:
            # Método genérico para cualquier estilo
            # Intentar dividir por líneas en blanco
            paragraphs = re.split(r'\n\s*\n', text)
            
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Verificar que parece una entrada bibliográfica
                    # (comienza con autor o número, tiene más de X caracteres)
                    if (re.match(r'^[A-Za-zÀ-ÿ\-]+,', para) or 
                        re.match(r'^\[\d+\]', para) or 
                        re.match(r'^\d+\.', para)) and len(para) > 20:
                        entries.append(para)
            
            # Si no se encuentran entradas con párrafos, intentar por líneas
            if not entries:
                lines = text.split('\n')
                current_entry = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_entry:
                            entries.append(current_entry)
                            current_entry = ""
                    elif re.match(r'^[A-Za-zÀ-ÿ\-]+,', line) or re.match(r'^\[\d+\]', line) or re.match(r'^\d+\.', line):
                        # Inicio de nueva entrada
                        if current_entry:
                            entries.append(current_entry)
                        current_entry = line
                    else:
                        # Continuación de entrada actual
                        current_entry += " " + line
                
                if current_entry:
                    entries.append(current_entry)
        
        return [entry.strip() for entry in entries if entry.strip()]
    
    def normalize_citation(self, citation: str, style: str) -> str:
        """
        Normaliza el formato de una cita según un estilo específico.
        
        Args:
            citation (str): Texto de la cita
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            
        Returns:
            str: Cita normalizada
        """
        if not citation:
            return ""
        
        normalized = citation
        
        if style == 'APA':
            # Normalizar (Autor, año, p. xx)
            
            # Asegurar coma entre autor y año
            normalized = re.sub(r'\(([A-Za-zÀ-ÿ\-]+(?: et al\.)?)\s(\d{4})', r'(\1, \2', normalized)
            
            # Asegurar espacio después de 'p.' o 'pp.'
            normalized = re.sub(r'(p\.|pp\.)(\d)', r'\1 \2', normalized)
            
            # Asegurar 'p.' antes de número de página
            if re.search(r'\d{4},\s\d+', normalized) and not re.search(r'\d{4},\sp\.', normalized):
                normalized = re.sub(r'(\d{4}),\s(\d+)', r'\1, p. \2', normalized)
            
            # Normalizar '&' vs 'y'
            if '(' in normalized:  # Cita parentética
                normalized = normalized.replace(' y ', ' & ')
            else:  # Cita narrativa
                normalized = normalized.replace(' & ', ' y ')
        
        elif style == 'MLA':
            # Normalizar (Autor página)
            
            # Eliminar coma entre autor y página
            normalized = re.sub(r'\(([A-Za-zÀ-ÿ\-]+(?: et al\.)?),\s(\d+)', r'(\1 \2', normalized)
            
            # Eliminar 'p.' o 'pp.' antes de número de página
            normalized = re.sub(r'(p\.|pp\.)?\s?(\d+)', r'\2', normalized)
            
            # Normalizar 'and' vs '&'
            normalized = normalized.replace(' & ', ' and ')
        
        elif style == 'CHICAGO':
            if re.match(r'^\d+\.', normalized):  # Nota al pie
                # Normalizar formato de nota
                pass  # Complejo, dependería de qué tipo de obra
            else:  # Autor-fecha
                # Normalizar (Autor año, página)
                
                # Eliminar coma entre autor y año
                normalized = re.sub(r'\(([A-Za-zÀ-ÿ\-]+(?: et al\.)?),\s(\d{4})', r'(\1 \2', normalized)
                
                # Asegurar coma entre año y página
                normalized = re.sub(r'(\d{4})\s(\d+)', r'\1, \2', normalized)
                
                # Normalizar 'and' vs '&'
                normalized = normalized.replace(' & ', ' and ')
        
        elif style == 'IEEE' or style == 'VANCOUVER':
            # Normalizar [n] o (n)
            
            if style == 'IEEE':
                # Usar corchetes en lugar de paréntesis
                if normalized.startswith('(') and normalized.endswith(')'):
                    number = normalized[1:-1]
                    normalized = f"[{number}]"
            
            elif style == 'VANCOUVER':
                # Preferir superíndice o paréntesis según convención
                if normalized.startswith('[') and normalized.endswith(']'):
                    number = normalized[1:-1]
                    normalized = f"({number})"
        
        return normalized
    
    def normalize_bibliography_entry(self, entry: str, style: str) -> str:
        """
        Normaliza el formato de una entrada bibliográfica según un estilo específico.
        
        Args:
            entry (str): Texto de la entrada bibliográfica
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            
        Returns:
            str: Entrada normalizada
        """
        if not entry:
            return ""
        
        normalized = entry
        
        if style == 'APA':
            # Normalizar capitalización de título
            title_match = re.search(r'\(\d{4}\)\.\s([^\.]+)', normalized)
            if title_match:
                title = title_match.group(1)
                # Primera letra mayúscula, resto minúsculas (excepto nombres propios)
                new_title = title[0].upper() + title[1:].lower()
                normalized = normalized.replace(title, new_title)
            
            # Asegurar cursiva para títulos de libros y revistas
            # Nota: No se puede aplicar formato en texto plano
            
            # Normalizar formato de autor et al.
            normalized = re.sub(r'([A-Za-zÀ-ÿ\-]+,\s[A-Z]\.)(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.){6,}', r'\1, et al.', normalized)
        
        elif style == 'MLA':
            # Normalizar título entre comillas para artículos
            title_match = re.search(r'(?<=[A-Za-zÀ-ÿ\s\-]+\.)\s([^\.]+)', normalized)
            if title_match:
                title = title_match.group(1)
                if not (title.startswith('"') and title.endswith('"')):
                    if re.search(r'(?:Journal|Review|Quarterly|Studies|Reports|Proceedings)', normalized):
                        new_title = f'"{title}"'
                        normalized = normalized.replace(title, new_title)
        
        elif style == 'CHICAGO':
            # Normalizar título entre comillas para artículos
            # Similar a MLA
            pass
        
        elif style == 'IEEE':
            # Normalizar formato de autor (iniciales primero)
            author_match = re.search(r'^\[\d+\]\s([A-Za-zÀ-ÿ\s\-,\.]+),', normalized)
            if author_match:
                author = author_match.group(1)
                if ',' in author:  # Si está en formato "Apellido, Nombre"
                    last, first = author.split(',', 1)
                    first = first.strip()
                    # Convertir a iniciales si no lo son ya
                    if not re.match(r'^[A-Z]\.(\s[A-Z]\.)*$', first):
                        initials = ''.join(word[0].upper() + '.' for word in first.split() if word)
                        new_author = f"{initials} {last}"
                        normalized = normalized.replace(author, new_author)
        
        return normalized
    
    def find_citation_context(self, text: str, citation: str, context_size: int = 100) -> str:
        """
        Encuentra el contexto textual alrededor de una cita.
        
        Args:
            text (str): Texto completo
            citation (str): Cita a buscar
            context_size (int): Número de caracteres de contexto a cada lado
            
        Returns:
            str: Texto de contexto con la cita
        """
        if not text or not citation:
            return ""
        
        # Escapar caracteres especiales en la cita
        escaped_citation = re.escape(citation)
        
        # Encontrar posición de la cita
        match = re.search(escaped_citation, text)
        if not match:
            return ""
        
        start_pos, end_pos = match.span()
        
        # Determinar inicio y fin del contexto
        context_start = max(0, start_pos - context_size)
        context_end = min(len(text), end_pos + context_size)
        
        # Extender a límites de palabras
        while context_start > 0 and text[context_start] != ' ' and text[context_start] != '\n':
            context_start -= 1
        
        while context_end < len(text) - 1 and text[context_end] != ' ' and text[context_end] != '\n':
            context_end += 1
        
        # Extraer contexto
        context = text[context_start:context_end]
        
        # Añadir indicadores de truncamiento
        if context_start > 0:
            context = "..." + context
        
        if context_end < len(text):
            context = context + "..."
        
        return context
    
    def detect_citation_style(self, text: str) -> Tuple[str, float]:
        """
        Detecta el estilo de citación predominante en el texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Tuple[str, float]: Estilo de citación y nivel de confianza
        """
        if not text:
            return ("desconocido", 0.0)
        
        # Contar ocurrencias de patrones de cada estilo
        style_scores = {
            'APA': 0,
            'MLA': 0,
            'CHICAGO': 0,
            'IEEE': 0,
            'VANCOUVER': 0
        }
        
        # Buscar patrones de APA
        apa_patterns = [
            # (Autor, año) o (Autor, año, p. xx)
            r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
            # Autor (año)
            r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\(\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
            # Bibliografía: Apellido, I. (Año).
            r'[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)\.'
        ]
        
        for pattern in apa_patterns:
            matches = re.findall(pattern, text)
            style_scores['APA'] += len(matches)
        
        # Buscar patrones de MLA
        mla_patterns = [
            # (Autor página)
            r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\d+(?:-\d+)?\)',
            # Bibliografía: Apellido, Nombre.
            r'[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+\.\s.+\.\s.+,\s\d{4}\.'
        ]
        
        for pattern in mla_patterns:
            matches = re.findall(pattern, text)
            style_scores['MLA'] += len(matches)
        
        # Buscar patrones de Chicago
        chicago_patterns = [
            # Autor-fecha: (Autor año, página)
            r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\d{4}(?:,\s\d+(?:-\d+)?)?\)',
            # Notas al pie: Número. 
            r'^\d+\.\s.+$',
            # Términos latinos
            r'\bIbid\.|Op\. cit\.|Loc\. cit\.'
        ]
        
        for pattern in chicago_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            style_scores['CHICAGO'] += len(matches)
        
        # Buscar patrones de IEEE
        ieee_patterns = [
            # Citas numéricas [n]
            r'\[\d+(?:,\s*\d+)*\]',
            # Bibliografía: [n] I. Apellido
            r'\[\d+\]\s[A-Z]\.\s[A-Za-zÀ-ÿ\-]+'
        ]
        
        for pattern in ieee_patterns:
            matches = re.findall(pattern, text)
            style_scores['IEEE'] += len(matches)
        
        # Buscar patrones de Vancouver
        vancouver_patterns = [
            # Citas numéricas (n)
            r'\(\d+(?:,\s*\d+)*\)',
            # Bibliografía: n. Apellido AB
            r'^\d+\.\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,3}'
        ]
        
        for pattern in vancouver_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            style_scores['VANCOUVER'] += len(matches)
        
        # Determinar el estilo predominante
        if sum(style_scores.values()) == 0:
            return ("desconocido", 0.0)
        
        max_style = max(style_scores.items(), key=lambda x: x[1])
        style = max_style[0]
        score = max_style[1]
        
        # Calcular nivel de confianza
        total_matches = sum(style_scores.values())
        confidence = score / total_matches if total_matches > 0 else 0.0
        
        return (style, confidence)
    
    def compare_texts(self, text1: str, text2: str) -> Dict[str, float]:
        """
        Compara dos textos para determinar similitudes en términos de citas.
        
        Args:
            text1 (str): Primer texto
            text2 (str): Segundo texto
            
        Returns:
            Dict[str, float]: Métricas de similitud
        """
        if not text1 or not text2:
            return {"similarity": 0.0, "shared_citations": 0, "citation_overlap": 0.0}
        
        # Extraer citas de ambos textos
        style1, _ = self.detect_citation_style(text1)
        style2, _ = self.detect_citation_style(text2)
        
        citations1 = set(self.extract_citations(text1, style1))
        citations2 = set(self.extract_citations(text2, style2))
        
        # Calcular similitud
        shared_citations = citations1.intersection(citations2)
        total_unique_citations = citations1.union(citations2)
        
        num_shared = len(shared_citations)
        num_total = len(total_unique_citations)
        
        # Calcular coeficiente de Jaccard para citas
        citation_overlap = num_shared / num_total if num_total > 0 else 0.0
        
        # Calcular similitud general (podría incluir más factores)
        # Por ahora, solo basado en citas
        similarity = citation_overlap
        
        return {
            "similarity": similarity,
            "shared_citations": num_shared,
            "citation_overlap": citation_overlap
        }
    
    def format_citation(self, metadata: Dict[str, str], style: str, 
                      citation_type: str = 'in_text') -> str:
        """
        Formatea una cita a partir de metadatos según un estilo específico.
        
        Args:
            metadata (Dict[str, str]): Metadatos de la fuente
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            citation_type (str): Tipo de cita ('in_text', 'bibliography')
            
        Returns:
            str: Cita formateada
        """
        if not metadata:
            return ""
        
        # Extraer campos comunes
        author = metadata.get('author', '')
        year = metadata.get('year', '')
        title = metadata.get('title', '')
        page = metadata.get('page', '')
        
        # Extraer campos específicos según el tipo de fuente
        source_type = metadata.get('type', '')
        journal = metadata.get('journal', '')
        volume = metadata.get('volume', '')
        issue = metadata.get('issue', '')
        publisher = metadata.get('publisher', '')
        url = metadata.get('url', '')
        doi = metadata.get('doi', '')
        
        # Formatear cita según estilo y tipo
        if citation_type == 'in_text':
            # Citas en texto
            if style == 'APA':
                if page:
                    return f"({author}, {year}, p. {page})"
                else:
                    return f"({author}, {year})"
            
            elif style == 'MLA':
                return f"({author} {page})"
            
            elif style == 'CHICAGO':
                if page:
                    return f"({author} {year}, {page})"
                else:
                    return f"({author} {year})"
            
            elif style == 'IEEE' or style == 'VANCOUVER':
                # Requiere un número de referencia
                ref_num = metadata.get('ref_num', '?')
                if style == 'IEEE':
                    return f"[{ref_num}]"
                else:
                    return f"({ref_num})"
        
        else:
            # Entradas bibliográficas
            if style == 'APA':
                if source_type == 'article':
                    return f"{author}. ({year}). {title}. {journal}, {volume}({issue}), {page}."
                else:  # Libro por defecto
                    return f"{author}. ({year}). {title}. {publisher}."
            
            elif style == 'MLA':
                if source_type == 'article':
                    return f"{author}. \"{title}.\" {journal}, vol. {volume}, no. {issue}, {year}, pp. {page}."
                else:  # Libro por defecto
                    return f"{author}. {title}. {publisher}, {year}."
            
            elif style == 'CHICAGO':
                if source_type == 'article':
                    return f"{author}. \"{title}.\" {journal} {volume}, no. {issue} ({year}): {page}."
                else:  # Libro por defecto
                    return f"{author}. {title}. {publisher}, {year}."
            
            elif style == 'IEEE':
                ref_num = metadata.get('ref_num', '?')
                if source_type == 'article':
                    return f"[{ref_num}] {author}, \"{title},\" {journal}, vol. {volume}, no. {issue}, pp. {page}, {year}."
                else:  # Libro por defecto
                    return f"[{ref_num}] {author}, {title}. {publisher}, {year}."
            
            elif style == 'VANCOUVER':
                ref_num = metadata.get('ref_num', '?')
                if source_type == 'article':
                    return f"{ref_num}. {author}. {title}. {journal}. {year};{volume}({issue}):{page}."
                else:  # Libro por defecto
                    return f"{ref_num}. {author}. {title}. {publisher}; {year}."
        
        return ""


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del procesador de texto
    processor = TextProcessor()
    
    # Ejemplo de texto con citas (estilo APA)
    sample_text = """
    Los estudios recientes han demostrado que existe una correlación significativa entre estos factores (Smith, 2020, p. 45). Según Johnson et al. (2019), los resultados son consistentes con investigaciones previas.

    En otro estudio, Williams (2021) encontró patrones similares en diferentes contextos culturales. Estos hallazgos contrastan con trabajos anteriores en el campo (Brown & Davis, 2018).

    Referencias:
    Smith, J. A. (2020). Patterns of correlation in environmental studies. Journal of Environmental Science, 45(2), 78-92.
    Johnson, R. B., Thompson, C., & Davis, K. (2019). Cultural contexts and research methodology. Academic Press.
    Williams, P. T. (2021). Cross-cultural patterns in social behavior. Social Psychology, 33(4), 156-170.
    Brown, M., & Davis, L. (2018). Contrasting methodologies in social research. Research Methods, 12(3), 45-67.
    """
    
    # Limpiar texto
    clean_text = processor.clean_text(sample_text, level='medium')
    print("TEXTO LIMPIO:")
    print(clean_text[:200] + "...\n")
    
    # Segmentar por párrafos
    paragraphs = processor.segment_text(sample_text, unit='paragraph')
    print(f"PÁRRAFOS IDENTIFICADOS: {len(paragraphs)}")
    for i, para in enumerate(paragraphs[:2]):
        print(f"{i+1}: {para[:50]}...")
    print()
    
    # Extraer bibliografía
    main_text, bibliography = processor.extract_bibliography(sample_text)
    print("BIBLIOGRAFÍA EXTRAÍDA:")
    print(bibliography[:200] + "...\n")
    
    # Extraer citas
    style, confidence = processor.detect_citation_style(sample_text)
    print(f"ESTILO DETECTADO: {style} (confianza: {confidence:.2f})")
    
    citations = processor.extract_citations(main_text, style)
    print("CITAS EXTRAÍDAS:")
    for citation in citations:
        print(f"- {citation}")
    print()
    
    # Extraer entradas bibliográficas
    bib_entries = processor.extract_bibliography_entries(bibliography, style)
    print("ENTRADAS BIBLIOGRÁFICAS:")
    for entry in bib_entries:
        print(f"- {entry[:50]}...")
    print()
    
    # Contexto de cita
    if citations:
        context = processor.find_citation_context(sample_text, citations[0], 50)
        print(f"CONTEXTO DE CITA: {context}")
