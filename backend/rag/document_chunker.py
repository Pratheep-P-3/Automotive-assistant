"""
Document-Aware Chunker for Automotive Knowledge Bases.

Preserves complete automotive knowledge units instead of character-based splitting:
- OBD entries (code + description + causes + steps)
- Maintenance procedures (one per procedure)
- Troubleshooting workflows (one per symptom)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentAwareChunker:
    """Intelligently chunks documents while preserving semantic units."""

    # Patterns for OBD codes - more robust to detect various formats
    # Supports: P0300, Code: P0300, OBD Code: P0300, P0300 - Random Misfire, DTC P0300, etc.
    OBD_PATTERN = re.compile(
        r"(?:^|^\s*|\b)(?:OBD\s+)?(?:Code|DTC)\s*[:\-]?\s*([PUCB]\d{4})(?:\s|$|\-)",
        re.MULTILINE | re.IGNORECASE,
    )
    
    # More robust maintenance header detection
    # Supports: 5000 km Service, 10000 km Service, ENGINE OIL CHANGE, Oil Change, Scheduled Maintenance, etc.
    MAINTENANCE_HEADER_PATTERN = re.compile(
        r"^\s*(?:"
        r"(?:\d+(?:[,.]\d+)?\s*(?:km|mile|KM|MILE))\s+(?:service|maintenance|Service|Maintenance)|"  # 5000 km Service
        r"(?:ENGINE\s+)?OIL\s+CHANGE|"  # ENGINE OIL CHANGE
        r"(?:Brake|Coolant|Air\s+Filter|Transmission|Battery|Spark\s+Plug|Tire)\s+(?:Inspection|Replacement|Change|Service|Maintenance)|"  # Specific services
        r"(?:Scheduled\s+)?(?:Maintenance|Service)(?:\s+Schedule)?|"  # Maintenance Schedule
        r"Regular\s+Service|"  # Regular Service
        r"(?:Wheel|Fluid|Belt|Hose)\s+(?:Inspection|Replacement|Check)"  # Additional services
        r")\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    
    # More robust troubleshooting/symptom detection
    # Supports: Engine Misfire, Vehicle Stalling, Poor Fuel Economy, Hard Starting, Transmission Slipping, etc.
    TROUBLESHOOTING_PATTERN = re.compile(
        r"^\s*(?:"
        r"(?:Engine|Vehicle|Transmission|Brake|Cooling|Electrical|Fuel|Battery|Charging|Steering|Suspension)\s+(?:Misfire|Stalling|Noise|Drain|Slipping|Overheat|Hard\s+Start|Rough\s+Idle|Poor\s+Economy|Light|Fault|Warning|Malfunction|Failure)|"  # Symptom patterns
        r"(?:Check\s+)?Engine\s+Light|"  # Check Engine Light
        r"(?:Hard|Difficult)\s+Starting|"  # Hard Starting
        r"(?:Rough|Idle)\s+(?:Idle|Operation)|"  # Rough Idle
        r"(?:Poor|Low)\s+Fuel\s+Economy|"  # Poor Fuel Economy
        r"(?:Transmission|Brake|Engine)\s+(?:Slipping|Grinding|Knocking)|"  # Slipping/Grinding
        r"Battery\s+(?:Drain|Discharge)|"  # Battery Drain
        r"(?:Engine|Coolant)\s+(?:Overheating|Overheat)|"  # Overheating
        r"\w+\s+(?:Symptom|Problem|Fault|Warning|Issue)"  # Generic symptom
        r")\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Size limits
    MAX_CHUNK_SIZE = 2000  # Split only if larger
    MIN_CHUNK_SIZE = 200

    def __init__(self) -> None:
        """Initialize DocumentAwareChunker."""
        logger.info("[DocumentAwareChunker] ✓ Initialized")

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        Intelligently chunk documents while preserving semantic units.

        Args:
            documents: List of LangChain Document objects

        Returns:
            List of semantically-aware chunks
        """
        chunked_docs = []

        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            category = doc.metadata.get("category", "unknown")

            logger.info(f"[DocumentAwareChunker] Processing: {source} (category: {category})")

            # Route to appropriate chunker based on category
            if category == "obd":
                chunks = self._chunk_obd_document(doc)
            elif category == "maintenance":
                chunks = self._chunk_maintenance_document(doc)
            elif category == "symptom" or category == "troubleshooting":
                chunks = self._chunk_troubleshooting_document(doc)
            else:
                # Fallback: use section-based chunking
                chunks = self._chunk_generic_document(doc)

            chunked_docs.extend(chunks)
            logger.info(f"[DocumentAwareChunker] Created {len(chunks)} chunks from {source}")

        logger.info(f"[DocumentAwareChunker] ✓ Total chunks created: {len(chunked_docs)}")
        return chunked_docs

    def _chunk_obd_document(self, doc: Document) -> list[Document]:
        """
        Chunk OBD document by code entries.

        Each OBD code with its full definition stays in one chunk.
        Supports multiple OBD format variations.

        Args:
            doc: Document to chunk

        Returns:
            List of OBD entry chunks
        """
        chunks = []
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")

        # Find all OBD code positions
        matches = list(self.OBD_PATTERN.finditer(text))

        if not matches:
            # No OBD codes found, log warning and fallback
            logger.warning(
                f"[DocumentAwareChunker] ✗ No OBD pattern matched in {source}. "
                f"Supported formats: P0300, Code: P0300, OBD Code: P0300, P0300 - Description"
            )
            logger.warning(f"[DocumentAwareChunker] Using fallback chunking for {source}")
            return [doc]

        logger.info(f"[DocumentAwareChunker] File={source} | Category=obd | OBD Entries Found={len(matches)} | Chunks Produced={len(matches)}")

        # Create chunks between OBD codes
        for i, match in enumerate(matches):
            start_pos = match.start()

            # End position is either next OBD code or end of document
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            chunk_text = text[start_pos:end_pos].strip()

            # Only create chunk if it has substantial content
            if len(chunk_text) > self.MIN_CHUNK_SIZE:
                # Extract code from match
                code = match.group(1)

                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        "chunk_type": "obd_entry",
                        "code": code,
                        "chunk_size": len(chunk_text),
                    },
                )
                chunks.append(chunk_doc)

        return chunks if chunks else [doc]

    def _chunk_maintenance_document(self, doc: Document) -> list[Document]:
        """
        Chunk maintenance document by procedures.

        Each maintenance procedure stays in one chunk.
        Supports multiple maintenance header formats.

        Args:
            doc: Document to chunk

        Returns:
            List of maintenance procedure chunks
        """
        chunks = []
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")

        # Find maintenance sections
        sections = self._split_by_headers(text, self.MAINTENANCE_HEADER_PATTERN)

        if not sections:
            logger.warning(
                f"[DocumentAwareChunker] ✗ No maintenance pattern matched in {source}. "
                f"Supported formats: 5000 km Service, Oil Change, Brake Inspection, Scheduled Maintenance"
            )
            logger.warning(f"[DocumentAwareChunker] Using fallback chunking for {source}")
            return [doc]

        logger.info(f"[DocumentAwareChunker] File={source} | Category=maintenance | Sections Detected={len(sections)} | Chunks Produced={len(sections)}")

        for section_title, section_content in sections:
            if len(section_content) > self.MIN_CHUNK_SIZE:
                chunk_text = f"{section_title}\n{section_content}".strip()

                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        "chunk_type": "maintenance_procedure",
                        "procedure": section_title,
                        "chunk_size": len(chunk_text),
                    },
                )
                chunks.append(chunk_doc)

        return chunks if chunks else [doc]

    def _chunk_troubleshooting_document(self, doc: Document) -> list[Document]:
        """
        Chunk troubleshooting document by symptom/workflow.

        Each symptom workflow stays in one chunk.
        Supports multiple symptom header formats with various capitalizations.

        Args:
            doc: Document to chunk

        Returns:
            List of symptom workflow chunks
        """
        chunks = []
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")

        # Find troubleshooting sections
        sections = self._split_by_headers(text, self.TROUBLESHOOTING_PATTERN)

        if not sections:
            logger.warning(
                f"[DocumentAwareChunker] ✗ No troubleshooting pattern matched in {source}. "
                f"Supported formats: Engine Misfire, Vehicle Stalling, Transmission Slipping, Battery Drain, Check Engine Light"
            )
            logger.warning(f"[DocumentAwareChunker] Using fallback chunking for {source}")
            return [doc]

        logger.info(f"[DocumentAwareChunker] File={source} | Category=symptom/troubleshooting | Sections Detected={len(sections)} | Chunks Produced={len(sections)}")

        for section_title, section_content in sections:
            if len(section_content) > self.MIN_CHUNK_SIZE:
                chunk_text = f"{section_title}\n{section_content}".strip()

                # If chunk is too large, split it further
                if len(chunk_text) > self.MAX_CHUNK_SIZE:
                    sub_chunks = self._split_large_chunk(chunk_text, section_title, doc.metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_type": "troubleshooting_workflow",
                            "symptom": section_title,
                            "chunk_size": len(chunk_text),
                        },
                    )
                    chunks.append(chunk_doc)

        return chunks if chunks else [doc]

    def _chunk_generic_document(self, doc: Document) -> list[Document]:
        """
        Chunk unknown document type by sections.

        Fallback for documents without clear structure.

        Args:
            doc: Document to chunk

        Returns:
            List of section-based chunks
        """
        chunks = []
        text = doc.page_content

        # Split by double newlines (paragraphs)
        sections = text.split("\n\n")

        for section in sections:
            section = section.strip()
            if len(section) > self.MIN_CHUNK_SIZE:
                if len(section) > self.MAX_CHUNK_SIZE:
                    # Split large sections
                    sub_chunks = self._split_large_chunk(section, "generic_section", doc.metadata)
                    chunks.extend(sub_chunks)
                else:
                    chunk_doc = Document(
                        page_content=section,
                        metadata={
                            **doc.metadata,
                            "chunk_type": "section",
                            "chunk_size": len(section),
                        },
                    )
                    chunks.append(chunk_doc)

        return chunks if chunks else [doc]

    def _split_by_headers(
        self, text: str, header_pattern: re.Pattern
    ) -> list[tuple[str, str]]:
        """
        Split text by header patterns.

        Args:
            text: Text to split
            header_pattern: Regex pattern for headers

        Returns:
            List of (header, content) tuples
        """
        sections = []
        matches = list(header_pattern.finditer(text))

        if not matches:
            return []

        for i, match in enumerate(matches):
            header = match.group(1).strip()
            start_pos = match.end()

            # End position is next header or end of document
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            content = text[start_pos:end_pos].strip()
            sections.append((header, content))

        return sections

    def _split_large_chunk(
        self, text: str, title: str, metadata: dict[str, Any]
    ) -> list[Document]:
        """
        Split very large chunk into smaller pieces.

        Only called if chunk exceeds MAX_CHUNK_SIZE.

        Args:
            text: Text to split
            title: Section title
            metadata: Document metadata

        Returns:
            List of Document chunks
        """
        chunks = []
        words = text.split()
        chunk_words = []

        for word in words:
            chunk_words.append(word)
            chunk_text = " ".join(chunk_words)

            if len(chunk_text) > self.MAX_CHUNK_SIZE:
                # Start new chunk
                chunks.append(
                    Document(
                        page_content=chunk_text.rsplit(" ", 1)[0],  # Remove last word
                        metadata={
                            **metadata,
                            "chunk_type": metadata.get("chunk_type", "large_split"),
                            "title": title,
                            "chunk_size": len(chunk_text),
                        },
                    )
                )
                chunk_words = [word]  # Start new chunk with current word

        # Add remaining text
        if chunk_words:
            chunks.append(
                Document(
                    page_content=" ".join(chunk_words),
                    metadata={
                        **metadata,
                        "chunk_type": metadata.get("chunk_type", "large_split"),
                        "title": title,
                        "chunk_size": len(" ".join(chunk_words)),
                    },
                )
            )

        return chunks
