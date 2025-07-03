import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.components import Aura


def test_get_timestamps_for_ticks_this_frame():
    """Test get_timestamps_for_ticks_this_frame method with various scenarios."""

    # Test case 1: Aura with regular ticking, frame contains multiple ticks
    aura = Aura(
        aura_id=1,
        source_id=1,
        target_id=1,
        start_time=0.0,
        duration=5.0,
        ticks=5  # tick every 1.0 seconds
    )

    # Frame from 2.5 to 5.5 should contain ticks at 3.0, 4.0, 5.0
    timestamps = aura.tick_timestamps  # pylint: disable=W0212
    expected = (1.0, 2.0, 3.0, 4.0, 5.0)
    assert timestamps == expected, f"Expected {expected}, got {timestamps}"

if __name__ == "__main__":
    pytest.main([__file__])