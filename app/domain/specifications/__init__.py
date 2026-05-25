from app.domain.specifications.specification import Specification, AndSpecification, OrSpecification, NotSpecification
from app.domain.specifications.document_specifications import (
    DocumentProcessedSpecification,
    DocumentFailedSpecification,
    DocumentByFileNameSpecification,
    DocumentByExtensionSpecification,
    DocumentWithContentSpecification,
    PROCESSED,
    FAILED,
    TXT_FILES,
)

__all__ = [
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "DocumentProcessedSpecification",
    "DocumentFailedSpecification",
    "DocumentByFileNameSpecification",
    "DocumentByExtensionSpecification",
    "DocumentWithContentSpecification",
    "PROCESSED",
    "FAILED",
    "TXT_FILES",
]
