from owlready2 import *

onto = get_ontology("http://example.org/ifixit.owl")

with onto:

    class Item(Thing):
        """Represents the device being repaired."""
        pass

    class Part(Thing):
        """Represents a component or part of an item."""
        pass

    class Tool(Thing):
        """Represents a tool used in repair procedures."""
        pass

    class Procedure(Thing):
        """Represents a repair procedure."""
        pass

    class Step(Thing):
        """Represents a single step in a procedure."""
        pass

    class Image(Thing):
        """Represents an image associated with a step or item."""
        pass

    class Action(Thing):
        """Represents an action performed in a step (from Removal_verbs)."""
        pass

    class DeviceCategory(Thing):
        """Represents a category in the device hierarchy."""
        pass

    # Object Properties

    class is_subclass_of(ObjectProperty, TransitiveProperty):
        """Defines a transitive subclass relationship among Items."""
        domain = [Item]
        range = [Item]

    class consists_of(ObjectProperty):
        """Procedure consists of steps."""
        domain = [Procedure]
        range = [Step]

    class uses_tool(ObjectProperty):
        """Associates tools with Procedures and Steps."""
        domain = [Procedure, Step]
        range = [Tool]

    class involves_part(ObjectProperty):
        """Step involves part."""
        domain = [Step]
        range = [Part]

    class has_action(ObjectProperty):
        """Step has an action."""
        domain = [Step]
        range = [Action]

    class has_image(ObjectProperty):
        """Associates images with items or steps."""
        domain = [Item, Step]
        range = [Image]

    class part_of(ObjectProperty, TransitiveProperty):
        """Defines a transitive part-of relationship."""
        domain = [Item, Part, Procedure]
        range = [Item]

    class is_subcategory_of(ObjectProperty, TransitiveProperty):
        """Defines the category hierarchy."""
        domain = [DeviceCategory]
        range = [DeviceCategory]

    class belongs_to_category(ObjectProperty):
        """Links item to its device category."""
        domain = [Item]
        range = [DeviceCategory]

    class has_subprocedure(ObjectProperty):
        """Links a Procedure to its sub-procedures."""
        domain = [Procedure]
        range = [Procedure]

    # Data Properties
    class has_title(DataProperty, FunctionalProperty):
        """Title or name."""
        domain = [Thing]
        range = [str]

    class has_description(DataProperty, FunctionalProperty):
        """Text description."""
        domain = [Procedure, Step, Action]
        range = [str]

    class has_order(DataProperty, FunctionalProperty):
        """Order number in a sequence."""
        domain = [Step]
        range = [int]

    class has_url(DataProperty, FunctionalProperty):
        """URL link."""
        domain = [Item, Tool, Procedure, Image]
        range = [str]

    class has_thumbnail(DataProperty, FunctionalProperty):
        """Thumbnail image URL."""
        domain = [Tool, Image]
        range = [str]

    class has_guidid(DataProperty, FunctionalProperty):
        """Unique guide ID."""
        domain = [Procedure]
        range = [int]

    class has_stepid(DataProperty, FunctionalProperty):
        """Unique step ID."""
        domain = [Step]
        range = [int]

# Save the ontology to a file
onto.save(file="ifixit_ontology.owl", format="rdfxml")
