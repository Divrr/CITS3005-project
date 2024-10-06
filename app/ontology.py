# app/ontology.py
from owlready2 import get_ontology, sync_reasoner

# Load your ontology
ontology_path = "ifixit_ontology.owl"
onto = get_ontology(ontology_path).load()

print(f"Ontology loaded with {len(list(onto.Procedure.instances()))} procedures.")

# for cls in onto.classes():
#     print(f"Class: {cls.name}")
#     instances = list(cls.instances())
#     if instances:
#         print(f"  Number of instances: {len(instances)}")
#         for instance in instances[:20]:
#             print(f"    Instance: {instance.name}")
