# language_detector.py
# Detector de idiomas para análisis de estilos de citación

import re
import unicodedata
import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from collections import Counter, defaultdict
import math

# Intentar importar bibliotecas opcionales
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    import langid
    LANGID_AVAILABLE = True
except ImportError:
    LANGID_AVAILABLE = False


class LanguageDetector:
    """
    Detector de idiomas especializado para textos académicos y citas.
    
    Soporta detección de idiomas con o sin bibliotecas externas como
    langdetect o langid. Incluye características específicas para
    analizar patrones de citación en diferentes idiomas.
    """
    
    def __init__(self, 
                 use_external_libs: bool = True, 
                 min_text_length: int = 20,
                 default_language: str = 'en'):
        """
        Inicializa el detector de idiomas.
        
        Args:
            use_external_libs (bool): Si se deben usar bibliotecas externas cuando estén disponibles
            min_text_length (int): Longitud mínima para análisis confiable
            default_language (str): Idioma por defecto si no se puede determinar
        """
        self.logger = logging.getLogger('LanguageDetector')
        self.use_external_libs = use_external_libs
        self.min_text_length = min_text_length
        self.default_language = default_language
        
        # Inicializar modelos de lenguaje interno
        self._init_language_models()
        
        # Verificar disponibilidad de bibliotecas externas
        self.external_libs_available = False
        if self.use_external_libs:
            if LANGDETECT_AVAILABLE:
                self.external_libs_available = True
                self.logger.info("Usando langdetect para detección de idiomas")
            elif LANGID_AVAILABLE:
                self.external_libs_available = True
                self.logger.info("Usando langid para detección de idiomas")
        
        # Inicializar características específicas de citación por idioma
        self._init_citation_language_features()
    
    def _init_language_models(self):
        """
        Inicializa modelos internos para detección de idiomas.
        """
        # Frecuencias de n-gramas de caracteres por idioma (simplificado)
        # Se podrían cargar modelos más completos desde archivos
        self.char_ngrams = {
            'en': self._load_ngrams('english'),
            'es': self._load_ngrams('spanish'),
            'fr': self._load_ngrams('french'),
            'de': self._load_ngrams('german'),
            'it': self._load_ngrams('italian'),
            'pt': self._load_ngrams('portuguese')
        }
        
        # Palabras comunes por idioma
        self.common_words = {
            'en': {'the', 'and', 'of', 'to', 'in', 'a', 'is', 'that', 'for', 'it', 'as', 'was', 'with', 'be', 'this', 'on', 'by', 'not', 'are', 'from'},
            'es': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le'},
            'fr': {'le', 'la', 'de', 'et', 'à', 'les', 'des', 'un', 'une', 'du', 'en', 'est', 'que', 'qui', 'dans', 'pour', 'ce', 'pas', 'au', 'sur'},
            'de': {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als'},
            'it': {'il', 'di', 'che', 'la', 'e', 'in', 'a', 'per', 'è', 'un', 'con', 'su', 'una', 'sono', 'da', 'dei', 'le', 'come', 'questo', 'al'},
            'pt': {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais'}
        }
        
        # Características morfológicas por idioma (artículos, preposiciones, etc.)
        self.morphological_features = {
            'en': {
                'articles': {'the', 'a', 'an'},
                'prepositions': {'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by'}
            },
            'es': {
                'articles': {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'},
                'prepositions': {'de', 'en', 'a', 'con', 'por', 'para', 'sin', 'sobre', 'entre'}
            },
            'fr': {
                'articles': {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'au', 'aux'},
                'prepositions': {'de', 'à', 'en', 'dans', 'sur', 'avec', 'pour', 'par', 'sans'}
            },
            'de': {
                'articles': {'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'eines', 'einem', 'einen'},
                'prepositions': {'in', 'an', 'auf', 'für', 'von', 'mit', 'zu', 'bei', 'nach', 'über'}
            },
            'it': {
                'articles': {'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una'},
                'prepositions': {'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra'}
            },
            'pt': {
                'articles': {'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas'},
                'prepositions': {'de', 'em', 'a', 'para', 'por', 'com', 'sem', 'sobre', 'entre'}
            }
        }
    
    def _load_ngrams(self, language: str) -> Dict[str, float]:
        """
        Carga modelos de n-gramas para un idioma.
        
        En una implementación real, estos datos se cargarían desde archivos
        entrenados con corpus grandes. Aquí usamos un conjunto simplificado.
        
        Args:
            language (str): Nombre del idioma
            
        Returns:
            Dict[str, float]: Diccionario de n-gramas y sus frecuencias
        """
        # Conjuntos simplificados de n-gramas frecuentes por idioma
        # En una implementación real, estos modelos serían mucho más extensos
        ngram_models = {
            'english': {
                'th': 0.027, 'he': 0.025, 'in': 0.023, 'er': 0.022, 'an': 0.021,
                'en': 0.020, 're': 0.019, 'on': 0.018, 'at': 0.017, 'ed': 0.016,
                'nd': 0.015, 'to': 0.015, 'or': 0.014, 'ea': 0.013, 'ti': 0.013,
                'ar': 0.012, 'te': 0.012, 'al': 0.011, 'nt': 0.011, 'ha': 0.010
            },
            'spanish': {
                'de': 0.031, 'es': 0.028, 'en': 0.027, 'el': 0.023, 'la': 0.022,
                'que': 0.021, 'os': 0.018, 'ar': 0.018, 'as': 0.017, 'er': 0.016,
                'nt': 0.015, 'ci': 0.014, 'ra': 0.014, 'co': 0.013, 'do': 0.012,
                'ad': 0.012, 'al': 0.011, 'an': 0.011, 'ta': 0.010, 'or': 0.010
            },
            'french': {
                'es': 0.031, 'en': 0.030, 'le': 0.027, 'de': 0.024, 'nt': 0.023,
                'on': 0.022, 'la': 0.021, 're': 0.020, 'ou': 0.019, 'qu': 0.018,
                'an': 0.017, 'ai': 0.016, 'ur': 0.015, 'et': 0.014, 'us': 0.013,
                'ne': 0.013, 'it': 0.012, 'el': 0.011, 'au': 0.010, 'me': 0.010
            },
            'german': {
                'en': 0.036, 'er': 0.031, 'ch': 0.027, 'de': 0.026, 'ei': 0.024,
                'in': 0.023, 'nd': 0.020, 'ie': 0.019, 'ge': 0.018, 'un': 0.017,
                'te': 0.016, 'be': 0.015, 'ic': 0.015, 'di': 0.014, 'st': 0.013,
                'sc': 0.013, 'an': 0.012, 'es': 0.011, 'zu': 0.010, 'uf': 0.010
            },
            'italian': {
                'di': 0.030, 'la': 0.027, 'to': 0.025, 'che': 0.024, 'il': 0.023,
                'e': 0.022, 'in': 0.021, 'al': 0.020, 'a': 0.019, 'per': 0.018,
                'co': 0.017, 'te': 0.016, 'ri': 0.015, 'le': 0.014, 'ar': 0.013,
                'nt': 0.013, 'ti': 0.012, 'es': 0.011, 'at': 0.010, 'me': 0.009
            },
            'portuguese': {
                'de': 0.031, 'os': 0.029, 'do': 0.028, 'ar': 0.026, 'es': 0.025,
                'ra': 0.024, 'as': 0.022, 'en': 0.021, 'da': 0.020, 'o': 0.019,
                'que': 0.018, 'co': 0.017, 'em': 0.016, 'a': 0.015, 'nt': 0.014,
                'ao': 0.014, 'to': 0.013, 'er': 0.012, 'ad': 0.011, 'ou': 0.010
            }
        }
        
        return ngram_models.get(language, {})
    
    def _init_citation_language_features(self):
        """
        Inicializa características específicas de citación por idioma.
        """
        # Palabras clave relacionadas con citas en diferentes idiomas
        self.citation_keywords = {
            'en': ['cited', 'reference', 'according to', 'et al', 'ibid', 'see', 'cf'],
            'es': ['citado', 'referencia', 'según', 'et al', 'ibídem', 'véase', 'cf'],
            'fr': ['cité', 'référence', 'selon', 'et al', 'ibid', 'voir', 'cf'],
            'de': ['zitiert', 'referenz', 'laut', 'et al', 'ebd', 'siehe', 'vgl'],
            'it': ['citato', 'riferimento', 'secondo', 'et al', 'ibid', 'vedi', 'cf'],
            'pt': ['citado', 'referência', 'segundo', 'et al', 'ibid', 'veja', 'cf']
        }
        
        # Conectores entre autores en diferentes idiomas
        self.author_connectors = {
            'en': ['and', '&'],
            'es': ['y', 'e'],
            'fr': ['et'],
            'de': ['und'],
            'it': ['e'],
            'pt': ['e']
        }
        
        # Indicadores de página en diferentes idiomas
        self.page_indicators = {
            'en': ['p', 'pp', 'page', 'pages'],
            'es': ['p', 'pp', 'pág', 'págs', 'página', 'páginas'],
            'fr': ['p', 'pp', 'page', 'pages'],
            'de': ['S', 'Seite', 'Seiten'],
            'it': ['p', 'pp', 'pag', 'pagg', 'pagina', 'pagine'],
            'pt': ['p', 'pp', 'pág', 'págs', 'página', 'páginas']
        }
        
        # Secciones bibliográficas en diferentes idiomas
        self.bibliography_sections = {
            'en': ['references', 'bibliography', 'works cited', 'sources'],
            'es': ['referencias', 'bibliografía', 'obras citadas', 'fuentes'],
            'fr': ['références', 'bibliographie', 'ouvrages cités', 'sources'],
            'de': ['literaturverzeichnis', 'bibliographie', 'quellen', 'referenzen'],
            'it': ['riferimenti', 'bibliografia', 'opere citate', 'fonti'],
            'pt': ['referências', 'bibliografia', 'obras citadas', 'fontes']
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detecta el idioma principal de un texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Tuple[str, float]: Código ISO del idioma detectado y nivel de confianza
        """
        # Verificar longitud mínima
        if not text or len(text) < self.min_text_length:
            return self.default_language, 0.0
        
        # Normalizar texto
        normalized_text = self._normalize_text(text)
        
        # Intentar usar bibliotecas externas si están disponibles
        if self.use_external_libs and self.external_libs_available:
            lang, confidence = self._detect_with_external_libs(normalized_text)
            if confidence > 0.5:  # Umbral de confianza razonable
                return lang, confidence
        
        # Si las bibliotecas externas fallan o no están disponibles, usar métodos propios
        return self._detect_with_internal_methods(normalized_text)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza el texto para análisis de idioma.
        
        Args:
            text (str): Texto original
            
        Returns:
            str: Texto normalizado
        """
        # Convertir a minúsculas
        normalized = text.lower()
        
        # Eliminar URLs y correos electrónicos
        normalized = re.sub(r'https?://\S+', '', normalized)
        normalized = re.sub(r'\S+@\S+', '', normalized)
        
        # Eliminar números
        normalized = re.sub(r'\d+', '', normalized)
        
        # Eliminar puntuación excesiva
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _detect_with_external_libs(self, text: str) -> Tuple[str, float]:
        """
        Detecta el idioma usando bibliotecas externas si están disponibles.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            Tuple[str, float]: Código ISO del idioma y nivel de confianza
        """
        try:
            if LANGDETECT_AVAILABLE:
                # Usar langdetect
                from langdetect import detect_langs
                results = detect_langs(text)
                if results:
                    top_result = results[0]
                    return top_result.lang, top_result.prob
            
            elif LANGID_AVAILABLE:
                # Usar langid
                lang, confidence = langid.classify(text)
                return lang, confidence
        
        except Exception as e:
            self.logger.warning(f"Error al detectar idioma con bibliotecas externas: {e}")
        
        # Si falla, devolver valor por defecto
        return self.default_language, 0.0
    
    def _detect_with_internal_methods(self, text: str) -> Tuple[str, float]:
        """
        Detecta el idioma usando métodos internos basados en n-gramas y palabras clave.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            Tuple[str, float]: Código ISO del idioma y nivel de confianza
        """
        # Combinar múltiples métodos para mayor precisión
        scores = {}
        
        # 1. Detección por n-gramas de caracteres
        ngram_scores = self._detect_with_char_ngrams(text)
        
        # 2. Detección por palabras comunes
        word_scores = self._detect_with_common_words(text)
        
        # 3. Detección por características morfológicas
        morph_scores = self._detect_with_morphology(text)
        
        # 4. Detección por características específicas de citación
        citation_scores = self._detect_with_citation_features(text)
        
        # Combinar puntuaciones (con pesos)
        for lang in self.char_ngrams.keys():
            scores[lang] = (
                ngram_scores.get(lang, 0) * 0.4 +
                word_scores.get(lang, 0) * 0.3 +
                morph_scores.get(lang, 0) * 0.2 +
                citation_scores.get(lang, 0) * 0.1
            )
        
        # Encontrar el idioma con mayor puntuación
        if not scores:
            return self.default_language, 0.0
        
        best_lang = max(scores, key=scores.get)
        confidence = scores[best_lang]
        
        return best_lang, confidence
    
    def _detect_with_char_ngrams(self, text: str) -> Dict[str, float]:
        """
        Detecta el idioma basado en frecuencias de n-gramas de caracteres.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            Dict[str, float]: Puntuación por idioma
        """
        scores = {}
        
        # Extraer n-gramas del texto
        text_ngrams = self._extract_char_ngrams(text, n=2)
        
        if not text_ngrams:
            return scores
        
        # Calcular similitud con modelos de idioma
        for lang, model in self.char_ngrams.items():
            if not model:
                continue
            
            score = 0
            for ngram, freq in text_ngrams.items():
                if ngram in model:
                    score += freq * model[ngram]
            
            # Normalizar puntuación
            scores[lang] = score / (sum(text_ngrams.values()) or 1)
        
        # Normalizar a un total de 1.0
        total = sum(scores.values()) or 1
        scores = {lang: score / total for lang, score in scores.items()}
        
        return scores
    
    def _extract_char_ngrams(self, text: str, n: int = 2) -> Dict[str, float]:
        """
        Extrae n-gramas de caracteres de un texto y calcula sus frecuencias.
        
        Args:
            text (str): Texto del que extraer n-gramas
            n (int): Tamaño de los n-gramas
            
        Returns:
            Dict[str, float]: Frecuencias de n-gramas
        """
        if not text or len(text) < n:
            return {}
        
        # Extraer n-gramas
        ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
        
        # Contar frecuencias
        ngram_counts = Counter(ngrams)
        
        # Convertir a frecuencias relativas
        total = sum(ngram_counts.values())
        ngram_freqs = {ngram: count / total for ngram, count in ngram_counts.items()}
        
        return ngram_freqs
    
    def _detect_with_common_words(self, text: str) -> Dict[str, float]:
        """
        Detecta el idioma basado en palabras comunes.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            Dict[str, float]: Puntuación por idioma
        """
        scores = {}
        
        # Dividir en palabras
        words = text.split()
        
        if not words:
            return scores
        
        # Contar presencia de palabras comunes por idioma
        for lang, common_words in self.common_words.items():
            count = sum(1 for word in words if word in common_words)
            scores[lang] = count / len(words)
        
        # Normalizar a un total de 1.0
        total = sum(scores.values()) or 1
        scores = {lang: score / total for lang, score in scores.items()}
        
        return scores
    
    def _detect_with_morphology(self, text: str) -> Dict[str, float]:
        """
        Detecta el idioma basado en características morfológicas.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            Dict[str, float]: Puntuación por idioma
        """
        scores = {}
        
        # Dividir en palabras
        words = text.split()
        
        if not words:
            return scores
        
        # Contar presencia de características morfológicas por idioma
        for lang, features in self.morphological_features.items():
            # Contar artículos
            article_count = sum(1 for word in words if word in features.get('articles', set()))
            
            # Contar preposiciones
            preposition_count = sum(1 for word in words if word in features.get('prepositions', set()))
            
            # Calcular puntuación
            scores[lang] = (article_count + preposition_count) / len(words)
        
        # Normalizar a un total de 1.0
        total = sum(scores.values()) or 1
        scores = {lang: score / total for lang, score in scores.items()}
        
        return scores
    
    def _detect_with_citation_features(self, text: str) -> Dict[str, float]:
        """
        Detecta el idioma basado en características específicas de citación.
        
        Args:
            text (str): Texto original (no normalizado)
            
        Returns:
            Dict[str, float]: Puntuación por idioma
        """
        scores = {}
        text_lower = text.lower()
        
        # Buscar palabras clave de citación
        for lang, keywords in self.citation_keywords.items():
            count = sum(text_lower.count(keyword.lower()) for keyword in keywords)
            scores[lang] = count
        
        # Buscar conectores entre autores
        for lang, connectors in self.author_connectors.items():
            # Buscar patrones como "Autor1 y Autor2" o "Autor1 & Autor2"
            for connector in connectors:
                connector_pattern = r'[A-Z][a-zÀ-ÿ]+\s+' + re.escape(connector) + r'\s+[A-Z][a-zÀ-ÿ]+'
                connector_count = len(re.findall(connector_pattern, text))
                scores[lang] = scores.get(lang, 0) + connector_count * 2  # Mayor peso
        
        # Buscar indicadores de página
        for lang, indicators in self.page_indicators.items():
            for indicator in indicators:
                indicator_pattern = r'\b' + re.escape(indicator) + r'\.?\s\d+'
                indicator_count = len(re.findall(indicator_pattern, text_lower))
                scores[lang] = scores.get(lang, 0) + indicator_count
        
        # Buscar nombres de secciones bibliográficas
        for lang, sections in self.bibliography_sections.items():
            for section in sections:
                if section in text_lower:
                    scores[lang] = scores.get(lang, 0) + 5  # Mayor peso
        
        # Normalizar a un total de 1.0
        total = sum(scores.values()) or 1
        scores = {lang: score / total for lang, score in scores.items()}
        
        return scores
    
    def detect_citation_language_features(self, text: str, detected_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Detecta características específicas de citación por idioma.
        
        Args:
            text (str): Texto a analizar
            detected_lang (str, optional): Idioma detectado previamente
            
        Returns:
            Dict[str, Any]: Características detectadas
        """
        # Si no se especifica idioma, detectarlo
        if not detected_lang:
            detected_lang, _ = self.detect_language(text)
        
        features = {
            'language': detected_lang,
            'citation_terms': [],
            'author_connectors': [],
            'page_indicators': [],
            'bibliography_sections': []
        }
        
        text_lower = text.lower()
        
        # Detectar términos de citación
        if detected_lang in self.citation_keywords:
            for keyword in self.citation_keywords[detected_lang]:
                if keyword.lower() in text_lower:
                    features['citation_terms'].append(keyword)
        
        # Detectar conectores entre autores
        if detected_lang in self.author_connectors:
            for connector in self.author_connectors[detected_lang]:
                connector_pattern = r'[A-Z][a-zÀ-ÿ]+\s+' + re.escape(connector) + r'\s+[A-Z][a-zÀ-ÿ]+'
                if re.search(connector_pattern, text):
                    features['author_connectors'].append(connector)
        
        # Detectar indicadores de página
        if detected_lang in self.page_indicators:
            for indicator in self.page_indicators[detected_lang]:
                indicator_pattern = r'\b' + re.escape(indicator) + r'\.?\s\d+'
                if re.search(indicator_pattern, text_lower):
                    features['page_indicators'].append(indicator)
        
        # Detectar secciones bibliográficas
        if detected_lang in self.bibliography_sections:
            for section in self.bibliography_sections[detected_lang]:
                if section in text_lower:
                    features['bibliography_sections'].append(section)
        
        return features
    
    def suggest_citation_style(self, text: str) -> Dict[str, Any]:
        """
        Sugiere un estilo de citación basado en el idioma y características del texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Dict[str, Any]: Sugerencia de estilo de citación
        """
        # Detectar idioma
        lang, conf = self.detect_language(text)
        
        # Detectar características de citación
        features = self.detect_citation_language_features(text, lang)
        
        # Sugerir estilos basados en idioma y características
        suggestions = []
        
        if lang == 'en':
            suggestions = ['APA', 'MLA', 'Chicago', 'Harvard']
        elif lang == 'es':
            suggestions = ['APA', 'ISO 690', 'Chicago']
        elif lang == 'fr':
            suggestions = ['APA', 'ISO 690', 'MLA']
        elif lang == 'de':
            suggestions = ['APA', 'DIN 1505', 'Chicago']
        elif lang == 'it':
            suggestions = ['APA', 'Chicago', 'ISO 690']
        elif lang == 'pt':
            suggestions = ['ABNT', 'APA', 'Chicago']
        else:
            suggestions = ['APA', 'Chicago', 'MLA']  # Estilos internacionales
        
        # Detectar patrones específicos para refinar sugerencias
        
        # Patrón APA: (Autor, año)
        if re.search(r'\([A-Za-zÀ-ÿ\s]+,\s\d{4}\)', text):
            if 'APA' not in suggestions:
                suggestions.insert(0, 'APA')
            elif 'APA' in suggestions:
                suggestions.remove('APA')
                suggestions.insert(0, 'APA')
        
        # Patrón MLA: (Autor página)
        if re.search(r'\([A-Za-zÀ-ÿ\s]+\s\d+\)', text):
            if 'MLA' not in suggestions:
                suggestions.insert(0, 'MLA')
            elif 'MLA' in suggestions:
                suggestions.remove('MLA')
                suggestions.insert(0, 'MLA')
        
        # Patrón Chicago: notas al pie numeradas
        if re.search(r'^\d+\.\s', text, re.MULTILINE):
            if 'Chicago' not in suggestions:
                suggestions.insert(0, 'Chicago')
            elif 'Chicago' in suggestions:
                suggestions.remove('Chicago')
                suggestions.insert(0, 'Chicago')
        
        # Patrón IEEE/Vancouver: [1] o (1)
        if re.search(r'\[\d+\]|\(\d+\)', text):
            if 'IEEE' not in suggestions:
                suggestions.insert(0, 'IEEE')
            if 'Vancouver' not in suggestions and lang in ['en', 'es', 'fr']:
                suggestions.insert(1, 'Vancouver')
        
        return {
            'language': lang,
            'language_confidence': conf,
            'suggested_styles': suggestions,
            'features': features
        }
    
    def translate_citation_term(self, term: str, from_lang: str, to_lang: str) -> str:
        """
        Traduce términos de citación entre idiomas.
        
        Args:
            term (str): Término a traducir
            from_lang (str): Idioma de origen
            to_lang (str): Idioma de destino
            
        Returns:
            str: Término traducido o el original si no se encuentra
        """
        # Mapeo de términos comunes entre idiomas
        term_mappings = {
            'et al': {lang: 'et al' for lang in ['en', 'es', 'fr', 'de', 'it', 'pt']},
            'ibid': {'en': 'ibid', 'es': 'ibídem', 'fr': 'ibid', 'de': 'ebd', 'it': 'ibid', 'pt': 'ibid'},
            'cited in': {'en': 'cited in', 'es': 'citado en', 'fr': 'cité dans', 'de': 'zitiert in', 'it': 'citato in', 'pt': 'citado em'},
            'see': {'en': 'see', 'es': 'véase', 'fr': 'voir', 'de': 'siehe', 'it': 'vedi', 'pt': 'veja'},
            'page': {'en': 'page', 'es': 'página', 'fr': 'page', 'de': 'Seite', 'it': 'pagina', 'pt': 'página'},
            'pages': {'en': 'pages', 'es': 'páginas', 'fr': 'pages', 'de': 'Seiten', 'it': 'pagine', 'pt': 'páginas'},
            'and': {'en': 'and', 'es': 'y', 'fr': 'et', 'de': 'und', 'it': 'e', 'pt': 'e'},
            'references': {'en': 'references', 'es': 'referencias', 'fr': 'références', 'de': 'referenzen', 'it': 'riferimenti', 'pt': 'referências'},
            'bibliography': {'en': 'bibliography', 'es': 'bibliografía', 'fr': 'bibliographie', 'de': 'literaturverzeichnis', 'it': 'bibliografia', 'pt': 'bibliografia'}
        }
        
        # Normalizar término para buscar en el mapeo
        term_lower = term.lower()
        
        for key, translations in term_mappings.items():
            if term_lower == key or term_lower == translations.get(from_lang, '').lower():
                # Devolver traducción manteniendo capitalización original
                translation = translations.get(to_lang, term)
                if term.isupper():
                    return translation.upper()
                elif term[0].isupper():
                    return translation.capitalize()
                return translation
        
        # Si no se encuentra, devolver el original
        return term
    
    def adapt_citation_format(self, citation: str, detected_style: str, 
                            from_lang: str, to_lang: str) -> str:
        """
        Adapta una cita a otro idioma manteniendo el estilo.
        
        Args:
            citation (str): Texto de la cita
            detected_style (str): Estilo de citación detectado
            from_lang (str): Idioma de origen
            to_lang (str): Idioma de destino
            
        Returns:
            str: Cita adaptada al idioma de destino
        """
        # Si los idiomas son iguales, no hay necesidad de adaptar
        if from_lang == to_lang:
            return citation
        
        adapted_citation = citation
        
        # Adaptar según el estilo
        if detected_style == 'APA':
            # Reemplazar conectores
            if from_lang in self.author_connectors and to_lang in self.author_connectors:
                for connector in self.author_connectors[from_lang]:
                    # Solo reemplazar si es un conector completo (no parte de otra palabra)
                    connector_pattern = r'\b' + re.escape(connector) + r'\b'
                    to_connector = self.author_connectors[to_lang][0] if self.author_connectors[to_lang] else connector
                    adapted_citation = re.sub(connector_pattern, to_connector, adapted_citation)
            
            # Reemplazar indicadores de página
            if from_lang in self.page_indicators and to_lang in self.page_indicators:
                for from_indicator in self.page_indicators[from_lang]:
                    indicator_pattern = r'\b' + re.escape(from_indicator) + r'\.?\s\d+'
                    matches = re.findall(indicator_pattern, adapted_citation, re.IGNORECASE)
                    
                    if matches:
                        to_indicator = self.page_indicators[to_lang][0] if self.page_indicators[to_lang] else from_indicator
                        for match in matches:
                            # Extraer número de página
                            page_num = re.search(r'\d+', match).group(0)
                            # Reemplazar con nuevo formato
                            new_format = f"{to_indicator}. {page_num}"
                            adapted_citation = adapted_citation.replace(match, new_format)
        
        elif detected_style == 'MLA' or detected_style == 'Chicago':
            # Reemplazar términos similares a APA
            if from_lang in self.author_connectors and to_lang in self.author_connectors:
                for connector in self.author_connectors[from_lang]:
                    connector_pattern = r'\b' + re.escape(connector) + r'\b'
                    to_connector = self.author_connectors[to_lang][0] if self.author_connectors[to_lang] else connector
                    adapted_citation = re.sub(connector_pattern, to_connector, adapted_citation)
            
            # Para Chicago, adaptar también términos latinos
            if detected_style == 'Chicago':
                latin_terms = ['ibid', 'op. cit.', 'loc. cit.']
                for term in latin_terms:
                    translated_term = self.translate_citation_term(term, from_lang, to_lang)
                    if translated_term != term:
                        term_pattern = r'\b' + re.escape(term) + r'\b'
                        adapted_citation = re.sub(term_pattern, translated_term, adapted_citation, flags=re.IGNORECASE)
        
        # Términos generales de citación
        for term in self.citation_keywords.get(from_lang, []):
            translated_term = self.translate_citation_term(term, from_lang, to_lang)
            if translated_term != term:
                term_pattern = r'\b' + re.escape(term) + r'\b'
                adapted_citation = re.sub(term_pattern, translated_term, adapted_citation, flags=re.IGNORECASE)
        
        return adapted_citation
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Obtiene el nombre completo de un idioma a partir de su código ISO.
        
        Args:
            lang_code (str): Código ISO del idioma
            
        Returns:
            str: Nombre completo del idioma
        """
        language_names = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'nl': 'Nederlands',
            'sv': 'Svenska',
            'ru': 'Русский',
            'ja': '日本語',
            'zh': '中文',
            'ar': 'العربية',
            'ko': '한국어',
            'hi': 'हिन्दी',
            'tr': 'Türkçe',
            'pl': 'Polski',
            'uk': 'Українська',
            'vi': 'Tiếng Việt',
            'th': 'ไทย',
            'el': 'Ελληνικά'
        }
        
        return language_names.get(lang_code, f"Language ({lang_code})")


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del detector de idiomas
    detector = LanguageDetector(use_external_libs=False)  # Sin usar bibliotecas externas
    
    # Ejemplos de texto en diferentes idiomas
    samples = {
        'en': """
        Recent studies have shown a significant correlation between these factors (Smith, 2020, p. 45).
        According to Johnson et al. (2019), the results are consistent with previous research.
        """,
        
        'es': """
        Estudios recientes han demostrado una correlación significativa entre estos factores (García, 2020, p. 45).
        Según Martínez et al. (2019), los resultados son consistentes con investigaciones previas.
        """,
        
        'fr': """
        Des études récentes ont montré une corrélation significative entre ces facteurs (Dubois, 2020, p. 45).
        Selon Martin et al. (2019), les résultats sont cohérents avec les recherches précédentes.
        """,
        
        'de': """
        Neue Studien haben eine signifikante Korrelation zwischen diesen Faktoren gezeigt (Schmidt, 2020, S. 45).
        Laut Müller et al. (2019) stimmen die Ergebnisse mit früheren Forschungen überein.
        """
    }
    
    # Detectar idioma de cada muestra
    print("DETECCIÓN DE IDIOMAS:")
    for lang_code, sample in samples.items():
        detected_lang, confidence = detector.detect_language(sample)
        print(f"Muestra ({lang_code}) -> Detectado: {detected_lang} (confianza: {confidence:.2f})")
        
        # Detectar características específicas de citación
        features = detector.detect_citation_language_features(sample)
        print(f"  Características de citación: {features['citation_terms']}")
        print(f"  Conectores: {features['author_connectors']}")
        
        # Sugerir estilo de citación
        suggestion = detector.suggest_citation_style(sample)
        print(f"  Estilos sugeridos: {suggestion['suggested_styles']}")
        print()
    
    # Ejemplo de adaptación de cita a otro idioma
    print("\nADAPTACIÓN DE CITAS:")
    
    en_citation = "(Smith & Johnson, 2020, p. 45)"
    es_adapted = detector.adapt_citation_format(en_citation, 'APA', 'en', 'es')
    print(f"Original (en): {en_citation}")
    print(f"Adaptada (es): {es_adapted}")
    
    fr_citation = "Selon Dubois et Martin (2019, p. 45)"
    en_adapted = detector.adapt_citation_format(fr_citation, 'APA', 'fr', 'en')
    print(f"Original (fr): {fr_citation}")
    print(f"Adaptada (en): {en_adapted}")