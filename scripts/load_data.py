import json
from owlready2 import *
import os

from pathlib import Path

# Get the absolute path to the ontology file
ontology_path = Path("ifixit_ontology.owl").resolve()
print("Ontology absolute path:", ontology_path)

if not ontology_path.is_file():
    print("Ontology file not found at:", ontology_path)
    exit(1)


ontology_uri = ontology_path.as_uri()
print("Ontology URI:", ontology_uri)

onto = get_ontology(ontology_uri).load(only_local=True, reload=True)

print("Verifying 'has_url' property:")
has_url_property = onto.search_one(iri="*has_url")
if has_url_property:
    is_functional = isinstance(has_url_property, FunctionalProperty)
    print(f"'has_url' is {'functional' if is_functional else 'non-functional'}")
else:
    print("'has_url' property not found in the ontology.")


with open("data/Mac.json", 'r') as f:
    data = [json.loads(line) for line in f]

with onto:
    for manual in data:

        categories = []
        previous_category = None
        for category_name in reversed(manual["Ancestors"]):
            category_id = category_name.replace(" ", "_")
            category = onto.search_one(iri="*" + category_id)
            if not category:
                category = onto.DeviceCategory(category_id)
                category.has_title = category_name 
                if previous_category:
                    category.is_subcategory_of.append(previous_category)
            categories.append(category)
            previous_category = category

        # Create Item instance
        item_id = manual["Category"].replace(" ", "_")
        item = onto.search_one(iri="*" + item_id)
        if not item:
            item = onto.Item(item_id)
            item.has_title = manual["Category"] 
            item.belongs_to_category = [categories[-1]]
            item.has_url = manual["Url"] 

        procedure_id = f"Procedure_{manual['Guidid']}"
        procedure = onto.search_one(iri="*" + procedure_id)
        if not procedure:
            procedure = onto.Procedure(procedure_id)
            procedure.has_title = manual["Title"] 
            procedure.has_url = manual["Url"]  
            procedure.has_guidid = manual["Guidid"] 
            procedure.part_of = [item]

        tools = []
        for tool_data in manual["Toolbox"]:
            tool_name = tool_data["Name"].replace(" ", "_")
            tool = onto.search_one(iri="*" + tool_name)
            if not tool:
                tool = onto.Tool(tool_name)
                tool.has_title = tool_data["Name"] 
                tool.has_url = tool_data["Url"] 
                tool.has_thumbnail = tool_data["Thumbnail"] 
            tools.append(tool)
        procedure.uses_tool = tools

        steps = []
        for step_data in manual["Steps"]:
            step_id = f"Step_{step_data['StepId']}"
            step = onto.search_one(iri="*" + step_id)
            if not step:
                step = onto.Step(step_id)
                step.has_order = step_data["Order"] 
                step.has_stepid = step_data["StepId"] 
                step.has_description = step_data["Text_raw"] 
                procedure.consists_of.append(step)

            # Create Action instances and associate with step
            for action_data in step_data.get("Removal_verbs", []):
                action_name = action_data["name"].replace(" ", "_")
                action = onto.search_one(iri="*" + action_name)
                if not action:
                    action = onto.Action(action_name)
                    action.has_title = action_data["name"] 
                step.has_action.append(action)

            # Create Part instances and associate with step
            for part_name in step_data.get("Word_level_parts_clean", []):
                part_id = part_name.replace(" ", "_")
                part = onto.search_one(iri="*" + part_id)
                if not part:
                    part = onto.Part(part_id)
                    part.has_title = part_name 
                step.involves_part.append(part)

            # Associate tools with step
            for tool_name in step_data.get("Tools_annotated", []):
                if tool_name != "NA":
                    tool = onto.search_one(has_title=tool_name)
                    if not tool:
                        tool = onto.Tool(tool_name.replace(" ", "_"))
                        tool.has_title = tool_name 
                    step.uses_tool.append(tool)

            # Associate images with step
            for image_url in step_data.get("Images", []):
                image_id = image_url.split('/')[-1].split('.')[0]
                image = onto.search_one(iri="*" + image_id)
                if not image:
                    image = onto.Image(image_id)
                    image.has_url = image_url 
                step.has_image.append(image)


    onto.save(file="ifixit_ontology.owl", format="rdfxml")