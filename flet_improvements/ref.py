__all__ = ['T', 'Ref']

from flet.ref import Ref as OriginalRef, T as OriginalT
from typing import Generic, Any


class Ref(OriginalRef[OriginalT]):
    def __call__(self, **kwds: Any) -> Any:
        for key, val in kwds:
            setattr(self._current, key, val)
        
        return self._current
