'''
from dataclasses import dataclass
from typing import Dict, List, Callable
from collections import defaultdict
from enum import Enum
import time

# ============= CORE MODELS =============
@dataclass
class CombatEvent:
    event_type: str
    source: str
    target: str
    value: int
    timestamp: float

class ActionType(Enum):
    PLAY_AUDIO = "PLAY_AUDIO"
    SHOW_ICON = "SHOW_ICON"
    UPDATE_BAR = "UPDATE_BAR"
    SHOW_TEXT = "SHOW_TEXT"

@dataclass
class ActionRequest:
    action_type: ActionType
    params: Dict

# ============= EVENT BUS =============
class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, action_type: ActionType, handler: Callable):
        self.subscribers[action_type].append(handler)
        print(f"📌 Subscribed to {action_type.value}")

    def publish(self, action_type: ActionType, params: Dict):
        for handler in self.subscribers[action_type]:
            handler(params)

# ============= GAME CLIENT =============
class GameClient:
    def __init__(self):
        self.event_bus = EventBus()
        self._register_handlers()
        self.active_icons = set()
        self.bars = {}

    def _register_handlers(self):
        """Register all action handlers"""
        self.event_bus.subscribe(ActionType.PLAY_AUDIO, self.pygame_play_audio)
        self.event_bus.subscribe(ActionType.SHOW_ICON, self.show_icon)
        self.event_bus.subscribe(ActionType.UPDATE_BAR, self.update_bar)
        self.event_bus.subscribe(ActionType.SHOW_TEXT, self.show_text)

    def pygame_play_audio(self, params: Dict):
        """Actual pygame audio call"""
        filename = params["filename"]
        volume = params.get("volume", 1.0)
        # In real implementation:
        # sound = pygame.mixer.Sound(filename)
        # sound.set_volume(volume)
        # sound.play()
        print(f"🔊 PYGAME: Playing {filename} at volume {volume}")

    def show_icon(self, params: Dict):
        icon = params["icon"]
        duration = params.get("duration", 3.0)
        self.active_icons.add(icon)
        print(f"🖼️  RENDER: Icon {icon} visible for {duration}s")
        # In real: schedule removal after duration

    def update_bar(self, params: Dict):
        bar_name = params["bar_name"]
        value = params["value"]
        self.bars[bar_name] = self.bars.get(bar_name, 0) + value
        print(f"📊 UI: {bar_name} = {self.bars[bar_name]}")

    def show_text(self, params: Dict):
        text = params["text"]
        color = params.get("color", "white")
        print(f"💬 SCREEN: {text} ({color})")

# ============= AURA SYSTEM =============
class AuraBuilder:
    def __init__(self, name: str):
        self.name = name
        self.event_bus = EventBus()
        self.triggers = []
        self.actions = []
        self.cooldown = 0

    # Trigger conditions
    def when_damage_exceeds(self, threshold: int):
        self.triggers.append(lambda e: e.event_type == "DAMAGE" and e.value > threshold)
        return self

    def when_event_type(self, event_type: str):
        self.triggers.append(lambda e: e.event_type == event_type)
        return self

    def when_source(self, source: str):
        self.triggers.append(lambda e: e.source == source)
        return self

    def when_target(self, target: str):
        self.triggers.append(lambda e: e.target == target)
        return self

    # Actions (emit to event bus)
    def play_sound(self, filename: str, volume: float = 1.0):
        def action(event):
            self.event_bus.publish(ActionType.PLAY_AUDIO, {
                "filename": filename,
                "volume": volume
            })
        self.actions.append(action)
        return self

    def show_icon(self, icon: str, duration: float = 3.0):
        def action(event):
            self.event_bus.publish(ActionType.SHOW_ICON, {
                "icon": icon,
                "duration": duration
            })
        self.actions.append(action)
        return self

    def update_bar(self, bar_name: str):
        def action(event):
            self.event_bus.publish(ActionType.UPDATE_BAR, {
                "bar_name": bar_name,
                "value": event.value
            })
        self.actions.append(action)
        return self

    def show_text(self, text: str, color: str = "white"):
        def action(event):
            self.event_bus.publish(ActionType.SHOW_TEXT, {
                "text": text,
                "color": color
            })
        self.actions.append(action)
        return self

    def with_cooldown(self, seconds: float):
        self.cooldown = seconds
        return self

    def build(self):
        return Aura(self.name, self.triggers, self.actions, self.cooldown)

class Aura:
    def __init__(self, name: str, triggers: List[Callable],
                 actions: List[Callable], cooldown: float):
        self.name = name
        self.triggers = triggers
        self.actions = actions
        self.cooldown = cooldown
        self.last_trigger = 0

    def process_event(self, event: CombatEvent):
        # Check cooldown
        if event.timestamp - self.last_trigger < self.cooldown:
            return

        # Check all triggers
        if all(trigger(event) for trigger in self.triggers):
            print(f"✨ AURA TRIGGERED: {self.name}")
            for action in self.actions:
                action(event)
            self.last_trigger = event.timestamp

# ============= USAGE =============
def main():
    print("=" * 70)
    print("WEAKAURA SYSTEM - EVENT BUS PATTERN")
    print("=" * 70)

    # Initialize game client (registers audio/visual handlers)
    game_client = GameClient()
    print()

    # Create auras (they automatically use the event bus)
    crit_alert = (AuraBuilder("Critical Strike Alert")
                  .when_damage_exceeds(100)
                  .when_event_type("DAMAGE")
                  .play_sound("sounds/critical.mp3", volume=0.8)
                  .show_icon("icons/crit.png", duration=2.0)
                  .show_text("CRITICAL HIT!", color="red")
                  .update_bar("DamageDealt")
                  .with_cooldown(1.0)
                  .build())

    low_health = (AuraBuilder("Low Health Warning")
                  .when_target("Player")
                  .when_event_type("DAMAGE")
                  .play_sound("sounds/danger.mp3", volume=1.0)
                  .show_icon("icons/skull.png")
                  .show_text("DANGER!", color="red")
                  .with_cooldown(3.0)
                  .build())

    execute_phase = (AuraBuilder("Execute Phase")
                     .when_damage_exceeds(200)
                     .play_sound("sounds/execute.mp3")
                     .show_icon("icons/execute.png")
                     .show_text("EXECUTE!", color="gold")
                     .build())

    # Simulate combat events
    events = [
        CombatEvent("DAMAGE", "Player", "Enemy", 150, time.time()),
        CombatEvent("DAMAGE", "Enemy", "Player", 80, time.time() + 0.5),
        CombatEvent("DAMAGE", "Player", "Enemy", 120, time.time() + 1.5),
        CombatEvent("DAMAGE", "Player", "Boss", 250, time.time() + 2.0),
        CombatEvent("HEAL", "Player", "Player", 50, time.time() + 2.5),
    ]

    print("\n" + "=" * 70)
    print("COMBAT SIMULATION")
    print("=" * 70 + "\n")

    for event in events:
        print(f"⚔️  EVENT: {event.event_type} | {event.source} → {event.target} ({event.value})")
        print("-" * 70)

        # Process event through all auras
        crit_alert.process_event(event)
        low_health.process_event(event)
        execute_phase.process_event(event)

        print()
        time.sleep(0.5)

if __name__ == "__main__":
    main()
'''