__all__ = ['ControlType', 'NodeAlreadyInPageError', 'NodeContainerType', 'NodeContainer', 'NC', 'ContainerNotProvidedError', 'ContainerTypeMismatchError', 'SecondAssignmentAttemptForASingleValueContainerError', 'SingleValueContainersValueWasInitiallyDefinedError', 'ContainersHasAPredefinedDictValueError', 'ContainersHasAPredefinedValueOfUnsupportedTypeError', 'UnsupportedEntityClass', 'UnsupportedEntityType', 'NodeApplier', 'NodeAlreadyConstructedToPageError', 'Node', 'EntityNode', 'ENode']


from enum import Enum
from flet import *
from typing import List, Type, Tuple, Dict, Set, Union, Optional, Any, Hashable, Callable, Union
from cengal.code_flow_control.python_bytecode_manipulator import get_code, code_param_names, CodeParamNames


def find_entity_arguments_description(entity: Callable) -> Tuple[Set[str], Sequence[str], Sequence[str], Sequence[str]]:
    init_code = get_code(entity)
    cpn: CodeParamNames = code_param_names(init_code)
    positional = cpn.positional
    positional_only = cpn.positional_only
    keyword_only = cpn.keyword_only
    all: Set[str] = set(positional) | set(positional_only) | set(keyword_only)
    return all, positional, positional_only, keyword_only


def find_entity_arguments_positions(positional: Sequence[str], keyword_only: Sequence[str]) -> Dict[str, Optional[int]]:
    positions: Dict[str, Optional[int]] = dict()
    for index, name in enumerate(positional):
        positions[name] = index
    
    for index, name in enumerate(keyword_only):
        positions[name] = None

    return positions


def find_arg_position_and_value(arg_name: str, positions: Dict[str, Optional[int]], args: Tuple, kwargs: Dict) -> Tuple[bool, bool, Optional[int], Any]:
    found_in_positions: bool = False
    found_in_all_args: bool = False
    pos = None
    value = None

    original_arg_pos: Optional[int] = None
    try:
        original_arg_pos = positions[arg_name]
        found_in_positions = True
    except KeyError:
        pass
    
    if not found_in_positions:
        return found_in_positions, found_in_all_args, pos, value
    
    if original_arg_pos is None:
        found_in_args = False
    else:
        if len(args) > original_arg_pos:
            found_in_args = True
        else:
            found_in_args = False
    
    if found_in_args:
        pos = original_arg_pos
        value = args[pos]
        found_in_all_args = True
    else:
        try:
            value = kwargs.get(arg_name, None)
            found_in_all_args = True
        except KeyError:
            pass
    
    return found_in_positions, found_in_all_args, pos, value


def is_content_or_controls_in_args(all_arg_names) -> Tuple[bool, bool]:
    content_present: bool = 'content' in all_arg_names
    controls_present: bool = 'controls' in all_arg_names
    return content_present, controls_present


ControlType = Type[Control]


class NodeAlreadyInPageError(Exception):
    pass


class NodeContainerType(Enum):
    single = 0
    sequence = 1


class NodeContainer:
    def __init__(self, name: str, container_type: NodeContainerType = NodeContainerType.single) -> None:
        self.name: str = name
        self.container_type: NodeContainerType = container_type


NC = NodeContainer


class ContainerNotProvidedError(Exception):
    pass


class ContainerTypeMismatchError(Exception):
    pass


class SecondAssignmentAttemptForASingleValueContainerError(Exception):
    pass


class SingleValueContainersValueWasInitiallyDefinedError(Exception):
    pass


class ContainersHasAPredefinedDictValueError(Exception):
    pass


class ContainersHasAPredefinedValueOfUnsupportedTypeError(Exception):
    pass


class EntityShouldBeMade:
    def __init__(self, container: Optional['NodeContainer'], entity: ControlType, args = None, kwargs = None) -> None:
        self.container: Optional['NodeContainer'] = container
        self.entity: ControlType = entity
        self.args: Tuple = tuple() if args is None else args
        self.kwargs: Dict = dict() if kwargs is None else kwargs
        self.result_args: Tuple = list(args)
        self.result_kwargs: Dict = dict(kwargs)
        self.components: List['EntityShouldBeMade'] = list()
        self.constructed: bool = False
        self.constructed_entity: Optional[Control] = None
    
    def add_child(self, child: 'EntityShouldBeMade'):
        self.components.append(child)
    
    def construct(self):
        if self.constructed:
            return
        
        for child in self.components:
            child.construct()
        
        containers_dict: Dict[str, Union[EntityShouldBeMade, List[EntityShouldBeMade]]] = dict()
        contaiter_types: Dict[str, NodeContainerType] = {
            'content': NodeContainerType.single,
            'controls': NodeContainerType.sequence,
        }
        all_arg_names, positional_arg_names, positional_only_arg_names, keyword_only_arg_names = find_entity_arguments_description(self.entity.__init__)
        args_positions = find_entity_arguments_positions(positional_arg_names, keyword_only_arg_names)
        content_present, controls_present = is_content_or_controls_in_args(all_arg_names)
        if content_present and (not controls_present):
            default_container_name = 'content'
            default_container_type = NodeContainerType.single
        elif (not content_present) and controls_present:
            default_container_name = 'controls'
            default_container_type = NodeContainerType.sequence
        else:
            default_container_name = None
            default_container_type = None
        
        for child in self.components:
            child_container: NodeContainer = child.container
            if child_container is None:
                if default_container_name is None:
                    raise ContainerNotProvidedError(f'Contaiter for a child <{child.entity}> class in parent <{self.entity}> class was not provided')

                child_container_name = default_container_name
                child_container_type = default_container_type
            else:
                child_container_name = child_container.name
                child_container_type = child_container.container_type
                if child_container_name not in contaiter_types:
                    contaiter_types[child_container_name] = child_container_type
                
                if child_container_type != contaiter_types[child_container_name]:
                    raise ContainerTypeMismatchError(f'<{self.entity}> was prepared for a container <{child_container_name}> with type <{contaiter_types[child_container_name]}> by one of the previous children, but child <{child.entity}> ties to use that container as a <{child_container_type}> type')
            
            if child_container_name not in containers_dict:
                if NodeContainerType.sequence == child_container_type:
                    containers_dict[child_container_name] = list()
            
            if (NodeContainerType.single == child_container_type) and (child_container_name in containers_dict):
                raise SecondAssignmentAttemptForASingleValueContainerError(f'<{child.entity}> can\'t be assigned to <{child_container_name}> container of the <{self.entity}> class')
            
            if NodeContainerType.single == child_container_type:
                containers_dict[child_container_name] = child
            elif NodeContainerType.sequence == child_container_type:
                containers_dict[child_container_name].append(child)
            
        for container_name, child_or_children in containers_dict.items():
            container_type = contaiter_types[container_name]
            found_in_positions, found_in_all_args, pos, value = find_arg_position_and_value(container_name, args_positions, self.args, self.kwargs)
            value_already_defined: bool = False
            if pos is None:
                if found_in_all_args:
                    value_already_defined = True
                else:
                    value_already_defined = False
            else:
                value_already_defined = True
            
            if NodeContainerType.single == container_type:
                result_child_or_children = child_or_children.constructed_entity
            else:
                result_child_or_children = list([child.constructed_entity for child in child_or_children])

            if value_already_defined:
                if value is None:
                    value = result_child_or_children
                else:
                    if NodeContainerType.single == container_type:
                        raise SingleValueContainersValueWasInitiallyDefinedError(f'Entity of <{self.entity}> class has a defined value for it\'s single-value <{container_name}> container. Can not assign other child to this predefined container.')
                    else:
                        if isinstance(value, list):
                            value.extend(result_child_or_children)
                        elif isinstance(value, (set, tuple)):
                            value = list(value)
                            value.extend(result_child_or_children)
                        elif isinstance(value, dict):
                            raise ContainersHasAPredefinedDictValueError(f'Entity of <{self.entity}> class has a predefined <{container_name}> value. Can not update Dict with a Sequence of children')
                        else:
                            raise ContainersHasAPredefinedValueOfUnsupportedTypeError(f'Entity of <{self.entity}> class has a predefined <{container_name}> value of unsupported <{type(value)}> type. Can not update it with a Sequence of children')
            else:
                value = result_child_or_children
            
            if pos is None:
                self.result_kwargs[container_name] = value
            else:
                self.result_args[pos] = value
        
        self.constructed_entity = self.entity(*self.result_args, **self.result_kwargs)
        self.constructed = True
    
    def reconstruct(self):
        self.result_args = list(self.args)
        self.result_kwargs = dict(self.kwargs)
        self.constructed = False
        self.constructed_entity = None
        self.construct()


class UnsupportedEntityClass(Exception):
    pass


class UnsupportedEntityType(Exception):
    pass


class NodeApplier:
    def __init__(self, node: 'Node', container: Optional['NodeContainer'] = None) -> None:
        self.node: 'Node' = node
        self.container: Optional['NodeContainer'] = container

    def __call__(self, entity: Union[ControlType, Control], *args, **kwargs) -> 'Node':
        if isinstance(entity, Control):
            entity_should_be_made: EntityShouldBeMade = EntityShouldBeMade(self.container, type(entity))
            entity_should_be_made.constructed_entity = entity
            entity_should_be_made.constructed = True
            self.node.register_entity_should_be_made(entity_should_be_made)
            node = Node(parent=self, entity_should_be_made=entity_should_be_made)
            node.constructed = True
            return node
        else:
            if isinstance(entity, type):
                if issubclass(entity, Control):
                    entity_should_be_made: EntityShouldBeMade = EntityShouldBeMade(self.container, entity, args, kwargs)
                    self.node.register_entity_should_be_made(entity_should_be_made)
                    return Node(parent=self, entity_should_be_made=entity_should_be_made)
                else:
                    raise UnsupportedEntityClass(f'Entity of <{entity}> class must be subclass of the <{Control}> class')
            else:
                raise UnsupportedEntityType(f'Entity of <{type(entity)}> class must be either an instance or a subclass of the <{Control}> class')
        

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise exc_val.with_traceback(exc_tb)


class NodeAlreadyConstructedToPageError(Exception):
    pass


class Node:
    def __init__(self, parent: Optional[Union['Node', NodeApplier]] = None, entity_should_be_made: Optional[EntityShouldBeMade] = None, page: Optional[Page] = None) -> None:
        self.parent: Optional[Union['Node', NodeApplier]] = parent
        self.entity_should_be_made: Optional[EntityShouldBeMade] = entity_should_be_made
        self.page: Optional[Page] = page
        self.components: List[EntityShouldBeMade] = list()
        self._constructed_components: List[Control] = list()
        self.constructed: bool = False
        self.is_page_node: bool = None
        self.calculate_is_page_node()

    def __call__(self, container: Optional[NodeContainer] = None) -> NodeApplier:
        if self.constructed:
            raise NodeAlreadyConstructedToPageError
        
        return NodeApplier(self, container)

    def add_to_page(self, page: Page):
        if self.constructed:
            raise NodeAlreadyConstructedToPageError

        if self.page is None:
            self.page = page
            self.calculate_is_page_node()
        else:
            raise NodeAlreadyInPageError

    def remove_from_page(self):
        if self.constructed:
            raise NodeAlreadyConstructedToPageError

        self.page = None
        self.calculate_is_page_node()
    
    def calculate_is_page_node(self):
        if self.page is None:
            if self.entity_should_be_made is None:
                self.is_page_node = True
            else:
                self.is_page_node = False
        else:
            self.is_page_node = True
    
    def register_entity_should_be_made(self, entity_should_be_made: EntityShouldBeMade):
        if self.is_page_node:
            self.components.append(entity_should_be_made)
        else:
            self.entity_should_be_made.add_child(entity_should_be_made)
    
    def construct(self):
        if self.constructed:
            if self.is_page_node:
                return self._constructed_components
            else:
                return self.entity_should_be_made.constructed_entity
        
        if self.is_page_node:
            components = self.components
            for component in components:
                component.construct()
            
            self._constructed_components = list([component.constructed_entity for component in components])
            if self.page is not None:
                self.page.add(*self._constructed_components)
            
            self.constructed = True
            return self._constructed_components
        else:
            self.entity_should_be_made.construct()
            self.constructed = True
            return self.entity_should_be_made.constructed_entity
    
    def reconstruct(self):
        self._constructed_components = list()
        self.constructed = False
        self.construct()

    @property
    def item(self):
        result = None
        if self.is_page_node:
            result = self.page
        else:
            self.construct()
            result = self.entity_should_be_made.constructed_entity
        
        return result
    
    @property
    def constructed_components(self):
        return self._constructed_components
    
    @property
    def cc(self):
        return self._constructed_components

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.construct()
        if exc_val:
            raise exc_val.with_traceback(exc_tb)


class EntityNode(Node):
    def __init__(self, entity: Union[ControlType, Control], *args, **kwargs) -> None:
        super().__init__(entity_should_be_made=EntityShouldBeMade(None, entity, args, kwargs))


ENode = EntityNode
