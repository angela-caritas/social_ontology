import json
import os
from typing import Any, Dict
from uuid import uuid4


class CaritasExtractor:
    def __init__(self, path_graph: str) -> None:
        self.graph: Dict[str, Any] = self._load_carigraph(path_graph=path_graph)
        self.searchword_dict: Dict[str, Any] = self._build_dictionary()

    def _load_carigraph(self, path_graph: str) -> Any:
        with open(path_graph, "r") as file:
            graph = json.load(file)
        return graph

    def _find_related_labels(self, label_uris: list[str]) -> list[str]:
        res = list(
            set(
                [
                    edge["target"]
                    for edge in self.graph["edges"]
                    if edge["source"] in label_uris and edge["hierachical"]
                ]
            )
        )
        return res

    def _find_all_related_labels(self, label_uri: str) -> list[str]:
        labels = [label_uri]
        labels_new: list[str] = []
        while len(labels) != len(labels_new):
            if len(labels_new) != 0:
                labels = labels_new
            related = self._find_related_labels(labels)
            if len(related) == 0:
                break
            labels_new = list(set(labels + related))
        return labels

    def _build_dictionary(self) -> dict[str, Any]:
        # build concept dictionary
        label_dictionary: Dict[Any, Any] = {}
        labels = [label for label in self.graph["nodes"] if label["concept_type"] == "ROOT_LABEL"]
        for label in labels:
            related_uris = self._find_all_related_labels(label_uri=label["uri"])

            related_nodes = [el for el in self.graph["nodes"] if el["uri"] in related_uris]

            label_dictionary[label["label"]] = related_nodes
        return label_dictionary

    def build_carifix_seed_concepts(self) -> dict[str, Any]:
        """Generates a list of concepts that can be used for seeding the Carifix database.

        Returns
        -------
        list
            _description_
        """
        # filter concepts
        concepts = [
            {
                "pref_label": label["label"],
                "id": label["uuid"],
                "parent_id": label["parent_label_uuid"] or None,
            }
            for label in self.graph["nodes"]
            if label["concept_type"] in ["DIMENSION_LABEL", "TOPIC_LABEL", "ROOT_LABEL"]
        ]

        # add alternative labels
        alt_labels: list[Any] = []
        for concept in concepts:
            if concept["pref_label"] in self.searchword_dict:
                alt_labels += [
                    {
                        "pref_label": sw["label"],
                        "id": str(uuid4()),
                        "concept_id": concept["id"],
                        "source": "CariGraph",
                    }
                    for sw in self.searchword_dict[concept["pref_label"]]
                ]

        return {"concepts": concepts, "alt_labels": alt_labels}

    def extract_concepts(self, text: str) -> list[str]:
        result = []
        for label in self.searchword_dict:
            res_ = (
                len(
                    [
                        el["label"]
                        for el in self.searchword_dict[label]
                        if str(el["label"]).lower() in text.lower()
                    ]
                )
                > 0
            )
            if res_:
                result.append(label)
        return list(set(result))


if __name__ == "__main__":
    DIR_NAME = os.path.dirname(__file__)
    PATH_GRAPH = os.path.join(DIR_NAME, "../data/processed/carigraph_v1.json")
    PATH_CARIFIX_SEED_FILE = os.path.join(
        DIR_NAME, "../data/processed/carifix_seed_concepts_v1.json"
    )
    extractor = CaritasExtractor(path_graph=PATH_GRAPH)

    # build carifix seed concepts
    seed_concepts = extractor.build_carifix_seed_concepts()

    # save seed concepts
    with open(PATH_CARIFIX_SEED_FILE, "w") as file:
        json.dump(seed_concepts, file, ensure_ascii=False)
