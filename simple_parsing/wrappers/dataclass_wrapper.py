import dataclasses
import enum
import logging
from typing import *
import argparse
import enum
from .. import docstring, utils
from ..utils import Dataclass, DataclassType

from .field_wrapper import FieldWrapper
logger = logging.getLogger(__name__)

@dataclasses.dataclass
class DataclassWrapper(Generic[Dataclass]):
    dataclass: Type[Dataclass]
    attribute_name: str
    fields: List[FieldWrapper] = dataclasses.field(default_factory=list, repr=False)
    _destinations: List[str] = dataclasses.field(default_factory=list)
    _multiple: bool = False
    _required: bool = False
    _explicit: bool = False
    _prefix: str = ""
    _children: List["DataclassWrapper"] = dataclasses.field(default_factory=list, repr=False)
    _parent: Optional["DataclassWrapper"] = dataclasses.field(default=None, repr=False)

    _field: Optional[dataclasses.Field] = None
    _default: Optional[Dataclass] = None
    def __post_init__(self):
        self.destinations
        for field in dataclasses.fields(self.dataclass):
            if dataclasses.is_dataclass(field.type):
                # handle a nested dataclass.
                dataclass = field.type
                attribute_name = field.name
                child_wrapper = DataclassWrapper(dataclass, attribute_name, _parent=self)
                child_wrapper._field = field
                # TODO: correctly handle the default value for a Dataclass attribute.
                child_wrapper.prefix = self.prefix                 
                self._children.append(child_wrapper)
                
            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """)
            else:
                # regular field.
                field_wrapper = FieldWrapper(field, parent=self)
                self.fields.append(field_wrapper)

    @property
    def default(self) -> Optional[Dataclass]:
        if self._default:
            return self._default
        if self._field is None:
            return None
        
        assert self._parent is not None
        if self._field.default is not dataclasses.MISSING:
            self._default = self._field.default
        elif self._field.default_factory is not dataclasses.MISSING: # type: ignore
            self._default = self._field.default_factory() # type: ignore
        return self._default
        
    @property
    def description(self) -> Optional[str]:
        if self._parent and self._field:    
            doc = docstring.get_attribute_docstring(self._parent.dataclass, self._field.name)            
            if doc is not None:
                if doc.docstring_below:
                    return doc.docstring_below
                elif doc.comment_above:
                    return doc.comment_above
                elif doc.comment_inline:
                    return doc.comment_inline
        return self.dataclass.__doc__

    @property
    def title(self) -> str:
        names_string = f""" [{', '.join(f"'{dest}'" for dest in self.destinations)}]"""
        title = self.dataclass.__qualname__ + names_string
        return title

    def add_arguments(self, parser: argparse.ArgumentParser):
        from ..parsing import ArgumentParser
        parser : ArgumentParser = parser # type: ignore
        
       
        group = parser.add_argument_group(
            title=self.title,
            description=self.description
        )

        if self.default:
            logger.debug(f"The nested dataclass had a default value of {self.default}")
            for wrapped_field in self.fields:
                default_field_value = getattr(self.default, wrapped_field.name, None)
                if default_field_value is not None:
                    logger.debug(f"wrapped field at {wrapped_field.dest} has a default value of {wrapped_field.default}")
                    wrapped_field.default = default_field_value

        for wrapped_field in self.fields:
            if wrapped_field.arg_options: 
                logger.debug(f"Adding argument for field '{wrapped_field.name}'")
                logger.debug(f"Arg options for field '{wrapped_field.name}': {wrapped_field.arg_options}")
                # TODO: CustomAction isn't very easy to debug, and is not working. Maybe look into that. Simulating it for now.
                # group.add_argument(wrapped_field.option_strings[0], action=CustomAction, field=wrapped_field, **wrapped_field.arg_options)
                group.add_argument(wrapped_field.option_strings[0], dest=wrapped_field.dest, **wrapped_field.arg_options)

    @property
    def prefix(self) -> str:
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        self._prefix = value
        for child_wrapper in self._children:
            child_wrapper.prefix = value

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for child_wrapper in self._children:
            child_wrapper.required = value

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        for wrapped_field in self.fields:
            wrapped_field.multiple = value
        for child_wrapper in self._children:
            child_wrapper.multiple = value
        self._multiple = value

    @property
    def descendants(self):
        for child in self._children:
            yield child
            yield from child.descendants

    @property
    def dest(self):
        lineage = []
        parent = self._parent
        while parent is not None:
            lineage.append(parent.attribute_name)
            parent = parent._parent
        lineage = list(reversed(lineage))
        lineage.append(self.attribute_name)
        _dest = ".".join(lineage)
        logger.debug(f"getting dest, returning {_dest}")
        return _dest
           

    @property
    def destinations(self) -> List[str]:
        # logger.debug(f"getting destinations of {self}")
        # logger.debug(f"self._destinations is {self._destinations}")
        # logger.debug(f"Parent is {self._parent}")
        if not self._destinations:
            if self._parent:
                self._destinations = [f"{d}.{self.attribute_name}" for d in self._parent.destinations]
            else:
                self._destinations = [self.attribute_name]
        # logger.debug(f"returning {self._destinations}")
        return self._destinations

    @property
    def explicit(self) -> bool:
        return self._explicit

    @explicit.setter
    def explicit(self, value: bool):
        if self._explicit != value:
            pass
        self._explicit = value



    def merge(self, other: "DataclassWrapper"):
        """Absorb all the relevant attributes from another wrapper.
        Args:
            other (DataclassWrapper): Another instance to absorb into this one.
        """
        logger.debug(f"merging \n{self}\n with \n{other}")
        self.destinations.extend(other.destinations)
        for child, other_child in zip(self.descendants, other.descendants):
            child.merge(other_child)
        self.multiple = True

    def instantiate_dataclass(self, constructor_args: Dict[str, Any]) -> Dataclass:
        """
        Creates an instance of the dataclass using the given dict of constructor arguments, including nested dataclasses if present.
        """
        logger.debug(f"args dict: {constructor_args}")
        
        dataclass = self.dataclass
        logger.debug(f"Constructor arguments for dataclass {dataclass}: {constructor_args}")
        instance: T = dataclass(**constructor_args) #type: ignore
        return instance
