import json
import os
from typing import Any, Dict, List
from uuid import uuid4

from ontology.v1.extractor.extractor import CaritasExtractor


class DocumentEnricher:
    def __init__(self, extractor: CaritasExtractor) -> None:
        self.extractor = extractor
        self.documents: List[Dict[str, Any]] = []
        self.document_concepts: List[Dict[str, Any]] = []
        self.labels = self.extractor.build_carifix_seed_concepts()["concepts"]

    def load_glossary(self, path: str) -> None:
        with open(path, "r") as file:
            documents: List[Dict[str, Any]] = json.load(file)

        for doc in documents:
            uuid = str(uuid4())
            # create document
            doc_map = {
                "id": uuid,
                "title": "Glossar: " + doc["pref_label"],
                "text": " ".join(doc["description"]),
                "published_at": "2022-01-01",
                "url": doc["link"],
            }

            # create document concepts
            concepts_raw = self.extractor.extract_concepts(doc["pref_label"])
            if len(concepts_raw) > 0:
                concept = next(
                    label for label in self.labels if label["pref_label"] == concepts_raw[0]
                )
                if concept:
                    doc_concept_map = {
                        "id": str(uuid4()),
                        "document_id": uuid,
                        "concept_id": concept["id"],
                        "weight": 5,
                    }
                    self.document_concepts.append(doc_concept_map)

            self.documents.append(doc_map)

    def load_neue_caritas(self, path: str) -> None:
        with open(path, "r") as file:
            documents: List[Dict[str, Any]] = json.load(file)

        for doc in documents:
            uuid = str(uuid4())
            # create document
            doc_map = {
                "id": uuid,
                "title": "Neue Caritas:" + doc["title"],
                "text": doc["teaser"],
                "published_at": doc["updated_at"].split(".")[2]
                + "-"
                + doc["updated_at"].split(".")[1]
                + "-"
                + doc["updated_at"].split(".")[0],
                "url": doc["link"],
            }

            # create document concepts
            concepts_raw = self.extractor.extract_concepts(doc["teaser"])
            for concept in concepts_raw:
                concept = next(
                    label for label in self.labels if label["pref_label"] == concepts_raw[0]
                )
                if concept:
                    doc_concept_map = {
                        "id": str(uuid4()),
                        "document_id": uuid,
                        "concept_id": concept["id"],
                        "weight": 2,
                    }
                    self.document_concepts.append(doc_concept_map)

            self.documents.append(doc_map)

    def load_raphaelswerk(self, path: str) -> None:
        with open(path, "r") as file:
            documents: List[Dict[str, Any]] = json.load(file)

        for doc in documents:
            uuid = str(uuid4())
            # create document
            doc_map = {
                "id": uuid,
                "title": "Raphaelswerk-Glossar: " + doc["pref_label"],
                "text": " ".join(doc["description"]),
                "published_at": "2022-01-01",
                "url": doc["link"],
            }

            # create document concepts
            concepts_raw = self.extractor.extract_concepts(doc["pref_label"])
            if len(concepts_raw) > 0:
                concept = next(
                    label for label in self.labels if label["pref_label"] == concepts_raw[0]
                )

                if concept:
                    doc_concept_map = {
                        "id": str(uuid4()),
                        "document_id": uuid,
                        "concept_id": concept["id"],
                        "weight": 4,
                    }
                    self.document_concepts.append(doc_concept_map)

            self.documents.append(doc_map)


if __name__ == "__main__":
    DIR_NAME = os.path.dirname(__file__)
    PATH_GRAPH = os.path.join(DIR_NAME, "../data/processed/carigraph_v1.json")
    PATH_GLOSSARY = os.path.join(DIR_NAME, "../data/raw/glossary.json")
    PATH_RW = os.path.join(DIR_NAME, "../data/raw/raphaelswerk_glossary.json")
    PATH_NEUE_CARITAS = os.path.join(DIR_NAME, "../data/raw/neue_caritas_articles.json")

    PATH_CARIFIX_DOC_SEED_FILE = os.path.join(
        DIR_NAME, "../data/processed/carifix_seed_documents_v1.json"
    )

    extractor = CaritasExtractor(path_graph=PATH_GRAPH)

    enricher = DocumentEnricher(extractor=extractor)

    enricher.load_glossary(path=PATH_GLOSSARY)
    enricher.load_raphaelswerk(path=PATH_RW)
    enricher.load_neue_caritas(path=PATH_NEUE_CARITAS)

    # save seed concepts
    seed_file = {"documents": enricher.documents, "document_concepts": enricher.document_concepts}
    with open(PATH_CARIFIX_DOC_SEED_FILE, "w") as file:
        json.dump(seed_file, file, ensure_ascii=False)
