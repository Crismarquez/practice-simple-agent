"""
Define the schemas for the agents, workflows and tools.
"""

from typing import Literal, List
from pydantic import BaseModel, Field

# ===== STRUCTURED OUTPUT SCHEMAS =====

class GuardrailsSchema(BaseModel):
    reason: str = Field(
        description="Reason for the classification of the question. This should be a short and concise explanation (10-15 words) that the user can understand.",
    )
    classification: Literal["accepted", "rejected"] = Field(
        description="Question classification: 'accepted' if the question is related to who performs certain tasks or who can assist with specific processes, "
        "'rejected'  if the question is about topics outside of this context.",)
    

class EnrichmentSchema(BaseModel):
    """Schema for enriched sentences generation"""
    sentences: List[str] = Field(
        description="List of clear, concise sentences that capture main ideas and keywords for semantic search"
    )

class GoldenDatasetPair(BaseModel):
    question: str = Field(description="A clear, specific question based on the text chunk")
    answer: str = Field(description="The accurate answer derived solely from the text chunk")

class GoldenDatasetSchema(BaseModel):
    """Schema for golden dataset generation"""
    qa_pairs: List[GoldenDatasetPair] = Field(
        description="List of 2-5 question-answer pairs generated from the document chunk"
    )

    
# ===== TOOLS =====

class RetrieveDocuments(BaseModel):
    """Retrieve documents using existing RAG infrastructure."""
    
    query: str = Field(description="Search query to retrieve documents")

class RetrieveDocumentsDomain(BaseModel):
    """Retrieve documents using existing RAG infrastructure."""
    
    domain: str = Field(description="Domain of the documents")
    query: str = Field(description="Search query or document name")
