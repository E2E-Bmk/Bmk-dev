from __future__ import annotations

import pytest

from asciimatics.effects import Background, Effect, Print, Scroll, Sprite, Wipe
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.paths import DynamicPath, Path
from asciimatics.renderers import StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Canvas, Screen
from asciimatics.widgets import (
    Button,
    CheckBox,
    DropdownList,
    Frame,
    Label,
    Layout,
    ListBox,
    RadioButtons,
    Text,
    TextBox,
    Widget,
)

from conftest import RecordingScreen, SpyEffect


class RecordingPath(DynamicPath):
    def process_event(self, event):
        self._x, self._y = event.x, event.y
        return None


def test_public_import_surface_exposes_core_modules():
    import asciimatics
    import asciimatics.effects
    import asciimatics.event
    import asciimatics.paths
    import asciimatics.renderers
    import asciimatics.scene
    import asciimatics.screen
    import asciimatics.widgets

    assert asciimatics.__version__
    assert Effect and Path and Scene and Screen


def test_keyboard_event_projects_code_and_text():
    event = KeyboardEvent(65)
    assert event.key_code == 65
    assert "65" in str(event)


def test_mouse_event_projects_coordinates_and_flags():
    event = MouseEvent(3, 4, MouseEvent.LEFT_CLICK | MouseEvent.DOUBLE_CLICK)
    assert (event.x, event.y, event.buttons) == (3, 4, 5)
    assert MouseEvent.SCROLL_UP != MouseEvent.SCROLL_DOWN
    assert "(3, 4)" in str(event)


def test_scene_projects_name_duration_clear_and_effects():
    effect = SpyEffect(stop_frame=5)
    scene = Scene([effect], duration=7, clear=False, name="intro")
    assert (scene.name, scene.duration, scene.clear) == ("intro", 7, False)
    assert scene.effects == [effect]
    assert effect.scene is scene


def test_scene_add_and_remove_effect_updates_registration():
    scene = Scene([], duration=-1)
    effect = SpyEffect()
    scene.add_effect(effect)
    assert scene.effects == [effect]
    assert effect.scene is scene
    scene.remove_effect(effect)
    assert scene.effects == []


def test_scene_sends_events_in_reverse_effect_order():
    first = SpyEffect()
    second = SpyEffect()
    scene = Scene([first, second], duration=-1)
    event = KeyboardEvent(9)
    assert scene.process_event(event) is event
    assert second.events == [event]
    assert first.events == [event]


def test_effect_updates_only_inside_configured_frame_window(screen):
    effect = SpyEffect(screen, stop_frame=3)
    effect.update(-1)
    effect.update(0)
    effect.update(2)
    effect.update(3)
    assert effect.update_frames == [0, 2]
    assert effect.screen is screen
    assert effect.stop_frame == 3


def test_effect_reset_delete_count_and_default_properties(screen):
    effect = Background(screen, bg=2, stop_frame=6, delete_count=4)
    effect.reset()
    effect.delete_count = 2
    assert effect.delete_count == 2
    assert effect.frame_update_count > 0
    assert effect.safe_to_default_unhandled_input is True
    assert effect.process_event("event") == "event"


def test_path_jump_and_wait_replays_positions():
    path = Path()
    path.jump_to(4, 2)
    path.wait(2)
    path.reset()
    positions = []
    while not path.is_finished():
        positions.append(path.next_pos())
    assert positions == [(4, 2), (4, 2), (4, 2)]


def test_path_straight_motion_reaches_endpoint():
    path = Path()
    path.jump_to(0, 0)
    path.move_straight_to(6, 3, 3)
    path.reset()
    positions = []
    while not path.is_finished():
        positions.append(path.next_pos())
    assert positions == [(0, 0), (2, 1), (4, 2), (6, 3)]


def test_path_round_motion_is_repeatable_after_reset():
    path = Path()
    path.move_round_to([(0, 0), (4, 2), (8, 0), (12, 2)], 8)
    path.reset()
    first = []
    while not path.is_finished():
        first.append(path.next_pos())
    path.reset()
    second = []
    while not path.is_finished():
        second.append(path.next_pos())
    assert first == second
    assert first[-1] == (12, 2)


def test_dynamic_path_starts_at_configured_position_and_moves_on_event():
    path = RecordingPath(None, 1, 2)
    assert path.next_pos() == (1, 2)
    assert path.is_finished() is False
    assert path.process_event(MouseEvent(8, 5, 0)) is None
    assert path.next_pos() == (8, 5)
    path.reset()
    assert path.next_pos() == (1, 2)


def test_static_renderer_projects_dimensions_and_images():
    renderer = StaticRenderer(images=["ab", "longer"])
    assert renderer.max_width == 6
    assert renderer.max_height == 1
    assert list(renderer.images) == [["ab"], ["longer"]]


def test_static_renderer_animation_and_reset_are_public():
    renderer = StaticRenderer(images=["first", "second"], animation=lambda: 1)
    assert renderer.rendered_text[0] == ["second"]
    renderer.reset()
    assert renderer.rendered_text[0] == ["second"]


def test_static_renderer_projects_colour_sequences_without_ansi_snapshot():
    renderer = StaticRenderer(images=["${2}green"])
    image, colours = renderer.rendered_text
    assert image == ["green"]
    assert colours[0][0][0] == 2


def test_print_effect_uses_renderer_projection_and_screen_paint(screen):
    effect = Print(screen, StaticRenderer(images=["hello"]), 2, x=3, speed=1)
    effect.reset()
    effect.update(0)
    assert screen.calls[0][0] == "paint"
    assert screen.calls[0][1:4] == ("hello", 3, 2)
    assert effect.stop_frame == 0


def test_print_effect_speed_gates_repaints(screen):
    effect = Print(screen, StaticRenderer(images=["hello"]), 2, x=3, speed=3)
    effect.reset()
    effect.update(0)
    effect.update(1)
    effect.update(2)
    assert len([call for call in screen.calls if call[0] == "paint"]) == 1
    assert effect.frame_update_count == 1


def test_wipe_effect_advances_on_even_frames(screen):
    effect = Wipe(screen, bg=1)
    effect.reset()
    effect.update(0)
    effect.update(1)
    effect.update(2)
    prints = [call for call in screen.calls if call[0] == "print_at"]
    assert [call[3] for call in prints] == [0, 1]
    assert prints[0][1] == " " * screen.width


def test_scroll_effect_uses_configured_rate(screen):
    effect = Scroll(screen, 2)
    effect.reset()
    effect.update(1)
    effect.update(2)
    effect.update(4)
    assert [call for call in screen.calls if call[0] == "scroll"] == [
        ("scroll", 1),
        ("scroll", 1),
    ]


def test_sprite_follows_path_and_records_last_position(screen):
    path = Path()
    path.jump_to(5, 3)
    renderer = StaticRenderer(images=["X"])
    sprite = Sprite(screen, {"default": renderer}, path, speed=1)
    sprite.update(0)
    assert any(call[0] == "paint" and call[1] == "X" for call in screen.calls)
    assert sprite.last_position() == (5, 3, 1, 1)


def test_sprite_overlap_uses_last_positions(screen):
    first_path = Path()
    first_path.jump_to(5, 3)
    second_path = Path()
    second_path.jump_to(5, 3)
    first = Sprite(screen, {"default": StaticRenderer(images=["X"])}, first_path, speed=1)
    second = Sprite(screen, {"default": StaticRenderer(images=["Y"])}, second_path, speed=1)
    first.update(0)
    second.update(0)
    assert first.overlaps(second)


def test_sprite_forwards_events_to_dynamic_paths(screen):
    path = RecordingPath(screen, 1, 1)
    sprite = Sprite(screen, {"default": StaticRenderer(images=["X"])}, path, speed=1)
    event = MouseEvent(7, 6, MouseEvent.LEFT_CLICK)
    assert sprite.process_event(event) is None
    assert path.next_pos() == (7, 6)


def test_widget_constants_and_label_value_contract():
    assert Widget.FILL_FRAME != Widget.FILL_COLUMN
    label = Label("Status", name="status")
    assert label.name == "status"
    assert label.text == "Status"
    assert label.value is None
    label.text = "Ready"
    assert label.text == "Ready"


def test_button_keyboard_event_invokes_callback():
    calls = []
    button = Button("Run", lambda: calls.append("clicked"))
    assert button.process_event(KeyboardEvent(ord(" "))) is None
    assert calls == ["clicked"]
    assert button.process_event(KeyboardEvent(ord("x"))).key_code == ord("x")


def test_checkbox_toggle_and_callback():
    calls = []
    checkbox = CheckBox("Accept", on_change=lambda: calls.append(checkbox.value))
    assert checkbox.value is None
    assert checkbox.process_event(KeyboardEvent(ord(" "))) is None
    assert checkbox.value is True
    assert calls == [True]


def test_radio_buttons_navigation_and_value_selection():
    radio = RadioButtons([("One", 1), ("Two", 2), ("Three", 3)])
    assert radio.value == 1
    assert radio.process_event(KeyboardEvent(Screen.KEY_DOWN)) is None
    assert radio.value == 2
    radio.value = 3
    assert radio.value == 3


def test_text_editing_and_validator_state():
    text = Text(validator="^[a-z]*$")
    text.value = "ab"
    assert text.process_event(KeyboardEvent(ord("c"))) is None
    assert text.value == "abc"
    assert text.is_valid is True
    text.process_event(KeyboardEvent(ord("1")))
    assert text.value == "abc1"
    assert text.is_valid is False


def test_textbox_multiline_value_and_enter_transition():
    textbox = TextBox(3)
    textbox.value = ["ab"]
    textbox.process_event(KeyboardEvent(10))
    assert textbox.value == ["ab", ""]
    textbox.process_event(KeyboardEvent(ord("x")))
    assert textbox.value == ["ab", "x"]


def test_dropdown_value_and_options_projection():
    dropdown = DropdownList([("One", 1), ("Two", 2)])
    assert dropdown.value == 1
    dropdown.value = 2
    assert dropdown.value == 2
    dropdown.options = [("New", 3)]
    assert dropdown.value is None


def test_listbox_selection_and_start_line_projection():
    listbox = ListBox(2, [("One", 1), ("Two", 2), ("Three", 3)])
    assert listbox.value is None
    listbox.value = 2
    assert listbox.value == 2
    listbox.start_line = 1
    assert listbox.start_line == 1


def test_layout_focus_and_find_widget(simple_frame):
    frame, layout = simple_frame
    first = layout.add_widget(Text(name="first"))
    second = layout.add_widget(Button("Next", lambda: None, name="second"))
    frame.fix()
    layout.focus(force_first=True)
    assert layout.get_current_widget() is first
    assert layout.find_widget("second") is second
    layout.process_event(KeyboardEvent(Screen.KEY_TAB), hover_focus=False)
    assert layout.get_current_widget() is second


def test_frame_data_round_trip_with_named_widgets(simple_frame):
    frame, layout = simple_frame
    text = layout.add_widget(Text(name="title"))
    checkbox = layout.add_widget(CheckBox("Enabled", name="enabled"))
    frame.fix()
    text.value = "Demo"
    checkbox.value = True
    frame.save()
    assert frame.data["title"] == "Demo"
    assert frame.data["enabled"] is True
    frame.data = {"title": "Restored", "enabled": False}
    assert (text.value, checkbox.value) == ("Restored", False)


def test_frame_theme_and_title_are_public():
    frame = Frame(RecordingScreen(), 8, 20, title="Dashboard", has_border=False, can_scroll=False)
    frame.set_theme("bright")
    assert frame.title.startswith(" Dashboard")
    assert frame.canvas.origin == (10, 2)


def test_frame_update_flushes_canvas_to_recording_screen(simple_frame, screen):
    frame, layout = simple_frame
    layout.add_widget(Label("Hello"))
    frame.fix()
    frame.update(0)
    transfers = [call for call in screen.calls if call[0] == "block_transfer"]
    assert len(transfers) == 1
    assert frame.canvas.origin == (5, 1)


def test_canvas_location_and_visibility_are_stable(canvas):
    assert canvas.origin == (2, 1)
    assert canvas.dimensions == (10, 30)
    assert canvas.is_visible(0, 0)
    assert not canvas.is_visible(30, 0)


def test_screen_control_and_key_constants_are_deterministic():
    assert Screen.ctrl("A") == 1
    assert Screen.ctrl(66) == 2
    assert Screen.KEY_LEFT != Screen.KEY_RIGHT
