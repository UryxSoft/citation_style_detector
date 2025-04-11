# Validación de citas
# validator.py
# Implementación de la validación de citas

import re
from typing import Dict, List, Tuple, Optional, Set, Any
import logging
from collections import Counter


class CitationValidator:
    """
    Clase que implementa la validación de citas según diferentes estilos.
    
    Realiza verificaciones de consistencia, formato y correspondencia entre 
    citas en texto y entradas bibliográficas.
    """
    
    def __init__(self, patterns=None):
        """
        Inicializa el validador de citas.
        
        Args:
            patterns: Instancia opcional de CitationPatterns para usar patrones predefinidos
        """
        self.logger = logging.getLogger('CitationValidator')
        self.patterns = patterns
        
        # Reglas de validación por estilo
        self._init_validation_rules()
    
    def _init_validation_rules(self):
        """
        Inicializa las reglas de validación específicas para cada estilo.
        """
        self.validation_rules = {
            'APA': {
                'in_text': [
                    ('comma_between_author_year', r'\([A-Za-z\-]+ \d{4}\)', 
                     'Falta una coma entre el autor y el año', 
                     'Usar coma entre autor y año: (Autor, 2020) en lugar de (Autor 2020)'),
                    
                    ('page_indicator', r'\d{4}, \d+', 
                     'Falta el indicador de página', 
                     'Incluir "p." antes del número de página: (Autor, 2020, p. 25)'),
                    
                    ('ampersand_in_parenthetical', r'\([A-Za-z\-]+ and [A-Za-z\-]+,', 
                     'Se usa "and" en lugar de "&" en cita parentética', 
                     'Usar "&" en citas parentéticas: (Autor & Autor, 2020)'),
                    
                    ('y_in_narrative', r'[A-Za-z\-]+ & [A-Za-z\-]+ \(\d{4}', 
                     'Se usa "&" en lugar de "y" en cita narrativa', 
                     'Usar "y" en citas narrativas: "Autor y Autor (2020)"')
                ],
                'bibliography': [
                    ('title_capitalization', r'\.\s[a-z]', 
                     'El título debe comenzar con mayúscula después de un punto', 
                     'Comenzar con mayúscula después de punto en título'),
                    
                    ('journal_italics', None,  # No se puede detectar cursiva en texto plano
                     'Los nombres de revistas deben estar en cursiva', 
                     'Poner en cursiva los nombres de revistas'),
                    
                    ('publisher_location', r'\)\.(?:[^\.]+)?[A-Za-z\-]+\.',
                     'Puede faltar la ubicación de la editorial',
                     'Incluir la ubicación antes de la editorial: (2020). Título. Ciudad: Editorial.')
                ]
            },
            'MLA': {
                'in_text': [
                    ('no_comma_author_page', r'\([A-Za-z\-]+, \d+', 
                     'No debe haber coma entre autor y página', 
                     'Eliminar la coma entre autor y página: (Autor 25) en lugar de (Autor, 25)'),
                    
                    ('no_p_indicator', r'\([A-Za-z\-]+ p\. \d+', 
                     'No usar "p." en citas MLA', 
                     'Omitir "p." en las citas: (Autor 25) en lugar de (Autor p. 25)'),
                    
                    ('and_not_ampersand', r'[A-Za-z\-]+ & [A-Za-z\-]+ \d+', 
                     'Se usa "&" en lugar de "and"', 
                     'Usar "and" en lugar de "&": (Autor and Autor 25)')
                ],
                'bibliography': [
                    ('title_quotes', r'(?<!\")[A-Z][^\"]+\."', 
                     'Los títulos de artículos deben estar entre comillas', 
                     'Poner títulos de artículos entre comillas: "Título del artículo"'),
                    
                    ('journal_title_italics', None,  # No se puede detectar cursiva en texto plano
                     'Los nombres de revistas deben estar en cursiva', 
                     'Poner en cursiva los nombres de revistas'),
                    
                    ('page_abbreviation', r'pp\.\s\d+', 
                     'Usar "pp." para páginas en MLA',
                     'Mantener abreviatura "pp." para indicar rango de páginas'),
                    
                    ('work_cited_format', r'^[A-Z][a-z]+,\s[A-Z][a-z]+',
                     'Formato de autor: Apellido, Nombre',
                     'Formatear autores como: Apellido, Nombre completo')
                ]
            },
            'CHICAGO': {
                'in_text': [
                    ('note_numbering', r'^\d+\.(?!\s)', 
                     'Debe haber un espacio después del número de nota', 
                     'Añadir espacio después del número de nota: "1. " en lugar de "1."'),
                    
                    ('ibid_format', r'(?i)ibid(?!\.|,)', 
                     'Ibid debe terminar con punto', 
                     'Añadir punto después de Ibid: "Ibid." o "Ibid., 25."'),
                    
                    ('parenthetical_format', r'\([A-Za-z\-]+ \d{4}, \d+\)', 
                     'En Chicago autor-fecha, no se usa coma antes de la página',
                     'Usar formato (Autor 2020, 25) sin coma entre autor y año')
                ],
                'bibliography': [
                    ('author_format', r'^[A-Z][a-z]+, [A-Z][a-z]+',
                     'Formato de autor: Apellido, Nombre',
                     'Formatear autores como: Apellido, Nombre'),
                    
                    ('journal_article_title', r'(?<!\")[A-Z][^\"]+\."',
                     'Los títulos de artículos deben estar entre comillas',
                     'Poner títulos de artículos entre comillas: "Título del artículo"'),
                    
                    ('journal_title_italics', None,  # No se puede detectar cursiva en texto plano
                     'Los nombres de revistas deben estar en cursiva',
                     'Poner en cursiva los nombres de revistas'),
                    
                    ('publisher_location', r'\d{4}(?![^\)]*\))(?!:)',
                     'Debe incluir la ubicación de la editorial',
                     'Incluir ubicación de la editorial: Título. Ciudad: Editorial, 2020.')
                ]
            },
            'HARVARD': {
                'in_text': [
                    ('colon_for_pages', r'\([A-Za-z\-]+, \d{4}, \d+', 
                     'Usar dos puntos en lugar de coma antes de la página', 
                     'Usar formato (Autor, 2020: 25) con dos puntos antes de la página'),
                    
                    ('parentheses_format', r'[A-Za-z\-]+ \(\d{4}, \d+', 
                     'Usar dos puntos en lugar de coma antes de la página', 
                     'Usar formato Autor (2020: 25) con dos puntos antes de la página')
                ],
                'bibliography': [
                    ('author_initials', r'^[A-Za-z\-]+,\s[A-Z](?!\.)(?!\s[A-Z]\.)',
                     'Las iniciales de autor deben llevar punto',
                     'Añadir punto a las iniciales: Smith, J.'),
                    
                    ('year_parentheses', r'^[A-Za-z\-]+,\s[A-Z]\.\s\d{4}',
                     'El año debe estar entre paréntesis',
                     'Poner el año entre paréntesis: Smith, J. (2020)'),
                    
                    ('title_after_year', r'\)\s(?![A-Z])',
                     'El título debe comenzar después del año',
                     'Comenzar el título inmediatamente después del año: (2020) Título.')
                ]
            },
            'IEEE': {
                'in_text': [
                    ('bracket_format', r'\(\d+\)',
                     'Usar corchetes en lugar de paréntesis para las citas',
                     'Usar formato [1] en lugar de (1)'),
                    
                    ('multiple_citations', r'\[\d+, \d+\]',
                     'Usar formato correcto para múltiples citas',
                     'Para múltiples citas usar formato [1], [2] o [1]-[3]')
                ],
                'bibliography': [
                    ('numbering_format', r'^\[\d+\]\s[a-z]',
                     'La primera palabra después del número debe comenzar con mayúscula',
                     'Comenzar con mayúscula después del número: [1] Autor'),
                    
                    ('author_initials', r'^\[\d+\]\s[A-Z]\.',
                     'Iniciales antes del apellido',
                     'Usar formato [1] A. B. Autor'),
                    
                    ('title_quotes', r'(?<!\")[A-Z][^\"]+\,"',
                     'Títulos de artículos entre comillas',
                     'Poner títulos de artículos entre comillas: "Título del artículo"')
                ]
            },
            'VANCOUVER': {
                'in_text': [
                    ('citation_format', r'\(\d+, \d+\)',
                     'Formato incorrecto para múltiples citas',
                     'Usar formato (1,2) o [1,2] sin espacios entre citas'),
                    
                    ('superscript_missing', None,  # Difícil de detectar en texto plano
                     'Considere usar superíndices para las citas',
                     'Es recomendable usar superíndices para las citas en estilo Vancouver')
                ],
                'bibliography': [
                    ('author_format', r'^(?!\d+\.)[A-Za-z\-]+ [A-Z]{1,2}(?!\s[A-Z])',
                     'Formato de autor: Apellido AB (inicial con 2 letras)',
                     'Utilizar formato Apellido AB para autores: Smith JA'),
                    
                    ('journal_abbreviation', r'\.\s[A-Za-z\s]{20,}\.',
                     'Los nombres de revistas deben estar abreviados',
                     'Abreviar nombres de revistas: J Biomed Sci en lugar de Journal of Biomedical Science'),
                    
                    ('page_format', r'\d{4};\d+(?:\(\d+\))?;\d+',
                     'Usar dos puntos antes de las páginas',
                     'Utilizar formato año;volumen(número):páginas - 2020;12(3):45-50')
                ]
            },
            'CSE': {
                'in_text': [
                    ('name_year_format', r'\([A-Za-z\-]+, \d{4}\)',
                     'En CSE nombre-año no hay coma entre autor y año',
                     'Usar formato (Smith 2020) sin coma entre autor y año'),
                    
                    ('citation_sequence_format', r'\(\d+\)',
                     'En sistema de cita-secuencia usar corchetes, no paréntesis',
                     'Usar formato [1] en lugar de (1) para sistema de secuencia')
                ],
                'bibliography': [
                    ('author_format', r'^[A-Za-z\-]+,\s[A-Z][A-Z]',
                     'En CSE los nombres se abrevian sin comas',
                     'Utilizar formato Apellido AB sin coma: Smith JA'),
                    
                    ('year_after_author', r'^[A-Za-z\-]+ [A-Z]{1,2}(?:[,;]|\.(?!\s\d{4}))',
                     'El año debe ir después del autor',
                     'Colocar el año después del autor: Smith JA. 2020.'),
                    
                    ('journal_title_format', r'\.\s[^\.]+\.[A-Z]',
                     'Abreviar nombre de revista con la primera letra de cada palabra en mayúscula',
                     'Abreviar revistas como: J Biol Chem.')
                ]
            }
        }
        
        # Reglas comunes para todos los estilos
        self.common_rules = {
            'consistency': [
                ('mixed_citation_styles', None,
                 'Se detectan múltiples estilos de citación',
                 'Mantener consistencia en un solo estilo de citación en todo el documento'),
                
                ('mixed_date_formats', None,
                 'Formatos de fecha inconsistentes',
                 'Mantener consistencia en el formato de fechas'),
                
                ('inconsistent_author_names', None,
                 'Nombres de autores inconsistentes en diferentes citas',
                 'Mantener consistencia en la forma de citar a los mismos autores')
            ],
            'completeness': [
                ('missing_bibliography', None,
                 'Citas sin entrada en la bibliografía',
                 'Incluir todas las obras citadas en la bibliografía'),
                
                ('uncited_references', None,
                 'Entradas bibliográficas no citadas en el texto',
                 'Todas las entradas bibliográficas deben ser citadas en el texto'),
                
                ('incomplete_information', None,
                 'Información incompleta en las entradas bibliográficas',
                 'Incluir toda la información requerida en las entradas bibliográficas')
            ]
        }
    
    def validate_citation_format(self, citation: str, style: str, citation_type: str) -> List[Dict[str, str]]:
        """
        Valida el formato de una cita específica según el estilo correspondiente.
        
        Args:
            citation (str): Texto de la cita a validar
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            citation_type (str): Tipo de cita ('in_text', 'bibliography')
            
        Returns:
            List[Dict[str, str]]: Lista de problemas detectados con sus recomendaciones
        """
        issues = []
        
        # Obtener reglas específicas para el estilo y tipo
        style_rules = self.validation_rules.get(style, {}).get(citation_type, [])
        
        # Aplicar cada regla
        for rule_id, pattern, issue_desc, recommendation in style_rules:
            # Si el patrón es None, no se puede validar en texto plano
            if pattern is None:
                continue
            
            # Comprobar si la cita cumple o no la regla
            if re.search(pattern, citation):
                issues.append({
                    'rule_id': rule_id,
                    'description': issue_desc,
                    'recommendation': recommendation,
                    'citation': citation
                })
        
        return issues
    
    def validate_citation_consistency(self, citations: Dict[str, List[str]], 
                                    style: str) -> List[Dict[str, str]]:
        """
        Valida la consistencia entre citas en texto y entradas bibliográficas.
        
        Args:
            citations (Dict[str, List[str]]): Diccionario con citas por tipo
            style (str): Estilo de citación
            
        Returns:
            List[Dict[str, str]]: Lista de problemas de consistencia
        """
        issues = []
        
        # Extraer información clave de citas en texto
        in_text_keys = self._extract_citation_keys(citations.get('en_texto', []), style)
        
        # Extraer información clave de entradas bibliográficas
        bib_keys = self._extract_bibliography_keys(citations.get('bibliograficas', []), style)
        
        # Comprobar citas que no tienen entrada en la bibliografía
        for author, year in in_text_keys:
            if not self._find_matching_reference(author, year, bib_keys, style):
                issues.append({
                    'rule_id': 'missing_bibliography',
                    'description': f"La cita ({author}, {year}) no tiene entrada correspondiente en la bibliografía",
                    'recommendation': "Añadir la entrada bibliográfica completa",
                    'citation': f"({author}, {year})"
                })
        
        # Comprobar entradas bibliográficas que no están citadas en el texto
        for key in bib_keys:
            author, year = key[:2]  # Los primeros dos elementos son autor y año
            if not self._find_matching_citation(author, year, in_text_keys, style):
                if len(key) > 2:  # Si hay más información como título
                    title = key[2]
                    entry_desc = f"{author} ({year}), '{title}'"
                else:
                    entry_desc = f"{author} ({year})"
                
                issues.append({
                    'rule_id': 'uncited_references',
                    'description': f"La entrada bibliográfica {entry_desc} no está citada en el texto",
                    'recommendation': "Citar esta fuente en el texto o eliminarla de la bibliografía",
                    'citation': entry_desc
                })
        
        # Comprobar consistencia en nombres de autores
        author_variants = {}
        for author, _ in in_text_keys:
            author_base = self._normalize_author_name(author)
            if author_base in author_variants:
                if author != author_variants[author_base]:
                    issues.append({
                        'rule_id': 'inconsistent_author_names',
                        'description': f"Variantes inconsistentes del mismo autor: '{author}' y '{author_variants[author_base]}'",
                        'recommendation': "Mantener consistencia en los nombres de autores",
                        'citation': f"{author}, {author_variants[author_base]}"
                    })
            else:
                author_variants[author_base] = author
        
        return issues
    
    def validate_all_citations(self, citations: Dict[str, List[str]], 
                             style: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Valida todas las citas del documento en un estilo específico.
        
        Args:
            citations (Dict[str, List[str]]): Diccionario con citas por tipo
            style (str): Estilo de citación
            
        Returns:
            Dict[str, List[Dict[str, str]]]: Diccionario con problemas agrupados por categoría
        """
        all_issues = {
            'formato_incorrecto': [],
            'inconsistencias_estilo': [],
            'recomendaciones': []
        }
        
        # Validar citas en texto
        for citation in citations.get('en_texto', []):
            issues = self.validate_citation_format(citation, style, 'in_text')
            if issues:
                all_issues['formato_incorrecto'].extend(issues)
        
        # Validar entradas bibliográficas
        for citation in citations.get('bibliograficas', []):
            issues = self.validate_citation_format(citation, style, 'bibliography')
            if issues:
                all_issues['formato_incorrecto'].extend(issues)
        
        # Validar consistencia
        consistency_issues = self.validate_citation_consistency(citations, style)
        if consistency_issues:
            all_issues['inconsistencias_estilo'].extend(consistency_issues)
        
        # Comprobar consistencia general de estilos en todo el documento
        style_consistency_issues = self._check_overall_style_consistency(citations, style)
        if style_consistency_issues:
            all_issues['inconsistencias_estilo'].extend(style_consistency_issues)
        
        # Generar recomendaciones generales
        all_issues['recomendaciones'] = self._generate_recommendations(citations, style, all_issues)
        
        return all_issues
    
    def _extract_citation_keys(self, citations: List[str], style: str) -> List[Tuple[str, str]]:
        """
        Extrae información clave (autor, año) de las citas en texto.
        
        Args:
            citations (List[str]): Lista de citas en texto
            style (str): Estilo de citación
            
        Returns:
            List[Tuple[str, str]]: Lista de pares (autor, año)
        """
        keys = []
        
        for citation in citations:
            # Patrones específicos según estilo
            if style == 'APA' or style == 'HARVARD':
                # Cita parentética: (Autor, año)
                match = re.search(r'\(([A-Za-z\-]+(?: et al\.)?),\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(2)))
                    continue
                
                # Cita narrativa: Autor (año)
                match = re.search(r'([A-Za-z\-]+(?: et al\.)?)\s\((\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(2)))
                    continue
                
                # Dos autores: (Autor & Autor, año)
                match = re.search(r'\(([A-Za-z\-]+(?:\s[A-Za-z\-]+)?)(?:\s&|\sy)\s([A-Za-z\-]+(?:\s[A-Za-z\-]+)?),\s(\d{4})', citation)
                if match:
                    keys.append((f"{match.group(1)} & {match.group(2)}", match.group(3)))
                    continue
            
            elif style == 'MLA':
                # Cita con página: (Autor página)
                match = re.search(r'\(([A-Za-z\-]+(?: et al\.)?)\s\d+', citation)
                if match:
                    keys.append((match.group(1), ""))  # MLA no tiene año en la cita
                    continue
                
                # Dos autores: (Autor and Autor página)
                match = re.search(r'\(([A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\sand\s([A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\s\d+', citation)
                if match:
                    keys.append((f"{match.group(1)} and {match.group(2)}", ""))
                    continue
            
            elif style == 'CHICAGO':
                # Chicago autor-fecha: (Autor año)
                match = re.search(r'\(([A-Za-z\-]+(?: et al\.)?)\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(2)))
                    continue
                
                # Chicago notas: No podemos extraer fácilmente autores de notas al pie
                pass
            
            elif style == 'IEEE' or style == 'VANCOUVER':
                # Citas numéricas: No extraemos autor/año
                pass
        
        return keys
    
    def _extract_bibliography_keys(self, citations: List[str], style: str) -> List[Tuple]:
        """
        Extrae información clave de las entradas bibliográficas.
        
        Args:
            citations (List[str]): Lista de entradas bibliográficas
            style (str): Estilo de citación
            
        Returns:
            List[Tuple]: Lista de tuplas (autor, año, título)
        """
        keys = []
        
        for citation in citations:
            # Patrones específicos según estilo
            if style == 'APA':
                # Apellido, I. (Año). Título.
                match = re.search(r'^([A-Za-z\-]+),\s[A-Z]\.(?:,\s(?:[A-Za-z\-]+),\s[A-Z]\.)*(?:,?\s&\s(?:[A-Za-z\-]+),\s[A-Z]\.)?(?:,\set\sal\.)?\s\((\d{4})\)\.\s(.+?)\.', citation)
                if match:
                    keys.append((match.group(1), match.group(2), match.group(3)))
                    continue
            
            elif style == 'MLA':
                # Apellido, Nombre. Título.
                match = re.search(r'^([A-Za-z\-]+),\s[A-Za-z\-\s]+\.\s(?:")?(.+?)(?:")?\.\s.+,\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(3), match.group(2)))
                    continue
            
            elif style == 'CHICAGO':
                # Apellido, Nombre. Título.
                match = re.search(r'^([A-Za-z\-]+),\s[A-Za-z\-\s]+\.\s(?:")?(.+?)(?:")?\.\s.+,\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(3), match.group(2)))
                    continue
            
            elif style == 'HARVARD':
                # Apellido, I. (Año) Título.
                match = re.search(r'^([A-Za-z\-]+),\s[A-Z]\.(?:,\s(?:[A-Za-z\-]+),\s[A-Z]\.)*(?:,?\sand\s(?:[A-Za-z\-]+),\s[A-Z]\.)?(?:,\set\sal\.)?\s\((\d{4})\)\s(.+?)\.', citation)
                if match:
                    keys.append((match.group(1), match.group(2), match.group(3)))
                    continue
            
            elif style == 'IEEE':
                # [n] I. Apellido, "Título,"
                match = re.search(r'^\[\d+\]\s(?:[A-Z]\.\s)?([A-Za-z\-]+)(?:,\s(?:[A-Z]\.\s)?[A-Za-z\-]+)*(?:,\sand\s(?:[A-Z]\.\s)?[A-Za-z\-]+)?,\s"(.+?),".+,\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(3), match.group(2)))
                    continue
            
            elif style == 'VANCOUVER':
                # Apellido AB, Apellido CD. Título.
                match = re.search(r'^(?:\d+\.\s)?([A-Za-z\-]+)\s[A-Z]{1,2}(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*(?:,\set\sal)?\.\s(.+?)\.(?:.+?)\s(\d{4})', citation)
                if match:
                    keys.append((match.group(1), match.group(3), match.group(2)))
                    continue
            
            elif style == 'CSE':
                # Apellido AB. Año. Título.
                match = re.search(r'^([A-Za-z\-]+)\s[A-Z]{1,2}(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*(?:,\set\sal)?\.\s(\d{4})\.\s(.+?)\.', citation)
                if match:
                    keys.append((match.group(1), match.group(2), match.group(3)))
                    continue
        
        return keys
    
    def _find_matching_reference(self, author: str, year: str, 
                               bib_keys: List[Tuple], style: str) -> bool:
        """
        Busca una entrada bibliográfica que corresponda a una cita en texto.
        
        Args:
            author (str): Autor citado
            year (str): Año citado
            bib_keys (List[Tuple]): Lista de claves de bibliografía
            style (str): Estilo de citación
            
        Returns:
            bool: True si se encuentra una coincidencia, False en caso contrario
        """
        if not year and style == 'MLA':
            # En MLA, solo verificamos por autor
            for key in bib_keys:
                bib_author = key[0]
                if self._match_author_names(author, bib_author):
                    return True
            return False
        
        for key in bib_keys:
            bib_author, bib_year = key[:2]
            if self._match_author_names(author, bib_author) and year == bib_year:
                return True
        
        return False
    
    def _find_matching_citation(self, author: str, year: str, 
                              in_text_keys: List[Tuple[str, str]], style: str) -> bool:
        """
        Busca una cita en texto que corresponda a una entrada bibliográfica.
        
        Args:
            author (str): Autor en la bibliografía
            year (str): Año en la bibliografía
            in_text_keys (List[Tuple[str, str]]): Lista de claves de citas en texto
            style (str): Estilo de citación
            
        Returns:
            bool: True si se encuentra una coincidencia, False en caso contrario
        """
        for citation_author, citation_year in in_text_keys:
            if style == 'MLA':
                # En MLA, solo verificamos por autor
                if self._match_author_names(author, citation_author):
                    return True
            else:
                if self._match_author_names(author, citation_author) and year == citation_year:
                    return True
        
        return False
    
    def _match_author_names(self, author1: str, author2: str) -> bool:
        """
        Compara nombres de autores para determinar si son el mismo.
        
        Args:
            author1 (str): Primer autor
            author2 (str): Segundo autor
            
        Returns:
            bool: True si los autores coinciden, False en caso contrario
        """
        # Normalizar los nombres
        auth1_norm = self._normalize_author_name(author1)
        auth2_norm = self._normalize_author_name(author2)
        
        # Comparación exacta
        if auth1_norm == auth2_norm:
            return True
        
        # Si uno contiene al otro (para manejar "et al.")
        if "et al" in auth1_norm:
            main_author1 = auth1_norm.split("et al")[0].strip()
            if main_author1 in auth2_norm:
                return True
        
        if "et al" in auth2_norm:
            main_author2 = auth2_norm.split("et al")[0].strip()
            if main_author2 in auth1_norm:
                return True
        
        # Si uno es subconjunto del otro (para múltiples autores)
        if auth1_norm in auth2_norm or auth2_norm in auth1_norm:
            return True
        
        # Si el apellido principal es el mismo
        main_author1 = auth1_norm.split()[0] if " " in auth1_norm else auth1_norm
        main_author2 = auth2_norm.split()[0] if " " in auth2_norm else auth2_norm
        
        if main_author1 == main_author2:
            return True
        
        return False
    
    def _normalize_author_name(self, author: str) -> str:
        """
        Normaliza un nombre de autor para comparaciones.
        
        Args:
            author (str): Nombre de autor
            
        Returns:
            str: Nombre normalizado
        """
        # Convertir a minúsculas
        normalized = author.lower()
        
        # Eliminar puntuación
        normalized = re.sub(r'[.,;:]', '', normalized)
        
        # Reemplazar caracteres especiales
        normalized = normalized.replace('&', 'and')
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _check_overall_style_consistency(self, citations: Dict[str, List[str]], 
                                        style: str) -> List[Dict[str, str]]:
        """
        Verifica la consistencia general de estilos en todo el documento.
        
        Args:
            citations (Dict[str, List[str]]): Diccionario con citas por tipo
            style (str): Estilo de citación principal
            
        Returns:
            List[Dict[str, str]]: Lista de problemas de consistencia general
        """
        issues = []
        
        # Detectar inconsistencias en formato de citas en texto
        in_text = citations.get('en_texto', [])
        if in_text:
            # Verificar mezcla de estilos de paréntesis
            has_parenthetical = any('(' in cit and ')' in cit for cit in in_text)
            has_brackets = any('[' in cit and ']' in cit for cit in in_text)
            
            if has_parenthetical and has_brackets:
                issues.append({
                    'rule_id': 'mixed_citation_styles',
                    'description': 'Se mezclan citas con paréntesis () y corchetes []',
                    'recommendation': f'En estilo {style}, mantener consistencia en el uso de paréntesis o corchetes',
                    'citation': None
                })
            
            # Verificar citas de autor-fecha vs numéricas
            has_author_year = any(re.search(r'\([A-Za-z].*\d{4}', cit) for cit in in_text)
            has_numeric = any(re.search(r'[\[\(]\d+[\]\)]', cit) for cit in in_text)
            
            if has_author_year and has_numeric:
                issues.append({
                    'rule_id': 'mixed_citation_systems',
                    'description': 'Se mezclan sistemas de citación autor-fecha y numérico',
                    'recommendation': f'Elegir un solo sistema de citación para todo el documento',
                    'citation': None
                })
        
        # Detectar inconsistencias en formato de entradas bibliográficas
        bib = citations.get('bibliograficas', [])
        if bib:
            # Verificar formatos de autor
            has_last_first = any(re.match(r'^[A-Za-z\-]+,\s[A-Za-z]', entry) for entry in bib)
            has_first_last = any(re.match(r'^[A-Z]\.\s[A-Za-z\-]+', entry) for entry in bib)
            
            if has_last_first and has_first_last:
                issues.append({
                    'rule_id': 'mixed_author_formats',
                    'description': 'Se mezclan formatos de autor (Apellido, Nombre y Inicial. Apellido)',
                    'recommendation': f'En estilo {style}, mantener consistencia en el formato de autores en la bibliografía',
                    'citation': None
                })
            
            # Verificar entradas numeradas vs no numeradas
            has_numbered = any(re.match(r'^\d+\.|\[\d+\]', entry) for entry in bib)
            has_unnumbered = any(re.match(r'^[A-Za-z]', entry) for entry in bib)
            
            if has_numbered and has_unnumbered:
                issues.append({
                    'rule_id': 'mixed_bibliography_numbering',
                    'description': 'La bibliografía mezcla entradas numeradas y no numeradas',
                    'recommendation': f'En estilo {style}, mantener consistencia en la numeración de entradas bibliográficas',
                    'citation': None
                })
        
        return issues
    
    def _generate_recommendations(self, citations: Dict[str, List[str]], style: str, 
                                issues: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """
        Genera recomendaciones generales basadas en el análisis.
        
        Args:
            citations (Dict[str, List[str]]): Diccionario con citas por tipo
            style (str): Estilo de citación principal
            issues (Dict[str, List[Dict[str, str]]]): Problemas detectados
            
        Returns:
            List[Dict[str, str]]: Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones para problemas comunes
        if issues['formato_incorrecto'] or issues['inconsistencias_estilo']:
            # Contar tipos de problemas para priorizar recomendaciones
            issue_types = Counter([issue['rule_id'] for issue_list in issues.values() 
                                  for issue in issue_list])
            
            # Recomendar guía de estilo
            recommendations.append({
                'rule_id': 'consult_style_guide',
                'description': f'Revisar guía oficial de estilo {style}',
                'recommendation': f'Consultar la guía oficial del estilo {style} para asegurar consistencia',
                'citation': None
            })
            
            # Recomendar herramientas
            if style in ['APA', 'MLA', 'CHICAGO', 'HARVARD']:
                recommendations.append({
                    'rule_id': 'use_citation_tool',
                    'description': 'Considerar el uso de un gestor de referencias',
                    'recommendation': 'Herramientas como Zotero, Mendeley o EndNote pueden ayudar a mantener consistencia en las citas',
                    'citation': None
                })
        
        # Recomendaciones específicas por estilo
        if style == 'APA':
            in_text = citations.get('en_texto', [])
            bib = citations.get('bibliograficas', [])
            
            # Verificar si hay citas con múltiples autores
            has_multiple_authors = any('&' in cit or 'et al' in cit for cit in in_text)
            if has_multiple_authors:
                recommendations.append({
                    'rule_id': 'apa_et_al',
                    'description': 'Regla APA para múltiples autores',
                    'recommendation': 'Para tres o más autores, usar "et al." desde la primera cita (APA 7ª edición)',
                    'citation': None
                })
            
            # Verificar si hay DOIs en la bibliografía
            has_doi = any('doi' in entry.lower() for entry in bib)
            if not has_doi and bib:
                recommendations.append({
                    'rule_id': 'apa_doi',
                    'description': 'Incluir DOI en entradas bibliográficas',
                    'recommendation': 'APA 7ª edición recomienda incluir DOI para artículos académicos cuando estén disponibles',
                    'citation': None
                })
        
        elif style == 'MLA':
            # Verificar uso de "et al."
            in_text = citations.get('en_texto', [])
            has_et_al = any('et al' in cit for cit in in_text)
            
            if has_et_al:
                recommendations.append({
                    'rule_id': 'mla_et_al',
                    'description': 'Regla MLA para múltiples autores',
                    'recommendation': 'En MLA 9ª edición, usar "et al." para obras con tres o más autores',
                    'citation': None
                })
            
            # Recomendar inclusión de URL para recursos web
            bib = citations.get('bibliograficas', [])
            has_web = any('web' in entry.lower() or 'www' in entry.lower() or 'http' in entry.lower() for entry in bib)
            
            if has_web:
                recommendations.append({
                    'rule_id': 'mla_web',
                    'description': 'Formato MLA para recursos web',
                    'recommendation': 'Para recursos web, incluir la URL y la fecha de acceso',
                    'citation': None
                })
        
        elif style == 'CHICAGO':
            # Verificar si hay notas al pie
            in_text = citations.get('en_texto', [])
            has_footnotes = any(re.match(r'^\d+\.', cit) for cit in in_text)
            
            if has_footnotes:
                recommendations.append({
                    'rule_id': 'chicago_notes',
                    'description': 'Sistema de notas Chicago',
                    'recommendation': 'En el sistema de notas Chicago, se puede usar forma abreviada para citas repetidas',
                    'citation': None
                })
            else:
                recommendations.append({
                    'rule_id': 'chicago_author_date',
                    'description': 'Sistema autor-fecha Chicago',
                    'recommendation': 'En el sistema autor-fecha Chicago, asegurar que cada cita tenga su entrada correspondiente en la bibliografía',
                    'citation': None
                })
        
        # Recomendaciones sobre completitud
        in_text_count = len(citations.get('en_texto', []))
        bib_count = len(citations.get('bibliograficas', []))
        
        if in_text_count > 0 and bib_count == 0:
            recommendations.append({
                'rule_id': 'missing_bibliography_section',
                'description': 'No se detecta sección de bibliografía',
                'recommendation': 'Añadir una sección de bibliografía con todas las obras citadas',
                'citation': None
            })
        
        # Priorizar recomendaciones
        return recommendations
    
    def list_common_issues(self, style: str) -> Dict[str, List[str]]:
        """
        Ofrece información sobre problemas comunes en el estilo especificado.
        
        Args:
            style (str): Estilo de citación
            
        Returns:
            Dict[str, List[str]]: Diccionario con problemas comunes agrupados por categoría
        """
        common_issues = {
            'formato': [],
            'contenido': [],
            'errores_frecuentes': []
        }
        
        if style == 'APA':
            common_issues['formato'] = [
                'Usar coma entre autor y año: (Smith, 2020)',
                'Usar "&" en citas parentéticas y "y" en citas narrativas',
                'Para citas con página: (Smith, 2020, p. 25)',
                'Para tres o más autores, usar "et al." desde la primera cita (7ª ed.)'
            ]
            common_issues['contenido'] = [
                'Incluir DOI para artículos cuando esté disponible',
                'URLs sin "Recuperado de" (7ª ed.)',
                'Hasta 20 autores en la bibliografía antes de usar "et al." (7ª ed.)',
                'Incluir el lugar de publicación sólo para libros (7ª ed.)'
            ]
            common_issues['errores_frecuentes'] = [
                'Inconsistencia en el uso de "&" y "y"',
                'Falta de coma entre autor y año',
                'Formato incorrecto para artículos electrónicos',
                'Inconsistencia en el uso de cursivas para títulos'
            ]
        
        elif style == 'MLA':
            common_issues['formato'] = [
                'Sin coma entre autor y página: (Smith 25)',
                'No incluir el año en citas en texto',
                'Usar "and" para conectar autores, no "&"',
                'Títulos de artículos entre comillas, títulos de libros en cursiva'
            ]
            common_issues['contenido'] = [
                'Incluir el nombre del editor para sitios web',
                'Fecha completa para artículos de revista (día mes año)',
                'Incluir URL y fecha de acceso para recursos web',
                'Especificar medio de publicación (Print, Web, etc.)'
            ]
            common_issues['errores_frecuentes'] = [
                'Incluir año en citas en texto (sólo se usa en bibliografía)',
                'Usar "&" en lugar de "and"',
                'Olvidar la fecha de acceso para recursos web',
                'Formato incorrecto para autores (debe ser Apellido, Nombre)'
            ]
        
        elif style == 'CHICAGO':
            common_issues['formato'] = [
                'Dos sistemas: notas al pie y autor-fecha',
                'Notas al pie: número superíndice en texto, nota completa a pie de página',
                'Autor-fecha: (Apellido año, página)',
                'Bibliografía: Apellido, Nombre completo'
            ]
            common_issues['contenido'] = [
                'Primera nota al pie debe ser completa, las siguientes pueden ser abreviadas',
                'Usar "Ibid." para referencias repetidas consecutivas',
                'Incluir URL y fecha de acceso para recursos web',
                'Títulos de artículos entre comillas, títulos de libros en cursiva'
            ]
            common_issues['errores_frecuentes'] = [
                'Mezclar los dos sistemas (notas y autor-fecha)',
                'Usar "et al." incorrectamente (Chicago permite hasta tres autores)',
                'Formato incorrecto para editores y traductores',
                'Uso incorrecto de abreviaturas latinas (Ibid., Op. cit.)'
            ]
        
        elif style == 'HARVARD':
            common_issues['formato'] = [
                'Citas en texto: (Apellido, año: página)',
                'Usar dos puntos antes de la página, no coma',
                'Bibliografía: Apellido, Iniciales. (año)',
                'Títulos en cursiva para libros y revistas'
            ]
            common_issues['contenido'] = [
                'Incluir lugar de publicación y editorial',
                'Incluir URL y fecha de acceso para recursos web',
                'Usar "et al." para cuatro o más autores en citas en texto',
                'Listar todos los autores en la bibliografía'
            ]
            common_issues['errores_frecuentes'] = [
                'Usar coma en lugar de dos puntos antes de la página',
                'Formato incorrecto para iniciales de autor',
                'No incluir paréntesis para el año en la bibliografía',
                'Orden incorrecto de elementos en la bibliografía'
            ]
        
        elif style == 'IEEE':
            common_issues['formato'] = [
                'Citas numéricas: [1] o [1, 2, 3]',
                'Bibliografía numerada en orden de aparición',
                'Iniciales antes del apellido: A. B. Autor',
                'Títulos de artículos entre comillas'
            ]
            common_issues['contenido'] = [
                'Incluir DOI para artículos cuando esté disponible',
                'Abreviar nombres de revistas',
                'Incluir rango de páginas completo',
                'Mes y año para conferencias y revistas'
            ]
            common_issues['errores_frecuentes'] = [
                'Formato incorrecto para números de página (pp. 123-145)',
                'No abreviar nombres de revistas',
                'Formato incorrecto para autores múltiples',
                'Uso de paréntesis en lugar de corchetes para citas'
            ]
        
        elif style == 'VANCOUVER':
            common_issues['formato'] = [
                'Citas numéricas: (1) o superíndice¹',
                'Referencias numeradas por orden de aparición',
                'Autores: Apellido AB, Apellido CD',
                'Usar "et al." después de seis autores'
            ]
            common_issues['contenido'] = [
                'Abreviar nombres de revistas sin puntos',
                'Formato de fecha: año;volumen(número):páginas',
                'No incluir lugar de publicación para artículos',
                'Usar ';' para separar año y volumen'
            ]
            common_issues['errores_frecuentes'] = [
                'No abreviar nombres de revistas',
                'Formato incorrecto para volumen, número y páginas',
                'Incluir títulos de capítulos cuando no es necesario',
                'Usar paréntesis en lugar de superíndices'
            ]
        
        elif style == 'CSE':
            common_issues['formato'] = [
                'Tres sistemas: cita-secuencia, cita-nombre, nombre-año',
                'Cita-secuencia: [1] o superíndice¹',
                'Nombre-año: (Autor año)',
                'Autores: Apellido AB (sin coma)'
            ]
            common_issues['contenido'] = [
                'Abreviar nombres de revistas',
                'Año inmediatamente después del autor',
                'No usar "and" o "&", simplemente separar autores con comas',
                'Usar punto después del año'
            ]
            common_issues['errores_frecuentes'] = [
                'Mezclar diferentes sistemas de citación',
                'Formato incorrecto para autores (con coma)',
                'No abreviar nombres de revistas',
                'Orden incorrecto de elementos en la bibliografía'
            ]
        
        else:
            # Problemas generales para cualquier estilo
            common_issues['formato'] = [
                'Inconsistencia en el formato de citas',
                'Mezcla de múltiples estilos de citación',
                'Formato incorrecto para múltiples autores',
                'Uso incorrecto de cursivas y comillas'
            ]
            common_issues['contenido'] = [
                'Información incompleta en entradas bibliográficas',
                'Citas sin entrada correspondiente en la bibliografía',
                'Entradas bibliográficas no citadas en el texto',
                'Información de publicación incorrecta o incompleta'
            ]
            common_issues['errores_frecuentes'] = [
                'Inconsistencia en nombres de autores',
                'Formato incorrecto para recursos electrónicos',
                'Ordenamiento incorrecto de la bibliografía',
                'Uso incorrecto de abreviaturas'
            ]
        
        return common_issues


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del validador
    validator = CitationValidator()
    
    # Ejemplo de citas en texto (estilo APA)
    in_text_citations = [
        "(Smith, 2020, p. 45)",
        "Según Johnson et al. (2019)",
        "(Brown & Davis, 2018)",
        "Williams (2021) argumenta que"
    ]
    
    # Ejemplo de entradas bibliográficas (estilo APA)
    bibliography = [
        "Smith, J. A. (2020). Patterns of correlation in environmental studies. Journal of Environmental Science, 45(2), 78-92.",
        "Johnson, R. B., Thompson, C., & Davis, K. (2019). Cultural contexts and research methodology. Academic Press.",
        "Williams, P. T. (2021). Cross-cultural patterns in social behavior. Social Psychology, 33(4), 156-170.",
        "Brown, M., & Davis, L. (2018). Contrasting methodologies in social research. Research Methods, 12(3), 45-67."
    ]
    
    # Validar citas
    issues = validator.validate_all_citations({
        'en_texto': in_text_citations,
        'bibliograficas': bibliography
    }, 'APA')
    
    # Imprimir problemas detectados
    print("PROBLEMAS DETECTADOS:")
    for category, category_issues in issues.items():
        if category_issues:
            print(f"\n{category.upper()}:")
            for issue in category_issues:
                print(f"- {issue['description']}")
                print(f"  Recomendación: {issue['recommendation']}")