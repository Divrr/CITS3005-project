25% A User Manual that explains how to use and run the applications, including: 
- an overview of the schema, and ontology rules.
- example queries, describing how to form the queries and interpret the output.
- instructions on how to add, update or remove data in the knowledge graph, and add rules to the ontology.
The user manual maybe presented as a pdf file, or using HTML/Markdown. 

# User Manual for iFixit Knowledge Graph Application
## Introduction
The application built is designed to create a knowledge graph and ontology around iFixit instruction manuals.  It allows users to browse procedures, tools, and items while enforcing certain relationships and querying capabilities. This manual provides an overview of the ontology, key queries, and instructions on how to interact with the knowledge graph.

## Overview of the Schema and Ontology Rules
The main concepts of the ontology are:
  - Procedure: Represents a set of steps for fixing an item.
  - Item: Any physical object described in the procedure.
  - Part: A component that makes up an item. 
  - Tool: Tools used within a procedure's steps.
  - Step: Individual actions or tasks within a procedure.

Other objects include:
  - DeviceCategory: All ancestor category classes of items -- for example, "Macbook" and "Powershell".
  - Image: Node linking to image and thumbnail URLs. 
  - Action: Represents an action performed in a step. These are extracted from the json file's "removal_verbs" section.

Properties include:
  - All items have a `title`. Procedures, steps and actions can have further `description`s, which are the extracted raw texts.
  - The Image object connect steps and items to `url` and `thumbnail` properties.
  - Each procedure has a unique `guidid`, and each step has a unique `stepid`.

Reltionships include:
  - Procedures connect to each of their steps using `consists_of`. Each step contains a step `order`.
  - Both procedures and steps have the `uses_tool` relation, based on what has been extracted in the json. Steps can additionally be associated with `action`s.
  - Steps have the `involves_part` relation
  - A procedure, part or item can be `part_of` another item. This is useful in creating relations between procedures relating to related items.
  - The device category hierarchy is outlined using a transitive `is_subcategory_of` relation. An item connects to its most specific category using the `belongs_to_category` relation.
  - A procedure can be part of another procedure for the same or related items. This is outlined by the `subprocedure` relation.

Inference rules allow us to infer transitive and inverse relations of items. 
- Transitive relations are `subclass_of`, `part_of` and `subprocedure`.
- Inverse relations are 
  - part `involved_in_step`, which is the invere of step `involves_part`.
  - tool `used_in` step or procedure, which is the inverse of step or procedure `uses_tool`
  - step `in_procedure`, which is the inverse of procedure `consists of` step.

## Example Queries
The following example SPARQL Queries display the name of the element you have searched for in the ontology:
1. This example returns all procedures with more than 6 steps:
    `SELECT ?procedure WHERE { ?procedure :hasStep ?step . FILTER (COUNT(?step) > 6) } GROUP BY ?procedure`
2. This example returns all items with more than 10 procedures:
    `SELECT ?item WHERE { ?item :hasProcedure ?procedure . FILTER (COUNT(?procedure) > 10) } GROUP BY ?item`
3. This example returns tools included in a procedure but not mentioned in any of its steps:
    `SELECT ?tool WHERE { ?procedure :hasTool ?tool . FILTER NOT EXISTS { ?step :usesTool ?tool } }`
4. This example returns all hazardous steps. We define a hazardous step as one with the words "careful" or "dangerous" written in the raw text:
    `SELECT ?step WHERE { ?step :description ?desc . FILTER (CONTAINS(?desc, "careful") || CONTAINS(?desc, "dangerous")) }` 

You can run more examples in the `scripts/query_ontology.py` file.

## Instructions for Adding, Updating, and Removing Data
### To add data:
Use RDFLib's 'add' function to insert a triple into the graph.
Example: `g.add((procedure_uri, URIRef("http://ontology/usesTool"), tool_uri))`

### To update data:
Remove the old triple and insert a new one.
Example: 
`g.remove((procedure_uri, URIRef("http://ontology/usesTool"), old_tool_uri))`
`g.add((procedure_uri, URIRef("http://ontology/usesTool"), tool_uri))`

### To remove data:
Simply use the 'remove' function.
Example: `g.remove((procedure_uri, URIRef("http://ontology/usesTool"), tool_uri))`

### To add rules:
Open the owl ontology in python, then run your new SWRL rule. After this, you will need to re-synchronize your reasoner. In our example, this will be done automatically for you when you rerun the flask application.
Example:
```python
import owlready2 as owl
onto = owl.get_ontology("http://test.org/onto.owl")
with onto:
  rule1 = Imp()
  rule1.set_as_rule("[rule]")
```

## Running the Application
### Command-line:
To run the scripts to generate the OWL files execute the following via the commandline:
`python ontology/ifixit_ontology.py`
`python scripts/load_data.py`
`python scripts/query_ontology.py`

### Flask Application:
To start the Flask application, run:
`flask run`
Then access the application on `localhost:5000` in a web browser.    

The webpage allows for searching by key words in procedure titles, as well as filtering by parts, tools and categories. Beyond this, one can also browse the categories independently, mirroring what is done on the iFixit website.