"""Type stubs for resources.instance_manager.InstanceManager."""

from typing import Any, Optional, Dict, Iterator
from sims4.resources import Types


class InstanceManager:
    """Manages loaded tuning instances for a given resource type.

    The game creates one InstanceManager per resource type (TRAIT, BUFF,
    OBJECT, etc.) and loads XML tuning into it during startup.

    The key method for mod hooks:
        load_data_into_class_instances() -- called after XML is parsed
    """
    TYPE: Types
    _tuned_classes: Dict[int, Any]

    def load_data_into_class_instances(self) -> None: ...
    def get(self, tuning_id: int) -> Optional[Any]: ...

    @property
    def types(self) -> Dict[int, Any]: ...

    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
