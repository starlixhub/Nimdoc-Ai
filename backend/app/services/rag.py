from typing import List
from app.core.config import settings
from app.core.prompts import SYSTEM_RAG_PROMPT
from app.models.chat import ChatResponse
from app.services.citation import CitationService
from app.services.llm import llm_service
from app.services.retrieval import retrieval_service


class RAGService:
    """Coordinates retrieval, grounded prompt construction, LLM inference, and citation assembly."""

    def __init__(self):
        self.min_relevance_score = settings.min_relevance_score

    async def answer_question(
        self,
        question: str,
        document_ids: List[str],
        session_id: str,
    ) -> ChatResponse:
        # 1. Retrieve relevant chunks
        chunks = await retrieval_service.retrieve(
            query=question,
            document_ids=document_ids,
            top_k=settings.top_k_retrieval,
        )

        # 2. Check if evidence exists
        if not chunks or (chunks and chunks[0].get("score", 1.0) < self.min_relevance_score):
            return ChatResponse(
                session_id=session_id,
                answer="I couldn't find this information in the uploaded documents.",
                citations=[],
                grounded=False,
            )

        # 3. Construct grounded context prompt
        context_blocks = []
        for i, chunk in enumerate(chunks, start=1):
            doc_name = chunk.get("document_name", "Document")
            page = chunk.get("page", "?")
            text = chunk.get("text", "")
            context_blocks.append(f"[{i}] ({doc_name}, Page {page})\n\"{text}\"")

        context_str = "\n\n".join(context_blocks)
        user_prompt = f"CONTEXT:\n{context_str}\n\nQUESTION:\n{question}\n\nANSWER:"

        # 4. Call NVIDIA LLM via Nebius
        answer = await llm_service.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_RAG_PROMPT,
        )

        # 5. Build citations from retrieved chunks
        citations = CitationService.build_citations_from_chunks(chunks)

        return ChatResponse(
            session_id=session_id,
            answer=answer.strip(),
            citations=citations,
            grounded=True,
        )


rag_service = RAGService()
