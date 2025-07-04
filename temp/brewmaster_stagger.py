
# EXPERIMENTAL: MOVE THIS LATER
class BrewmasterStagger:
    def __init__(self) -> None:
        self.stagger_duration: int = 10000
        self.amount: float = 0.0
        self.last_updated: int = 0

    def update(self, new_timestamp: int) -> float:
        time_elapsed = new_timestamp - self.last_updated
        ratio_of_total_duration = time_elapsed / self.stagger_duration
        assert ratio_of_total_duration <= 1.0  # For now, let's assume this is always true
        amount_consumed_since_last_update = self.amount * ratio_of_total_duration
        self.amount -= amount_consumed_since_last_update
        self.last_updated = new_timestamp
        return amount_consumed_since_last_update

    def add_amount(self, added_amount: float, new_timestamp: int) -> float:
        amount_consumed_since_last_update = self.update(new_timestamp)
        self.amount += added_amount
        return amount_consumed_since_last_update

stagger = BrewmasterStagger()
total_consumed_amount = 0.0

timestamp = 1000
amount_to_add = 50.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 6000
amount_to_add = 25.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 16000
amount_to_add = 50.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 19000
amount_to_add = 400.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 23000
amount_to_add = 300.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 25000
amount_to_add = 500.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

timestamp = 35000
amount_to_add = 0.0
total_consumed_amount += stagger.add_amount(amount_to_add, timestamp)
print(stagger.amount)

print(total_consumed_amount)