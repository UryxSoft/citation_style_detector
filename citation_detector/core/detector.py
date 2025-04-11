# Clase principal CitationStyleDetector
# detector.py
# Implementación de la clase principal CitationStyleDetector

import re
import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from collections import Counter

class CitationStyleDetector:
    """
    Clase para detectar y verificar estilos de citación en textos.
    Puede identificar APA, MLA, Chicago y otros estilos tanto para citas completas como en el texto.
    """
    
    def __init__(self, load_custom_patterns: bool = False, custom_patterns_path: str = None):
        """
        Inicializa el detector de estilos de citación.
        
        Args:
            load_custom_patterns (bool): Si se deben cargar patrones personalizados
            custom_patterns_path (str): Ruta al archivo JSON con patrones personalizados
        """
        # Configurar logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('CitationStyleDetector')
        
        # Patrones para detectar citas en texto
        self.in_text_patterns = {
            'APA': [
                # (Autor, 2020) o (Autor, 2020, p. 25)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?),\s(?P<year>\d{4})(?:,\s(?P<pages>p\.?\s\d+(?:-\d+)?))?\)',
                
                # (Autor & Autor, 2020)
                r'\((?P<author1>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\s&\s(?P<author2>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?),\s(?P<year>\d{4})(?:,\s(?P<pages>p\.?\s\d+(?:-\d+)?))?\)',
                
                # (Autor et al., 2020)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\set\sal\.,\s(?P<year>\d{4})(?:,\s(?P<pages>p\.?\s\d+(?:-\d+)?))?\)',
                
                # Autor (2020) o Autor (2020, p. 25)
                r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\s\((?P<year>\d{4})(?:,\s(?P<pages>p\.?\s\d+(?:-\d+)?))?\)'
            ],
            'MLA': [
                # (Smith 25)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) (?P<pages>\d+(?:-\d+)?)\)',
                
                # (Smith and Johnson 25)
                r'\((?P<author1>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?) and (?P<author2>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?) (?P<pages>\d+(?:-\d+)?)\)',
                
                # Smith (25)
                r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) \((?P<pages>\d+(?:-\d+)?)\)'
            ],
            'CHICAGO_AUTHOR_DATE': [
                # (Autor 2020, 25)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) (?P<year>\d{4})(?:, (?P<pages>\d+(?:-\d+)?))?\)',
                
                # (Autor and Autor 2020, 25)
                r'\((?P<author1>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?) and (?P<author2>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?) (?P<year>\d{4})(?:, (?P<pages>\d+(?:-\d+)?))?\)',
                
                # Autor (2020, 25)
                r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) \((?P<year>\d{4})(?:, (?P<pages>\d+(?:-\d+)?))?\)'
            ],
            'CHICAGO_NOTES': [
                # Footnote format
                r'^\d+\.\s(?P<citation>.+)',
                
                # Ibid., Op. cit., etc.
                r'(?P<citation>(?:Ibid\.|Op\. cit\.|Loc\. cit\.)(?:,\s\d+(?:-\d+)?)?)'
            ],
            'HARVARD': [
                # (Autor, 2020) o (Autor, 2020: 25)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?),\s(?P<year>\d{4})(?:: (?P<pages>\d+(?:-\d+)?))?\)',
                
                # Autor (2020)
                r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) \((?P<year>\d{4})(?:: (?P<pages>\d+(?:-\d+)?))?\)'
            ],
            'IEEE': [
                # [1] o [1, 2, 3]
                r'\[(?P<citation>\d+(?:,\s*\d+)*)\]'
            ],
            'VANCOUVER': [
                # (1) o (1-3)
                r'\((?P<citation>\d+(?:-\d+)?)\)',
                
                # Superíndice¹,²,³
                r'(?P<citation>[\u00B9\u00B2\u00B3\u2070-\u2079]+)'
            ],
            'CSE': [
                # (Autor 2020) o (Autor and Autor 2020)
                r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) (?P<year>\d{4})\)',
                
                # Autor 2020
                r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?) (?P<year>\d{4})'
            ]
        }
        
        # Patrones para detectar citas bibliográficas completas
        self.full_citation_patterns = {
            'APA': [
                # Libro: Apellido, I. (Año). Título. Editorial.
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)(?:,\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*(?:,?\s&\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?\s\((?P<year>\d{4})\)\.\s(?P<title>.+?)\.\s(?P<publisher>[A-Za-z\s]+)\.',
                
                # Artículo: Apellido, I. (Año). Título del artículo. Nombre de la revista, vol(num), pp-pp.
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)(?:,\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*(?:,?\s&\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?\s\((?P<year>\d{4})\)\.\s(?P<title>.+?)\.\s(?P<journal>.+?),\s(?P<volume>\d+)(?:\((?P<issue>\d+)\))?,\s(?P<pages>\d+-\d+)\.',
                
                # Recurso web: Apellido, I. (Año). Título. Recuperado de URL
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)(?:,\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*(?:,?\s&\s[A-Za-z\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?\s\((?P<year>\d{4})(?:,\s[A-Za-z]+\s\d+)?\)\.\s(?P<title>.+?)\.\s(?:Recuperado|Retrieved)(?:\son|\sde)\s(?P<url>https?://[^\s]+)'
            ],
            'MLA': [
                # Libro: Apellido, Nombre. Título. Editorial, Año.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*\.\s(?P<title>.+?)\.\s(?P<publisher>[A-Za-z\s]+),\s(?P<year>\d{4})\.',
                
                # Artículo: Apellido, Nombre. "Título del artículo." Nombre de la revista, vol. número, año, pp. xx-xx.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*\.\s"(?P<title>.+?)\."\s(?P<journal>.+?),\svol\.\s(?P<volume>\d+)(?:,\sno\.\s(?P<issue>\d+))?,\s(?P<year>\d{4}),\spp\.\s(?P<pages>\d+-\d+)\.',
                
                # Recurso web: Apellido, Nombre. "Título del artículo." Nombre del sitio web, Fecha, URL. Accessed Fecha.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*\.\s"(?P<title>.+?)\."\s(?P<site>.+?),\s(?P<date>[A-Za-z\.\s\d,]+),\s(?P<url>https?://[^\s]+)(?:\.\s(?:Accessed|Accedido)\s(?P<access_date>[A-Za-z\.\s\d,]+))?.'
            ],
            'CHICAGO': [
                # Libro: Apellido, Nombre. Título. Ciudad: Editorial, Año.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)?\.\s(?P<title>.+?)\.\s(?P<city>[A-Za-z\s]+):\s(?P<publisher>[A-Za-z\s]+),\s(?P<year>\d{4})\.',
                
                # Artículo: Apellido, Nombre. "Título del artículo." Nombre de la revista vol, no. número (Año): pp-pp.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)?\.\s"(?P<title>.+?)\."\s(?P<journal>.+?)\s(?P<volume>\d+),\sno\.\s(?P<issue>\d+)\s\((?P<year>\d{4})\):\s(?P<pages>\d+-\d+)\.',
                
                # Recurso web: Apellido, Nombre. "Título." Sitio web. Fecha. URL.
                r'(?P<author>[A-Za-z\-]+,\s[A-Za-z\s\-]+)(?:,\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)*(?:,\sand\s[A-Za-z\-]+,\s[A-Za-z\s\-]+)?\.\s"(?P<title>.+?)\."\s(?P<site>.+?)\.\s(?P<date>[A-Za-z\.\s\d,]+)\.\s(?P<url>https?://[^\s]+)\.'
            ],
            'HARVARD': [
                # Libro: Apellido, I. (Año) Título. Lugar de publicación: Editorial.
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.)(?:,\s[A-Za-z\-]+,\s[A-Z]\.)*(?:\sand\s[A-Za-z\-]+,\s[A-Z]\.)?\s\((?P<year>\d{4})\)\s(?P<title>.+?)\.\s(?P<city>[A-Za-z\s]+):\s(?P<publisher>[A-Za-z\s]+)\.',
                
                # Artículo: Apellido, I. (Año) 'Título del artículo', Nombre de la revista, Volumen(Número), pp. xx-xx.
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.)(?:,\s[A-Za-z\-]+,\s[A-Z]\.)*(?:\sand\s[A-Za-z\-]+,\s[A-Z]\.)?\s\((?P<year>\d{4})\)\s\'(?P<title>.+?)\',\s(?P<journal>.+?),\s(?P<volume>\d+)(?:\((?P<issue>\d+)\))?,\spp\.\s(?P<pages>\d+-\d+)\.',
                
                # Recurso web: Apellido, I. (Año) Título [Online]. Disponible en: URL [Accedido: fecha].
                r'(?P<author>[A-Za-z\-]+,\s[A-Z]\.)(?:,\s[A-Za-z\-]+,\s[A-Z]\.)*(?:\sand\s[A-Za-z\-]+,\s[A-Z]\.)?\s\((?P<year>\d{4})\)\s(?P<title>.+?)\s\[Online\]\.\s(?:Available|Disponible)(?:\sat|\sen):\s(?P<url>https?://[^\s]+)\s\[(?:Accessed|Accedido):\s(?P<access_date>[A-Za-z\.\s\d,]+)\]'
            ],
            'IEEE': [
                # [1] I. Apellido, "Título del artículo," Nombre de la revista, vol. x, no. x, pp. xx-xx, Fecha.
                r'\[(?P<number>\d+)\]\s(?P<author>[A-Z]\.\s[A-Za-z\-]+)(?:,\s[A-Z]\.\s[A-Za-z\-]+)*(?:,\sand\s[A-Z]\.\s[A-Za-z\-]+)?,\s"(?P<title>.+?)(?:,|")(?:\s(?P<journal>.+?),\svol\.\s(?P<volume>\d+),\sno\.\s(?P<issue>\d+),\spp\.\s(?P<pages>\d+-\d+),\s(?P<date>[A-Za-z\.\s\d,]+))?',
                
                # [1] I. Apellido, Título del libro. Ciudad: Editorial, Año, pp. xx-xx.
                r'\[(?P<number>\d+)\]\s(?P<author>[A-Z]\.\s[A-Za-z\-]+)(?:,\s[A-Z]\.\s[A-Za-z\-]+)*(?:,\sand\s[A-Z]\.\s[A-Za-z\-]+)?,\s(?P<title>.+?)\.\s(?P<city>[A-Za-z\s]+):\s(?P<publisher>[A-Za-z\s]+),\s(?P<year>\d{4})(?:,\spp\.\s(?P<pages>\d+-\d+))?'
            ],
            'VANCOUVER': [
                # 1. Apellido AB, Apellido CD. Título del artículo. Nombre de la revista. Año;Volumen(Número):Páginas.
                r'(?P<number>\d+)\.\s(?P<author>[A-Za-z\-]+\s[A-Z]{1,2})(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})?\.\s(?P<title>.+?)\.\s(?P<journal>.+?)\.\s(?P<year>\d{4});(?P<volume>\d+)(?:\((?P<issue>\d+)\))?:(?P<pages>\d+-\d+)\.',
                
                # 1. Apellido AB. Título del libro. Edición. Ciudad: Editorial; Año.
                r'(?P<number>\d+)\.\s(?P<author>[A-Za-z\-]+\s[A-Z]{1,2})(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})?\.\s(?P<title>.+?)(?:\.\s(?P<edition>\d+)(?:rd|nd|st|th)\sed)?(?:\.\s(?P<city>[A-Za-z\s]+):\s(?P<publisher>[A-Za-z\s]+);\s(?P<year>\d{4}))?'
            ],
            'CSE': [
                # Apellido IN. Año. Título del artículo. Nombre de la revista. Volumen(Número):Páginas.
                r'(?P<author>[A-Za-z\-]+\s[A-Z]{1,2})(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*\.\s(?P<year>\d{4})\.\s(?P<title>.+?)\.\s(?P<journal>.+?)\.\s(?P<volume>\d+)(?:\((?P<issue>\d+)\))?:(?P<pages>\d+-\d+)\.',
                
                # Apellido IN, Apellido IN. Año. Título del libro. Ciudad (Estado): Editorial. Páginas p.
                r'(?P<author>[A-Za-z\-]+\s[A-Z]{1,2})(?:,\s[A-Za-z\-]+\s[A-Z]{1,2})*\.\s(?P<year>\d{4})\.\s(?P<title>.+?)\.\s(?P<city>[A-Za-z\s]+)(?:\s\([A-Z]{2}\))?:\s(?P<publisher>[A-Za-z\s]+)(?:\.\s(?P<pages>\d+)\sp)?'
            ]
        }
        
        # Cargar patrones personalizados si se solicita
        if load_custom_patterns and custom_patterns_path:
            self._load_custom_patterns(custom_patterns_path)
    
    def _load_custom_patterns(self, path: str) -> None:
        """
        Carga patrones personalizados desde un archivo JSON.
        
        Args:
            path (str): Ruta al archivo JSON con patrones personalizados
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                custom_patterns = json.load(f)
            
            # Actualizar patrones in-text
            if 'in_text_patterns' in custom_patterns:
                for style, patterns in custom_patterns['in_text_patterns'].items():
                    if style in self.in_text_patterns:
                        self.in_text_patterns[style].extend(patterns)
                    else:
                        self.in_text_patterns[style] = patterns
            
            # Actualizar patrones de citas completas
            if 'full_citation_patterns' in custom_patterns:
                for style, patterns in custom_patterns['full_citation_patterns'].items():
                    if style in self.full_citation_patterns:
                        self.full_citation_patterns[style].extend(patterns)
                    else:
                        self.full_citation_patterns[style] = patterns
            
            self.logger.info(f"Patrones personalizados cargados desde {path}")
        
        except Exception as e:
            self.logger.error(f"Error cargando patrones personalizados: {e}")
    
    def detect_citation_styles(self, text: str) -> Dict[str, Dict[str, int]]:
        """
        Detecta los estilos de citación presentes en el texto.
        
        Args:
            text (str): El texto a analizar
            
        Returns:
            Dict[str, Dict[str, int]]: Un diccionario con el conteo de ocurrencias de cada estilo
        """
        results = {
            'in_text': {style: 0 for style in self.in_text_patterns},
            'full_citation': {style: 0 for style in self.full_citation_patterns}
        }
        
        # Detectar citas en texto
        for style, patterns in self.in_text_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                results['in_text'][style] += len(matches)
        
        # Detectar citas bibliográficas completas
        for style, patterns in self.full_citation_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                results['full_citation'][style] += len(matches)
        
        return results
    
    def identify_primary_style(self, text: str) -> Tuple[str, float]:
        """
        Identifica el estilo de citación principal utilizado en el texto.
        
        Args:
            text (str): El texto a analizar
            
        Returns:
            Tuple[str, float]: El estilo predominante y su nivel de confianza (0.0-1.0)
        """
        results = self.detect_citation_styles(text)
        
        # Sumar todas las ocurrencias
        total_in_text = sum(results['in_text'].values())
        total_full = sum(results['full_citation'].values())
        total = total_in_text + total_full
        
        if total == 0:
            return "No se detectaron citas", 0.0
        
        # Combinar resultados para cada estilo
        combined_results = {}
        for style in self.in_text_patterns:
            if style == "CHICAGO_AUTHOR_DATE" or style == "CHICAGO_NOTES":
                # Combinar los estilos de Chicago
                if "CHICAGO" not in combined_results:
                    combined_results["CHICAGO"] = 0
                combined_results["CHICAGO"] += results['in_text'][style]
            else:
                if style not in combined_results:
                    combined_results[style] = 0
                combined_results[style] += results['in_text'][style]
        
        for style in self.full_citation_patterns:
            if style not in combined_results:
                combined_results[style] = 0
            combined_results[style] += results['full_citation'][style]
        
        # Encontrar el estilo predominante
        if not combined_results:
            return "No se detectaron citas", 0.0
            
        primary_style = max(combined_results, key=combined_results.get)
        confidence = combined_results[primary_style] / total
        
        return primary_style, confidence
    
    def validate_citations(self, text: str) -> Dict[str, List[str]]:
        """
        Valida la consistencia de las citas en el texto.
        
        Args:
            text (str): El texto a analizar
            
        Returns:
            Dict[str, List[str]]: Un diccionario con problemas detectados por categoría
        """
        primary_style, confidence = self.identify_primary_style(text)
        
        issues = {
            'inconsistencias_estilo': [],
            'formato_incorrecto': [],
            'recomendaciones': []
        }
        
        if primary_style == "No se detectaron citas":
            issues['recomendaciones'].append("No se detectaron citas en el texto.")
            return issues
        
        if confidence < 0.7:
            issues['inconsistencias_estilo'].append(
                f"Se detectaron múltiples estilos de citación. El estilo predominante es {primary_style} "
                f"con una confianza de {confidence:.2f}. Se recomienda unificar al estilo {primary_style}."
            )
        
        # Validar formato según el estilo predominante
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Verificaciones específicas de cada estilo
            if primary_style == "APA":
                # Verificar formato de fecha en citas APA
                if re.search(r'\([A-Za-z]+ \d{4}\)', line) and not re.search(r'\([A-Za-z]+, \d{4}\)', line):
                    issues['formato_incorrecto'].append(
                        f"Línea {line_num}: La cita parece ser APA pero falta una coma entre el autor y el año."
                    )
                
                # Verificar página en formato correcto
                if re.search(r'\d{4}, \d+', line) and not re.search(r'\d{4}, p\.? \d+', line):
                    issues['formato_incorrecto'].append(
                        f"Línea {line_num}: La cita parece ser APA pero falta indicador de página (p. o pp.)."
                    )
            
            elif primary_style == "MLA":
                # Verificar que no haya comas entre autor y página en MLA
                if re.search(r'\([A-Za-z]+, \d+\)', line):
                    issues['formato_incorrecto'].append(
                        f"Línea {line_num}: La cita parece ser MLA pero tiene una coma entre el autor y el número de página."
                    )
                
                # Verificar uso correcto de "and" en vez de "&"
                if re.search(r'[A-Za-z]+ & [A-Za-z]+ \d+', line):
                    issues['formato_incorrecto'].append(
                        f"Línea {line_num}: En MLA debe usarse 'and' en lugar de '&' para conectar autores."
                    )
            
            elif primary_style == "CHICAGO":
                # Verificar notas al pie numeradas correctamente
                footnote_match = re.search(r'^(\d+)\.\s', line)
                if footnote_match:
                    # Verificar si el número de nota corresponde a la secuencia
                    footnote_num = int(footnote_match.group(1))
                    expected_num = 1
                    for prev_line in lines[:i]:
                        prev_match = re.search(r'^(\d+)\.\s', prev_line)
                        if prev_match:
                            expected_num += 1
                    
                    if footnote_num != expected_num:
                        issues['formato_incorrecto'].append(
                            f"Línea {line_num}: Número de nota al pie incorrecto. Se esperaba {expected_num}, se encontró {footnote_num}."
                        )
            
            elif primary_style == "HARVARD":
                # Verificar dos puntos para separar año y página
                if re.search(r'\d{4}, \d+', line) and not re.search(r'\d{4}: \d+', line):
                    issues['formato_incorrecto'].append(
                        f"Línea {line_num}: En Harvard se usa dos puntos (año: página) en lugar de coma."
                    )
        
        # Validar cruce de citas en texto y bibliografía
        in_text_citations = self._extract_citation_keys(text, primary_style)
        bibliography_entries = self._extract_bibliography_entries(text, primary_style)
        
        # Verificar citas sin entrada bibliográfica
        cited_not_referenced = self._find_citations_without_references(in_text_citations, bibliography_entries, primary_style)
        for citation in cited_not_referenced:
            issues['inconsistencias_estilo'].append(
                f"La cita '{citation}' aparece en el texto pero no tiene una entrada correspondiente en la bibliografía."
            )
        
        # Verificar entradas bibliográficas no citadas
        referenced_not_cited = self._find_references_without_citations(in_text_citations, bibliography_entries, primary_style)
        if referenced_not_cited:
            issues['recomendaciones'].append(
                f"Se encontraron {len(referenced_not_cited)} entradas bibliográficas que no están citadas en el texto."
            )
        
        # Recomendaciones según estilo
        if primary_style == "APA":
            issues['recomendaciones'].append(
                "En APA 7ª edición, las citas en texto con tres o más autores deben abreviarse usando 'et al.'"
            )
        elif primary_style == "MLA":
            issues['recomendaciones'].append(
                "En MLA, incluir solo apellido y página en las citas parentéticas. El año solo va en la bibliografía."
            )
        elif primary_style == "CHICAGO":
            issues['recomendaciones'].append(
                "Chicago permite dos sistemas: notas al pie (más común en humanidades) y autor-fecha (más común en ciencias)."
            )
        
        return issues
    
    def _extract_citation_keys(self, text: str, style: str) -> List[Tuple[str, str]]:
        """
        Extrae identificadores clave (autor, año) de las citas en texto.
        
        Args:
            text (str): El texto a analizar
            style (str): El estilo de citación predominante
            
        Returns:
            List[Tuple[str, str]]: Lista de tuplas (autor, año) o (autor, página)
        """
        keys = []
        
        # Patrones específicos según estilo
        if style == "APA" or style == "HARVARD":
            # Para APA: extraer pares (autor, año)
            pattern = r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?),\s(?P<year>\d{4})'
            matches = re.finditer(pattern, text)
            for match in matches:
                author = match.group('author').strip()
                year = match.group('year').strip()
                keys.append((author, year))
            
            # También forma narrativa: Autor (año)
            pattern = r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?)\s\((?P<year>\d{4})'
            matches = re.finditer(pattern, text)
            for match in matches:
                author = match.group('author').strip()
                year = match.group('year').strip()
                keys.append((author, year))
        
        elif style == "MLA":
            # Para MLA: extraer pares (autor, página) pero para comparar usamos autor
            pattern = r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?)\s\d+'
            matches = re.finditer(pattern, text)
            for match in matches:
                author = match.group('author').strip()
                keys.append((author, ""))  # Año vacío ya que MLA usa páginas
            
            # También forma narrativa
            pattern = r'(?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?)\s\(\d+'
            matches = re.finditer(pattern, text)
            for match in matches:
                author = match.group('author').strip()
                keys.append((author, ""))
        
        elif style == "CHICAGO":
            # Para Chicago autor-fecha
            pattern = r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?(?: et al\.)?)\s(?P<year>\d{4})'
            matches = re.finditer(pattern, text)
            for match in matches:
                author = match.group('author').strip()
                year = match.group('year').strip()
                keys.append((author, year))
            
            # No extraemos notas al pie aquí (requiere análisis más complejo)
        
        # Eliminar duplicados
        return list(set(keys))
    
    def _extract_bibliography_entries(self, text: str, style: str) -> List[Dict[str, str]]:
        """
        Extrae entradas bibliográficas completas del texto.
        
        Args:
            text (str): El texto a analizar
            style (str): El estilo de citación predominante
            
        Returns:
            List[Dict[str, str]]: Lista de diccionarios con metadatos de cada entrada
        """
        entries = []
        
        # Encontrar sección de bibliografía
        bibliography_section = self._find_bibliography_section(text, style)
        if not bibliography_section:
            return entries
        
        # Patrones específicos según estilo
        patterns = self.full_citation_patterns.get(style, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, bibliography_section, re.MULTILINE)
            for match in matches:
                if hasattr(match, 'groupdict'):
                    entry = match.groupdict()
                    # Limpiar valores None
                    entry = {k: v for k, v in entry.items() if v is not None}
                    entries.append(entry)
        
        return entries
    
    def _find_bibliography_section(self, text: str, style: str) -> str:
        """
        Encuentra la sección de bibliografía en el texto.
        
        Args:
            text (str): El texto completo
            style (str): El estilo de citación
            
        Returns:
            str: Texto de la sección de bibliografía o cadena vacía
        """
        # Encabezados comunes por estilo
        headers = {
            "APA": [r'Referencias', r'Bibliografía', r'Referencias bibliográficas', 
                   r'References', r'Bibliography', r'Reference List'],
            "MLA": [r'Obras citadas', r'Bibliografía', r'Works Cited', r'Bibliography'],
            "CHICAGO": [r'Bibliografía', r'Notas', r'Bibliography', r'Notes', r'References'],
            "HARVARD": [r'Referencias', r'Bibliografía', r'References', r'Bibliography'],
            "IEEE": [r'Referencias', r'References'],
            "VANCOUVER": [r'Referencias', r'Bibliografía', r'References', r'Bibliography'],
            "CSE": [r'Referencias', r'Bibliografía', r'References', r'Bibliography', r'Cited References']
        }
        
        # Obtener encabezados para el estilo actual
        style_headers = headers.get(style, [])
        
        # Buscar encabezados en el texto
        for header in style_headers:
            pattern = fr'(?i)(?:^|\n)\s*{header}\s*(?:\n|$)'
            match = re.search(pattern, text)
            if match:
                # Extraer desde el encabezado hasta el final
                start_pos = match.start()
                return text[start_pos:]
        
        # Si no se encontró un encabezado, buscar patrones de referencias al final del texto
        lines = text.split('\n')
        for i in range(len(lines) - 1, 0, -1):
            for pattern in self.full_citation_patterns.get(style, []):
                if re.match(pattern, lines[i]):
                    # Encontró una línea que parece ser una referencia
                    # Buscar hacia atrás hasta encontrar una línea en blanco o un encabezado
                    start_line = i
                    while start_line > 0 and lines[start_line-1].strip():
                        start_line -= 1
                        if any(re.search(fr'(?i){h}', lines[start_line]) for h in style_headers):
                            break
                    
                    return '\n'.join(lines[start_line:])
        
        return ""
    
    def _find_citations_without_references(self, citations: List[Tuple[str, str]], 
                                         references: List[Dict[str, str]], 
                                         style: str) -> List[str]:
        """
        Encuentra citas en texto que no tienen entrada en la bibliografía.
        
        Args:
            citations (List[Tuple[str, str]]): Lista de citas en texto (autor, año)
            references (List[Dict[str, str]]): Lista de entradas bibliográficas
            style (str): Estilo de citación
            
        Returns:
            List[str]: Lista de citas sin referencia correspondiente
        """
        missing = []
        
        for author, year in citations:
            found = False
            
            for ref in references:
                # Comparar según el estilo
                if style in ["APA", "HARVARD", "CHICAGO"]:
                    # Extraer apellido del autor de la referencia
                    ref_author = ref.get('author', '')
                    if ref_author:
                        ref_author = ref_author.split(',')[0].strip()
                    
                    ref_year = ref.get('year', '')
                    
                    # Comparar apellido y año
                    if author and ref_author and year and ref_year:
                        # Normalizar para comparación
                        author_norm = author.lower().replace('et al.', '').strip()
                        ref_author_norm = ref_author.lower().strip()
                        
                        if author_norm in ref_author_norm or ref_author_norm in author_norm:
                            if year == ref_year:
                                found = True
                                break
                
                elif style == "MLA":
                    # En MLA solo comparamos autor (apellido)
                    ref_author = ref.get('author', '')
                    if ref_author:
                        ref_author = ref_author.split(',')[0].strip()
                    
                    if author and ref_author:
                        # Normalizar para comparación
                        author_norm = author.lower().replace('et al.', '').strip()
                        ref_author_norm = ref_author.lower().strip()
                        
                        if author_norm in ref_author_norm or ref_author_norm in author_norm:
                            found = True
                            break
            
            if not found and author.strip():  # Evitar falsos positivos con cadenas vacías
                citation_text = f"{author} ({year})" if year else author
                missing.append(citation_text)
        
        return missing
    
    def _find_references_without_citations(self, citations: List[Tuple[str, str]], 
                                         references: List[Dict[str, str]], 
                                         style: str) -> List[Dict[str, str]]:
        """
        Encuentra entradas bibliográficas que no están citadas en el texto.
        
        Args:
            citations (List[Tuple[str, str]]): Lista de citas en texto (autor, año)
            references (List[Dict[str, str]]): Lista de entradas bibliográficas
            style (str): Estilo de citación
            
        Returns:
            List[Dict[str, str]]: Lista de referencias no citadas
        """
        unused = []
        
        for ref in references:
            cited = False
            
            # Extraer autor y año de la referencia
            ref_author = ref.get('author', '')
            if ref_author:
                ref_author = ref_author.split(',')[0].strip()
            
            ref_year = ref.get('year', '')
            
            for author, year in citations:
                # Comparar según el estilo
                if style in ["APA", "HARVARD", "CHICAGO"]:
                    if author and ref_author and year and ref_year:
                        # Normalizar para comparación
                        author_norm = author.lower().replace('et al.', '').strip()
                        ref_author_norm = ref_author.lower().strip()
                        
                        if author_norm in ref_author_norm or ref_author_norm in author_norm:
                            if year == ref_year:
                                cited = True
                                break
                
                elif style == "MLA":
                    # En MLA solo comparamos autor (apellido)
                    if author and ref_author:
                        # Normalizar para comparación
                        author_norm = author.lower().replace('et al.', '').strip()
                        ref_author_norm = ref_author.lower().strip()
                        
                        if author_norm in ref_author_norm or ref_author_norm in author_norm:
                            cited = True
                            break
            
            if not cited and ref_author.strip():  # Evitar falsos positivos
                unused.append(ref)
        
        return unused
    
    def extract_citations(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae todas las citas encontradas en el texto.
        
        Args:
            text (str): El texto del que se extraerán las citas
            
        Returns:
            Dict[str, List[str]]: Un diccionario con las citas extraídas por tipo
        """
        citations = {
            'en_texto': [],
            'bibliograficas': []
        }
        
        # Detectar estilo predominante para usar patrones más específicos
        primary_style, confidence = self.identify_primary_style(text)
        
        if primary_style == "No se detectaron citas":
            return citations
        
        # Extraer citas en texto para el estilo predominante
        if primary_style in self.in_text_patterns:
            patterns = self.in_text_patterns[primary_style]
            if primary_style == "CHICAGO":
                # Para Chicago, incluir tanto autor-fecha como notas
                patterns = self.in_text_patterns.get("CHICAGO_AUTHOR_DATE", []) + \
                          self.in_text_patterns.get("CHICAGO_NOTES", [])
            
            for pattern in patterns:
                # Usar finditer para obtener el texto completo de la coincidencia
                matches = re.finditer(pattern, text, re.MULTILINE)
                for match in matches:
                    citations['en_texto'].append(match.group(0))
        
        # Extraer citas bibliográficas para el estilo predominante
        if primary_style in self.full_citation_patterns:
            # Encontrar la sección de bibliografía
            bibliography_section = self._find_bibliography_section(text, primary_style)
            if bibliography_section:
                patterns = self.full_citation_patterns[primary_style]
                
                for pattern in patterns:
                    # Buscar coincidencias en la sección de bibliografía
                    matches = re.finditer(pattern, bibliography_section, re.MULTILINE)
                    for match in matches:
                        citations['bibliograficas'].append(match.group(0))
                
                # Si no se encontraron coincidencias con los patrones,
                # usar un enfoque línea por línea para capturar posibles referencias
                if not citations['bibliograficas']:
                    lines = bibliography_section.split('\n')
                    current_ref = ""
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            if current_ref:
                                citations['bibliograficas'].append(current_ref)
                                current_ref = ""
                        else:
                            # Detectar si es el inicio de una nueva referencia o continuación
                            if (re.match(r'^[A-Za-z\-]+,', line) or  # Inicia con apellido
                                re.match(r'^\[\d+\]', line) or       # Inicia con [n]
                                re.match(r'^\d+\.', line)):          # Inicia con n.
                                if current_ref:
                                    citations['bibliograficas'].append(current_ref)
                                current_ref = line
                            else:
                                current_ref += " " + line
                    
                    # Añadir la última referencia si existe
                    if current_ref:
                        citations['bibliograficas'].append(current_ref)
        
        # Eliminar duplicados y ordenar
        citations['en_texto'] = sorted(list(set(citations['en_texto'])))
        citations['bibliograficas'] = sorted(list(set(citations['bibliograficas'])))
        
        return citations
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analiza un texto completo y devuelve un informe detallado sobre sus citas.
        
        Args:
            text (str): El texto a analizar
            
        Returns:
            Dict: Un diccionario con el análisis completo
        """
        style_counts = self.detect_citation_styles(text)
        primary_style, confidence = self.identify_primary_style(text)
        validation = self.validate_citations(text)
        
        # Contar citas totales
        total_in_text = sum(style_counts['in_text'].values())
        total_full = sum(style_counts['full_citation'].values())
        
        # Generar recomendaciones adicionales
        recommendations = []
        if primary_style != "No se detectaron citas":
            if confidence < 0.7:
                recommendations.append(f"Unificar todas las citas al estilo {primary_style}.")
            
            if total_in_text > 0 and total_full == 0:
                recommendations.append("Incluir una bibliografía completa al final del documento.")
            
            if total_in_text == 0 and total_full > 0:
                recommendations.append("Incluir citas en el texto que correspondan a las referencias bibliográficas.")
            
            # Recomendaciones específicas por estilo
            if primary_style == "APA":
                if confidence > 0.7:  # Solo si estamos seguros del estilo
                    recommendations.append("Para múltiples autores en APA, use '&' en citas parentéticas y 'y' en citas narrativas.")
            
            elif primary_style == "MLA":
                if confidence > 0.7:
                    recommendations.append("En MLA, incluya el número de página sin 'p.' o 'pp.' en las citas parentéticas.")
            
            elif primary_style == "CHICAGO":
                if confidence > 0.7:
                    chicago_notes = style_counts['in_text'].get('CHICAGO_NOTES', 0)
                    chicago_author = style_counts['in_text'].get('CHICAGO_AUTHOR_DATE', 0)
                    
                    if chicago_notes > 0 and chicago_author > 0:
                        recommendations.append("Elija un solo sistema Chicago: notas al pie o autor-fecha, no mezcle ambos.")
            
            # Verificar consistencia entre citas y bibliografía
            if total_in_text > 0 and total_full > 0:
                in_text_citations = self._extract_citation_keys(text, primary_style)
                bibliography_entries = self._extract_bibliography_entries(text, primary_style)
                
                cited_not_referenced = self._find_citations_without_references(
                    in_text_citations, bibliography_entries, primary_style
                )
                
                if cited_not_referenced:
                    recommendations.append(
                        f"Añadir entradas bibliográficas para las {len(cited_not_referenced)} citas que no tienen referencia."
                    )
        
        # Combinar con recomendaciones de la validación
        all_recommendations = recommendations + validation['recomendaciones']
        
        # Eliminar duplicados preservando el orden
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return {
            'estilo_predominante': primary_style,
            'nivel_confianza': confidence,
            'conteo_citas': {
                'en_texto': total_in_text,
                'bibliograficas': total_full,
                'desglose': style_counts
            },
            'problemas': {
                'inconsistencias_estilo': validation['inconsistencias_estilo'],
                'formato_incorrecto': validation['formato_incorrecto']
            },
            'recomendaciones': unique_recommendations
        }
    
    def analyze_citation_patterns(self, text: str) -> Dict:
        """
        Analiza patrones de citación avanzados como distribución y densidad.
        
        Args:
            text (str): El texto a analizar
            
        Returns:
            Dict: Información sobre patrones de citación
        """
        # Extraer todas las citas
        citations = self.extract_citations(text)
        
        # Contar párrafos y palabras
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        words = re.findall(r'\b\w+\b', text)
        total_paragraphs = len(paragraphs)
        total_words = len(words)
        
        # Calcular densidad de citas
        citation_count = len(citations['en_texto'])
        word_density = citation_count / total_words if total_words > 0 else 0
        paragraph_density = citation_count / total_paragraphs if total_paragraphs > 0 else 0
        
        # Análisis de distribución
        paragraphs_with_citations = 0
        citations_per_paragraph = []
        
        for paragraph in paragraphs:
            count = 0
            for citation in citations['en_texto']:
                if citation in paragraph:
                    count += 1
            
            citations_per_paragraph.append(count)
            if count > 0:
                paragraphs_with_citations += 1
        
        # Calcular estadísticas
        max_citations = max(citations_per_paragraph) if citations_per_paragraph else 0
        avg_citations = sum(citations_per_paragraph) / len(citations_per_paragraph) if citations_per_paragraph else 0
        median_citations = sorted(citations_per_paragraph)[len(citations_per_paragraph)//2] if citations_per_paragraph else 0
        
        # Calcular patrón de uso (principio, medio, final)
        if total_paragraphs >= 3:
            first_third = sum(citations_per_paragraph[:total_paragraphs//3])
            middle_third = sum(citations_per_paragraph[total_paragraphs//3:2*total_paragraphs//3])
            last_third = sum(citations_per_paragraph[2*total_paragraphs//3:])
            
            distribution = {
                'principio': first_third / citation_count if citation_count > 0 else 0,
                'medio': middle_third / citation_count if citation_count > 0 else 0,
                'final': last_third / citation_count if citation_count > 0 else 0
            }
        else:
            distribution = {'principio': 0, 'medio': 0, 'final': 0}
        
        return {
            'densidad': {
                'citas_por_palabra': word_density,
                'citas_por_parrafo': paragraph_density,
                'porcentaje_parrafos_con_citas': paragraphs_with_citations / total_paragraphs if total_paragraphs > 0 else 0
            },
            'distribucion': {
                'max_citas_en_parrafo': max_citations,
                'promedio_citas_por_parrafo': avg_citations,
                'mediana_citas_por_parrafo': median_citations,
                'distribucion_documento': distribution
            },
            'estadisticas': {
                'total_citas': citation_count,
                'total_referencias': len(citations['bibliograficas']),
                'total_parrafos': total_paragraphs,
                'total_palabras': total_words
            }
        }
    
    def generate_fixed_citations(self, text: str, target_style: str) -> Dict[str, Dict[str, str]]:
        """
        Genera versiones corregidas de las citas según un estilo objetivo.
        
        Args:
            text (str): El texto con citas
            target_style (str): El estilo objetivo para las correcciones
            
        Returns:
            Dict[str, Dict[str, str]]: Diccionario con citas originales y corregidas
        """
        # Extraer citas existentes
        citations = self.extract_citations(text)
        
        # Diccionario para almacenar correcciones
        corrections = {
            'en_texto': {},
            'bibliograficas': {}
        }
        
        # Obtener estilo actual
        current_style, confidence = self.identify_primary_style(text)
        
        if current_style == target_style:
            # Si ya está en el estilo objetivo, solo corregir errores de formato
            for citation in citations['en_texto']:
                fixed = self._fix_citation_format(citation, target_style)
                if fixed != citation:
                    corrections['en_texto'][citation] = fixed
            
            for citation in citations['bibliograficas']:
                fixed = self._fix_citation_format(citation, target_style)
                if fixed != citation:
                    corrections['bibliograficas'][citation] = fixed
                    
        else:
            # Convertir al estilo objetivo
            for citation in citations['en_texto']:
                converted = self._convert_citation_style(citation, current_style, target_style, 'in_text')
                corrections['en_texto'][citation] = converted
            
            for citation in citations['bibliograficas']:
                converted = self._convert_citation_style(citation, current_style, target_style, 'bibliography')
                corrections['bibliograficas'][citation] = converted
        
        return corrections
    
    def _fix_citation_format(self, citation: str, style: str) -> str:
        """
        Corrige errores comunes de formato en una cita.
        
        Args:
            citation (str): La cita a corregir
            style (str): El estilo de citación
            
        Returns:
            str: Cita corregida
        """
        fixed = citation
        
        if style == "APA":
            # Corregir falta de coma entre autor y año
            fixed = re.sub(r'\(([A-Za-z\-]+(?:\s[A-Za-z\-]+)?) (\d{4})', r'(\1, \2', fixed)
            
            # Corregir indicador de página
            fixed = re.sub(r'(\d{4}), (\d+)', r'\1, p. \2', fixed)
            
            # Corregir 'and' por '&' en citas parentéticas
            if fixed.startswith('('):
                fixed = re.sub(r' and ', r' & ', fixed)
        
        elif style == "MLA":
            # Corregir coma entre autor y página
            fixed = re.sub(r'\(([A-Za-z\-]+(?:\s[A-Za-z\-]+)?), (\d+)', r'(\1 \2', fixed)
            
            # Corregir '&' por 'and'
            fixed = re.sub(r' & ', r' and ', fixed)
        
        elif style == "CHICAGO":
            # Corregir formato autor-fecha
            if "et al" in fixed:
                fixed = re.sub(r'et al ', r'et al., ', fixed)
        
        return fixed
    
    def _convert_citation_style(self, citation: str, from_style: str, to_style: str, citation_type: str) -> str:
        """
        Convierte una cita de un estilo a otro.
        
        Args:
            citation (str): La cita a convertir
            from_style (str): Estilo de origen
            to_style (str): Estilo de destino
            citation_type (str): Tipo de cita ('in_text' o 'bibliography')
            
        Returns:
            str: Cita convertida
        """
        # Nota: Esta es una implementación básica. Una solución completa
        # requeriría extraer metadatos de cada cita y reformatear.
        
        # Para citas en texto
        if citation_type == 'in_text':
            if from_style == "APA" and to_style == "MLA":
                # De (Autor, 2020, p. 25) a (Autor 25)
                match = re.search(r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?),\s\d{4}(?:,\sp\.\s(?P<page>\d+))?\)', citation)
                if match:
                    author = match.group('author')
                    page = match.group('page') or ""
                    if page:
                        return f"({author} {page})"
                    else:
                        return f"({author})"
            
            elif from_style == "MLA" and to_style == "APA":
                # De (Autor 25) a (Autor, 2020, p. 25)
                # Necesitaríamos el año que no está en la cita MLA
                match = re.search(r'\((?P<author>[A-Za-z\-]+(?:\s[A-Za-z\-]+)?)\s(?P<page>\d+)\)', citation)
                if match:
                    return f"({match.group('author')}, YYYY, p. {match.group('page')})"
            
            # Más conversiones...
        
        # Para bibliografía
        else:
            # La conversión de bibliografía es más compleja y requiere un análisis
            # más detallado para extraer y reformatear todos los componentes
            return f"[Conversión de bibliografía no implementada: {citation}]"
        
        # Si no hay regla específica, devolver la cita original
        return citation

# Ejemplo de uso
if __name__ == "__main__":
    # Crear una instancia del detector
    detector = CitationStyleDetector()
    
    # Texto de ejemplo
    sample_text = """
    Los estudios recientes han demostrado que existe una correlación significativa entre estos factores (Smith, 2020, p. 45). Según Johnson et al. (2019), los resultados son consistentes con investigaciones previas.

    En otro estudio, Williams (2021) encontró patrones similares en diferentes contextos culturales. Estos hallazgos contrastan con trabajos anteriores en el campo (Brown & Davis, 2018).

    Referencias:
    Smith, J. A. (2020). Patterns of correlation in environmental studies. Journal of Environmental Science, 45(2), 78-92.
    Johnson, R. B., Thompson, C., & Davis, K. (2019). Cultural contexts and research methodology. Academic Press.
    Williams, P. T. (2021). Cross-cultural patterns in social behavior. Social Psychology, 33(4), 156-170.
    Brown, M., & Davis, L. (2018). Contrasting methodologies in social research. Research Methods, 12(3), 45-67.
    """
    
    # Realizar análisis
    results = detector.analyze_text(sample_text)
    
    # Imprimir resultados
    print(f"Estilo predominante: {results['estilo_predominante']}")
    print(f"Nivel de confianza: {results['nivel_confianza']:.2f}")
    print(f"Total de citas en texto: {results['conteo_citas']['en_texto']}")
    print(f"Total de citas bibliográficas: {results['conteo_citas']['bibliograficas']}")
    
    print("\nProblemas detectados:")
    for categoria, problemas in results['problemas'].items():
        if problemas:
            print(f"\n{categoria.upper()}:")
            for problema in problemas:
                print(f"- {problema}")
    
    print("\nRecomendaciones:")
    for recomendacion in results['recomendaciones']:
        print(f"- {recomendacion}")