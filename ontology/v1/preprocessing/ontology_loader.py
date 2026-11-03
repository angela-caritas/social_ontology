"""
Build the first version of the ontology with the following sources:

- Crea Client
- Vivendi
- Glossary

"""

import json
import os
from enum import Enum
from typing import Any, Dict, Union
from uuid import UUID, uuid4


class ConceptType(Enum):
    DIMENSION_LABEL = 1
    TOPIC_LABEL = 2
    ROOT_LABEL = 3
    LABEL = 4
    ALT_LABEL = 5


class CariConcept:
    def __init__(
        self,
        label: str,
        concept_source: str,
        concept_type: ConceptType,
        uri: str | None = None,
        uuid: UUID | None = None,
        parent_label_uuid: UUID | None = None,
        description: str | None = None,
        url: str | None = None,
    ):
        self.label: str = label
        self.uri: str = uri or self.create_uri(label)
        self.uuid: UUID = uuid or uuid4()
        self.concept_source: str = concept_source
        self.parent_label_uuid: Union[None, UUID] = parent_label_uuid
        self.broader: list[str] = []
        self.narrower: list[str] = []
        self.concept_type: ConceptType = concept_type
        self.description: Union[None, str] = description
        self.url: Union[None, str] = url

    def __repr__(self) -> str:
        return "node|" + self.uri

    @staticmethod
    def create_uri(label: str) -> str:
        uri = label.lower().replace("/ ", "").replace(" ", "-")
        return uri

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "concept_source": self.concept_source,
            "concept_type": self.concept_type.name,
            "uri": self.uri,
            "uuid": str(self.uuid),
            "parent_label_uuid": str(self.parent_label_uuid) if self.parent_label_uuid else None,
            "description": self.description,
            "url": self.url,
        }


class CariLink:
    def __init__(self, source: str, target: str, directed: bool = True, hierachical: bool = True):
        self.source = source
        self.target = target
        self.directed = directed
        self.hierachical = hierachical

    def __repr__(self) -> str:
        return "edge|" + self.source + ">>" + self.target

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "directed": self.directed,
            "hierachical": self.hierachical,
        }


class CariGraph:
    def __init__(self) -> None:
        self.nodes: list[CariConcept] = []
        self.edges: list[CariLink] = []

    def __repr__(self) -> str:
        return (
            "Graph with " + str(len(self.nodes)) + " Nodes and " + str(len(self.edges)) + " Edges."
        )

    def build_nodes(self) -> None:
        pass

    def build_edges(self) -> None:
        pass

    def get_concept_by_uri(self, uri: str) -> CariConcept | None:
        try:
            return [node for node in self.nodes if node.uri == uri][0]
        except IndexError:
            print("Concept not found")
            return None

    def get_concept_by_label(self, label: str) -> CariConcept | None:
        try:
            return [node for node in self.nodes if node.label == label][0]
        except IndexError:
            print("Concept " + label + " not found")
            return None

    def save_to_file(self, path: str) -> None:
        out_file = {
            "nodes": [el.to_dict() for el in self.nodes],
            "edges": [el.to_dict() for el in self.edges],
        }

        with open(path, "w", encoding="utf-8") as file:
            json.dump(out_file, file, ensure_ascii=False)

    def load_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            graph = json.load(file)
            self.nodes = graph["nodes"]
            self.edges = graph["edges"]

    def add_crea_categories(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            crea_file = json.load(file)
            crea_categories = crea_file["sub_topics"]

        # create dimension label
        dimension_concept = CariConcept(
            label="Beratungsthema", concept_source="base", concept_type=ConceptType.DIMENSION_LABEL
        )
        self.nodes.append(dimension_concept)
        # create root nodes
        for cat in crea_categories.keys():
            cat_concept = CariConcept(
                label=cat,
                concept_source="base",
                concept_type=ConceptType.TOPIC_LABEL,
                parent_label_uuid=dimension_concept.uuid,
            )
            cat_uri = cat_concept.uri
            self.nodes.append(cat_concept)

            # create link to dimension
            dimension_topic_link = CariLink(
                source=dimension_concept.uri,
                target=cat_concept.uri,
                hierachical=True,
                directed=True,
            )
            self.edges.append(dimension_topic_link)

            for sub_cat in crea_categories[cat]:
                # create label
                sub_cat_concept = CariConcept(
                    label=sub_cat,
                    concept_source="base",
                    concept_type=ConceptType.ROOT_LABEL,
                    parent_label_uuid=cat_concept.uuid,
                )
                self.nodes.append(sub_cat_concept)
                sub_cat_uri = sub_cat_concept.uri
                # create edge
                edge = CariLink(source=cat_uri, target=sub_cat_uri, hierachical=True, directed=True)
                self.edges.append(edge)

                # create Crea Label

                crea_concept = CariConcept(
                    label=sub_cat,
                    concept_source="crea-client",
                    uri="crea-" + CariConcept.create_uri(label=sub_cat),
                    concept_type=ConceptType.LABEL,
                )
                self.nodes.append(crea_concept)
                # create crea client edge
                edge = CariLink(
                    source=sub_cat_uri, target=crea_concept.uri, hierachical=True, directed=False
                )
                self.edges.append(edge)

    def add_vivendi_categories(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            vivendi_file = json.load(file)
            vivendi_categories = vivendi_file["categories"]

        for cat in vivendi_categories:
            cat_concept = CariConcept(
                label=cat["title"],
                concept_source="vivendi",
                concept_type=ConceptType.LABEL,
                uri="vivendi-" + CariConcept.create_uri(label=cat["title"]),
            )
            cat_uri = cat_concept.uri
            self.nodes.append(cat_concept)

            for m in cat["mapping"]:
                # create edge
                source = self.get_concept_by_label(label=m)
                if source:
                    edge = CariLink(
                        source=source.uri, target=cat_uri, hierachical=True, directed=False
                    )
                    self.edges.append(edge)

    def add_glossary_categories(self, path: str, path_mapping: str) -> None:

        # Add main categories
        main_cats = [
            "Schulden",
            "Sucht",
            "Alter und Pflege",
            "Caritas",
            "Haft",
            "Kinder und Jugendliche",
            "Migration",
            "Behinderung",
            "Familienhilfe",
            "Fachinformation",
            "Sozialrecht",
            "Ehrenamt",
        ]

        for main_cat in main_cats:
            cat_concept = CariConcept(
                label=main_cat,
                concept_source="glossary-root",
                concept_type=ConceptType.LABEL,
                uri="glossary-root-" + CariConcept.create_uri(main_cat),
            )
            self.nodes.append(cat_concept)

        # Add all labels
        with open(path, "r", encoding="utf-8") as file:
            glossary_file = json.load(file)
            glossary_categories = [el for el in glossary_file if el["broader"] in main_cats]

        seen_cat = []
        for cat in glossary_categories:
            cat_concept = CariConcept(
                label=cat["pref_label"],
                concept_source="glossary",
                concept_type=ConceptType.LABEL,
                uri="glossary-" + cat["uri"],
                url=cat["url"] if "url" in cat else None,
                description=" ".join(cat["description"]),
            )
            if cat_concept.uri not in seen_cat:
                self.nodes.append(cat_concept)
                seen_cat.append(cat_concept.uri)

            source_uri = "glossary-root-" + CariConcept.create_uri(cat["broader"])
            edge = CariLink(
                source=source_uri, target=cat_concept.uri, hierachical=True, directed=True
            )
            self.edges.append(edge)

        # Add links between glossary items
        for cat in glossary_categories:
            for mapping in cat["related"]:
                edge = CariLink(
                    source="glossary-" + cat["uri"],
                    target="glossary-" + mapping,
                    hierachical=False,
                    directed=False,
                )
                self.edges.append(edge)

        # Add Base Label - Glossary Mapping
        with open(path_mapping, "r", encoding="utf-8") as file:
            mapping_file = json.load(file)["sub_topics"]
            mapping_categories = [
                item for sublist in list(mapping_file.values()) for item in sublist
            ]

        for cat in mapping_categories:
            source = self.get_concept_by_label(cat["title"])
            if source:
                source_uri = source.uri
                for mapping in cat["mapping"]:
                    t = "glossary-" + mapping
                    target = self.get_concept_by_uri(t)
                    if target:
                        target_uri = target.uri
                        edge = CariLink(source_uri, target_uri, hierachical=True, directed=True)
                        self.edges.append(edge)

    def add_asyl_net_categories(self, path: str, path_mapping: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            asyl_net_file = json.load(file)
            asyl_net_categories = [
                el for el in asyl_net_file if el["link"].split("/")[1] == "themen"
            ]

        seen_cat = []
        for main_cat in asyl_net_categories:
            cat_concept = CariConcept(
                label=main_cat["title"],
                concept_source="asyl-net",
                concept_type=ConceptType.LABEL,
                uri="asylnet-" + main_cat["link"].split("/")[-1],
            )
            if cat_concept.uri not in seen_cat:
                self.nodes.append(cat_concept)
                seen_cat.append(cat_concept.uri)

        for main_cat in [el for el in asyl_net_categories if el["broader"] is not None]:
            edge = CariLink(
                source="asylnet-" + main_cat["broader"],
                target="asylnet-" + main_cat["link"].split("/")[-1],
                hierachical=True,
                directed=True,
            )
            self.edges.append(edge)

        # manual mappings
        with open(path_mapping, "r", encoding="utf-8") as file:
            mapping_file = json.load(file)["sub_topics"]
            mapping_categories = [
                item for sublist in list(mapping_file.values()) for item in sublist
            ]

        for cat in mapping_categories:
            source = self.get_concept_by_uri(CariConcept.create_uri(cat["title"]))
            if source:
                source_uri = source.uri
                for mapping in cat["mapping"]:
                    t = "asylnet-" + mapping
                    print(t)
                    target = self.get_concept_by_uri(t)
                    if target:
                        target_uri = target.uri
                        edge = CariLink(source_uri, target_uri, hierachical=True, directed=True)
                        self.edges.append(edge)

    def add_geldundschulden_categories(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            gus_categories = json.load(file)

        seen_cat = []
        for main_cat in gus_categories:
            cat_concept = CariConcept(
                label=main_cat["pref_label"],
                concept_source="geld-und-schulden",
                concept_type=ConceptType.LABEL,
                uri=main_cat["uri"],
                url=main_cat["link"],
            )
            if cat_concept.uri not in seen_cat:
                self.nodes.append(cat_concept)
                seen_cat.append(cat_concept.uri)

        # Add links between glossary items
        for cat in gus_categories:
            for mapping in cat["related"]:
                edge = CariLink(
                    source=cat["uri"],
                    target=[el for el in gus_categories if el["pref_label"] == mapping][0]["uri"],
                    hierachical=False,
                    directed=False,
                )
                self.edges.append(edge)

        source_uri = "verschuldung-überschuldung"
        for cat in gus_categories:
            target_uri = cat["uri"]
            edge = CariLink(source_uri, target_uri, directed=True, hierachical=True)
            self.edges.append(edge)

    def add_ebis_categories(self, path: str, path_mapping: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            ebis_categories = json.load(file)

        # create root nodes
        for cat in ebis_categories.keys():
            cat_concept = CariConcept(
                label=cat,
                concept_source="ebis",
                uri="ebis-" + CariConcept.create_uri(label=cat),
                concept_type=ConceptType.LABEL,
            )
            cat_uri = cat_concept.uri
            self.nodes.append(cat_concept)

            for sub_cat in ebis_categories[cat]:
                # create label
                sub_cat_concept = CariConcept(
                    label=sub_cat,
                    concept_source="ebis",
                    uri="ebis-" + CariConcept.create_uri(label=sub_cat),
                    concept_type=ConceptType.LABEL,
                )
                self.nodes.append(sub_cat_concept)
                sub_cat_uri = sub_cat_concept.uri
                # create edge
                edge = CariLink(source=cat_uri, target=sub_cat_uri)
                self.edges.append(edge)

        # manual mappings
        with open(path_mapping, "r", encoding="utf-8") as file:
            mapping_file = json.load(file)["sub_topics"]
            mapping_categories = [
                item for sublist in list(mapping_file.values()) for item in sublist
            ]

        for cat in mapping_categories:
            source = self.get_concept_by_uri(CariConcept.create_uri(cat["title"]))
            if source:
                source_uri = source.uri
                for mapping in cat["mapping"]:
                    t = "ebis-" + CariConcept.create_uri(mapping)
                    print(t)
                    target = self.get_concept_by_uri(t)
                    if target:
                        target_uri = target.uri
                        edge = CariLink(source_uri, target_uri, directed=True, hierachical=True)
                        self.edges.append(edge)

    def add_thesaurus_synonyms(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            synonym_categories = json.load(file)

        # create root nodes
        for cat in synonym_categories.keys():
            cat_concept = self.get_concept_by_label(cat)
            if cat_concept is None:
                print(cat + " not found.")
            else:
                for sub_cat in synonym_categories[cat]:
                    # check if word exists as label
                    exisiting_concept = self.get_concept_by_label(sub_cat)
                    if (
                        exisiting_concept is None
                        or exisiting_concept.concept_source == "glossary-root"
                    ):
                        # create label
                        sub_cat_concept = CariConcept(
                            label=sub_cat,
                            concept_source="synonym",
                            uri="synonym-" + CariConcept.create_uri(label=sub_cat),
                            concept_type=ConceptType.ALT_LABEL,
                        )
                        self.nodes.append(sub_cat_concept)
                        sub_cat_uri = sub_cat_concept.uri
                        # create edge
                        edge = CariLink(
                            source=cat_concept.uri,
                            target=sub_cat_uri,
                            directed=True,
                            hierachical=True,
                        )
                        self.edges.append(edge)

    def add_crea_dimensions(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            categories = json.load(file)

        dimensions_ = list(set([cat["dimension"] for cat in categories]))
        # exclude "Beratungsthema"
        dimensions = [el for el in dimensions_ if el != "Beratungsthema"]
        # create dimension labels
        for dimension in dimensions:
            concept_dimension = CariConcept(
                label=dimension, concept_source="base", concept_type=ConceptType.DIMENSION_LABEL
            )
            self.nodes.append(concept_dimension)

            topics = list(
                set([cat["title"] for cat in categories if cat["dimension"] == dimension])
            )

            for topic in topics:
                concept_topic = CariConcept(
                    label=topic,
                    concept_source="base",
                    concept_type=ConceptType.TOPIC_LABEL,
                    parent_label_uuid=concept_dimension.uuid,
                )
                self.nodes.append(concept_topic)
                dimension_topic_link = CariLink(
                    source=concept_dimension.uri,
                    target=concept_topic.uri,
                    hierachical=True,
                    directed=True,
                )
                self.edges.append(dimension_topic_link)

                topic_dict = [
                    cat
                    for cat in categories
                    if cat["dimension"] == dimension and cat["title"] == topic
                ][0]

                for label in topic_dict["auspraegungen"]:
                    if label["name"] != "ohne Eintragung":
                        concept_label = CariConcept(
                            label=label["name"],
                            concept_source="base",
                            concept_type=ConceptType.ROOT_LABEL,
                            parent_label_uuid=concept_topic.uuid,
                        )
                        self.nodes.append(concept_label)
                        topic_label_link = CariLink(
                            source=concept_topic.uri,
                            target=concept_label.uri,
                            hierachical=True,
                            directed=True,
                        )
                        self.edges.append(topic_label_link)


if __name__ == "__main__":

    dirname = os.path.dirname(__file__)

    PATH_CREA_CLIENT = os.path.join(dirname, "../data/raw/categories_crea_client.json")
    PATH_VIVENDI = os.path.join(dirname, "../data/raw/mapping_crea_vivendi.json")
    PATH_GLOSSARY = os.path.join(dirname, "../data/processed/categories_glossary.json")
    PATH_GLOSSARY_MAPPING = os.path.join(dirname, "../data/raw/mapping_crea_glossary.json")
    PATH_ASYLNET = os.path.join(dirname, "../data/processed/categories_asylnet.json")
    PATH_ASYLNET_MAPPING = os.path.join(dirname, "../data/raw/mapping_crea_asylnet.json")
    PATH_GELDUNDSCHULDEN = os.path.join(
        dirname, "../data/processed/categories_geldundschulden.json"
    )
    PATH_THESAURUS_MAPPING = os.path.join(dirname, "../data/raw/mapping_crea_thesaurus.json")
    PATH_EBIS = os.path.join(dirname, "../data/raw/categories_ebis.json")
    PATH_EBIS_MAPPING = os.path.join(dirname, "../data/raw/mapping_crea_ebis.json")
    PATH_OUTFILE = os.path.join(dirname, "../data/processed/carigraph_v1.json")
    PATH_DIMENSIONS = os.path.join(dirname, "../data/raw/categories_crea_client_enriched.json")

    graph = CariGraph()
    graph.add_crea_categories(PATH_CREA_CLIENT)
    graph.add_vivendi_categories(PATH_VIVENDI)
    graph.add_glossary_categories(PATH_GLOSSARY, PATH_GLOSSARY_MAPPING)
    graph.add_asyl_net_categories(PATH_ASYLNET, PATH_ASYLNET_MAPPING)
    graph.add_geldundschulden_categories(PATH_GELDUNDSCHULDEN)
    graph.add_ebis_categories(PATH_EBIS, PATH_EBIS_MAPPING)
    graph.add_thesaurus_synonyms(PATH_THESAURUS_MAPPING)

    graph.add_crea_dimensions(PATH_DIMENSIONS)

    graph.save_to_file(path=PATH_OUTFILE)

    # check if all uris are unqiue
    names = [el.uri for el in graph.nodes]
    print(len(names))
    print(len(list(set(names))))
