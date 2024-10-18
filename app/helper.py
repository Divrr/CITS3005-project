from app.ontology import onto

def populate_facet_choices(form=None):
    # initialise counts
    category_counts = {}
    tool_counts = {}
    part_counts = {}

    # Build a mapping of category titles to category instances
    categories_by_title = {cat.title: cat for cat in onto.DeviceCategory.instances() if cat.title}

    # Build category hierarchy and initialise counts
    category_hierarchy = build_category_hierarchy(categories_by_title)

    # Calculate counts
    for procedure in onto.Procedure.instances():
        # Categories
        item = procedure.part_of[0] if procedure.part_of else None
        if item and item.belongs_to_category:
            for category in item.belongs_to_category:
                # Increment counts for the category and all its ancestors
                propagate_category_count(category, category_counts)
        # Tools
        for tool in procedure.uses_tool:
            tool_title = tool.title
            tool_counts[tool_title] = tool_counts.get(tool_title, 0) + 1
        # Parts
        parts_in_procedure = set(part for step in procedure.consists_of for part in step.involves_part)
        for part in parts_in_procedure:
            part_title = part.title
            part_counts[part_title] = part_counts.get(part_title, 0) + 1

    if form:
        # Populate categories with counts
        form.categories.choices = [
            (cat.title, f"{cat.title} ({category_counts.get(cat.title, 0)})")
            for cat in onto.DeviceCategory.instances() if cat.title
        ]

        # Populate tools with counts
        form.tools.choices = [
            (tool.title, f"{tool.title} ({tool_counts.get(tool.title, 0)})")
            for tool in onto.Tool.instances() if tool.title
        ]

        # Populate parts with counts
        form.parts.choices = [
            (part.title, f"{part.title} ({part_counts.get(part.title, 0)})")
            for part in onto.Part.instances() if part.title
        ]

    return category_hierarchy, category_counts

def propagate_category_count(category, category_counts):
    # Increment count for the category
    category_counts[category.title] = category_counts.get(category.title, 0) + 1
    # Recursively increment counts for parent categories
    for parent in category.subcategory_of:
        propagate_category_count(parent, category_counts)

def build_category_hierarchy(categories_by_title):
    # Find all top-level categories (categories without parents)
    hierarchy = {}
    for category in categories_by_title.values():
        if not category.subcategory_of:
            hierarchy[category.title] = build_subtree(category, categories_by_title)
    return hierarchy

def build_subtree(category, categories_by_title):
    subtree = {'category': category, 'subcategories': {}}
    for subcategory in categories_by_title.values():
        if category in subcategory.subcategory_of:
            subtree['subcategories'][subcategory.title] = build_subtree(subcategory, categories_by_title)
    return subtree


def get_all_subcategories(category):
    """Recursively get all subcategories of a given category."""
    subcategories = set()
    to_visit = [category]

    while to_visit:
        current = to_visit.pop()
        for subcat in onto.DeviceCategory.instances():
            if current in subcat.subcategory_of and subcat not in subcategories:
                subcategories.add(subcat)
                to_visit.append(subcat)
    return subcategories

def select_all_selected_category_titles(selected_categories):
    all_selected_category_titles = set()
    if selected_categories:
        for cat_title in selected_categories:
            category = onto.search_one(title=cat_title)
            if category:
                # Add the selected category itself
                all_selected_category_titles.add(category.title.lower())
                # Add its subcategories
                subcategories = get_all_subcategories(category)
                for subcat in subcategories:
                    all_selected_category_titles.add(subcat.title.lower())
            else:
                app.logger.warning(f"Category with title '{cat_title}' not found.")
    return all_selected_category_titles


def find_all_matching_procedures(query, selected_categories, selected_tools, selected_parts):
    matching_procedures = []
    all_selected_category_titles = set(selected_categories)
    # Find all procedures that match the query and selected facets

    for procedure in onto.Procedure.instances():
        # Filter by query
        if query and (not procedure.title or query not in procedure.title.lower()):
            continue

        # Filter by categories
        if selected_categories:
            item = procedure.part_of[0] if procedure.part_of else None
            if not item or not item.belongs_to_category:
                continue

            item_category_titles = {category.title.lower() for category in item.belongs_to_category}
            if not item_category_titles.intersection(all_selected_category_titles):
                continue

        # Filter by tools
        if selected_tools:
            procedure_tool_titles = set(tool.title for tool in procedure.uses_tool)
            if not set(selected_tools).issubset(procedure_tool_titles):
                continue

        # Filter by parts
        if selected_parts:
            # Extract parts involved in each step of the procedure
            parts_in_procedure = set(part.title for step in procedure.consists_of for part in step.involves_part)
            if not set(selected_parts).issubset(parts_in_procedure):
                continue

        matching_procedures.append(procedure)
    
    return matching_procedures