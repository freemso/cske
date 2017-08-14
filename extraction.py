# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    
"""
import logging
from collections import Counter

import dataset

import numpy

__author__ = "freemso"

# Hyper-parameters
ALPHA = 0.7

id_node_map = {}


def id2node(uuid):
    """
    Get the node of id
    :param uuid: universal identifier of the node
    :return: <Node>
    """
    if uuid in id_node_map:
        return id_node_map[uuid]
    else:
        node = Node(uuid)
        id_node_map[uuid] = node
        return node


def extract(target_uuid):
    target_node = id2node(target_uuid)
    logging.info("Extracting common sense knowledge for {}".format(target_node.get_name()))

    parents = target_node.get_parents()
    num_parents = len(parents)
    logging.info("{} has {} parents: {}".format(
        target_node.get_name(),
        num_parents,
        ", ".join([p.get_name() for p in parents])
    ))

    siblings = target_node.get_siblings()
    num_siblings = len(siblings)
    logging.info("{} has {} siblings: {}".format(
        target_node.get_name(),
        num_siblings,
        ", ".join([s.get_name() for s in siblings])
    ))

    target_attributes = target_node.get_attributes()

    parents_attributes_counter = count_nodes_attributes(parents)
    siblings_attributes_counter = count_nodes_attributes(siblings)

    # Inference from sibling
    for attribute in siblings_attributes_counter:
        if siblings_attributes_counter[attribute] > num_siblings ** ALPHA:
            # This attribute is valid
            pass

    # Inherit from parent
    # TODO

    # Merge results(from parents and from siblings) and conflict detection
    # TODO

    # Show the result


def count_nodes_attributes(nodes):
    """
    Count the attributes of a list of nodes
    :param nodes: <list> of <Node>
    :return: <Counter> of attributes with their occurrences
    """
    attributes_counter = Counter()
    for node in nodes:
        attributes = node.get_attributes()
        for attribute in attributes:
            attributes_counter[attribute] += 1
    return attributes_counter


class Node(object):
    """
    Node of the knowledge graph.
    Entity, category, type and value in PV-pair are all nodes.
    """

    def __init__(self, uuid):
        """
        :param uuid: universal identifier
        """
        self.uuid = uuid  # uri
        self.parents = None
        self.siblings = None
        self.attributes = None  # CSK from ConceptNet and PV-pairs from DB-pedia are all considered as attributes
        self.extracted_attributes = None  # Newly extracted attributes during this extraction process
        self.extracted_correct_attributes = None  # Attributes that are considered as correct after validation

    def __eq__(self, other):
        return hasattr(other, "uuid") and self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    def get_name(self):
        """
        Get a human readable name of the node
        :return: <str>
        """
        names = dataset.get_resource_name(self.uuid)
        return names[0] if len(names) > 0 else self.uuid.rsplit("/", 1)[-1]

    def get_parents(self):
        """
        Get parent nodes of the target node
        :return: <list> of <Node>
        """
        self.parents = set()
        if not self.parents:
            all_subjects={subject_id for subject_id in dataset.get_subjects(self.uuid)}
            all_types = {type_id for type_id in dataset.get_types(self.uuid)}
            ontology_types=dataset.filter_get_ontology(all_types)
            for type_id in ontology_types:
                p=type_id
                while True :
                    temp = dataset.get_parent_class(p)
                    if len(temp)==0:
                        break
                    else:
                        p=temp[0]
                        if p in all_types:
                            all_types.remove(p)
                        else:
                            continue
            all_parents=all_types|all_subjects
            self.parents = [id2node(parent_id) for parent_id in all_parents]
        return self.parents

    def get_siblings(self):
        """
        Get sibling nodes of the target node
        :return: <list> of <Node>
        """
        if not self.siblings:
            self.siblings = set()
            for p in self.parents:
                children = dataset.get_all_type_member(p.uuid)
                self.siblings = self.siblings.union({id2node(c) for c in children})
        return self.siblings

    def get_attributes(self):
        """
        Get the valid attributes of the node
        :return: <list> of (property<Edge>, value<Node>)
        """
        if not self.attributes:
            # Get PV-pairs and CSK from database
            pv_pairs = dataset.get_pv_pairs(self.uuid)
            csks = dataset.get_csks(self.uuid)
            # Merge duplicated attributes
            self.attributes = set(pv_pairs + csks)

        if self.extracted_correct_attributes:
            return self.attributes.union(self.extracted_correct_attributes)
        else:
            return self.attributes


def is_multi_valued(property_id):
    """
    Check if the edge is multi-valued.
    Calculate all predicates of <SPO> in DB-pedia, those objectives values of
    predicates that occur more than once are treated as multi-value attributes.
    :return: <bool>
    """
    n = dataset.is_multi_valued(property_id)
    return n>0


# def immediate_category_filter(category_nodes):
#     """
#     Filter out those categories who are at a higher level in the hierarchy.
#     Hierarchy information is available in DB-pedia Ontology.
#     :param category_nodes: <list> of <Node>
#     :return: <list> of <Node>, with no hierarchy conflict(granularity)
#     """
#     origin = category_nodes[:]
#     result = category_nodes[:]
#
#     for id in origin:
#         cur_cate = dataset.get_categories(id)  # Does Category has parent category?
#         result = list(set(result) - (set(result) & set(cur_cate)))
#     return result


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
    logging.root.setLevel(level=logging.INFO)
    node = id2node("http://dbpedia.org/resource/Huawei_P9")
    all_parents=node.get_parents()
    for x in all_parents:
        print x.uuid
    print is_multi_valued("dct:subject")


