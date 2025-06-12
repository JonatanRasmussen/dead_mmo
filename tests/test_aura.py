import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.aura import Aura
from src.handlers.id_gen import IdGen


def test_get_timestamps_for_ticks_this_frame():
    """Test get_timestamps_for_ticks_this_frame method with various scenarios."""

    # Test case 1: Aura with regular ticking, frame contains multiple ticks
    aura = Aura(
        aura_id=1,
        source_id=1,
        target_id=1,
        start_time=0.0,
        duration=10.0,
        ticks=10  # tick every 1.0 seconds
    )

    # Frame from 2.5 to 5.5 should contain ticks at 3.0, 4.0, 5.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(2.5, 5.5)
    expected = (3.0, 4.0, 5.0)
    assert timestamps == expected, f"Expected {expected}, got {timestamps}"


def test_frame_starts_exactly_at_tick():
    """Test when frame starts exactly when a tick occurs (should exclude it)."""
    aura = Aura(
        start_time=0.0,
        duration=5.0,
        ticks=5  # tick every 1.0 seconds: at 0, 1, 2, 3, 4, 5
    )

    # Frame from 2.0 to 4.5 should include tick at 2.0 (frame start) and ticks at 3.0, 4.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(2.0, 4.5)
    expected = (3.0, 4.0)
    assert timestamps == expected


def test_frame_ends_exactly_at_tick():
    """Test when frame ends exactly when a tick occurs (should include it)."""
    aura = Aura(
        start_time=0.0,
        duration=5.0,
        ticks=5  # tick every 1.0 seconds
    )

    # Frame from 1.5 to 3.0 should include tick at 2.0 but exclude tick at 3.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(1.5, 3.0)
    expected = (2.0, 3.0)
    assert timestamps == expected


def test_frame_with_no_ticks():
    """Test frame that contains no ticks."""
    aura = Aura(
        start_time=0.0,
        duration=10.0,
        ticks=5  # tick every 2.0 seconds: at 0, 2, 4, 6, 8, 10
    )

    # Frame from 2.5 to 3.5 contains no ticks
    timestamps = aura._get_timestamps_for_ticks_this_frame(2.5, 3.5)
    expected = ()
    assert timestamps == expected


def test_frame_before_aura_starts():
    """Test frame that occurs before aura starts."""
    aura = Aura(
        start_time=5.0,
        duration=5.0,
        ticks=5
    )

    # Frame from 1.0 to 3.0 is before aura starts
    timestamps = aura._get_timestamps_for_ticks_this_frame(1.0, 3.0)
    expected = ()
    assert timestamps == expected


def test_frame_after_aura_ends():
    """Test frame that occurs after aura ends."""
    aura = Aura(
        start_time=0.0,
        duration=5.0,
        ticks=5
    )

    # Frame from 7.0 to 9.0 is after aura ends
    timestamps = aura._get_timestamps_for_ticks_this_frame(7.0, 9.0)
    expected = ()
    assert timestamps == expected


def test_frame_overlaps_aura_start():
    """Test frame that starts before aura and overlaps aura start."""
    aura = Aura(
        start_time=4.0,
        duration=6.0,
        ticks=3  # tick every 2.0 seconds: at 6, 8, 10
    )

    # Frame from 1.0 to 5.0 should contain ticks at 4.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(3.0, 7.0)
    expected = (6.0,)
    assert timestamps == expected


def test_frame_overlaps_aura_end():
    """Test frame that overlaps aura end."""
    aura = Aura(
        start_time=0.0,
        duration=5.0,
        ticks=5  # tick every 1.0 seconds: at 0, 1, 2, 3, 4, 5
    )

    # Frame from 3.5 to 7.0 should contain ticks at 4.0, 5.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(3.5, 7.0)
    expected = (4.0, 5.0)
    assert timestamps == expected


def test_single_tick_aura():
    """Test aura with only one tick."""
    aura = Aura(
        start_time=1.0,
        duration=3.0,
        ticks=1  # single tick at start_time + duration = 4.0
    )

    # Frame that contains the single tick
    timestamps = aura._get_timestamps_for_ticks_this_frame(0.5, 5.0)
    expected = (4.0,)  # tick occurs at start_time + duration
    assert timestamps == expected


def test_very_short_frame():
    """Test very short frame that might contain part of a tick interval."""
    aura = Aura(
        start_time=0.0,
        duration=10.0,
        ticks=10  # tick every 1.0 seconds
    )

    # Very short frame from 2.9 to 3.1 should contain tick at 3.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(2.99, 3.01)
    expected = (3.0,)
    assert timestamps == expected


def test_zero_ticks():
    """Test aura with zero ticks."""
    aura = Aura(
        start_time=0.0,
        duration=5.0,
        ticks=0
    )

    timestamps = aura._get_timestamps_for_ticks_this_frame(1.0, 4.0)
    expected = ()
    assert timestamps == expected


def test_zero_duration():
    """Test aura with zero duration."""
    aura = Aura(
        start_time=2.0,
        duration=0.0,
        ticks=5
    )

    timestamps = aura._get_timestamps_for_ticks_this_frame(1.0, 4.0)
    expected = ()
    assert timestamps == expected


def test_fractional_tick_intervals():
    """Test aura with fractional tick intervals."""
    aura = Aura(
        start_time=0.0,
        duration=3.0,
        ticks=6  # tick every 0.5 seconds: at 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0
    )

    # Frame from 0.75 to 2.25 should contain ticks at 1.0, 1.5, 2.0
    timestamps = aura._get_timestamps_for_ticks_this_frame(0.75, 2.25)
    expected = (1.0, 1.5, 2.0)
    assert timestamps == expected


if __name__ == "__main__":
    pytest.main([__file__])