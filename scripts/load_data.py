import json
from owlready2 import *
import os
from pathlib import Path
from tqdm import tqdm  # Import tqdm

# Get the absolute path to the ontology file
ontology_path = Path("ifixit_ontology.owl").resolve()
print("Ontology absolute path:", ontology_path)

if not ontology_path.is_file():
    print("Ontology file not found at:", ontology_path)
    exit(1)

ontology_uri = ontology_path.as_uri()
print("Ontology URI:", ontology_uri)

onto = get_ontology(ontology_uri).load(only_local=True, reload=True)

# Verify 'has_url' property
print("Verifying 'has_url' property:")
has_url_property = onto.search_one(iri="*has_url")
if has_url_property:
    is_functional = FunctionalProperty in has_url_property.is_a
    print(f"'has_url' is {'functional' if is_functional else 'non-functional'}")
else:
    print("'has_url' property not found in the ontology.")
    
def sanitize_id(s):
    if s:
        return s.replace('"', '').replace("'", '').replace(" ", "_").replace("&", "and").replace("<", "").replace(">", "").replace("/", "_")
    return s

# Open the sample data
with open("data/Mac.json", 'r') as f:
    data = [json.loads(line) for line in f][:100]

with onto:
    # Wrap the data loop with tqdm
    for manual in tqdm(data, desc="Processing manuals"):
        # Create DeviceCategory instances
        categories = []
        previous_category = None
        for category_name in reversed(manual["Ancestors"]):
            if not category_name:
                continue  # Skip if category_name is None or empty
            category_id = sanitize_id(category_name)
            category = onto.search_one(iri="*" + category_id)
            if not category:
                category = onto.DeviceCategory(category_id)
                category.title = category_name
                if previous_category:
                    category.subcategory_of.append(previous_category)
            categories.append(category)
            previous_category = category

        # Create Item instance
        item_id = sanitize_id(manual["Category"])
        item = onto.search_one(iri="*" + item_id)
        if not item:
            item = onto.Item(item_id)
            item.title = manual["Category"]
            item.belongs_to_category = [categories[-1]]
            item.url = manual["Url"]
            # Attempt to establish subclass_of relationships based on categories
            if len(categories) > 1:
                # The immediate parent category
                parent_category = categories[-2]
                # Find or create parent item
                parent_item_id = parent_category.name
                parent_item = onto.search_one(iri="*" + parent_item_id)
                if not parent_item:
                    parent_item = onto.Item(parent_item_id)
                    parent_item.title = parent_category.title[0]
                # Establish subclass_of relationship
                item.subclass_of.append(parent_item)

        # Create Procedure instance
        procedure_id = f"Procedure_{manual['Guidid']}"
        procedure = onto.search_one(iri="*" + procedure_id)
        if not procedure:
            procedure = onto.Procedure(procedure_id)
            procedure.title = manual["Title"]
            procedure.url = manual["Url"]
            procedure.guidid = manual["Guidid"]
            procedure.part_of = [item]

        # Create Tool instances and associate with procedure
        tools = []
        for tool_data in manual["Toolbox"]:
            tool_name = tool_data["Name"]
            if not tool_name:
                continue  # Skip if tool_name is None or empty
            tool_name = tool_name.strip().lower()
            tool_name_clean = sanitize_id(tool_name)
            tool = onto.search_one(iri="*" + tool_name_clean)
            if not tool:
                tool = onto.Tool(tool_name_clean)
                tool.title = tool_name
                tool.url = tool_data["Url"]
                tool.thumbnail = tool_data["Thumbnail"]
            tools.append(tool)
        procedure.uses_tool = tools

        # Create Step instances and associate with procedure
        steps = []
        # Collect tools used in steps to check later
        tools_used_in_steps = set()
        for step_data in tqdm(manual["Steps"], desc="Processing steps", leave=False):
            step_id = f"Step_{step_data['StepId']}"
            step = onto.search_one(iri="*" + step_id)
            if not step:
                step = onto.Step(step_id)
                step.order = step_data["Order"]
                step.stepid = step_data["StepId"]
                step.description = step_data["Text_raw"]
                procedure.consists_of.append(step)

            # Create Action instances and associate with step
            for action_data in step_data.get("Removal_verbs", []):
                action_name = action_data.get("name")
                if not action_name:
                    continue  # Skip if action_name is None or empty
                action_name_clean = sanitize_id(action_name)
                action = onto.search_one(iri="*" + action_name_clean)
                if not action:
                    action = onto.Action(action_name_clean)
                    action.title = action_name
                step.action.append(action)

            # Create Part instances and associate with step
            for part_name in step_data.get("Word_level_parts_clean", []):
                if not part_name:
                    continue  # Skip if part_name is None or empty
                part_id = sanitize_id(part_name)
                part = onto.search_one(iri="*" + part_id)
                if not part:
                    part = onto.Part(part_id)
                    part.title = part_name
                step.involves_part.append(part)
                # Establish part_of relationship between Part and Item
                if item is not None and part is not None:
                    part.part_of.append(item)

            # Associate tools with step
            for tool_name in step_data.get("Tools_annotated", []):
                if tool_name and tool_name != "NA":
                    tool_name = tool_name.strip().lower()
                    tool_name_clean = sanitize_id(tool_name)
                    tool = onto.search_one(iri="*" + tool_name_clean)
                    if not tool:
                        tool = onto.Tool(tool_name_clean)
                        tool.title = tool_name
                    step.uses_tool.append(tool)
                    tools_used_in_steps.add(tool)

            # Associate images with step
            for image_url in step_data.get("Images", []):
                if not image_url:
                    continue  # Skip if image_url is None or empty
                image_id = sanitize_id(image_url.split('/')[-1].split('.')[0])
                image = onto.search_one(iri="*" + image_id)
                if not image:
                    image = onto.Image(image_id)
                    image.url = image_url
                step.image.append(image)

        # After processing steps, check if all tools used in steps are in the procedure's toolbox
        tools_in_toolbox = set(procedure.uses_tool)
        missing_tools = tools_used_in_steps - tools_in_toolbox
        if missing_tools:
            print(f"\nWarning: Procedure '{procedure.title}' (ID: {procedure_id}) is missing the following tools in its toolbox:")
            for tool in missing_tools:
                print(f" - Tool: {tool.title} (ID: {tool.name})")
            # Automatically add missing tools to procedure's toolbox
            procedure.uses_tool.extend(missing_tools)

    # Save the updated ontology
    onto.save(file="ifixit_ontology.owl", format="rdfxml")