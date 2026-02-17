import re
from aria_web import server as aria_server


def test_generate_tags_fallback_say_detection():
    tags = aria_server.generate_tags_fallback('please say hello everyone')
    # We expect at least one say tag
    assert any(re.match(r'^\[aria:say:.*hello everyone.*\]$', t, flags=re.I) for t in tags), f"Expected say tag in {tags}"


def test_determine_position_for_pickup():
    tag = aria_server.determine_position_from_context('pick up apple')
    assert tag.startswith('[aria:position'), 'pickup should return a position tag'


def test_generate_tags_fallback_add_object():
    tags = aria_server.generate_tags_fallback('add a bear to the scene')
    assert any('[aria:interact:add' in t for t in tags), 'Expected an interact:add tag for spawn/add commands'


# ===== Sparkle Functionality Tests =====

def test_sparkle_effect_basic():
    """Test basic sparkle command detection"""
    tags = aria_server.generate_tags_fallback('sparkle')
    assert any('[aria:effect:sparkle' in t for t in tags), f"Expected sparkle effect tag in {tags}"


def test_sparkle_effect_with_synonyms():
    """Test sparkle effect with synonym keywords"""
    test_commands = [
        'make it sparkle',
        'add some glitter',
        'shimmer effect',
        'make it shine',
        'sparkles please'
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any('[aria:effect:sparkle' in t for t in tags), \
            f"Expected sparkle effect tag for command '{cmd}' but got {tags}"


def test_sparkle_intensity_light():
    """Test light sparkle intensity detection"""
    test_commands = [
        'light sparkle',
        'subtle sparkle',
        'gentle shimmer'
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any('[aria:effect:sparkle:light]' in t for t in tags), \
            f"Expected light intensity sparkle tag for '{cmd}' but got {tags}"


def test_sparkle_intensity_normal():
    """Test normal sparkle intensity (default)"""
    tags = aria_server.generate_tags_fallback('sparkle')
    assert any('[aria:effect:sparkle:normal]' in t for t in tags), \
        f"Expected normal intensity sparkle tag but got {tags}"


def test_sparkle_intensity_heavy():
    """Test heavy sparkle intensity detection"""
    test_commands = [
        'heavy sparkle',
        'intense sparkle',
        'lots of sparkles',
        'many sparkles'
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any('[aria:effect:sparkle:heavy]' in t for t in tags), \
            f"Expected heavy intensity sparkle tag for '{cmd}' but got {tags}"


def test_glow_effect_basic():
    """Test glow effect detection"""
    tags = aria_server.generate_tags_fallback('glow')
    assert any('[aria:effect:glow' in t for t in tags), f"Expected glow effect tag in {tags}"


def test_glow_effect_synonyms():
    """Test glow effect with synonym keywords"""
    test_commands = [
        'make it glow',
        'glowing effect',
        'radiate light',
        'illuminate'
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any('[aria:effect:glow' in t for t in tags), \
            f"Expected glow effect tag for command '{cmd}' but got {tags}"


def test_hearts_effect_basic():
    """Test hearts effect detection"""
    tags = aria_server.generate_tags_fallback('hearts')
    assert any('[aria:effect:hearts' in t for t in tags), f"Expected hearts effect tag in {tags}"


def test_hearts_effect_synonyms():
    """Test hearts effect with synonym keywords"""
    test_commands = [
        'show hearts',
        'heart effect',
        'show some love'
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any('[aria:effect:hearts' in t for t in tags), \
            f"Expected hearts effect tag for command '{cmd}' but got {tags}"


def test_combined_dance_and_sparkle():
    """Test combined commands like 'dance with sparkles'"""
    tags = aria_server.generate_tags_fallback('dance with sparkles')
    assert any('dance' in t.lower() or 'animate' in t.lower() for t in tags), \
        f"Expected dance/animate tag in {tags}"
    assert any('[aria:effect:sparkle' in t for t in tags), \
        f"Expected sparkle effect tag in {tags}"


def test_keyword_frozensets_defined():
    """Test that effect keyword frozensets are defined"""
    assert hasattr(aria_server, 'SPARKLE_KEYWORDS'), "SPARKLE_KEYWORDS should be defined"
    assert hasattr(aria_server, 'GLOW_KEYWORDS'), "GLOW_KEYWORDS should be defined"
    assert hasattr(aria_server, 'HEARTS_KEYWORDS'), "HEARTS_KEYWORDS should be defined"

    # Verify they are frozensets
    assert isinstance(aria_server.SPARKLE_KEYWORDS, frozenset), "SPARKLE_KEYWORDS should be a frozenset"
    assert isinstance(aria_server.GLOW_KEYWORDS, frozenset), "GLOW_KEYWORDS should be a frozenset"
    assert isinstance(aria_server.HEARTS_KEYWORDS, frozenset), "HEARTS_KEYWORDS should be a frozenset"

    # Verify they contain expected keywords
    assert 'sparkle' in aria_server.SPARKLE_KEYWORDS
    assert 'glitter' in aria_server.SPARKLE_KEYWORDS
    assert 'glow' in aria_server.GLOW_KEYWORDS
    assert 'hearts' in aria_server.HEARTS_KEYWORDS


def test_effect_intensity_mutually_exclusive():
    """Test that only one intensity level is applied"""
    # When both keywords are present, 'light' takes precedence due to if-elif order
    tags = aria_server.generate_tags_fallback('light but intense sparkle')
    sparkle_tags = [t for t in tags if '[aria:effect:sparkle' in t]
    assert len(sparkle_tags) == 1, f"Expected exactly one sparkle tag but got {sparkle_tags}"
    # Light should be applied due to if-elif order (light is checked first)
    assert '[aria:effect:sparkle:light]' in sparkle_tags[0], \
        f"Expected light intensity to take precedence but got {sparkle_tags[0]}"
