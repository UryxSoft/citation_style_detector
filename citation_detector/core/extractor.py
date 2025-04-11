# extractor.py
# Implementación de extracción de citas

import re
import logging
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict


class CitationExtractor:
    """
    Clase para extraer citas y referencias bibliográficas de textos académicos.
    
    Permite identificar y extraer citas en texto y entradas bibliográficas
    para diferentes estilos de citación, incluyendo APA, MLA, Chicago, etc.
    """
    
    def __init__(self, patterns=None):
        """
        Inicializa el extractor de citas.
        
        Args:
            patterns: Instancia opcional de CitationPatterns para usar patrones predefinidos
        """
        self.logger = logging.getLogger('CitationExtractor')
        self.patterns = patterns
        
        # Inicializar patrones básicos para detección de secciones
        self._init_section_patterns()
    
    def _init_section_patterns(self):
        """
        Inicializa patrones para detectar secciones de bibliografía.
        """
        # Encabezados comunes de secciones de bibliografía por estilo
        self.bibliography_headers = {
            'APA': [
                r'(?i)^Referencias$',
                r'(?i)^Referencias bibliográficas$',
                r'(?i)^Bibliografía$',
                r'(?i)^References$',
                r'(?i)^Reference List$',
                r'(?i)^Bibliography$'
            ],
            'MLA': [
                r'(?i)^Obras citadas$',
                r'(?i)^Works Cited$',
                r'(?i)^Bibliografía$',
                r'(?i)^Bibliography$'
            ],
            'CHICAGO': [
                r'(?i)^Bibliografía$',
                r'(?i)^Bibliography$',
                r'(?i)^Referencias$',
                r'(?i)^References$',
                r'(?i)^Notas$',
                r'(?i)^Notes$'
            ],
            'HARVARD': [
                r'(?i)^Referencias$',
                r'(?i)^Referencias bibliográficas$',
                r'(?i)^Bibliografía$',
                r'(?i)^Reference List$',
                r'(?i)^References$'
            ],
            'IEEE': [
                r'(?i)^Referencias$',
                r'(?i)^References$'
            ],
            'VANCOUVER': [
                r'(?i)^Referencias$',
                r'(?i)^References$',
                r'(?i)^Bibliografía$',
                r'(?i)^Bibliography$'
            ],
            'CSE': [
                r'(?i)^Referencias$',
                r'(?i)^References$',
                r'(?i)^Cited References$',
                r'(?i)^Referencias citadas$',
                r'(?i)^Bibliografía$',
                r'(?i)^Bibliography$'
            ]
        }
        
        # Patrones básicos para citas en texto por estilo
        self.in_text_patterns = {
            'APA': [
                r'\((?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,| &| y) )?[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?, \d{4}(?:, p\.? \d+(?:-\d+)?)?\)',
                r'(?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?:,| &| y) )?[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)? \(\d{4}(?:, p\.? \d+(?:-\d+)?)?\)'
            ],
            'MLA': [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)? \d+(?:-\d+)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)? \(\d+(?:-\d+)?\)'
            ],
            'CHICAGO_AUTHOR_DATE': [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)? \d{4}(?:, \d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)? \(\d{4}(?:, \d+(?:-\d+)?)?\)'
            ],
            'CHICAGO_NOTES': [
                r'^\d+\.\s.+',
                r'(?:Ibid\.|Op\. cit\.|Loc\. cit\.)(?:,\s\d+(?:-\d+)?)?'
            ],
            'HARVARD': [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)?, \d{4}(?::\s?\d+(?:-\d+)?)?\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?(?: and [A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)? \(\d{4}(?::\s?\d+(?:-\d+)?)?\)'
            ],
            'IEEE': [
                r'\[\d+\]',
                r'\[\d+(?:,\s*\d+)*\]'
            ],
            'VANCOUVER': [
                r'\(\d+\)',
                r'\[\d+\]',
                r'(?:^|\s)[\u00B9\u00B2\u00B3\u2070-\u2079]+'
            ],
            'CSE': [
                r'\([A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)? \d{4}\)',
                r'[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)? \d{4}',
                r'\[\d+\]',
                r'\[[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?:,\s\d{4})?\]'
            ]
        }
    
    def extract_all_citations(self, text: str, style: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Extrae todas las citas de un texto.
        
        Args:
            text (str): Texto completo a analizar
            style (str, optional): Estilo de citación ('APA', 'MLA', etc.). Si es None,
                                  se intentará detectar automáticamente.
        
        Returns:
            Dict[str, List[str]]: Diccionario con citas extraídas por tipo
                                 ('en_texto', 'bibliograficas')
        """
        result = {
            'en_texto': [],
            'bibliograficas': []
        }
        
        # Si no se especifica un estilo, intentar detectarlo
        if not style:
            style = self._detect_citation_style(text)
        
        # Extraer citas en texto
        result['en_texto'] = self.extract_in_text_citations(text, style)
        
        # Extraer citas bibliográficas
        result['bibliograficas'] = self.extract_bibliography_citations(text, style)
        
        return result
    
    def extract_in_text_citations(self, text: str, style: str) -> List[str]:
        """
        Extrae citas en texto según un estilo específico.
        
        Args:
            text (str): Texto a analizar
            style (str): Estilo de citación
            
        Returns:
            List[str]: Lista de citas en texto encontradas
        """
        citations = []
        
        # Separar el texto de la bibliografía para evitar falsos positivos
        main_text = self._extract_main_text(text)
        
        # Patrones a utilizar según el estilo
        patterns = []
        
        # Si se usan patrones desde una clase externa
        if self.patterns and hasattr(self.patterns, 'get_pattern'):
            patterns = self.patterns.get_pattern(style, 'in_text')
        else:
            # Usar patrones locales básicos
            if style == 'CHICAGO':
                # Para Chicago, revisar tanto autor-fecha como notas
                patterns = self.in_text_patterns.get('CHICAGO_AUTHOR_DATE', []) + \
                          self.in_text_patterns.get('CHICAGO_NOTES', [])
            else:
                patterns = self.in_text_patterns.get(style, [])
        
        # Si no hay patrones disponibles, probar con todos los estilos
        if not patterns:
            for s, ps in self.in_text_patterns.items():
                patterns.extend(ps)
        
        # Aplicar cada patrón al texto principal
        for pattern in patterns:
            if isinstance(pattern, str):
                # Compilar el patrón si es una cadena
                pattern = re.compile(pattern)
            
            # Buscar coincidencias
            if hasattr(pattern, 'finditer'):
                for match in pattern.finditer(main_text):
                    citation = match.group(0)
                    
                    # Validar la cita (evitar falsos positivos)
                    if self._is_valid_citation(citation, style, 'in_text'):
                        citations.append(citation)
            else:
                # Fallback para patrones como cadenas
                matches = re.findall(pattern, main_text)
                for match in matches:
                    if isinstance(match, str):
                        citation = match
                    else:
                        # Para tuplas de grupos de captura
                        citation = match[0] if match else ""
                    
                    if citation and self._is_valid_citation(citation, style, 'in_text'):
                        citations.append(citation)
        
        # Eliminar duplicados preservando el orden
        unique_citations = []
        seen = set()
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def extract_bibliography_citations(self, text: str, style: str) -> List[str]:
        """
        Extrae entradas bibliográficas según un estilo específico.
        
        Args:
            text (str): Texto a analizar
            style (str): Estilo de citación
            
        Returns:
            List[str]: Lista de entradas bibliográficas encontradas
        """
        # Extraer la sección de bibliografía
        bib_section = self._extract_bibliography_section(text, style)
        if not bib_section:
            return []
        
        # Dividir la sección de bibliografía en entradas individuales
        entries = self._split_bibliography_entries(bib_section, style)
        
        # Limpiar y validar cada entrada
        valid_entries = []
        for entry in entries:
            entry = entry.strip()
            if entry and self._is_valid_citation(entry, style, 'bibliography'):
                valid_entries.append(entry)
        
        return valid_entries
    
    def _detect_citation_style(self, text: str) -> str:
        """
        Detecta el estilo de citación predominante en el texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            str: Estilo de citación detectado ('APA', 'MLA', etc.)
        """
        # Conteo de coincidencias por estilo
        style_counts = defaultdict(int)
        
        # Verificar encabezados de bibliografía
        for style, headers in self.bibliography_headers.items():
            for header in headers:
                if re.search(header, text, re.IGNORECASE | re.MULTILINE):
                    style_counts[style] += 5  # Dar mayor peso a los encabezados
        
        # Verificar patrones de citas en texto
        for style, patterns in self.in_text_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                style_counts[style] += len(matches)
        
        # Si es Chicago, combinar conteos de autor-fecha y notas
        if 'CHICAGO_AUTHOR_DATE' in style_counts or 'CHICAGO_NOTES' in style_counts:
            author_date = style_counts.pop('CHICAGO_AUTHOR_DATE', 0)
            notes = style_counts.pop('CHICAGO_NOTES', 0)
            style_counts['CHICAGO'] = author_date + notes
        
        # Encontrar el estilo con mayor número de coincidencias
        if style_counts:
            max_style = max(style_counts.items(), key=lambda x: x[1])
            if max_style[1] > 0:
                return max_style[0]
        
        # Si no se puede determinar, devolver APA como predeterminado
        return 'APA'
    
    def _extract_main_text(self, text: str) -> str:
        """
        Extrae el texto principal excluyendo la sección de bibliografía.
        
        Args:
            text (str): Texto completo
            
        Returns:
            str: Texto principal sin bibliografía
        """
        # Buscar el inicio de la sección de bibliografía
        for style, headers in self.bibliography_headers.items():
            for header in headers:
                match = re.search(f"(?i)^{header}\\s*$", text, re.MULTILINE)
                if match:
                    # Devolver el texto hasta el encabezado de bibliografía
                    return text[:match.start()]
        
        # Si no se encuentra un encabezado claro, buscar patrones típicos
        # que indiquen el inicio de una bibliografía
        
        # Patrón para una entrada bibliográfica APA
        apa_pattern = r'\n[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)\.'
        match = re.search(apa_pattern, text)
        if match:
            # Buscar la línea completa donde comienza esta entrada
            start_pos = match.start()
            while start_pos > 0 and text[start_pos-1] != '\n':
                start_pos -= 1
            # Retroceder hasta encontrar una línea en blanco o el inicio del texto
            while start_pos > 0:
                if text[start_pos:start_pos+2] == '\n\n':
                    start_pos += 2
                    break
                start_pos -= 1
            
            return text[:start_pos]
        
        # Si no se encuentra bibliografía, devolver el texto completo
        return text
    
    def _extract_bibliography_section(self, text: str, style: str) -> str:
        """
        Extrae la sección de bibliografía del texto.
        
        Args:
            text (str): Texto completo
            style (str): Estilo de citación
            
        Returns:
            str: Sección de bibliografía o cadena vacía si no se encuentra
        """
        # Buscar los encabezados específicos del estilo
        headers = self.bibliography_headers.get(style, [])
        if not headers:
            # Si no hay encabezados específicos, usar todos los encabezados conocidos
            for style_headers in self.bibliography_headers.values():
                headers.extend(style_headers)
        
        # Buscar el encabezado en el texto
        for header in headers:
            match = re.search(f"(?i)^{header}\\s*$", text, re.MULTILINE)
            if match:
                # Extraer desde el encabezado hasta el final
                bibliography = text[match.start():]
                
                # Verificar si hay otro encabezado después que indique
                # el final de la bibliografía (p.ej., "Apéndices", "Anexos", etc.)
                next_section = re.search(r'\n\s*[A-Z][A-Za-zÀ-ÿ\s]+\s*\n', bibliography[len(header):])
                if next_section:
                    # Limitar la bibliografía hasta el siguiente encabezado
                    bibliography = bibliography[:len(header) + next_section.start()]
                
                return bibliography
        
        # Si no se encuentra un encabezado claro, intentar detectar patrones típicos
        # de entradas bibliográficas según el estilo
        
        # Para APA
        if style == 'APA':
            # Buscar patrones como: Apellido, I. (Año).
            apa_pattern = r'\n[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?\s\(\d{4}\)\.'
            matches = list(re.finditer(apa_pattern, text))
            if matches:
                # Encontrar la primera coincidencia
                first_match = matches[0]
                # Buscar el inicio real de la bibliografía (línea en blanco anterior)
                start_pos = first_match.start()
                while start_pos > 0 and text[start_pos-1] != '\n':
                    start_pos -= 1
                # Retroceder hasta encontrar una línea en blanco o el inicio del texto
                while start_pos > 0:
                    if text[start_pos:start_pos+2] == '\n\n':
                        start_pos += 2
                        break
                    start_pos -= 1
                
                return text[start_pos:]
        
        # Para MLA
        elif style == 'MLA':
            # Buscar patrones como: Apellido, Nombre.
            mla_pattern = r'\n[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+\.\s'
            matches = list(re.finditer(mla_pattern, text))
            if matches:
                first_match = matches[0]
                start_pos = first_match.start()
                while start_pos > 0 and text[start_pos-1] != '\n':
                    start_pos -= 1
                while start_pos > 0:
                    if text[start_pos:start_pos+2] == '\n\n':
                        start_pos += 2
                        break
                    start_pos -= 1
                
                return text[start_pos:]
        
        # Para IEEE
        elif style == 'IEEE':
            # Buscar patrones como: [1] I. Apellido,
            ieee_pattern = r'\n\[\d+\]\s[A-Z]\.\s[A-Za-zÀ-ÿ\-]+'
            matches = list(re.finditer(ieee_pattern, text))
            if matches:
                first_match = matches[0]
                start_pos = first_match.start()
                while start_pos > 0 and text[start_pos-1] != '\n':
                    start_pos -= 1
                while start_pos > 0:
                    if text[start_pos:start_pos+2] == '\n\n':
                        start_pos += 2
                        break
                    start_pos -= 1
                
                return text[start_pos:]
        
        # No se encontró sección de bibliografía
        return ""
    
    def _split_bibliography_entries(self, bib_section: str, style: str) -> List[str]:
        """
        Divide la sección de bibliografía en entradas individuales.
        
        Args:
            bib_section (str): Sección de bibliografía
            style (str): Estilo de citación
            
        Returns:
            List[str]: Lista de entradas bibliográficas
        """
        # Eliminar el encabezado de la bibliografía
        for header in self.bibliography_headers.get(style, []):
            bib_section = re.sub(f"(?i)^{header}\\s*\n", "", bib_section)
        
        entries = []
        
        # Diferentes estrategias según el estilo
        if style == 'APA' or style == 'MLA' or style == 'CHICAGO' or style == 'HARVARD':
            # Para estilos con formato de autor-fecha o autor-título
            # Las entradas suelen comenzar con un apellido seguido de coma
            
            # Dividir por líneas
            lines = bib_section.split('\n')
            current_entry = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Línea vacía marca el final de una entrada
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                        current_entry = ""
                elif re.match(r'^[A-Za-zÀ-ÿ\-]+,', line):
                    # Línea que comienza con apellido y coma, posible inicio de nueva entrada
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                    current_entry = line
                else:
                    # Continuación de la entrada actual
                    current_entry += " " + line
            
            # Añadir la última entrada si existe
            if current_entry.strip():
                entries.append(current_entry.strip())
        
        elif style == 'IEEE' or style == 'VANCOUVER':
            # Para estilos con entradas numeradas
            
            # Dividir por líneas
            lines = bib_section.split('\n')
            current_entry = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Línea vacía marca el final de una entrada
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                        current_entry = ""
                elif re.match(r'^\[\d+\]|\d+\.', line):
                    # Línea que comienza con número entre corchetes o número seguido de punto
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                    current_entry = line
                else:
                    # Continuación de la entrada actual
                    current_entry += " " + line
            
            # Añadir la última entrada si existe
            if current_entry.strip():
                entries.append(current_entry.strip())
        
        elif style == 'CSE':
            # Para CSE, similar a Vancouver pero con formato específico
            
            # Dividir por líneas
            lines = bib_section.split('\n')
            current_entry = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Línea vacía marca el final de una entrada
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                        current_entry = ""
                elif re.match(r'^\[\d+\]|\d+\.|\w+\s\w+\s\d{4}\.', line):
                    # Inicio de nueva entrada (por número o autor año)
                    if current_entry.strip():
                        entries.append(current_entry.strip())
                    current_entry = line
                else:
                    # Continuación de la entrada actual
                    current_entry += " " + line
            
            # Añadir la última entrada si existe
            if current_entry.strip():
                entries.append(current_entry.strip())
        
        else:
            # Método genérico para cualquier estilo no reconocido
            # Intentar dividir por líneas en blanco
            raw_entries = re.split(r'\n\s*\n', bib_section)
            for entry in raw_entries:
                entry = entry.strip()
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _is_valid_citation(self, citation: str, style: str, citation_type: str) -> bool:
        """
        Verifica si una cita es válida según criterios básicos.
        
        Args:
            citation (str): Texto de la cita
            style (str): Estilo de citación
            citation_type (str): Tipo de cita ('in_text', 'bibliography')
            
        Returns:
            bool: True si la cita es válida, False en caso contrario
        """
        # Longitud mínima
        if len(citation) < 3:
            return False
        
        # Para citas en texto
        if citation_type == 'in_text':
            # Verificar estructuras comunes según el estilo
            if style == 'APA':
                # Debe contener un año de 4 dígitos
                if not re.search(r'\d{4}', citation):
                    return False
                # Para citas parentéticas, debe tener paréntesis balanceados
                if citation.startswith('(') and not citation.endswith(')'):
                    return False
            
            elif style == 'MLA':
                # Debe contener un número de página para la mayoría de citas
                if '(' in citation and ')' in citation and not re.search(r'\d+', citation):
                    return False
            
            elif style == 'CHICAGO_AUTHOR_DATE' or style == 'CHICAGO':
                # Similares a APA
                if not re.search(r'\d{4}', citation):
                    return False
                # Para citas parentéticas, debe tener paréntesis balanceados
                if citation.startswith('(') and not citation.endswith(')'):
                    return False
            
            elif style == 'IEEE' or style == 'VANCOUVER':
                # Debe contener un número
                if not re.search(r'\d+', citation):
                    return False
            
            # Longitud máxima razonable para una cita en texto
            if len(citation) > 100:
                return False
        
        # Para bibliografía
        elif citation_type == 'bibliography':
            # Criterios generales para entradas bibliográficas
            
            # Debe terminar con un signo de puntuación
            if not re.search(r'[.!?]$', citation):
                return False
            
            # Debe contener un año en la mayoría de estilos (excepto algunos casos MLA)
            if style != 'MLA' and not re.search(r'\d{4}', citation):
                return False
            
            # Para IEEE y Vancouver, debe comenzar con un número
            if (style == 'IEEE' or style == 'VANCOUVER') and not re.search(r'^\[\d+\]|\d+\.', citation):
                return False
            
            # Para otros estilos, debe comenzar con apellido y coma
            if style in ['APA', 'MLA', 'CHICAGO', 'HARVARD'] and not re.search(r'^[A-Za-zÀ-ÿ\-]+,', citation):
                return False
            
            # Longitud mínima para una entrada bibliográfica
            if len(citation) < 20:
                return False
            
            # Máximo razonable para evitar texto completo
            if len(citation) > 1000:
                return False
        
        return True
    
    def extract_citation_metadata(self, citation: str, style: str, citation_type: str) -> Dict[str, Any]:
        """
        Extrae metadatos estructurados de una cita.
        
        Args:
            citation (str): Texto de la cita
            style (str): Estilo de citación
            citation_type (str): Tipo de cita ('in_text', 'bibliography')
            
        Returns:
            Dict[str, Any]: Metadatos extraídos (autor, año, título, etc.)
        """
        metadata = {}
        
        # Para citas en texto
        if citation_type == 'in_text':
            if style == 'APA':
                # Cita parentética: (Autor, año, p. XX)
                match = re.search(r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s(?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)', citation)
                if match:
                    metadata.update(match.groupdict())
                else:
                    # Cita narrativa: Autor (año, p. XX)
                    match = re.search(r'(?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)', citation)
                    if match:
                        metadata.update(match.groupdict())
            
            elif style == 'MLA':
                # Cita parentética: (Autor página)
                match = re.search(r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s(?P<page>\d+(?:-\d+)?)\)', citation)
                if match:
                    metadata.update(match.groupdict())
                else:
                    # Cita narrativa: Autor (página)
                    match = re.search(r'(?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<page>\d+(?:-\d+)?)\)', citation)
                    if match:
                        metadata.update(match.groupdict())
            
            elif style == 'CHICAGO' or style == 'CHICAGO_AUTHOR_DATE':
                # Cita autor-fecha: (Autor año, página)
                match = re.search(r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s(?P<year>\d{4})(?:,\s(?P<page>\d+(?:-\d+)?))?\)', citation)
                if match:
                    metadata.update(match.groupdict())
                else:
                    # Cita narrativa: Autor (año, página)
                    match = re.search(r'(?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<year>\d{4})(?:,\s(?P<page>\d+(?:-\d+)?))?\)', citation)
                    if match:
                        metadata.update(match.groupdict())
            
            elif style == 'HARVARD':
                # Cita parentética: (Autor, año: página)
                match = re.search(r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s(?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)', citation)
                if match:
                    metadata.update(match.groupdict())
                else:
                    # Cita narrativa: Autor (año: página)
                    match = re.search(r'(?P<author>[A-Za-zÀ-ÿ\-]+(?: [A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)', citation)
                    if match:
                        metadata.update(match.groupdict())
            
            elif style == 'IEEE' or style == 'VANCOUVER':
                # Cita numérica: [1] o (1)
                match = re.search(r'[\[\(](?P<number>\d+)[\]\)]', citation)
                if match:
                    metadata['number'] = match.group('number')
        
        # Para bibliografía
        elif citation_type == 'bibliography':
            if style == 'APA':
                # Libro: Apellido, I. (Año). Título. Editorial.
                match = re.search(r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)(?:,\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?))*((?:,|\s)&\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?))?\s\((?P<year>\d{4})\)\.\s(?P<title>[^\.]+)\.\s(?P<publisher>[^\.]+)', citation)
                if match:
                    metadata.update(match.groupdict())
                else:
                    # Artículo: Apellido, I. (Año). Título del artículo. Revista, vol(num), pp-pp.
                    match = re.search(r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)(?:,\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?))*((?:,|\s)&\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?))?\s\((?P<year>\d{4})\)\.\s(?P<title>[^\.]+)\.\s(?P<journal>[^,]+),\s(?P<volume>\d+)(?:\((?P<issue>\d+)\))?,\s(?P<pages>\d+-\d+)', citation)
                    if match:
                        metadata.update(match.groupdict())
                        metadata['type'] = 'article'
                    else:
                        metadata['type'] = 'book'
            
            elif style == 'MLA':
                # Libro: Apellido, Nombre. Título. Editorial, Año.
                match = re.search(r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+)(?:,\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+))*(?:,? and (?:[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+))?\.\s(?P<title>[^\.]+)\.\s(?P<publisher>[^,]+),\s(?P<year>\d{4})', citation)
                if match:
                    metadata.update(match.groupdict())
                    metadata['type'] = 'book'
                else:
                    # Artículo: Apellido, Nombre. "Título del artículo." Revista, vol. num, año, pp. xx-xx.
                    match = re.search(r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+)(?:,\s(?:[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+))*(?:,? and (?:[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\s\-]+))?\.\s"(?P<title>[^"]+)\."\s(?P<journal>[^,]+),\svol\.\s(?P<volume>\d+)(?:,\sno\.\s(?P<issue>\d+))?,\s(?P<year>\d{4}),\s(?:pp\.|p\.)\s(?P<pages>\d+-\d+)', citation)
                    if match:
                        metadata.update(match.groupdict())
                        metadata['type'] = 'article'
        
        # Limpiar valores None
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    def extract_citation_graph(self, text: str, style: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Construye un grafo de citaciones mostrando relaciones entre
        citas en texto y sus entradas bibliográficas.
        
        Args:
            text (str): Texto completo a analizar
            style (str, optional): Estilo de citación. Si es None,
                                  se intentará detectar automáticamente.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Grafo de citaciones
        """
        # Detectar estilo si no se especifica
        if not style:
            style = self._detect_citation_style(text)
        
        # Extraer todas las citas
        citations = self.extract_all_citations(text, style)
        
        # Extraer metadatos de cada cita en texto
        in_text_nodes = []
        for citation in citations['en_texto']:
            metadata = self.extract_citation_metadata(citation, style, 'in_text')
            in_text_nodes.append({
                'text': citation,
                'metadata': metadata,
                'type': 'in_text'
            })
        
        # Extraer metadatos de cada entrada bibliográfica
        bib_nodes = []
        for citation in citations['bibliograficas']:
            metadata = self.extract_citation_metadata(citation, style, 'bibliography')
            bib_nodes.append({
                'text': citation,
                'metadata': metadata,
                'type': 'bibliography'
            })
        
        # Establecer relaciones entre citas
        edges = []
        for in_text in in_text_nodes:
            # Extraer autor y año (si están disponibles)
            author = in_text['metadata'].get('author', '')
            year = in_text['metadata'].get('year', '')
            
            if author or year:
                for bib in bib_nodes:
                    bib_author = bib['metadata'].get('author', '')
                    bib_year = bib['metadata'].get('year', '')
                    
                    # Comprobar si la cita en texto corresponde a esta entrada bibliográfica
                    if self._is_matching_citation(author, year, bib_author, bib_year, style):
                        edges.append({
                            'source': in_text['text'],
                            'target': bib['text'],
                            'source_idx': in_text_nodes.index(in_text),
                            'target_idx': bib_nodes.index(bib)
                        })
        
        return {
            'in_text_nodes': in_text_nodes,
            'bibliography_nodes': bib_nodes,
            'edges': edges
        }
    
    def _is_matching_citation(self, author: str, year: str, 
                           bib_author: str, bib_year: str, style: str) -> bool:
        """
        Determina si una cita en texto corresponde a una entrada bibliográfica.
        
        Args:
            author (str): Autor en la cita en texto
            year (str): Año en la cita en texto
            bib_author (str): Autor en la entrada bibliográfica
            bib_year (str): Año en la entrada bibliográfica
            style (str): Estilo de citación
            
        Returns:
            bool: True si hay correspondencia, False en caso contrario
        """
        # Si la cita no tiene autor ni año, no podemos emparejarla
        if not author and not year:
            return False
        
        # Simplificar nombres para comparación
        author_simple = author.lower().replace('et al.', '').strip()
        bib_author_simple = bib_author.lower().strip()
        
        # Extraer apellido principal de bib_author (antes de la primera coma)
        if ',' in bib_author_simple:
            bib_surname = bib_author_simple.split(',')[0].strip()
        else:
            bib_surname = bib_author_simple.split()[0].strip() if bib_author_simple else ""
        
        # En MLA, solo comparamos autor
        if style == 'MLA':
            # Verificar si el autor de la cita está en el autor bibliográfico
            return author_simple in bib_author_simple or bib_surname in author_simple
        
        # Para otros estilos, verificar autor y año
        author_match = author_simple in bib_author_simple or bib_surname in author_simple
        year_match = year == bib_year
        
        return author_match and year_match
    
    def identify_style_markers(self, text: str) -> Dict[str, Dict[str, int]]:
        """
        Identifica marcadores específicos de estilos de citación.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Dict[str, Dict[str, int]]: Marcadores identificados por estilo y tipo
        """
        markers = {
            'APA': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'MLA': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'CHICAGO': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'HARVARD': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'IEEE': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'VANCOUVER': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0},
            'CSE': {'in_text': 0, 'bibliography': 0, 'headers': 0, 'specific': 0}
        }
        
        # Verificar encabezados
        for style, headers in self.bibliography_headers.items():
            for header in headers:
                if re.search(header, text, re.IGNORECASE | re.MULTILINE):
                    markers[style]['headers'] += 1
        
        # Verificar marcadores específicos por estilo
        
        # APA: uso de "&" en citas parentéticas
        if re.search(r'\([A-Za-zÀ-ÿ\-]+ & [A-Za-zÀ-ÿ\-]+,', text):
            markers['APA']['specific'] += 1
        
        # APA: formato de fecha con p.
        if re.search(r'\d{4}, p\. \d+', text):
            markers['APA']['specific'] += 1
        
        # MLA: uso de "and" en lugar de "&"
        if re.search(r'\([A-Za-zÀ-ÿ\-]+ and [A-Za-zÀ-ÿ\-]+ \d+', text):
            markers['MLA']['specific'] += 1
        
        # MLA: páginas sin "p."
        if re.search(r'\([A-Za-zÀ-ÿ\-]+ \d+\)', text):
            markers['MLA']['specific'] += 1
        
        # Chicago: sistema de notas
        footnote_count = len(re.findall(r'^\d+\.\s', text, re.MULTILINE))
        if footnote_count > 0:
            markers['CHICAGO']['specific'] += min(footnote_count, 5)  # Limitar a 5 máximo
        
        # Chicago: términos latinos (Ibid., Op. cit.)
        latin_count = len(re.findall(r'Ibid\.|Op\. cit\.|Loc\. cit\.', text))
        if latin_count > 0:
            markers['CHICAGO']['specific'] += min(latin_count, 3)  # Limitar a 3 máximo
        
        # Harvard: uso de dos puntos para páginas
        if re.search(r'\d{4}: \d+', text):
            markers['HARVARD']['specific'] += 1
        
        # IEEE: citas numéricas entre corchetes
        bracket_count = len(re.findall(r'\[\d+\]', text))
        if bracket_count > 0:
            markers['IEEE']['specific'] += min(bracket_count, 5)  # Limitar a 5 máximo
        
        # Vancouver: citas numéricas entre paréntesis
        if re.search(r'\(\d+\)', text):
            markers['VANCOUVER']['specific'] += 1
        
        # CSE: formato específico de nombre-año
        if re.search(r'[A-Za-zÀ-ÿ\-]+ [A-Z]{1,2}\. \d{4}\.', text):
            markers['CSE']['specific'] += 1
        
        return markers


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del extractor
    extractor = CitationExtractor()
    
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
    
    # Extraer todas las citas
    citations = extractor.extract_all_citations(sample_text)
    
    # Imprimir resultados
    print("CITAS EN TEXTO:")
    for citation in citations['en_texto']:
        print(f"- {citation}")
    
    print("\nREFERENCIAS BIBLIOGRÁFICAS:")
    for citation in citations['bibliograficas']:
        print(f"- {citation}")
    
    # Detectar estilo
    style = extractor._detect_citation_style(sample_text)
    print(f"\nEstilo detectado: {style}")