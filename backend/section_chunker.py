import re
from typing import List, Dict


class SectionChunker:

    def __init__(self, chunk_size=1200, overlap=200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_sections(self, text: str) -> List[Dict]:
        """
        Split SEC filing into sections like:
        Item 1
        Item 1A
        Item 2
        Item 7
        Item 8
        """

        pattern = re.compile(
            r"(?=^Item\s+\d+[A-Z]?\.*\s)",
            flags=re.MULTILINE
        )

        positions = list(pattern.finditer(text))

        sections = []

        if not positions:
            return [{"section": "FULL_DOCUMENT", "text": text}]

        for i, match in enumerate(positions):

            start = match.start()

            end = (
                positions[i + 1].start()
                if i + 1 < len(positions)
                else len(text)
            )

            section_text = text[start:end].strip()

            title = section_text.split("\n", 1)[0]

            sections.append({
                "section": title,
                "text": section_text
            })

        return sections

    def chunk_text(self, text: str):

        paragraphs = text.split("\n\n")

        chunks = []
        current = ""

        for para in paragraphs:

            if len(current) + len(para) < self.chunk_size:
                current += "\n\n" + para

            else:
                chunks.append(current.strip())

                current = para

        if current:
            chunks.append(current.strip())

        return chunks

    def create_chunks(
        self,
        text,
        ticker,
        company,
        filing_type,
        filing_date,
        cik=None
    ):

        all_chunks = []

        sections = self.split_sections(text)

        chunk_id = 0

        for section in sections:

            chunks = self.chunk_text(section["text"])

            for i, chunk in enumerate(chunks):

                all_chunks.append({

                    "chunk_id": chunk_id,

                    "ticker": ticker,

                    "company": company,

                    "cik": cik,

                    "filing_type": filing_type,

                    "filing_date": filing_date,

                    "section": section["section"],

                    "chunk_index": i,

                    "text": chunk

                })

                chunk_id += 1

        return all_chunks