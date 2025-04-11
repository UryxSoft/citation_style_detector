# entity_extraction.py
# Implementación de extracción de entidades nombradas para análisis de citas

import re
import logging
from typing import Dict, List, Tuple, Set, Optional, Any
import unicodedata
from collections import defaultdict

# Intentar importar spaCy si está disponible
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class CitationEntityExtractor:
    """
    Clase para extraer entidades nombradas de textos académicos y citas.
    
    Utiliza técnicas de NLP para identificar autores, títulos, revistas,
    fechas y otros elementos relevantes en citas bibliográficas.
    """
    
    def __init__(self, use_spacy: bool = True, language: str = 'en'):
        """
        Inicializa el extractor de entidades para citas.
        
        Args:
            use_spacy (bool): Si se debe usar spaCy para una extracción más precisa
            language (str): Código ISO del idioma ('en', 'es', etc.)
        """
        self.logger = logging.getLogger('CitationEntityExtractor')
        self.language = language
        
        # Inicializar modelo spaCy si está disponible y se solicita
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.nlp = None
        
        if self.use_spacy:
            try:
                # Cargar el modelo adecuado según el idioma
                if language == 'es':
                    self.nlp = spacy.load("es_core_news_md")
                else:
                    # Por defecto, usar inglés
                    self.nlp = spacy.load("en_core_web_md")
                
                self.logger.info(f"Modelo spaCy cargado: {self.nlp.meta['name']}")
                
                # Registrar componente personalizado si es necesario
                if not Doc.has_extension("citation_entities"):
                    Doc.set_extension("citation_entities", default={})
                
            except Exception as e:
                self.use_spacy = False
                self.logger.warning(f"No se pudo cargar el modelo spaCy: {e}")
                self.logger.warning("Recurriendo a métodos basados en reglas")
        
        # Inicializar patrones y reglas para extracción de entidades
        self._init_entity_patterns()
    
    def _init_entity_patterns(self):
        """
        Inicializa patrones para detectar diferentes tipos de entidades.
        """
        # Patrones para detectar autores
        self.author_patterns = {
            'APA': [
                # Apellido, I. o Apellido, I. I.
                r'([A-Za-zÀ-ÿ\-]+),\s([A-Z]\.(?:\s[A-Z]\.)?)',
                # Autor & Autor o Autor, Autor, & Autor
                r'([A-Za-zÀ-ÿ\-]+(?:,\s[A-Z]\.(?:\s[A-Z]\.)?))(?:,\s|\s&\s|\sy\s)([A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ],
            'MLA': [
                # Apellido, Nombre
                r'([A-Za-zÀ-ÿ\-]+),\s([A-Za-zÀ-ÿ\s]+)',
                # Autor and Autor
                r'([A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s]+)(?:,\s|\sand\s)([A-Za-zÀ-ÿ\-]+(?:,\s[A-Za-zÀ-ÿ\s]+)?)',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ],
            'CHICAGO': [
                # Apellido, Nombre
                r'([A-Za-zÀ-ÿ\-]+),\s([A-Za-zÀ-ÿ\s]+)',
                # Nombre Apellido
                r'([A-Za-zÀ-ÿ\s]+)\s([A-Za-zÀ-ÿ\-]+)',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ],
            'HARVARD': [
                # Apellido, I. o Apellido, I. I.
                r'([A-Za-zÀ-ÿ\-]+),\s([A-Z]\.(?:\s[A-Z]\.)?)',
                # Autor and Autor
                r'([A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)\sand\s([A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ],
            'IEEE': [
                # I. Apellido
                r'([A-Z]\.(?:\s[A-Z]\.)?)\s([A-Za-zÀ-ÿ\-]+)',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ],
            'VANCOUVER': [
                # Apellido AB
                r'([A-Za-zÀ-ÿ\-]+)\s([A-Z]{1,3})',
                # Apellido AB, Apellido CD
                r'([A-Za-zÀ-ÿ\-]+\s[A-Z]{1,3})(?:,\s)([A-Za-zÀ-ÿ\-]+\s[A-Z]{1,3})',
                # et al.
                r'([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.'
            ]
        }
        
        # Patrones para detectar fechas
        self.year_patterns = [
            # Año entre paréntesis
            r'\((\d{4})\)',
            # Año sin paréntesis
            r'(?<![0-9])(\d{4})(?![0-9])',
            # Fecha completa
            r'(\d{1,2})\s(?:de\s)?([A-Za-zÀ-ÿ]+)(?:\sde)?\s(\d{4})',
            r'([A-Za-zÀ-ÿ]+)\s(\d{1,2})(?:,|,\s)?\s(\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]
        
        # Patrones para detectar títulos
        self.title_patterns = {
            'APA': [
                # Título después de año y punto
                r'\(\d{4}\)\.\s([^\.]+)\.',
                # Título de artículo
                r'\(\d{4}\)\.\s([^\.]+)\.\s[A-Za-zÀ-ÿ\s]+,\s\d+'
            ],
            'MLA': [
                # Título de libro (sin comillas)
                r'(?<!["])([A-Z][^\.]+)\.\s[A-Za-zÀ-ÿ\s]+,\s\d{4}',
                # Título de artículo (con comillas)
                r'"([^"]+)"'
            ],
            'CHICAGO': [
                # Título de libro (sin comillas)
                r'(?<!["])([A-Z][^\.]+)\.\s[A-Za-zÀ-ÿ\s]+:',
                # Título de artículo (con comillas)
                r'"([^"]+)"'
            ],
            'generic': [
                # Título entre comillas
                r'"([^"]+)"',
                r'"([^"]+)"',
                # Título en cursiva (difícil de detectar en texto plano)
                r'(?<=[.,:;]\s)([A-Z][^.,:;]+[.,:;])',
                # Título después de autor y año
                r'[A-Za-zÀ-ÿ\-]+(?:,\s[A-Za-zÀ-ÿ\s]+)?\.\s(\d{4}\.\s)([^\.]+)\.'
            ]
        }
        
        # Patrones para detectar revistas/journals
        self.journal_patterns = [
            # Revista, volumen(número)
            r'([A-Za-zÀ-ÿ\s&\-]+),\s\d+\(\d+\)',
            # Revista volumen, número
            r'([A-Za-zÀ-ÿ\s&\-]+)\s\d+,\s(?:no\.|num\.)\s\d+',
            # Revista vol. número
            r'([A-Za-zÀ-ÿ\s&\-]+),\svol\.\s\d+'
        ]
        
        # Patrones para detectar editoriales y lugares de publicación
        self.publisher_patterns = [
            # Editorial después de ciudad y dos puntos
            r'[A-Za-zÀ-ÿ\s\-]+:\s([A-Za-zÀ-ÿ\s&\-]+),\s\d{4}',
            # Editorial antes de año
            r'([A-Za-zÀ-ÿ\s&\-]+),\s\d{4}',
            # Editorial University Press
            r'([A-Za-zÀ-ÿ\s\-]+University\sPress)',
            # Otras editoriales académicas comunes
            r'((?:Oxford|Cambridge|Harvard|Yale|Princeton|Stanford|MIT|Chicago)\sPress)',
            r'(Elsevier|Springer|Wiley|Routledge|SAGE|Taylor\s&\sFrancis|IEEE|ACM)'
        ]
        
        # Patrones para detectar números de página
        self.page_patterns = [
            # p. XX o pp. XX-YY
            r'p\.\s(\d+)',
            r'pp\.\s(\d+)(?:-|\u2013|\u2014)(\d+)',
            # Solo números de página
            r'(?<=:|\s)(\d+)(?:-|\u2013|\u2014)(\d+)'
        ]
        
        # Patrones para detectar DOIs y URLs
        self.identifier_patterns = [
            # DOI
            r'(?:DOI|doi):\s?(10\.\d{4,}(?:\.\d+)*\/[-._;()/:A-Za-z0-9]+)',
            r'https?://doi\.org/(10\.\d{4,}(?:\.\d+)*\/[-._;()/:A-Za-z0-9]+)',
            # URL
            r'(https?://[^\s]+)'
        ]
        
        # Palabras clave para identificar roles de autor
        self.author_role_keywords = {
            'editor': [r'(?:Ed\.|Eds\.|Editor|Editores|edited by)'],
            'translator': [r'(?:Trans\.|Trad\.|Translator|Traductor|translated by)'],
            'compiler': [r'(?:Comp\.|Compilador|compiled by)'],
            'director': [r'(?:Dir\.|Director|directed by)']
        }
    
    def extract_entities(self, text: str, style: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Extrae todas las entidades nombradas relevantes del texto.
        
        Args:
            text (str): Texto del que extraer entidades
            style (str, optional): Estilo de citación. Si es None, se utilizarán
                                  patrones genéricos.
        
        Returns:
            Dict[str, List[str]]: Entidades extraídas por tipo
        """
        entities = {
            'authors': [],
            'years': [],
            'titles': [],
            'journals': [],
            'publishers': [],
            'pages': [],
            'identifiers': []
        }
        
        # Si se especificó usar spaCy y está disponible, usar estrategia híbrida
        if self.use_spacy and self.nlp:
            # Extraer entidades con spaCy
            doc = self.nlp(text)
            spacy_entities = self._extract_spacy_entities(doc)
            
            # Combinar con entidades basadas en reglas
            rule_entities = self._extract_rule_based_entities(text, style)
            
            # Fusionar resultados, priorizando spaCy para personas y organizaciones
            entities['authors'] = spacy_entities.get('PERSON', [])
            if not entities['authors']:
                entities['authors'] = rule_entities.get('authors', [])
            
            entities['publishers'] = spacy_entities.get('ORG', [])
            if not entities['publishers']:
                entities['publishers'] = rule_entities.get('publishers', [])
            
            # Para el resto, usar resultados basados en reglas
            entities['years'] = rule_entities.get('years', [])
            entities['titles'] = rule_entities.get('titles', [])
            entities['journals'] = rule_entities.get('journals', [])
            entities['pages'] = rule_entities.get('pages', [])
            entities['identifiers'] = rule_entities.get('identifiers', [])
            
            # Añadir lugares de publicación desde spaCy
            if 'GPE' in spacy_entities and spacy_entities['GPE']:
                entities['locations'] = spacy_entities['GPE']
        else:
            # Si spaCy no está disponible, usar solo reglas
            rule_entities = self._extract_rule_based_entities(text, style)
            for key in rule_entities:
                if key in entities:
                    entities[key] = rule_entities[key]
        
        # Post-procesar y limpiar entidades
        entities = self._clean_entities(entities)
        
        return entities
    
    def _extract_spacy_entities(self, doc) -> Dict[str, List[str]]:
        """
        Extrae entidades usando el modelo spaCy.
        
        Args:
            doc: Documento procesado por spaCy
            
        Returns:
            Dict[str, List[str]]: Entidades por tipo
        """
        entities = defaultdict(list)
        
        # Extraer entidades nombradas estándar
        for ent in doc.ents:
            # Filtrar entidades muy cortas
            if len(ent.text) > 1:
                entities[ent.label_].append(ent.text)
        
        # Buscar otras estructuras relevantes en el análisis sintáctico
        
        # Posibles títulos (sintagmas nominales largos)
        noun_chunks = list(doc.noun_chunks)
        for chunk in noun_chunks:
            # Si el sintagma es lo suficientemente largo para ser un título
            if len(chunk.text) > 15 and chunk.text not in entities['TITLE']:
                entities['TITLE'].append(chunk.text)
        
        # Detectar fechas no capturadas como entidades
        for token in doc:
            if token.is_digit and len(token.text) == 4 and 1900 <= int(token.text) <= 2100:
                if token.text not in entities['DATE']:
                    entities['DATE'].append(token.text)
        
        # Convertir a formato de texto
        result = {k: [str(v) for v in vals] for k, vals in entities.items()}
        
        return result
    
    def _extract_rule_based_entities(self, text: str, style: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Extrae entidades basadas en patrones y reglas.
        
        Args:
            text (str): Texto del que extraer entidades
            style (str, optional): Estilo de citación
            
        Returns:
            Dict[str, List[str]]: Entidades extraídas por tipo
        """
        entities = {
            'authors': self._extract_authors(text, style),
            'years': self._extract_years(text),
            'titles': self._extract_titles(text, style),
            'journals': self._extract_journals(text),
            'publishers': self._extract_publishers(text),
            'pages': self._extract_pages(text),
            'identifiers': self._extract_identifiers(text)
        }
        
        return entities
    
    def _extract_authors(self, text: str, style: Optional[str] = None) -> List[str]:
        """
        Extrae nombres de autores del texto.
        
        Args:
            text (str): Texto del que extraer autores
            style (str, optional): Estilo de citación
            
        Returns:
            List[str]: Lista de autores extraídos
        """
        authors = []
        
        # Seleccionar patrones según el estilo
        patterns = []
        if style and style in self.author_patterns:
            patterns = self.author_patterns[style]
        else:
            # Si no se especifica estilo, usar todos los patrones
            for style_patterns in self.author_patterns.values():
                patterns.extend(style_patterns)
        
        # Eliminar duplicados de patrones
        patterns = list(set(patterns))
        
        # Aplicar patrones
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Extraer autor completo (todo el match)
                author = match.group(0).strip()
                
                # Verificar si es un falso positivo típico
                if self._is_valid_author(author):
                    authors.append(author)
                
                # Extraer autores individuales en caso de múltiples
                if len(match.groups()) > 0:
                    for group in match.groups():
                        if group and self._is_valid_author(group):
                            if group not in authors:
                                authors.append(group.strip())
        
        # Detectar roles de autor (editor, traductor, etc.)
        authors_with_roles = []
        for author in authors:
            role = self._detect_author_role(author)
            if role:
                authors_with_roles.append((author, role))
            else:
                authors_with_roles.append((author, 'author'))
        
        # Simplificar resultado a solo nombres
        unique_authors = []
        seen = set()
        for author, _ in authors_with_roles:
            normalized_author = self._normalize_name(author)
            if normalized_author and normalized_author not in seen:
                seen.add(normalized_author)
                unique_authors.append(author)
        
        return unique_authors
    
    def _is_valid_author(self, author: str) -> bool:
        """
        Verifica si un texto extraído es realmente un nombre de autor válido.
        
        Args:
            author (str): Texto del autor extraído
            
        Returns:
            bool: True si es un autor válido, False en caso contrario
        """
        # Verificar longitud mínima
        if len(author) < 3:
            return False
        
        # Evitar falsos positivos comunes
        false_positives = [
            'vol.', 'p.', 'pp.', 'ed.', 'eds.', 'trans.', 'comp.',
            'retrieved', 'accessed', 'disponible', 'available',
            'http', 'www', 'doi', 'isbn', 'issn', 'pdf', 'html',
            'abstract', 'resumen', 'keywords', 'palabras clave',
            'introduction', 'introducción', 'method', 'método',
            'results', 'resultados', 'discussion', 'discusión',
            'conclusion', 'conclusión', 'references', 'referencias',
            'chapter', 'capítulo', 'section', 'sección'
        ]
        
        for fp in false_positives:
            if fp in author.lower():
                return False
        
        # Verificar que contiene al menos una letra
        if not re.search(r'[A-Za-zÀ-ÿ]', author):
            return False
        
        # Evitar fechas o números sueltos
        if re.match(r'^\d+$', author):
            return False
        
        return True
    
    def _normalize_name(self, name: str) -> str:
        """
        Normaliza un nombre para comparaciones.
        
        Args:
            name (str): Nombre a normalizar
            
        Returns:
            str: Nombre normalizado
        """
        # Convertir a minúsculas
        normalized = name.lower()
        
        # Eliminar puntuación excepto guiones
        normalized = re.sub(r'[^\w\s\-]', '', normalized)
        
        # Eliminar roles (editor, traductor, etc.)
        for role_patterns in self.author_role_keywords.values():
            for pattern in role_patterns:
                normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _detect_author_role(self, author: str) -> Optional[str]:
        """
        Detecta el rol de un autor (editor, traductor, etc.).
        
        Args:
            author (str): Nombre del autor
            
        Returns:
            Optional[str]: Rol detectado o None
        """
        for role, patterns in self.author_role_keywords.items():
            for pattern in patterns:
                if re.search(pattern, author, re.IGNORECASE):
                    return role
        
        return None
    
    def _extract_years(self, text: str) -> List[str]:
        """
        Extrae años y fechas del texto.
        
        Args:
            text (str): Texto del que extraer años
            
        Returns:
            List[str]: Lista de años y fechas
        """
        years = []
        
        for pattern in self.year_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Si el patrón captura año completo (YYYY)
                if len(match.groups()) == 1:
                    year = match.group(1)
                    # Verificar que es un año razonable (1400-2100)
                    if 1400 <= int(year) <= 2100:
                        years.append(year)
                
                # Si el patrón captura fecha completa
                elif len(match.groups()) >= 3:
                    # Extraer componentes de fecha
                    components = [g for g in match.groups() if g]
                    if len(components) >= 3:
                        # Buscar el componente que parece ser el año (4 dígitos)
                        for component in components:
                            if re.match(r'^\d{4}$', component) and 1400 <= int(component) <= 2100:
                                if component not in years:
                                    years.append(component)
        
        return years
    
    def _extract_titles(self, text: str, style: Optional[str] = None) -> List[str]:
        """
        Extrae títulos de obras del texto.
        
        Args:
            text (str): Texto del que extraer títulos
            style (str, optional): Estilo de citación
            
        Returns:
            List[str]: Lista de títulos
        """
        titles = []
        
        # Seleccionar patrones según el estilo
        patterns = []
        if style and style in self.title_patterns:
            patterns = self.title_patterns[style]
        else:
            # Usar patrones genéricos si no se especifica estilo
            patterns = self.title_patterns['generic']
        
        # Aplicar patrones
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.groups():
                    title = match.group(1).strip()
                    # Verificar que es un título válido
                    if self._is_valid_title(title):
                        titles.append(title)
        
        # Eliminar duplicados
        unique_titles = []
        seen = set()
        for title in titles:
            normalized = self._normalize_title(title)
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_titles.append(title)
        
        return unique_titles
    
    def _is_valid_title(self, title: str) -> bool:
        """
        Verifica si un texto extraído es realmente un título válido.
        
        Args:
            title (str): Texto del título
            
        Returns:
            bool: True si es un título válido, False en caso contrario
        """
        # Verificar longitud mínima
        if len(title) < 5:
            return False
        
        # Evitar fragmentos que parecen ser parte de URLs o DOIs
        if 'http://' in title or 'https://' in title or 'doi.org' in title:
            return False
        
        # Evitar fechas sueltas o páginas
        if re.match(r'^\d+$', title):
            return False
        
        # Evitar secciones típicas de artículos
        sections = [
            'abstract', 'resumen', 'introduction', 'introducción',
            'method', 'método', 'results', 'resultados',
            'discussion', 'discusión', 'conclusion', 'conclusión',
            'references', 'referencias', 'bibliography', 'bibliografía'
        ]
        
        if title.lower() in sections:
            return False
        
        return True
    
    def _normalize_title(self, title: str) -> str:
        """
        Normaliza un título para comparaciones.
        
        Args:
            title (str): Título a normalizar
            
        Returns:
            str: Título normalizado
        """
        # Convertir a minúsculas
        normalized = title.lower()
        
        # Eliminar puntuación
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_journals(self, text: str) -> List[str]:
        """
        Extrae nombres de revistas académicas del texto.
        
        Args:
            text (str): Texto del que extraer revistas
            
        Returns:
            List[str]: Lista de revistas
        """
        journals = []
        
        for pattern in self.journal_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.groups():
                    journal = match.group(1).strip()
                    # Verificar que es un nombre de revista válido
                    if self._is_valid_journal(journal):
                        journals.append(journal)
        
        # Eliminar duplicados
        unique_journals = []
        seen = set()
        for journal in journals:
            normalized = journal.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique_journals.append(journal)
        
        return unique_journals
    
    def _is_valid_journal(self, journal: str) -> bool:
        """
        Verifica si un texto extraído es realmente un nombre de revista válido.
        
        Args:
            journal (str): Texto de la revista
            
        Returns:
            bool: True si es una revista válida, False en caso contrario
        """
        # Verificar longitud mínima
        if len(journal) < 3:
            return False
        
        # Evitar fragmentos que parecen ser URLs o DOIs
        if 'http://' in journal or 'https://' in journal or 'doi.org' in journal:
            return False
        
        # Evitar años o números de página
        if re.match(r'^\d+$', journal):
            return False
        
        # Evitar nombres de editoriales comunes
        publishers = [
            'oxford university press', 'cambridge university press',
            'harvard university press', 'yale university press',
            'princeton university press', 'stanford university press',
            'mit press', 'university of chicago press',
            'elsevier', 'springer', 'wiley', 'routledge',
            'sage', 'taylor & francis', 'ieee', 'acm'
        ]
        
        if journal.lower() in publishers:
            return False
        
        return True
    
    def _extract_publishers(self, text: str) -> List[str]:
        """
        Extrae nombres de editoriales del texto.
        
        Args:
            text (str): Texto del que extraer editoriales
            
        Returns:
            List[str]: Lista de editoriales
        """
        publishers = []
        
        for pattern in self.publisher_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.groups():
                    publisher = match.group(1).strip()
                    # Verificar que es un nombre de editorial válido
                    if self._is_valid_publisher(publisher):
                        publishers.append(publisher)
        
        # Eliminar duplicados
        unique_publishers = []
        seen = set()
        for publisher in publishers:
            normalized = publisher.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique_publishers.append(publisher)
        
        return unique_publishers
    
    def _is_valid_publisher(self, publisher: str) -> bool:
        """
        Verifica si un texto extraído es realmente un nombre de editorial válido.
        
        Args:
            publisher (str): Texto de la editorial
            
        Returns:
            bool: True si es una editorial válida, False en caso contrario
        """
        # Verificar longitud mínima
        if len(publisher) < 3:
            return False
        
        # Evitar fragmentos que parecen ser URLs o DOIs
        if 'http://' in publisher or 'https://' in publisher or 'doi.org' in publisher:
            return False
        
        # Evitar años o números de página
        if re.match(r'^\d+$', publisher):
            return False
        
        return True
    
    def _extract_pages(self, text: str) -> List[str]:
        """
        Extrae números de página del texto.
        
        Args:
            text (str): Texto del que extraer páginas
            
        Returns:
            List[str]: Lista de referencias a páginas
        """
        pages = []
        
        for pattern in self.page_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Extraer info de páginas
                if match.groups():
                    # Un solo número de página
                    if len(match.groups()) == 1:
                        page = f"p. {match.group(1)}"
                        pages.append(page)
                    # Rango de páginas
                    elif len(match.groups()) == 2:
                        start, end = match.groups()
                        page_range = f"pp. {start}-{end}"
                        pages.append(page_range)
        
        # Eliminar duplicados
        unique_pages = list(set(pages))
        
        return unique_pages
    
    def _extract_identifiers(self, text: str) -> List[str]:
        """
        Extrae identificadores como DOIs y URLs del texto.
        
        Args:
            text (str): Texto del que extraer identificadores
            
        Returns:
            List[str]: Lista de identificadores
        """
        identifiers = []
        
        for pattern in self.identifier_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.groups():
                    identifier = match.group(1).strip()
                    # Eliminar caracteres finales que no pertenecen al identificador
                    identifier = re.sub(r'[,.\)]$', '', identifier)
                    identifiers.append(identifier)
        
        # Eliminar duplicados
        unique_identifiers = list(set(identifiers))
        
        return unique_identifiers
    
    def _clean_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Limpia y normaliza las entidades extraídas.
        
        Args:
            entities (Dict[str, List[str]]): Entidades extraídas
            
        Returns:
            Dict[str, List[str]]: Entidades limpias y normalizadas
        """
        cleaned = {}
        
        for key, values in entities.items():
            # Eliminar duplicados
            unique_values = []
            seen = set()
            
            for value in values:
                # Normalizar valor
                normalized = self._normalize_entity(value, key)
                
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    # Mantener el valor original, no el normalizado
                    unique_values.append(value)
            
            cleaned[key] = unique_values
        
        return cleaned
    
    def _normalize_entity(self, entity: str, entity_type: str) -> str:
        """
        Normaliza una entidad para comparación y deduplicación.
        
        Args:
            entity (str): Entidad a normalizar
            entity_type (str): Tipo de entidad
            
        Returns:
            str: Entidad normalizada
        """
        if not entity:
            return ""
        
        # Normalización básica para todos los tipos
        normalized = entity.strip()
        
        # Normalización específica por tipo
        if entity_type == 'authors':
            normalized = self._normalize_name(normalized)
        elif entity_type == 'titles':
            normalized = self._normalize_title(normalized)
        elif entity_type in ['journals', 'publishers']:
            # Convertir a minúsculas
            normalized = normalized.lower()
            # Eliminar puntuación
            normalized = re.sub(r'[^\w\s]', '', normalized)
            # Normalizar espacios
            normalized = re.sub(r'\s+', ' ', normalized).strip()
        elif entity_type == 'identifiers':
            # Para URLs y DOIs, eliminar elementos no esenciales
            normalized = re.sub(r'^https?://(www\.)?', '', normalized.lower())
            normalized = re.sub(r'/$', '', normalized)
        
        return normalized
    
    def extract_structured_citations(self, text: str, style: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extrae citas estructuradas con todas sus entidades relacionadas.
        
        Args:
            text (str): Texto completo a analizar
            style (str, optional): Estilo de citación
            
        Returns:
            List[Dict[str, Any]]: Lista de citas estructuradas
        """
        structured_citations = []
        
        # Dividir el texto en párrafos
        paragraphs = re.split(r'\n\s*\n', text)
        
        for i, paragraph in enumerate(paragraphs):
            # Identificar líneas que parecen ser entradas bibliográficas completas
            if self._looks_like_bibliography_entry(paragraph, style):
                # Extraer entidades de esta entrada
                entities = self.extract_entities(paragraph, style)
                
                # Crear una cita estructurada
                citation = {
                    'text': paragraph,
                    'type': 'bibliography',
                    'position': i,
                    'authors': entities.get('authors', []),
                    'year': entities.get('years', []),
                    'title': entities.get('titles', []),
                    'journal': entities.get('journals', []),
                    'publisher': entities.get('publishers', []),
                    'pages': entities.get('pages', []),
                    'identifiers': entities.get('identifiers', [])
                }
                
                structured_citations.append(citation)
            else:
                # Buscar citas en texto dentro del párrafo
                in_text_citations = self._extract_in_text_citations(paragraph, style)
                
                for citation_text in in_text_citations:
                    # Extraer entidades de esta cita
                    entities = self.extract_entities(citation_text, style)
                    
                    # Crear una cita estructurada
                    citation = {
                        'text': citation_text,
                        'type': 'in_text',
                        'position': i,
                        'context': paragraph,
                        'authors': entities.get('authors', []),
                        'year': entities.get('years', []),
                        'pages': entities.get('pages', [])
                    }
                    
                    structured_citations.append(citation)
        
        # Establecer relaciones entre citas en texto y entradas bibliográficas
        structured_citations = self._link_citations(structured_citations, style)
        
        return structured_citations
    
    def _looks_like_bibliography_entry(self, text: str, style: Optional[str] = None) -> bool:
        """
        Determina si un fragmento de texto parece ser una entrada bibliográfica.
        
        Args:
            text (str): Texto a analizar
            style (str, optional): Estilo de citación
            
        Returns:
            bool: True si parece una entrada bibliográfica, False en caso contrario
        """
        # Verificar longitud mínima
        if len(text) < 20:
            return False
        
        # Verificar si comienza con patrones típicos según el estilo
        if style == 'APA':
            # Apellido, I. (Año).
            return bool(re.match(r'^[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)\.', text))
        
        elif style == 'MLA':
            # Apellido, Nombre.
            return bool(re.match(r'^[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s]+\.', text))
        
        elif style == 'CHICAGO':
            # Apellido, Nombre.
            return bool(re.match(r'^[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s]+\.', text))
        
        elif style == 'HARVARD':
            # Apellido, I. (Año)
            return bool(re.match(r'^[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)', text))
        
        elif style == 'IEEE':
            # [n] I. Apellido,
            return bool(re.match(r'^\[\d+\]\s[A-Z]\.\s[A-Za-zÀ-ÿ\-]+', text))
        
        elif style == 'VANCOUVER':
            # n. Apellido AB,
            return bool(re.match(r'^\d+\.\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,3}', text))
        
        else:
            # Patrones generales para cualquier estilo
            patterns = [
                r'^[A-Za-zÀ-ÿ\-]+,\s',  # Comienza con apellido y coma
                r'^\[\d+\]',  # Comienza con número entre corchetes
                r'^\d+\.\s[A-Za-zÀ-ÿ\-]+'  # Comienza con número, punto y apellido
            ]
            
            return any(re.match(pattern, text) for pattern in patterns)
    
    def _extract_in_text_citations(self, text: str, style: Optional[str] = None) -> List[str]:
        """
        Extrae citas en texto de un párrafo.
        
        Args:
            text (str): Texto a analizar
            style (str, optional): Estilo de citación
            
        Returns:
            List[str]: Lista de citas en texto
        """
        citations = []
        
        # Patrones específicos según el estilo
        if style == 'APA':
            # (Autor, año) o (Autor, año, p. xx)
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,|\s&|\sy)\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\(\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)'
            ]
        
        elif style == 'MLA':
            # (Autor página)
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\d+(?:-\d+)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\(\d+(?:-\d+)?\)'
            ]
        
        elif style == 'CHICAGO':
            # (Autor año, página) o notas al pie
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\d{4}(?:,\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\(\d{4}(?:,\s\d+(?:-\d+)?)?\)',
                r'(?<!\w)(\d+)(?:\s*\[\s*nota\s*\]|\s*\[\s*footnote\s*\])?(?!\w)'
            ]
        
        elif style == 'HARVARD':
            # (Autor, año: página)
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,|\sand)\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?,\s\d{4}(?::\s\d+(?:-\d+)?)?\)',
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?,\s\d{4}(?::\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\(\d{4}(?::\s\d+(?:-\d+)?)?\)'
            ]
        
        elif style == 'IEEE' or style == 'VANCOUVER':
            # [n] o (n)
            patterns = [
                r'\[\d+(?:,\s*\d+)*\]',
                r'\(\d+(?:,\s*\d+)*\)',
                r'(?<!\w)(\d+)(?:\s*\[\s*ref\s*\])?(?!\w)'
            ]
        
        else:
            # Patrones genéricos para cualquier estilo
            patterns = [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,|\s&|\sy|\sand)\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?,\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?\s\(\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)',
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:\sand\s[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?\s\d+(?:-\d+)?\)',
                r'\[\d+(?:,\s*\d+)*\]',
                r'\(\d+(?:,\s*\d+)*\)'
            ]
        
        # Aplicar patrones
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group(0)
                citations.append(citation)
        
        return citations
    
    def _link_citations(self, citations: List[Dict[str, Any]], style: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Establece relaciones entre citas en texto y entradas bibliográficas.
        
        Args:
            citations (List[Dict[str, Any]]): Lista de citas estructuradas
            style (str, optional): Estilo de citación
            
        Returns:
            List[Dict[str, Any]]: Citas con relaciones establecidas
        """
        # Separar citas en texto y entradas bibliográficas
        in_text = [c for c in citations if c['type'] == 'in_text']
        bibliography = [c for c in citations if c['type'] == 'bibliography']
        
        # Para cada cita en texto, encontrar su correspondiente entrada bibliográfica
        for i, citation in enumerate(in_text):
            # Obtener autor y año de la cita
            authors = citation.get('authors', [])
            years = citation.get('year', [])
            
            author = authors[0] if authors else ""
            year = years[0] if years else ""
            
            # Buscar coincidencias en la bibliografía
            matches = []
            for bib_entry in bibliography:
                bib_authors = bib_entry.get('authors', [])
                bib_years = bib_entry.get('year', [])
                
                # Verificar coincidencia
                if self._is_matching_citation_entities(author, year, bib_authors, bib_years, style):
                    matches.append(bib_entry)
            
            # Añadir referencia a entrada bibliográfica
            if matches:
                in_text[i]['bibliography_ref'] = matches[0].get('text', '')
                in_text[i]['bibliography_idx'] = bibliography.index(matches[0])
        
        # Combinar las listas
        return in_text + bibliography
    
    def _is_matching_citation_entities(self, author: str, year: str, 
                                     bib_authors: List[str], bib_years: List[str], 
                                     style: Optional[str] = None) -> bool:
        """
        Determina si una cita en texto corresponde a una entrada bibliográfica.
        
        Args:
            author (str): Autor en la cita en texto
            year (str): Año en la cita en texto
            bib_authors (List[str]): Autores en la entrada bibliográfica
            bib_years (List[str]): Años en la entrada bibliográfica
            style (str, optional): Estilo de citación
            
        Returns:
            bool: True si hay correspondencia, False en caso contrario
        """
        # Si no hay información suficiente para comparar
        if not author and not year:
            return False
        
        if not bib_authors and not bib_years:
            return False
        
        # Normalizar autor
        author_norm = self._normalize_name(author) if author else ""
        
        # En MLA, solo comparamos autor
        if style == 'MLA':
            for bib_author in bib_authors:
                bib_author_norm = self._normalize_name(bib_author)
                
                # Verificar si el autor de la cita está en el autor bibliográfico
                if author_norm and bib_author_norm and (author_norm in bib_author_norm or bib_author_norm in author_norm):
                    return True
            
            return False
        
        # Para otros estilos, verificar autor y año
        for bib_author in bib_authors:
            bib_author_norm = self._normalize_name(bib_author)
            
            author_match = (author_norm and bib_author_norm and 
                           (author_norm in bib_author_norm or bib_author_norm in author_norm))
            
            if author_match:
                # Verificar coincidencia de año
                for bib_year in bib_years:
                    year_match = (year == bib_year)
                    
                    if year_match or not year:
                        return True
        
        return False
    
    def analyze_entity_relationships(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analiza relaciones entre las entidades extraídas.
        
        Args:
            entities (Dict[str, List[str]]): Entidades extraídas
            
        Returns:
            Dict[str, Any]: Análisis de relaciones
        """
        analysis = {
            'author_contributions': [],
            'publication_years': {},
            'journals_frequency': {},
            'publishers_frequency': {},
            'entity_network': {}
        }
        
        # Análisis de contribuciones por autor
        authors = entities.get('authors', [])
        years = entities.get('years', [])
        titles = entities.get('titles', [])
        
        # Crear grafo simple de co-autoría
        author_network = defaultdict(list)
        
        # Si hay suficientes datos para relacionar
        if authors and years and titles:
            # Asumir que las entidades están relacionadas por orden de aparición
            # (esto es una simplificación; en un sistema real, habría que analizar la estructura del texto)
            min_length = min(len(authors), len(years), len(titles))
            
            for i in range(min_length):
                author = authors[i]
                year = years[i] if i < len(years) else ""
                title = titles[i] if i < len(titles) else ""
                
                analysis['author_contributions'].append({
                    'author': author,
                    'year': year,
                    'title': title
                })
                
                # Actualizar estadísticas de años
                if year:
                    analysis['publication_years'][year] = analysis['publication_years'].get(year, 0) + 1
        
        # Frecuencia de revistas y editoriales
        for journal in entities.get('journals', []):
            analysis['journals_frequency'][journal] = analysis['journals_frequency'].get(journal, 0) + 1
        
        for publisher in entities.get('publishers', []):
            analysis['publishers_frequency'][publisher] = analysis['publishers_frequency'].get(publisher, 0) + 1
        
        # Construir grafo simple de relaciones entre entidades
        # (autores relacionados con títulos, revistas, etc.)
        entity_network = defaultdict(list)
        
        for key, values in entities.items():
            for value in values:
                entity_network[key].append(value)
                
                # Relacionar con otros tipos de entidades
                for other_key, other_values in entities.items():
                    if other_key != key:
                        entity_network[value] = other_values
        
        analysis['entity_network'] = dict(entity_network)
        
        return analysis


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del extractor de entidades
    extractor = CitationEntityExtractor(use_spacy=False)  # Sin spaCy para simplicidad
    
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
    
    # Extraer entidades
    entities = extractor.extract_entities(sample_text, 'APA')
    
    # Imprimir resultados
    print("ENTIDADES EXTRAÍDAS:")
    for entity_type, entity_list in entities.items():
        print(f"\n{entity_type.upper()}:")
        for entity in entity_list:
            print(f"- {entity}")
    
    # Extraer citas estructuradas
    print("\n\nCITAS ESTRUCTURADAS:")
    structured_citations = extractor.extract_structured_citations(sample_text, 'APA')
    
    for citation in structured_citations:
        print(f"\nTipo: {citation['type']}")
        print(f"Texto: {citation['text']}")
        
        if citation['type'] == 'in_text':
            if 'bibliography_ref' in citation:
                print(f"Referencia bibliográfica: {citation['bibliography_ref'][:50]}...")