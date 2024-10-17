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
    class subclass_of(ObjectProperty):
        """Defines a subclass relationship among Items."""
        domain = [Item]
        range = [DeviceCategory]

    class consists_of(ObjectProperty):
        """Procedure consists of steps."""
        domain = [Procedure]
        range = [Step]

    class uses_tool(ObjectProperty):
        """Associates tools with Procedures and Steps."""
        domain = [Procedure | Step]
        range = [Tool]

    class involves_part(ObjectProperty):
        """Step involves part."""
        domain = [Step]
        range = [Part]

    class action(ObjectProperty):
        """Step has an action."""
        domain = [Step]
        range = [Action]

    class image(ObjectProperty):
        """Associates images with items or steps."""
        domain = [Item | Step]
        range = [Image]

    class part_of(ObjectProperty):
        """Defines a part-of relationship."""
        domain = [Item | Part | Procedure]
        range = [Item]

    class subcategory_of(ObjectProperty):
        """Defines the category hierarchy."""
        domain = [DeviceCategory]
        range = [DeviceCategory]

    class belongs_to_category(ObjectProperty):
        """Links item to its device category."""
        domain = [Item]
        range = [DeviceCategory]

    class subprocedure(ObjectProperty):
        """Links a Procedure to its sub-procedures."""
        domain = [Procedure]
        range = [Procedure]

    # Data Properties
    class title(DataProperty, FunctionalProperty):
        """Title or name."""
        domain = [Thing]
        range = [str]

    class description(DataProperty, FunctionalProperty):
        """Text description."""
        domain = [Procedure | Step| Action]
        range = [str]

    class order(DataProperty, FunctionalProperty):
        """Order number in a sequence."""
        domain = [Step]
        range = [int]

    class url(DataProperty, FunctionalProperty):
        """URL link."""
        domain = [Item | Tool | Procedure | Image]
        range = [str]

    class thumbnail(DataProperty, FunctionalProperty):
        """Thumbnail image URL."""
        domain = [Tool | Image]
        range = [str]

    class guidid(DataProperty, FunctionalProperty):
        """Unique guide ID."""
        domain = [Procedure]
        range = [int]

    class stepid(DataProperty, FunctionalProperty):
        """Unique step ID."""
        domain = [Step]
        range = [int]
    
    class involved_in_step(ObjectProperty): pass
    class used_in(ObjectProperty): pass
    class in_procedure(ObjectProperty): pass

    rule1 = Imp()
    rule1.set_as_rule("""Step(?s) ^ involves_part(?s, ?p) -> Part(?p) ^ involved_in_step(?p, ?s)""")

    rule2 = Imp()
    rule2.set_as_rule("""Step(?s) ^ uses_tool(?s, ?t) -> Tool(?t) ^ used_in(?t, ?s)""")

    rule3 = Imp()
    rule3.set_as_rule("""Procedure(?p) ^ uses_tool(?p, ?t) -> Tool(?t) ^ used_in(?t, ?p)""")

    rule4 = Imp()
    rule4.set_as_rule("""Procedure(?p) ^ consists_of(?p, ?s) -> Step(?s) ^ in_procedure(?s, ?p)""")

    rule5 = Imp()
    rule5.set_as_rule("""Step(?s) ^ involves_part(?s, ?p) ^ part_of(?p, ?i) -> Item(?i) ^ part_of(?s, ?i)""")

    # SWRL rules for transitive properties
    rule6 = Imp()
    rule6.set_as_rule("""Item(?x) ^ subclass_of(?x, ?y) ^ subclass_of(?y, ?z) -> subclass_of(?x, ?z)""")

    rule7 = Imp()
    rule7.set_as_rule("""Item(?x) ^ part_of(?x, ?y) ^ part_of(?y, ?z) -> part_of(?x, ?z)""")

    rule8 = Imp()
    rule8.set_as_rule("""DeviceCategory(?x) ^ subcategory_of(?x, ?y) ^ subcategory_of(?y, ?z) -> subcategory_of(?x, ?z)""")

    rule9 = Imp()
    rule9.set_as_rule("""Procedure(?x) ^ subprocedure(?x, ?y) ^ subprocedure(?y, ?z) -> subprocedure(?x, ?z)""")

# Save the ontology to a file
onto.save(file="ifixit_ontology.owl", format="rdfxml")
