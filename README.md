# citation_style_detector
citation_style_detector
citation_style_detector/
│
├── README.md                    # Documentación principal y guía de inicio
├── setup.py                     # Configuración para instalación
├── requirements.txt             # Dependencias del proyecto
├── LICENSE                      # Licencia del software
│
├── citation_detector/           # Paquete principal
│   ├── __init__.py
│   ├── core/                    # Núcleo de funcionalidades
│   │   ├── __init__.py
│   │   ├── detector.py          # Clase principal CitationStyleDetector
│   │   ├── patterns.py          # Patrones de expresiones regulares
│   │   ├── validator.py         # Validación de citas
│   │   └── extractor.py         # Extracción de citas
│   │
│   ├── nlp/                     # Procesamiento de lenguaje natural
│   │   ├── __init__.py
│   │   ├── entity_extraction.py # Extracción de entidades nombradas
│   │   ├── language_detector.py # Detector de idiomas
│   │   └── text_processor.py    # Procesamiento de texto
│   │
│   ├── knowledge/               # Base de conocimiento
│   │   ├── __init__.py
│   │   ├── knowledge_base.py    # Clase principal para base de conocimiento
│   │   ├── data/                # Datos para la base de conocimiento
│   │   │   ├── journals.json    # Lista de revistas académicas
│   │   │   ├── publishers.json  # Lista de editoriales
│   │   │   └── style_guides.json # Guías de estilo
│   │   └── updater.py           # Actualizador de la base de conocimiento
│   │
│   ├── scoring/                 # Sistema de puntuación y confianza
│   │   ├── __init__.py
│   │   ├── confidence.py        # Cálculo de confianza
│   │   └── metrics.py           # Métricas de evaluación
│   │
│   ├── integration/             # Integración con herramientas académicas
│   │   ├── __init__.py
│   │   ├── exporters.py         # Exportación a formatos bibliográficos
│   │   ├── converters.py        # Conversión entre estilos
│   │   └── adapters/            # Adaptadores para sistemas específicos
│   │       ├── __init__.py
│   │       ├── zotero.py        # Integración con Zotero
│   │       ├── mendeley.py      # Integración con Mendeley
│   │       └── bibtex.py        # Gestión de BibTeX
│   │
│   ├── digital/                 # Manejo de recursos digitales
│   │   ├── __init__.py
│   │   ├── doi_validator.py     # Validación de DOIs
│   │   ├── url_processor.py     # Procesamiento de URLs
│   │   └── metadata_extractor.py # Extracción de metadatos web
│   │
│   ├── utils/                   # Utilidades generales
│   │   ├── __init__.py
│   │   ├── text_utils.py        # Utilidades de texto
│   │   ├── normalization.py     # Normalización de caracteres y texto
│   │   └── file_io.py           # Manejo de archivos
│   │
│   └── ui/                      # Interfaces de usuario
│       ├── __init__.py
│       ├── cli.py               # Interfaz de línea de comandos
│       ├── gui.py               # Interfaz gráfica (requiere tkinter)
│       ├── web_app.py           # Aplicación web (requiere Flask)
│       └── reports/             # Generación de informes
│           ├── __init__.py
│           ├── text_report.py   # Informes de texto
│           ├── visual_report.py # Informes visuales
│           └── templates/       # Plantillas para informes
│
├── tests/                       # Pruebas unitarias y de integración
│   ├── __init__.py
│   ├── test_detector.py         # Pruebas del detector principal
│   ├── test_patterns.py         # Pruebas de patrones
│   ├── test_validator.py        # Pruebas de validación
│   ├── test_nlp.py              # Pruebas de NLP
│   ├── test_knowledge_base.py   # Pruebas de la base de conocimiento
│   ├── test_integration.py      # Pruebas de integración
│   ├── test_scoring.py          # Pruebas del sistema de puntuación
│   ├── test_digital.py          # Pruebas de manejo de recursos digitales
│   └── test_data/               # Datos para pruebas
│       ├── apa_examples.txt
│       ├── mla_examples.txt
│       ├── chicago_examples.txt
│       ├── mixed_styles.txt
│       └── edge_cases.txt
│
├── examples/                    # Ejemplos de uso
│   ├── simple_analysis.py       # Ejemplo básico
│   ├── batch_processing.py      # Procesamiento por lotes
│   ├── custom_patterns.py       # Personalización de patrones
│   └── report_generation.py     # Generación de informes
│
├── docs/                        # Documentación
│   ├── index.md                 # Página principal
│   ├── installation.md          # Guía de instalación
│   ├── quickstart.md            # Inicio rápido
│   ├── api/                     # Documentación de API
│   │   ├── core.md
│   │   ├── nlp.md
│   │   ├── knowledge.md
│   │   └── integration.md
│   ├── guides/                  # Guías y tutoriales
│   │   ├── customization.md     # Personalización del detector
│   │   ├── style_conversion.md  # Conversión entre estilos
│   │   └── report_formats.md    # Formatos de informes
│   └── reference/               # Referencia técnica
│       ├── citation_styles.md   # Detalles de estilos de citación
│       ├── performance.md       # Métricas de rendimiento
│       └── regex_patterns.md    # Documentación de patrones regex
│
└── scripts/                     # Scripts auxiliares
    ├── update_knowledge_base.py # Actualizar base de conocimiento
    ├── generate_test_data.py    # Generar datos de prueba
    ├── benchmark.py             # Benchmarking de rendimiento
    └── validate_corpus.py       # Validar corpus de documentos