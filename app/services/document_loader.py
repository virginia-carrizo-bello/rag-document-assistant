from docx import Document

def load_docx_text(file_path: str) -> str:
    """
    Lee un archivo .docx y devuelve su texto completo.
    """
    document = Document(file_path)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def split_text_into_chunks(text: str) -> list[str]:
    """
    Divide el documento en fragmentos semánticos basados en las secciones del documento.
    Cada sección es corta y autocontenida, por lo que una sección se convierte en un fragmento.
    """
    section_titles = [
        "Ficción Espacial:",
        "Ficción Tecnológica:",
        "Naturaleza Deslumbrante:",
        "Cuento Corto:",
        "Características del Héroe Olvidado:",
    ]

    chunks = []

    for index, title in enumerate(section_titles):
        start = text.find(title)

        if start == -1:
            continue

        if index + 1 < len(section_titles):
            next_title = section_titles[index + 1]
            end = text.find(next_title)
            chunk = text[start:end].strip()
        else:
            chunk = text[start:].strip()

        chunks.append(chunk)

    return chunks


def load_document_chunks(file_path: str) -> list[str]:
    """
    Carga el documento y devuelve sus fragmentos.
    """
    text = load_docx_text(file_path)
    return split_text_into_chunks(text)