# iFixit: Know-How to Knowledge Graph
This project is due on **11.59pm October 18, 2024** and is worth **30% of your final grade.** You may choose to complete the project in a pair, or as an individual. If you complete the project as a pair, you must each submit a separate individual report. Each student should submit their work to [cssubmit](https://secure.csse.uwa.edu.au/run/cssubmit). If working in a pair, each student should submit the full set of files, but each file should clearly indicate both students who contributed to it.

---

## Overview:
  - [iFixit](https://www.ifixit.com/Manifesto) is a community project built around the right to repair, and shares knowledge about procedures for fixing broken things, including computers, phones, cars, clothes appliances and so on. The guides are organised so that they are easy to browse and search, and have a standardized format, so they are easy to use and write. In this project, you will choose a subcategory of instruction manuals, and build a knowledge graph and ontology around those manuals.
  - The iFixit corpus has already be partially processed and refined to build a [dataset](https://github.com/rub-ksv/MyFixit-Dataset) and related resources. The dataset is a [github repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)  which you can clone to your local machine, and explore the data which is in json format. Using this as a starting point, you should aim to build a lightweight ontology describing the procedures context of these manuals, populate the ontology with the data in the repository (or similar data you have sourced from elsewhere), and produce queries and processes demonstrating the operation of your ontology.
  - Your ontology should run as a small standalone application, that may be implemented as a command line program running in a python shell, or a small flask application.  
## Deliverables:
You should deliver the following elements:
- **25%** An OWLReady 2 ontology (possibly including pySHACL) describing the concepts in the graph, including: procedure, item, part, tool, step, image. These should allow natural and useful queries over the knowledge graph, and should enforce, at least:
  - An item, with a subclass relation that is transitive, and a part-of relation that identifies when one item is a part of another item 
  - Tools used in a step of the procedure appear in the toolbox of the procedure
  - A sub-procedure of a procedure must be a procedure for the same item or a part of that item.
    This should be submitted as an owl file, optionally a pySHACL file, and an python script for loading the ontology with the knowledge graph.
- **25%** A knowledge graph, implemented in OWLReady2 connecting the ontology to the iFixit Dataset. A test set of data should be provided with a python script provided to load the data into RDFLib and execute some SPARQL queries, including:
  - Find all procedures with more than 6 steps;
  - Find all items that have more than 10 procedures written for them;
  - Find all procedures that include a tool that is never mentioned in the procedure steps;
  - Flag potential hazards in the procedure by identifying steps with works like "careful" and "dangerous". 
- **15%** A python application, using the command line or Flask, that allows a use to browse and search the ontology/knowledge graph
  - The application should display the data as well as the inferred classes and relations.
  - The application should provide a syntax for searching the procedures
  - The application should identify any errors in the data (according to the ontology).
    The ontology, knowledge graph and application should be submitted as a zip file (*.zip). This should not include the entire iFixit dataset, but just enough data to demonstrate the functionality of the application.
- **25%** A User Manual that explains how to use and run the applications, including: 
  - an overview of the schema, and ontology rules.
  - example queries, describing how to form the queries and interpret the output.
  - instructions on how to add, update or remove data in the knowledge graph, and add rules to the ontology.
    The user manual maybe presented as a pdf file, or using HTML/Markdown. 
- **10%** An individual report describing the process of building the project, including:
  - The design choices made in the project. Which options were considered and why di you make the choice you did?
  - What tools you used in the project, how effective were they, and what you would recommend people use in the future.
  - An estimate of time spent on the different tasks in the project.
  - If you worked in pairs, describe how work was divided, how effective you thought the collaboration was, and an honest assessment of the relative contribution of both team members.
    The individual report should be a pdf file.
The marking criterion gives a rough indication of what is expected.

## Resources:
The resources page will be updated as the project progress. The basic tools that should be used when completing this project are:
  - [owlready2](https://owlready2.readthedocs.io/en/v0.42/) for representing the ontology and applying reasoning, including [RDFLib](https://rdflib.readthedocs.io/en/stable/) and Python for building the knowledge graph and executing SPARQL queries.
  - [pYSHACL](https://github.com/RDFLib/pySHACL) for applying and validating constraints on the graph (optional).
  - [owlready2](https://owlready2.readthedocs.io/en/v0.42/) for representing the ontology and applying reasoning.
  - [flask](https://flask.palletsprojects.com/en/3.0.x/) for building a basic webserver and interface (optional). If you haven't done [CITS3403](https://teaching.csse.uwa.edu.au/units/CITS3403/index-2023.html), this tutorial is an excellent resource.
  - an [ontology for maintenance](https://content.iospress.com/articles/applied-ontology/ao230279), by Caitlin Woods
You can access iFixit data from this [GitHub repo](https://github.com/rub-ksv/MyFixit-Dataset). Or derive your own from [iFixit](https://www.ifixit.com/) using tools like [beautifulsoup](https://pypi.org/project/beautifulsoup4/), or their [API](https://www.ifixit.com/api/2.0/doc?srsltid=AfmBOooTJFjt8OgGAMWqw_C1vJ_Uy4CfLo2BVYaYiDFle6FrlzGi60LI).