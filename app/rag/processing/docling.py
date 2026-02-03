"""
Docling Document Processor
Extracts text from various document formats using Docling (CPU-only mode)
"""

from typing import Dict, Any
import pypdf
from docx import Document as DocxDocument
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Process documents and extract text"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file using PyPDF (fast and reliable)
        """
        try:
            logger.info("Extracting text from PDF: %s", file_path)

            text_content = []
            metadata = {"pages": 0, "page_texts": []}

            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)

                logger.info("PDF has %s pages", metadata["pages"])

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()

                        if page_text.strip():
                            text_content.append(page_text)
                            metadata["page_texts"].append(
                                {"page": page_num + 1, "text": page_text}
                            )
                            logger.debug(
                                "Extracted page %s: %s chars",
                                page_num + 1,
                                len(page_text),
                            )
                        else:
                            logger.warning("Page %s has no text", page_num + 1)

                    except Exception as page_error:
                        logger.error(
                            "Error extracting page %s: %s", page_num + 1, page_error
                        )
                        continue

            if not text_content:
                raise ValueError("No text could be extracted from PDF")

            full_text = "\n\n".join(text_content)
            logger.info(
                "Successfully extracted %s characters from %s pages",
                len(full_text),
                len(text_content),
            )

            return {"text": full_text, "metadata": metadata}

        except Exception as e:
            logger.error("Error extracting text from PDF %s: %s", file_path, e)
            raise

    @staticmethod
    def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
        """
        Extract text from DOCX file
        """
        try:
            doc = DocxDocument(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            full_text = "\n\n".join(paragraphs)

            metadata = {"paragraphs": len(paragraphs), "sections": len(doc.sections)}

            logger.info(
                "Extracted text from DOCX: %s (%s paragraphs)",
                file_path,
                len(paragraphs),
            )

            return {"text": full_text, "metadata": metadata}
        except Exception as e:
            logger.error("Error extracting text from DOCX %s: %s", file_path, e)
            raise

    @staticmethod
    def extract_text_from_txt(file_path: str) -> Dict[str, Any]:
        """
        Extract text from TXT file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()

            metadata = {"lines": len(text.splitlines()), "characters": len(text)}

            logger.info("Extracted text from TXT: %s", file_path)

            return {"text": text, "metadata": metadata}
        except Exception as e:
            logger.error("Error extracting text from TXT %s: %s", file_path, e)
            raise

    @staticmethod
    def process_document(file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Process document based on file type
        """
        logger.info("Processing document: %s (type: %s)", file_path, file_type)

        if file_type == "application/pdf" or file_path.endswith(".pdf"):
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif (
            file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or file_path.endswith(".docx")
        ):
            return DocumentProcessor.extract_text_from_docx(file_path)
        elif file_type == "text/plain" or file_path.endswith(".txt"):
            return DocumentProcessor.extract_text_from_txt(file_path)
        else:
            logger.warning("Unsupported file type: %s", file_type)
            raise ValueError(f"Unsupported file type: {file_type}")
