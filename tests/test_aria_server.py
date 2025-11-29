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
