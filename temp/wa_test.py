'''
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Callable
import threading
import time
from enum import Enum

# ============= DATA MODELS =============
@dataclass
class CombatEvent:
    event_type: str
    source: str
    target: str
    value: int
    timestamp: float

class AlertType(Enum):
    SOUND = "sound"
    ICON = "icon"
    BAR = "bar"

# ============= OBSERVER PATTERN =============
class Observer(ABC):
    @abstractmethod
    def update(self, event: CombatEvent):
        pass

class AudioAlert(Observer):
    def __init__(self, name: str, sound_file: str):
        self.name = name
        self.sound_file = sound_file

    def update(self, event: CombatEvent):
        print(f"🔊 [{self.name}] Playing sound: {self.sound_file}")
        # In real implementation: pygame.mixer.Sound(self.sound_file).play()

class IconDisplay(Observer):
    def __init__(self, name: str, icon_path: str):
        self.name = name
        self.icon_path = icon_path
        self.active = False
        self.stacks = 0

    def update(self, event: CombatEvent):
        self.active = True
        self.stacks += 1
        print(f"🖼️  [{self.name}] Icon: {self.icon_path} | Stacks: {self.stacks}")

class ProgressBar(Observer):
    def __init__(self, name: str, max_value: int):
        self.name = name
        self.max_value = max_value
        self.current_value = 0

    def update(self, event: CombatEvent):
        self.current_value = min(self.current_value + event.value, self.max_value)
        percentage = (self.current_value / self.max_value) * 100
        ui_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
        print(f"📊 [{self.name}] {ui_bar} {percentage:.1f}%")

class Aura:
    def __init__(self, name: str, condition: Callable[[CombatEvent], bool]):
        self.name = name
        self.condition = condition
        self.observers: List[Observer] = []

    def attach(self, observer: Observer):
        self.observers.append(observer)

    def detach(self, observer: Observer):
        self.observers.remove(observer)

    def notify(self, event: CombatEvent):
        for observer in self.observers:
            observer.update(event)

    def process_event(self, event: CombatEvent):
        if self.condition(event):
            self.notify(event)

class CombatEventStream:
    def __init__(self):
        self.auras: List[Aura] = []

    def register_aura(self, aura_to_r: Aura):
        self.auras.append(aura_to_r)

    def process_event(self, event: CombatEvent):
        print(f"\n⚔️  Event: {event.event_type} | {event.source} → {event.target} ({event.value})")
        for an_aura in self.auras:
            an_aura.process_event(event)

# ============= USAGE =============
def demo_observer():
    print("=" * 60)
    print("OBSERVER PATTERN DEMO")
    print("=" * 60)

    stream = CombatEventStream()

    # Create aura for critical hits
    crit_aura = Aura(
        "Critical Hit Alert",
        lambda e: e.event_type == "DAMAGE" and e.value > 100
    )
    crit_aura.attach(AudioAlert("CritSound", "critical.mp3"))
    crit_aura.attach(IconDisplay("CritIcon", "crit.png"))

    # Create aura for low health
    health_aura = Aura(
        "Low Health Warning",
        lambda e: e.event_type == "DAMAGE" and e.target == "Player"
    )
    health_aura.attach(AudioAlert("DangerSound", "danger.mp3"))
    health_aura.attach(ProgressBar("HealthBar", 1000))

    stream.register_aura(crit_aura)
    stream.register_aura(health_aura)

    # Simulate events
    events = [
        CombatEvent("DAMAGE", "Player", "Enemy", 150, time.time()),
        CombatEvent("DAMAGE", "Enemy", "Player", 80, time.time()),
        CombatEvent("HEAL", "Player", "Player", 50, time.time()),
        CombatEvent("DAMAGE", "Player", "Enemy", 200, time.time()),
    ]

    for event in events:
        stream.process_event(event)
        time.sleep(0.5)



# ============= STRATEGY PATTERN =============
class TriggerStrategy(ABC):
    @abstractmethod
    def should_trigger(self, event: CombatEvent, context: Dict) -> bool:
        pass

class DamageThresholdTrigger(TriggerStrategy):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def should_trigger(self, event: CombatEvent, context: Dict) -> bool:
        return event.event_type == "DAMAGE" and event.value >= self.threshold

class CooldownTrigger(TriggerStrategy):
    def __init__(self, cooldown: float):
        self.cooldown = cooldown
        self.last_trigger = 0

    def should_trigger(self, event: CombatEvent, context: Dict) -> bool:
        current_time = event.timestamp
        if current_time - self.last_trigger >= self.cooldown:
            self.last_trigger = current_time
            return True
        return False

class StackCountTrigger(TriggerStrategy):
    def __init__(self, stack_threshold: int):
        self.stack_threshold = stack_threshold
        self.current_stacks = 0

    def should_trigger(self, event: CombatEvent, context: Dict) -> bool:
        if event.event_type == "BUFF_APPLIED":
            self.current_stacks += 1
        elif event.event_type == "BUFF_REMOVED":
            self.current_stacks = 0
        return self.current_stacks >= self.stack_threshold

class ComboTrigger(TriggerStrategy):
    """Triggers when multiple conditions are met"""
    def __init__(self, strategies: List[TriggerStrategy]):
        self.strategies = strategies

    def should_trigger(self, event: CombatEvent, context: Dict) -> bool:
        return all(strategy.should_trigger(event, context) for strategy in self.strategies)

class ActionStrategy(ABC):
    @abstractmethod
    def execute(self, event: CombatEvent):
        pass

class PlaySoundAction(ActionStrategy):
    def __init__(self, sound: str):
        self.sound = sound

    def execute(self, event: CombatEvent):
        print(f"🔊 Playing: {self.sound}")

class ShowIconAction(ActionStrategy):
    def __init__(self, icon: str, duration: float):
        self.icon = icon
        self.duration = duration

    def execute(self, event: CombatEvent):
        print(f"🖼️  Showing icon: {self.icon} for {self.duration}s")

class UpdateBarAction(ActionStrategy):
    def __init__(self, bar_name: str):
        self.bar_name = bar_name
        self.value = 0

    def execute(self, event: CombatEvent):
        self.value += event.value
        print(f"📊 {self.bar_name}: {self.value}")

class StrategyAura:
    def __init__(self, name: str, trigger: TriggerStrategy, actions: List[ActionStrategy]):
        self.name = name
        self.trigger = trigger
        self.actions = actions

    def process_event(self, event: CombatEvent, context: Dict):
        if self.trigger.should_trigger(event, context):
            print(f"✨ Aura triggered: {self.name}")
            for action in self.actions:
                action.execute(event)

def demo_strategy():
    print("\n" + "=" * 60)
    print("STRATEGY PATTERN DEMO")
    print("=" * 60)

    # Create aura with complex trigger
    combo_trigger = ComboTrigger([
        DamageThresholdTrigger(100),
        CooldownTrigger(2.0)
    ])

    big_hit_aura = StrategyAura(
        "Big Hit Alert",
        combo_trigger,
        [
            PlaySoundAction("bigHit.mp3"),
            ShowIconAction("explosion.png", 3.0),
            UpdateBarAction("DamageBar")
        ]
    )

    context = {}
    events = [
        CombatEvent("DAMAGE", "Player", "Enemy", 150, time.time()),
        CombatEvent("DAMAGE", "Player", "Enemy", 120, time.time() + 0.5),
        CombatEvent("DAMAGE", "Player", "Enemy", 200, time.time() + 2.5),
    ]

    for event in events:
        print(f"\n⚔️  Event: {event.event_type} | Value: {event.value}")
        big_hit_aura.process_event(event, context)
        time.sleep(0.3)


# ============= COMMAND PATTERN =============
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

class PlaySoundCommand(Command):
    def __init__(self, sound_file: str):
        self.sound_file = sound_file
        self.played = False

    def execute(self):
        print(f"🔊 Execute: Play {self.sound_file}")
        self.played = True

    def undo(self):
        if self.played:
            print(f"🔇 Undo: Stop {self.sound_file}")
            self.played = False

class ShowIconCommand(Command):
    def __init__(self, icon: str):
        self.icon = icon
        self.visible = False

    def execute(self):
        print(f"🖼️  Execute: Show {self.icon}")
        self.visible = True

    def undo(self):
        if self.visible:
            print(f"❌ Undo: Hide {self.icon}")
            self.visible = False

class UpdateProgressCommand(Command):
    def __init__(self, bar_name: str, delta: int):
        self.bar_name = bar_name
        self.delta = delta
        self.executed = False

    def execute(self):
        print(f"📊 Execute: {self.bar_name} +{self.delta}")
        self.executed = True

    def undo(self):
        if self.executed:
            print(f"↩️  Undo: {self.bar_name} -{self.delta}")
            self.executed = False

class CommandQueue:
    def __init__(self):
        self.commands: List[Command] = []
        self.history: List[Command] = []

    def add_command(self, command: Command):
        self.commands.append(command)

    def execute_all(self):
        while self.commands:
            command = self.commands.pop(0)
            command.execute()
            self.history.append(command)

    def undo_last(self):
        if self.history:
            command = self.history.pop()
            command.undo()

class CommandAura:
    def __init__(self, name: str, condition: Callable[[CombatEvent], bool]):
        self.name = name
        self.condition = condition
        self.command_queue = CommandQueue()

    def add_action(self, command: Command):
        self.command_queue.add_command(command)

    def process_event(self, event: CombatEvent):
        if self.condition(event):
            print(f"✨ Triggering: {self.name}")
            self.command_queue.execute_all()

def demo_command():
    print("\n" + "=" * 60)
    print("COMMAND PATTERN DEMO")
    print("=" * 60)

    an_aura = CommandAura(
        "Execute Phase",
        lambda e: e.event_type == "DAMAGE" and e.value > 150
    )

    # Queue up commands
    an_aura.add_action(PlaySoundCommand("execute.mp3"))
    an_aura.add_action(ShowIconCommand("skull.png"))
    an_aura.add_action(UpdateProgressCommand("ExecuteBar", 100))

    event = CombatEvent("DAMAGE", "Player", "Boss", 200, time.time())
    print(f"⚔️  Event: {event.event_type} | Value: {event.value}")
    an_aura.process_event(event)

    print("\n--- Undoing last action ---")
    an_aura.command_queue.undo_last()


# ============= BUILDER PATTERN =============
class AuraBuilder:
    def __init__(self, name: str):
        self.name = name
        self.triggers = []
        self.actions = []
        self.cooldown = 0
        self.duration = 0

    def when_damage_exceeds(self, threshold: int):
        self.triggers.append(lambda e: e.event_type == "DAMAGE" and e.value > threshold)
        return self

    def when_event_type(self, event_type: str):
        self.triggers.append(lambda e: e.event_type == event_type)
        return self

    def when_target(self, target: str):
        self.triggers.append(lambda e: e.target == target)
        return self

    def play_sound(self, sound: str):
        self.actions.append(lambda e: print(f"🔊 {sound}"))
        return self

    def show_icon(self, icon: str):
        self.actions.append(lambda e: print(f"🖼️  {icon}"))
        return self

    def update_bar(self, bar_name: str):
        self.actions.append(lambda e: print(f"📊 {bar_name}: +{e.value}"))
        return self

    def with_cooldown(self, seconds: float):
        self.cooldown = seconds
        return self

    def with_duration(self, seconds: float):
        self.duration = seconds
        return self

    def build(self):
        return BuiltAura(self.name, self.triggers, self.actions, self.cooldown)

class BuiltAura:
    def __init__(self, name: str, triggers: List[Callable], actions: List[Callable], cooldown: float):
        self.name = name
        self.triggers = triggers
        self.actions = actions
        self.cooldown = cooldown
        self.last_trigger = 0

    def process_event(self, event: CombatEvent):
        current_time = event.timestamp

        # Check cooldown
        if current_time - self.last_trigger < self.cooldown:
            return

        # Check all triggers
        if all(trigger(event) for trigger in self.triggers):
            print(f"✨ Aura activated: {self.name}")
            for action in self.actions:
                action(event)
            self.last_trigger = current_time

def demo_builder():
    print("\n" + "=" * 60)
    print("BUILDER PATTERN DEMO")
    print("=" * 60)

    # Fluent API for creating auras
    crit_alert = (AuraBuilder("Critical Strike Alert")
                  .when_damage_exceeds(100)
                  .when_event_type("DAMAGE")
                  .play_sound("crit.mp3")
                  .show_icon("critical.png")
                  .update_bar("DamageBar")
                  .with_cooldown(1.0)
                  .build())

    low_health = (AuraBuilder("Low Health Warning")
                  .when_target("Player")
                  .when_event_type("DAMAGE")
                  .play_sound("danger.mp3")
                  .show_icon("skull.png")
                  .with_cooldown(3.0)
                  .build())

    events = [
        CombatEvent("DAMAGE", "Player", "Enemy", 150, time.time()),
        CombatEvent("DAMAGE", "Enemy", "Player", 80, time.time() + 0.5),
        CombatEvent("DAMAGE", "Player", "Enemy", 120, time.time() + 1.5),
    ]

    for event in events:
        print(f"\n⚔️  Event: {event.event_type} | {event.source} → {event.target} ({event.value})")
        crit_alert.process_event(event)
        low_health.process_event(event)
        time.sleep(0.3)


class HybridWeakAuraSystem:
    """Combines the best of all patterns"""

    def __init__(self):
        self.auras: List[Aura] = []
        self.command_queue = CommandQueue()

    @staticmethod
    def create(name: str) -> AuraBuilder:
        """Use Builder for creation (user-friendly)"""
        return AuraBuilder(name)

    def register(self, aura_to_r: Aura):
        """Use Observer for event distribution"""
        self.auras.append(aura_to_r)

    def process_event(self, event: CombatEvent):
        """Process with Strategy pattern for flexibility"""
        for my_aura in self.auras:
            if hasattr(my_aura, 'process_event'):
                my_aura.process_event(event)

# Usage
system = HybridWeakAuraSystem()

# Builder for easy creation
aura = (system.create("Boss Mechanic")
        .when_damage_exceeds(200)
        .play_sound("alert.mp3")
        .show_icon("warning.png")
        .build())

system.register(aura)


if __name__ == "__main__":
    demo_observer()
    time.sleep(1)

    demo_strategy()
    time.sleep(1)

    demo_command()
    time.sleep(1)

    demo_builder()
'''