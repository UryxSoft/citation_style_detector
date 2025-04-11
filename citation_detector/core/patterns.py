# Patrones de expresiones regulares
# Extracción de citas
# patterns.py
# Patrones de expresiones regulares para la detección de estilos de citación

import re
from typing import Dict, List, Pattern, Union


class CitationPatterns:
    """
    Clase que contiene patrones de expresiones regulares para detectar diferentes
    estilos de citación en textos académicos.
    
    Incluye patrones para:
    - Citas en texto (in-text)
    - Referencias bibliográficas completas
    - Encabezados de secciones de bibliografía
    - Patrones especiales para casos particulares
    """
    
    def __init__(self):
        """
        Inicializa todos los patrones de detección de citas por estilo.
        """
        # Inicializar diccionarios de patrones
        self.in_text_patterns = {}
        self.bibliography_patterns = {}
        self.bibliography_headers = {}
        self.special_patterns = {}
        
        # Cargar todos los patrones
        self._load_apa_patterns()
        self._load_mla_patterns()
        self._load_chicago_patterns()
        self._load_harvard_patterns()
        self._load_ieee_patterns()
        self._load_vancouver_patterns()
        self._load_cse_patterns()
        self._load_bibliography_headers()
        self._load_special_patterns()
        
        # Compilar patrones para mejorar rendimiento
        self._compile_patterns()
    
    def _load_apa_patterns(self):
        """
        Carga patrones para el estilo APA (6ª y 7ª edición).
        """
        # Patrones para citas en texto APA
        self.in_text_patterns['APA'] = [
            # Cita parentética básica (Autor, Año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s(?P<year>\d{4})\)',
            
            # Cita parentética con página (Autor, Año, p. XX)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s(?P<year>\d{4}),\s(?P<page>p\.?\s\d+(?:-\d+)?)\)',
            
            # Cita narrativa: Autor (Año)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<year>\d{4})\)',
            
            # Cita narrativa con página: Autor (Año, p. XX)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?)\s\((?P<year>\d{4}),\s(?P<page>p\.?\s\d+(?:-\d+)?)\)',
            
            # Dos autores con & (Autor & Autor, Año)
            r'\((?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s&\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?),\s(?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)',
            
            # Dos autores con & narrativo: Autor y Autor (Año)
            r'(?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sy\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\((?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)',
            
            # Tres o más autores: (Autor et al., Año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.,\s(?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)',
            
            # Tres o más autores narrativo: Autor et al. (Año)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.\s\((?P<year>\d{4})(?:,\s(?P<page>p\.?\s\d+(?:-\d+)?))?\)',
            
            # Múltiples citas: (Autor, Año; Autor, Año)
            r'\((?:(?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?;\s?)+(?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?(?: et al\.)?),\s\d{4}(?:,\sp\.?\s\d+(?:-\d+)?)?\)'
        ]
        
        # Patrones para referencias bibliográficas APA
        self.bibliography_patterns['APA'] = [
            # Libro básico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:,?\s&\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor con & (opcional)
            r'\s\((?P<year>\d{4})\)\.\s'  # Año
            r'(?P<title>[^\.]+)\.'  # Título
            r'(?:\s\([^)]+\)\.)?'  # Información adicional en paréntesis (opcional) 
            r'(?:\s(?P<edition>\d+[a-zª]+\sed\.))?'  # Edición (opcional)
            r'(?:\s(?P<volume>Vol\.\s\d+))?'  # Volumen (opcional)
            r'\s(?P<publisher>[^\.]+)\.',  # Editorial
            
            # Artículo de revista
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:,?\s&\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor con & (opcional)
            r'\s\((?P<year>\d{4})\)\.\s'  # Año
            r'(?P<title>[^\.]+)\.\s'  # Título del artículo
            r'(?P<journal>[^,]+),\s'  # Nombre de la revista
            r'(?P<volume>\d+)'  # Volumen
            r'(?:\((?P<issue>\d+)\))?'  # Número (opcional)
            r',\s(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Capítulo de libro
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor del capítulo
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:,?\s&\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor con & (opcional)
            r'\s\((?P<year>\d{4})\)\.\s'  # Año
            r'(?P<chapter_title>[^\.]+)\.\s'  # Título del capítulo
            r'En\s(?:(?P<editor>[A-Za-zÀ-ÿ\-]+)(?:\s[A-Z]\.(?:\s[A-Z]\.)?)?)+'  # Editor(es)
            r'(?:(?:,\s|\s&\s)(?:[A-Za-zÀ-ÿ\-]+)(?:\s[A-Z]\.(?:\s[A-Z]\.)?)?)*'  # Editores adicionales
            r'(?:\s\(Ed[s]?\.\)|\s\(Eds\.\))?,\s'  # Indicador de editor(es)
            r'(?P<book_title>[^(]+)'  # Título del libro
            r'(?:\s\((?:pp\.|p\.)\s(?P<pages>\d+(?:-\d+)?)\))\.\s'  # Páginas
            r'(?P<publisher>[^\.]+)\.',  # Editorial
            
            # Recurso electrónico (APA 7)
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:,?\s&\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor con & (opcional)
            r'\s\((?P<year>\d{4})(?:,\s[A-Za-zÀ-ÿ]+\s\d+)?\)\.\s'  # Año y fecha específica (opcional)
            r'(?P<title>[^\.]+)\.\s'  # Título
            r'(?P<site>[^\.]+)\.'  # Nombre del sitio
            r'(?:\s(?P<url>https?://[^\s]+))?'  # URL (opcional)
        ]
    
    def _load_mla_patterns(self):
        """
        Carga patrones para el estilo MLA (8ª y 9ª edición).
        """
        # Patrones para citas en texto MLA
        self.in_text_patterns['MLA'] = [
            # Cita parentética básica (Apellido página)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<page>\d+(?:-\d+)?)\)',
            
            # Cita narrativa con página: Apellido (página)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\((?P<page>\d+(?:-\d+)?)\)',
            
            # Dos autores: (Apellido and Apellido página)
            r'\((?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sand\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<page>\d+(?:-\d+)?)\)',
            
            # Dos autores narrativo: Apellido and Apellido (página)
            r'(?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sand\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\((?P<page>\d+(?:-\d+)?)\)',
            
            # Tres o más autores: (Apellido et al. página)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.\s(?P<page>\d+(?:-\d+)?)\)',
            
            # Tres o más autores narrativo: Apellido et al. (página)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.\s\((?P<page>\d+(?:-\d+)?)\)',
            
            # Cita con título abreviado para múltiples obras del mismo autor: (Apellido, "Título abreviado" página)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?),\s[""](?P<title>[^""]+)[""]\s(?P<page>\d+(?:-\d+)?)\)',
            
            # Sin página, solo autor: (Apellido)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\)'
        ]
        
        # Patrones para referencias bibliográficas MLA
        self.bibliography_patterns['MLA'] = [
            # Libro básico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)(?:\.|,)'  # Autor principal 
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Co-autor (opcional)
            r'\s(?P<title>[^\.]+)(?:\.|,)'  # Título (en cursiva, pero no detectable en plaintext)
            r'(?:\stranslated\sby\s[A-Za-zÀ-ÿ\-\s]+,)?'  # Traductor (opcional)
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.)?,)?'  # Edición (opcional)
            r'(?:\s(?P<volume>vol\.\s\d+)?,)?'  # Volumen (opcional)
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4})\.',  # Año
            
            # Artículo de revista
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)(?:\.|,)'  # Autor principal
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Co-autor (opcional)
            r'\s[""](?P<title>[^""]+)[""]\.'  # Título del artículo (entre comillas)
            r'\s(?P<journal>[^,]+),'  # Nombre de la revista (en cursiva, no detectable)
            r'\svol\.\s(?P<volume>\d+),'  # Volumen
            r'(?:\sno\.\s(?P<issue>\d+),)?'  # Número (opcional)
            r'\s(?P<year>\d{4}),'  # Año
            r'\spp\.\s(?P<pages>\d+(?:-\d+)?).',  # Páginas
            
            # Capítulo de libro o ensayo en una colección
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)(?:\.|,)'  # Autor del capítulo
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Co-autor (opcional)
            r'\s[""](?P<chapter_title>[^""]+)[""]\.'  # Título del capítulo
            r'\s(?P<book_title>[^,]+),'  # Título del libro (en cursiva, no detectable)
            r'(?:\sedited\sby\s[A-Za-zÀ-ÿ\-\s]+,)?'  # Editor (opcional)
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4}),'  # Año
            r'\spp\.\s(?P<pages>\d+(?:-\d+)?).',  # Páginas
            
            # Recurso electrónico / Página web
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)?'  # Autor (opcional)
            r'(?:(?:\.|,)\s)?'  # Puntuación después del autor
            r'(?:[""])?(?P<title>[^""]+)(?:[""])?\.'  # Título (puede estar entre comillas o en cursiva)
            r'\s(?P<site>[^,]+),'  # Nombre del sitio web (en cursiva, no detectable)
            r'(?:\s(?P<publisher>[^,]+),)?'  # Editor/Publicador (opcional)
            r'(?:\s(?P<date>\d+\s[A-Za-zÀ-ÿ]+\s\d{4}|\d{1,2}\s[A-Za-zÀ-ÿ]+\.?\s\d{4}),)?'  # Fecha completa (opcional)
            r'(?:\s(?P<url>(?:www|http|https)[^,\s]+))?'  # URL (opcional)
            r'(?:,\sAccessed\s(?P<access_date>\d+\s[A-Za-zÀ-ÿ]+\s\d{4}|(?:[A-Za-zÀ-ÿ]+\.|[A-Za-zÀ-ÿ]+)\s\d{1,2},\s\d{4}))?'  # Fecha de acceso (opcional)
        ]
    
    def _load_chicago_patterns(self):
        """
        Carga patrones para el estilo Chicago (autor-fecha y notas-bibliografía).
        """
        # Patrones para citas en texto Chicago (autor-fecha)
        self.in_text_patterns['CHICAGO_AUTHOR_DATE'] = [
            # Cita parentética básica (Apellido año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<year>\d{4})(?:,\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Cita narrativa: Apellido (año)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\((?P<year>\d{4})(?:,\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Dos autores: (Apellido and Apellido año)
            r'\((?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sand\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<year>\d{4})(?:,\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Múltiples citas: (Apellido año; Apellido año)
            r'\((?:(?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\d{4}(?:,\s\d+(?:-\d+)?)?;\s)+(?:[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\d{4}(?:,\s\d+(?:-\d+)?)?\)'
        ]
        
        # Patrones para citas Chicago (notas al pie)
        self.in_text_patterns['CHICAGO_NOTES'] = [
            # Número de nota al pie
            r'(?:^|\s)(?P<note_num>\d+)\.\s',
            
            # Términos especiales de continuación
            r'(?:^|\s)(?P<term>Ibid\.|Op\.\scit\.|Loc\.\scit\.)(?:,\s(?P<page>\d+(?:-\d+)?))?\.',
            
            # Superíndice (más difícil de detectar en plaintext)
            r'(?P<superscript>[¹²³⁴⁵⁶⁷⁸⁹⁰]+)'
        ]
        
        # Patrones para referencias bibliográficas Chicago (bibliografía)
        self.bibliography_patterns['CHICAGO'] = [
            # Libro básico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-\s]+)*'  # Autores adicionales (opcional)
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Último autor (opcional)
            r'(?:\.|,)\s(?P<title>[^\.]+)\.'  # Título (en cursiva, no detectable)
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.))?'  # Edición (opcional)
            r'(?:\s(?P<volume>Vol\.\s\d+))?'  # Volumen (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4})\.',  # Año
            
            # Artículo de revista
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-\s]+)*'  # Autores adicionales (opcional)
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Último autor (opcional)
            r'(?:\.|,)\s[""](?P<title>[^""]+)[""]\.'  # Título del artículo
            r'\s(?P<journal>[^""\d]+)'  # Nombre de la revista
            r'\s(?P<volume>\d+)'  # Volumen
            r'(?:,\sno\.\s(?P<issue>\d+))?'  # Número (opcional)
            r'\s\((?P<year>\d{4})\):'  # Año
            r'\s(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Capítulo de libro
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)'  # Autor del capítulo
            r'(?:,\s[A-Za-zÀ-ÿ\-\s]+)*'  # Autores adicionales (opcional)
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Último autor (opcional)
            r'(?:\.|,)\s[""](?P<chapter_title>[^""]+)[""]\.'  # Título del capítulo
            r'\sIn\s(?P<book_title>[^,]+),'  # Título del libro
            r'(?:\sedited\sby\s[A-Za-zÀ-ÿ\-\s]+(?:,\s[A-Za-zÀ-ÿ\-\s]+)*(?:\sand\s[A-Za-zÀ-ÿ\-\s]+)?,)?'  # Editor(es) (opcional)
            r'\s(?P<pages>\d+(?:-\d+)?)\.'  # Páginas
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4})\.',  # Año
            
            # Recurso electrónico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Za-zÀ-ÿ\-\s]+)'  # Autor (opcional)
            r'(?:,\s[A-Za-zÀ-ÿ\-\s]+)*'  # Autores adicionales (opcional)
            r'(?:,\sand\s[A-Za-zÀ-ÿ\-\s]+)?'  # Último autor (opcional)
            r'(?:\.|,)\s[""](?P<title>[^""]+)[""]\.'  # Título
            r'\s(?P<site>[^\.]+)\.'  # Nombre del sitio web
            r'(?:\s(?P<date>[A-Za-zÀ-ÿ]+\s\d+,\s\d{4})\.)?'  # Fecha de publicación (opcional)
            r'(?:\s(?P<url>https?://[^\s]+)\.)?'  # URL (opcional)
            r'(?:\sAccessed\s(?P<access_date>[A-Za-zÀ-ÿ]+\s\d+,\s\d{4})\.)?'  # Fecha de acceso (opcional)
        ]
        
        # Patrones para notas al pie Chicago
        self.bibliography_patterns['CHICAGO_NOTES'] = [
            # Referencia de libro en nota
            r'^(?P<note_num>\d+\.\s)'  # Número de nota
            r'(?P<author>[A-Za-zÀ-ÿ\-\s]+),'  # Autor(es) (nombre completo, orden normal)
            r'\s(?P<title>[^(]+)'  # Título (en cursiva, no detectable)
            r'(?:\s\((?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4})\)),'  # Año
            r'\s(?P<page>\d+(?:-\d+)?).',  # Página(s)
            
            # Referencia de artículo en nota
            r'^(?P<note_num>\d+\.\s)'  # Número de nota
            r'(?P<author>[A-Za-zÀ-ÿ\-\s]+),'  # Autor(es) (nombre completo, orden normal)
            r'\s[""](?P<title>[^""]+)[""]\,'  # Título del artículo
            r'\s(?P<journal>[^""\d]+)'  # Nombre de la revista
            r'\s(?P<volume>\d+)'  # Volumen
            r'(?:,\sno\.\s(?P<issue>\d+))?'  # Número (opcional)
            r'\s\((?P<year>\d{4})\):'  # Año
            r'\s(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Ibid con página
            r'^(?P<note_num>\d+\.\s)'  # Número de nota
            r'(?P<term>Ibid\.),\s(?P<page>\d+(?:-\d+)?).',  # Ibid. con página
            
            # Ibid simple
            r'^(?P<note_num>\d+\.\s)'  # Número de nota
            r'(?P<term>Ibid\.)\.',  # Ibid. solo
        ]
    
    def _load_harvard_patterns(self):
        """
        Carga patrones para el estilo Harvard.
        """
        # Patrones para citas en texto Harvard
        self.in_text_patterns['HARVARD'] = [
            # Cita parentética básica (Apellido, año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?),\s(?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Cita narrativa: Apellido (año)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s\((?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Dos autores: (Apellido and Apellido, año)
            r'\((?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sand\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?),\s(?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Tres o más autores: (Apellido et al., año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\set\sal\.,\s(?P<year>\d{4})(?::\s(?P<page>\d+(?:-\d+)?))?\)',
            
            # Múltiples obras del mismo autor: (Apellido, año; año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?),\s(?:\d{4}(?::\s\d+(?:-\d+)?)?;\s)+\d{4}(?::\s\d+(?:-\d+)?)?\)'
        ]
        
        # Patrones para referencias bibliográficas Harvard
        self.bibliography_patterns['HARVARD'] = [
            # Libro básico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:\sand\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor (opcional)
            r'\s\((?P<year>\d{4})\)'  # Año
            r'\s(?P<title>[^\.]+)\.'  # Título (en cursiva, no detectable)
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.))?'  # Edición (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^\.]+)\.',  # Editorial
            
            # Artículo de revista
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:\sand\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor (opcional)
            r'\s\((?P<year>\d{4})\)'  # Año
            r'\s\'(?P<title>[^\']+)\','  # Título del artículo
            r'\s(?P<journal>[^,]+),'  # Nombre de la revista
            r'\s(?P<volume>\d+)'  # Volumen
            r'(?:\((?P<issue>\d+)\))?,'  # Número (opcional)
            r'\spp\.\s(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Recurso electrónico
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'  # Autor principal
            r'(?:,\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)*'  # Autores adicionales (opcional)
            r'(?:\sand\s[A-Za-zÀ-ÿ\-]+,\s[A-Z]\.(?:\s[A-Z]\.)?)?'  # Último autor (opcional)
            r'\s\((?P<year>\d{4})\)'  # Año
            r'\s(?P<title>[^\.]+)\s\[Online\]\.'  # Título y marcador [Online]
            r'(?:\s(?:Available|Disponible)\s(?:at|en):\s(?P<url>https?://[^\s]+))?'  # URL (opcional)
            r'(?:\s\[(?:Accessed|Accedido):\s(?P<access_date>\d+\s[A-Za-zÀ-ÿ]+\s\d{4})\])?'  # Fecha de acceso (opcional)
        ]
    
    def _load_ieee_patterns(self):
        """
        Carga patrones para el estilo IEEE.
        """
        # Patrones para citas en texto IEEE
        self.in_text_patterns['IEEE'] = [
            # Cita básica [n]
            r'\[(?P<ref_num>\d+)\]',
            
            # Múltiples citas [n, m, o]
            r'\[(?P<ref_nums>\d+(?:,\s*\d+)*)\]',
            
            # Cita con texto [n, texto]
            r'\[(?P<ref_num>\d+),\s(?P<text>[^\]]+)\]'
        ]
        
        # Patrones para referencias bibliográficas IEEE
        self.bibliography_patterns['IEEE'] = [
            # Libro básico
            r'^\[(?P<ref_num>\d+)\]\s'  # Número de referencia
            r'(?P<author>[A-Za-zÀ-ÿ\-\.\s]+),'  # Autor(es) (iniciales + apellido)
            r'\s(?P<title>[^,]+),'  # Título (en cursiva, no detectable)
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.)?,)?'  # Edición (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^,]+),'  # Editorial
            r'\s(?P<year>\d{4})(?:,\spp\.\s(?P<pages>\d+(?:-\d+)?))?\.',  # Año y páginas (opcional)
            
            # Artículo de revista
            r'^\[(?P<ref_num>\d+)\]\s'  # Número de referencia
            r'(?P<author>[A-Za-zÀ-ÿ\-\.\s]+),'  # Autor(es) (iniciales + apellido)
            r'\s[""](?P<title>[^""]+)[""]\,'  # Título del artículo
            r'\s(?P<journal>[^,]+),'  # Nombre de la revista
            r'\svol\.\s(?P<volume>\d+),'  # Volumen
            r'(?:\sno\.\s(?P<issue>\d+),)?'  # Número (opcional)
            r'\spp\.\s(?P<pages>\d+(?:-\d+)?),'  # Páginas
            r'\s(?P<date>[A-Za-zÀ-ÿ]+\.\s\d{4})\.',  # Fecha (mes+año)
            
            # Recurso electrónico
            r'^\[(?P<ref_num>\d+)\]\s'  # Número de referencia
            r'(?P<author>[A-Za-zÀ-ÿ\-\.\s]+)?'  # Autor(es) (opcional)
            r'(?:,\s)?[""](?P<title>[^""]+)[""]\,'  # Título
            r'(?:\s(?P<site>[^,]+),)?'  # Nombre del sitio (opcional)
            r'(?:\s(?P<date>[A-Za-zÀ-ÿ]+\.\s\d{1,2},\s\d{4}),)?'  # Fecha (opcional)
            r'(?:\s(?:Available|Disponible):\s(?P<url>https?://[^\s]+))?'  # URL (opcional)
            r'(?:\s\[(?:Accessed|Accedido):\s(?P<access_date>[A-Za-zÀ-ÿ]+\.\s\d{1,2},\s\d{4})\])?'  # Fecha de acceso (opcional)
        ]
    
    def _load_vancouver_patterns(self):
        """
        Carga patrones para el estilo Vancouver.
        """
        # Patrones para citas en texto Vancouver
        self.in_text_patterns['VANCOUVER'] = [
            # Cita básica (n)
            r'\((?P<ref_num>\d+)\)',
            
            # Cita básica [n]
            r'\[(?P<ref_num>\d+)\]',
            
            # Múltiples citas [n-m] o [n,m]
            r'\[(?P<ref_nums>\d+(?:-\d+|\s*,\s*\d+)*)\]',
            
            # Superíndice (más difícil de detectar en plaintext)
            r'(?P<superscript>[¹²³⁴⁵⁶⁷⁸⁹⁰]+)'
        ]
        
        # Patrones para referencias bibliográficas Vancouver
        self.bibliography_patterns['VANCOUVER'] = [
            # Artículo de revista
            r'^(?P<ref_num>\d+\.\s)?'  # Número de referencia (opcional)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Primer autor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<title>[^\.]+)\.'  # Título
            r'\s(?P<journal>[^\.]+)\.'  # Nombre de la revista (abreviado)
            r'\s(?P<year>\d{4})'  # Año
            r'(?:;(?P<volume>\d+)(?:\((?P<issue>\d+)\))?:(?P<pages>\d+(?:-\d+)?))?\.',  # Volumen(número):páginas
            
            # Libro
            r'^(?P<ref_num>\d+\.\s)?'  # Número de referencia (opcional)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Primer autor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<title>[^\.]+)\.'  # Título
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.))?'  # Edición (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^;]+);'  # Editorial
            r'\s(?P<year>\d{4})(?:\.\s(?P<pages>\d+)\sp)?',  # Año y páginas (opcional)
            
            # Capítulo de libro
            r'^(?P<ref_num>\d+\.\s)?'  # Número de referencia (opcional)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Autor del capítulo
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<chapter_title>[^\.]+)\.'  # Título del capítulo
            r'\sIn:\s(?P<editor>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Editor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Editores adicionales
            r'(?:,\seditors)?'  # Marcador de editores
            r'\.\s(?P<book_title>[^\.]+)\.'  # Título del libro
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.))?'  # Edición (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad
            r'\s(?P<publisher>[^;]+);'  # Editorial
            r'\s(?P<year>\d{4})(?:\.\sp\.\s(?P<pages>\d+(?:-\d+)?))?\.',  # Año y páginas
            
            # Recurso electrónico
            r'^(?P<ref_num>\d+\.\s)?'  # Número de referencia (opcional)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})?'  # Autor (opcional)
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'(?:\.)?\s(?P<title>[^\.]+)\s\[Internet\]\.'  # Título y marcador [Internet]
            r'(?:\s(?P<city>[A-Za-zÀ-ÿ\-\s]+):'  # Ciudad (opcional)
            r'\s(?P<publisher>[^;]+);)?'  # Editorial (opcional)
            r'(?:\s(?P<year>\d{4}))?'  # Año (opcional)
            r'(?:\s\[(?:cited|consultado)\s(?P<access_date>\d{4}\s[A-Za-zÀ-ÿ]+\s\d{1,2})\])?'  # Fecha de acceso (opcional)
            r'(?:\.\sAvailable\sfrom:\s(?P<url>https?://[^\s]+))?'  # URL (opcional)
        ]
    
    def _load_cse_patterns(self):
        """
        Carga patrones para el estilo CSE (Council of Science Editors).
        """
        # Patrones para citas en texto CSE (Sistema nombre-año)
        self.in_text_patterns['CSE'] = [
            # Cita básica (Apellido año)
            r'\((?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<year>\d{4})\)',
            
            # Cita narrativa: Apellido año
            r'(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<year>\d{4})',
            
            # Cita de dos autores (Apellido and Apellido año)
            r'\((?P<author1>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\sand\s(?P<author2>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\s(?P<year>\d{4})\)',
            
            # Sistema de cita-secuencia: [n]
            r'\[(?P<ref_num>\d+)\]',
            
            # Sistema de cita-nombre: [Apellido]
            r'\[(?P<author>[A-Za-zÀ-ÿ\-]+(?:\s[A-Za-zÀ-ÿ\-]+)?)\]'
        ]
        
        # Patrones para referencias bibliográficas CSE
        self.bibliography_patterns['CSE'] = [
            # Artículo de revista (sistema nombre-año)
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Primer autor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<year>\d{4})\.'  # Año
            r'\s(?P<title>[^\.]+)\.'  # Título
            r'\s(?P<journal>[^\.]+)\.'  # Nombre de la revista
            r'\s(?P<volume>\d+)'  # Volumen
            r'(?:\((?P<issue>\d+)\))?'  # Número (opcional)
            r':(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Libro (sistema nombre-año)
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Primer autor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<year>\d{4})\.'  # Año
            r'\s(?P<title>[^\.]+)\.'  # Título
            r'(?:\s(?P<edition>\d+[a-z]{2}\sed\.))?'  # Edición (opcional)
            r'\s(?P<city>[A-Za-zÀ-ÿ\-\s]+)(?:\s\([A-Z]{2}\))?:'  # Ciudad y estado (opcional)
            r'\s(?P<publisher>[^\.]+)(?:\.\s(?P<pages>\d+)\sp)?',  # Editorial y páginas (opcional)
            
            # Artículo de revista (sistema numérico)
            r'^(?P<ref_num>\d+\.\s)?'  # Número de referencia (sistema numérico)
            r'(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})'  # Primer autor
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'\.\s(?P<title>[^\.]+)\.'  # Título
            r'\s(?P<journal>[^\.]+)\.'  # Nombre de la revista
            r'\s(?P<year>\d{4})'  # Año
            r';(?P<volume>\d+)'  # Volumen
            r'(?:\((?P<issue>\d+)\))?'  # Número (opcional)
            r':(?P<pages>\d+(?:-\d+)?)\.',  # Páginas
            
            # Recurso electrónico (sistema nombre-año)
            r'^(?P<author>[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})?'  # Autor (opcional)
            r'(?:,\s[A-Za-zÀ-ÿ\-]+\s[A-Z]{1,2})*'  # Autores adicionales
            r'(?:,\set\sal)?'  # "et al" para muchos autores
            r'(?:\.)?\s(?P<year>\d{4})\.'  # Año
            r'\s(?P<title>[^\.]+)\s\[Internet\]\.'  # Título y marcador [Internet]
            r'(?:\s(?P<city>[A-Za-zÀ-ÿ\-\s]+)(?:\s\([A-Z]{2}\))?:'  # Ciudad y estado (opcional)
            r'\s(?P<publisher>[^;]+);)?'  # Editorial (opcional)
            r'(?:\s\[(?:cited|accessed)\s(?P<access_date>\d{4}\s[A-Za-zÀ-ÿ]+\s\d{1,2})\])?'  # Fecha de acceso (opcional)
            r'(?:\.\sAvailable\sfrom:\s(?P<url>https?://[^\s]+))?'  # URL (opcional)
        ]
    
    def _load_bibliography_headers(self):
        """
        Carga patrones para detectar encabezados de secciones de bibliografía.
        """
        # Encabezados comunes por estilo
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
    
    def _load_special_patterns(self):
        """
        Carga patrones especiales para casos específicos como términos en latín.
        """
        self.special_patterns = {
            # Términos latinos comunes en citas
            'latin_terms': {
                'ibid': r'(?i)Ibid\.(?:,\s(?:p\.|pp\.)?\s?\d+(?:-\d+)?)?',
                'op_cit': r'(?i)Op\.\s?cit\.(?:,\s(?:p\.|pp\.)?\s?\d+(?:-\d+)?)?',
                'loc_cit': r'(?i)Loc\.\s?cit\.',
                'et_al': r'(?i)et\s+al\.',
                'cf': r'(?i)cf\.',
                'sic': r'\[sic\]'
            },
            
            # Abreviaturas comunes
            'abbreviations': {
                'page': r'(?i)p\.\s\d+',
                'pages': r'(?i)pp\.\s\d+(?:-\d+)?',
                'volume': r'(?i)vol\.\s\d+',
                'chapter': r'(?i)cap\.\s\d+|ch\.\s\d+',
                'edition': r'(?i)\d+(?:st|nd|rd|th)\sed\.'
            },
            
            # Patrones para URL y DOI
            'digital_identifiers': {
                'url': r'https?://[^\s]+',
                'doi': r'(?i)(?:doi:|https?://doi\.org/)\d+\.\d+/.+',
                'accessed': r'(?i)(?:accessed|accedido)(?:\son|\sel)?\s\d{1,2}\s[A-Za-zÀ-ÿ]+\s\d{4}'
            }
        }
    
    def _compile_patterns(self):
        """
        Compila los patrones para mejorar el rendimiento.
        """
        # Compilar patrones in-text
        self.compiled_in_text = {}
        for style, patterns in self.in_text_patterns.items():
            self.compiled_in_text[style] = [re.compile(p, re.MULTILINE) for p in patterns]
        
        # Compilar patrones de bibliografía
        self.compiled_bibliography = {}
        for style, patterns in self.bibliography_patterns.items():
            self.compiled_bibliography[style] = [re.compile(p, re.MULTILINE) for p in patterns]
        
        # Compilar encabezados
        self.compiled_headers = {}
        for style, patterns in self.bibliography_headers.items():
            self.compiled_headers[style] = [re.compile(p, re.MULTILINE) for p in patterns]
        
        # Compilar patrones especiales
        self.compiled_special = {}
        for category, patterns in self.special_patterns.items():
            self.compiled_special[category] = {}
            for term, pattern in patterns.items():
                self.compiled_special[category][term] = re.compile(pattern, re.MULTILINE)
    
    def get_pattern(self, style: str, pattern_type: str, index: int = None) -> Union[Pattern, List[Pattern]]:
        """
        Obtiene un patrón compilado o lista de patrones por estilo y tipo.
        
        Args:
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            pattern_type (str): Tipo de patrón ('in_text', 'bibliography', 'headers')
            index (int, optional): Índice específico del patrón si se quiere uno solo
            
        Returns:
            Union[Pattern, List[Pattern]]: Patrón(es) compilado(s)
        """
        if pattern_type == 'in_text':
            patterns = self.compiled_in_text.get(style, [])
        elif pattern_type == 'bibliography':
            patterns = self.compiled_bibliography.get(style, [])
        elif pattern_type == 'headers':
            patterns = self.compiled_headers.get(style, [])
        else:
            return []
        
        if index is not None and 0 <= index < len(patterns):
            return patterns[index]
            
        return patterns
    
    def get_special_pattern(self, category: str, term: str) -> Pattern:
        """
        Obtiene un patrón especial compilado.
        
        Args:
            category (str): Categoría del patrón ('latin_terms', 'abbreviations', etc.)
            term (str): Término específico ('ibid', 'page', etc.)
            
        Returns:
            Pattern: Patrón compilado
        """
        return self.compiled_special.get(category, {}).get(term)
    
    def get_all_in_text_patterns(self) -> Dict[str, List[Pattern]]:
        """
        Obtiene todos los patrones compilados para citas en texto.
        
        Returns:
            Dict[str, List[Pattern]]: Diccionario con patrones por estilo
        """
        return self.compiled_in_text
    
    def get_all_bibliography_patterns(self) -> Dict[str, List[Pattern]]:
        """
        Obtiene todos los patrones compilados para referencias bibliográficas.
        
        Returns:
            Dict[str, List[Pattern]]: Diccionario con patrones por estilo
        """
        return self.compiled_bibliography
    
    def get_all_header_patterns(self) -> Dict[str, List[Pattern]]:
        """
        Obtiene todos los patrones compilados para encabezados de bibliografía.
        
        Returns:
            Dict[str, List[Pattern]]: Diccionario con patrones por estilo
        """
        return self.compiled_headers
    
    def add_custom_pattern(self, style: str, pattern_type: str, pattern: str) -> bool:
        """
        Añade un patrón personalizado y lo compila.
        
        Args:
            style (str): Estilo de citación ('APA', 'MLA', etc.)
            pattern_type (str): Tipo de patrón ('in_text', 'bibliography', 'headers')
            pattern (str): Patrón regex a añadir
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        try:
            compiled_pattern = re.compile(pattern, re.MULTILINE)
            
            if pattern_type == 'in_text':
                if style not in self.in_text_patterns:
                    self.in_text_patterns[style] = []
                    self.compiled_in_text[style] = []
                
                self.in_text_patterns[style].append(pattern)
                self.compiled_in_text[style].append(compiled_pattern)
                
            elif pattern_type == 'bibliography':
                if style not in self.bibliography_patterns:
                    self.bibliography_patterns[style] = []
                    self.compiled_bibliography[style] = []
                
                self.bibliography_patterns[style].append(pattern)
                self.compiled_bibliography[style].append(compiled_pattern)
                
            elif pattern_type == 'headers':
                if style not in self.bibliography_headers:
                    self.bibliography_headers[style] = []
                    self.compiled_headers[style] = []
                
                self.bibliography_headers[style].append(pattern)
                self.compiled_headers[style].append(compiled_pattern)
                
            else:
                return False
                
            return True
            
        except re.error:
            return False


# Ejemplo de uso
if __name__ == "__main__":
    # Crear una instancia de patrones
    patterns = CitationPatterns()
    
    # Obtener todos los patrones de citas en texto para APA
    apa_patterns = patterns.get_all_in_text_patterns().get('APA', [])
    
    # Ejemplo de texto con citas APA
    text = """
    Los estudios recientes han demostrado que existe una correlación significativa entre estos factores (Smith, 2020, p. 45). Según Johnson et al. (2019), los resultados son consistentes con investigaciones previas.
    """
    
    # Buscar coincidencias
    for i, pattern in enumerate(apa_patterns):
        matches = pattern.finditer(text)
        for match in matches:
            print(f"Patrón APA #{i+1} coincide: {match.group(0)}")
            if hasattr(match, 'groupdict'):
                print(f"  Grupos: {match.groupdict()}")