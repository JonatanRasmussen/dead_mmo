

class TestA:

    def __init__(self, hey_a: str) -> None:
        self.hey_a = hey_a

    def heya(self) -> str:
        return self.hey_a

class TestB(TestA):

    def __init__(self, hey_a: str, hey_b: str) -> None:
        super().__init__(hey_a)
        self.hey_b = hey_b

    def heya(self) -> str:
        return self.hey_a + self.hey_b

if __name__ == "__main__":
    my_test = TestB("Concat", "This")
    print(my_test.heya())  #"ConcatThis"