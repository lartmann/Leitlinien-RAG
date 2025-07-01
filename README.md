# Retrieval Augmented Generation für medizinische Leitlinien 

> Eine Demo des implementierten RAG-Systems ist auf meinem [Server](http://217.154.8.88:8501/) zu finden.

# Setup 

1. Erstelle eine `.env`-Datei und füge den Token für das LLM von Mistral unter `MISTRAL_API_KEY` hinzu.
2. Führe `python3 scraper.py` aus, um alle Leitlinien von der offiziellen Website herunterzuladen.
3. Führe `rag.ipynb` aus, um die Leitlinien in einer Vektor-Datenbank zu indexieren.
4. Starte die Demo mithilfe des Dockerfiles.

# Hintergrund
## Einleitung

Die medizinischen Fachgesellschaften erstellen für ihr jeweiliges Fachgebiet Leitlinien. Diese Leitlinien sind sehr wichtig, da Ärzte dort rechtlich haltbare Empfehlungen für die Behandlung ihrer Patienten finden. Auch Patienten können sich hier über die empfohlene Behandlung für ihre Krankheit informieren.
Alle aktuellen Leitlinien sind im Leitlinienregister der [Arbeitsgemeinschaft der Wissenschaftlichen Medizinischen Fachgesellschaften e.V. (AWMF)](https://register.awmf.org) frei verfügbar. Dort kann nach Fachgesellschaft sortiert und die entsprechende Leitlinie als PDF heruntergeladen werden.

Die Suche nach der richtigen Stelle kann allerdings sehr aufwendig sein. Aus über 800 Leitlinien muss erst einmal die passende ausgewählt werden. Wo findet man beispielsweise Informationen zur Anästhesiegabe für eine Zahnextraktion bei Menschen mit Nierentransplantation? In der Leitlinie [Immunsuppression nach pädiatrischer Nierentransplantation](https://register.awmf.org/de/leitlinien/detail/166-007), in der Leitlinie [Operative Entfernung von Weisheitszähnen](https://register.awmf.org/de/leitlinien/detail/007-003) oder in der Leitlinie [Zahnärztliche Behandlungsempfehlungen vor und nach einer Organtransplantation](https://register.awmf.org/de/leitlinien/detail/083-035)? Im schlimmsten Fall müsste man all diese Leitlinien überprüfen, um die richtige Empfehlung zu finden.
Doch damit nicht genug: Die Suche nach der richtigen Information endet nicht bei der richtigen Leitlinie. Oft haben die Leitlinien über 100 Seiten, auf denen im besten Fall irgendwo die gesuchte Information zu finden ist.
Insgesamt lässt sich sagen, dass die Suche in den Leitlinien aktuell sehr ineffizient ist.

## Ziel und Methodik
Das Ziel dieses Projekts ist es, diese Suche deutlich zu vereinfachen. Hierzu wird ein Retrieval-Augmented-Generation-System (RAG) erstellt, das alle Leitlinien indexiert und mithilfe einer Similarity Search die richtigen Informationen herausfiltert.
Für das RAG-System werden sowohl ein Embedding-Modell als auch ein Large Language Model für den Generierungsprozess benötigt.

## Scraping
Die Leitlinien wurden von der offiziellen Seite der [AWMF](https://register.awmf.org) gescrapt. Hierzu wurden zunächst alle Fachgesellschaften gespeichert, dann alle Links zu allen Leitlinien jeder einzelnen Fachgesellschaft. Mit diesen Links wurden die PDFs heruntergeladen und die Metadaten in einer JSON-Datei gespeichert. So sollte gewährleistet sein, dass alle Leitlinien erfasst wurden. 
Da das Leitlinienregister eine Website ist, die sich dynamisch mit JavaScript o. Ä. lädt, habe ich für das Scraping Selenium verwendet.

## Embedding
Das Embedding der Vektor-Datenbank wird mit einem Modell von HuggingFace[^1] erstellt. Ausschlaggebend für die Wahl dieses Embedding-Modells waren die gute Performance, insbesondere für die deutsche Sprache, und die relativ geringen Ansprüche an die Rechenleistung, die es ermöglichten, die Indexierung auf meinem Rechner auszuführen. Mithilfe des „RecursiveCharacterTextSplitter“ der LangChain-Bibliothek werden die Leitlinien in Abschnitte von ungefähr 1.000 Zeichen aufgeteilt, bevor sie in die Datenbank indexiert werden.
Die Indexierung aller Leitlinien in die Chroma-Vektordatenbank dauerte ca. 24 Stunden.

## Large Language Model
Für den Generationsprozess habe ich die API von Mistral ([Mistral Small 3.1](https://mistral.ai/news/mistral-small-3-1)) als Large Language Model verwendet.
Ausschlaggebend für die Wahl war hier die gute Performance für die deutsche Sprache und die Tatsache, dass die Nutzung der API mit diesem Modell kostenlos ist.
