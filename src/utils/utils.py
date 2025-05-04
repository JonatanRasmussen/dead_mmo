from typing import Any, List, Type


class Utils:
    @staticmethod
    def load_collection(class_with_methods: Type[Any]) -> List[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]
