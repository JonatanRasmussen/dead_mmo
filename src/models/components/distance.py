

class Distance(float):
    def __new__(cls, value: float) -> 'Distance':
        return super().__new__(cls, value)

    def __add__(self, other: float) -> 'Distance':
        return Distance(super().__add__(other))

    def __sub__(self, other: float) -> 'Distance':
        return Distance(super().__sub__(other))

    def __mul__(self, other: float) -> 'Distance':
        return Distance(super().__mul__(other))

    def __truediv__(self, other: float) -> 'Distance':
        return Distance(super().__truediv__(other))