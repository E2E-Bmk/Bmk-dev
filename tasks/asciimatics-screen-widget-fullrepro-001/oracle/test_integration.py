from __future__ import annotations

import pytest

from asciimatics.effects import Background, Print, Scroll, Sprite, Wipe
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.paths import DynamicPath, Path
from asciimatics.renderers import StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import (
    Button,
    CheckBox,
    DropdownList,
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


@pytest.mark.depends_on("test_scene_sends_events_in_reverse_effect_order")
def test_scene_event_workflow_preserves_unhandled_event():
    first = SpyEffect()
    second = SpyEffect()
    scene = Scene([first, second], duration=-1)
    event = MouseEvent(4, 5, MouseEvent.LEFT_CLICK)
    assert scene.process_event(event) is event
    assert [type(item).__name__ for item in second.events + first.events] == ["MouseEvent", "MouseEvent"]


@pytest.mark.depends_on("test_path_straight_motion_reaches_endpoint", "test_sprite_follows_path_and_records_last_position")
def test_path_and_sprite_workflow_draws_each_position():
    screen = RecordingScreen()
    path = Path()
    path.jump_to(4, 2)
    path.move_straight_to(10, 2, 2)
    sprite = Sprite(screen, {"default": StaticRenderer(images=["@"])}, path, speed=1)
    sprite.update(0)
    sprite.update(1)
    assert len([call for call in screen.calls if call[0] == "paint"]) == 2
    assert sprite.last_position()[0] == 7


@pytest.mark.depends_on("test_print_effect_uses_renderer_projection_and_screen_paint", "test_wipe_effect_advances_on_even_frames")
def test_print_and_wipe_compose_over_one_recording_screen():
    screen = RecordingScreen()
    printer = Print(screen, StaticRenderer(images=["Title"]), 1, x=2, speed=1)
    wipe = Wipe(screen)
    printer.update(0)
    wipe.update(0)
    assert [call[0] for call in screen.calls] == ["paint", "print_at"]
    assert screen.calls[0][1] == "Title"


@pytest.mark.depends_on("test_scroll_effect_uses_configured_rate", "test_effect_updates_only_inside_configured_frame_window")
def test_scene_update_workflow_runs_background_and_scroll_effects():
    screen = RecordingScreen()
    background = Background(screen, bg=3)
    scroll = Scroll(screen, 2)
    scene = Scene([background, scroll], duration=4)
    scene.reset()
    for frame_no in range(4):
        for effect in scene.effects:
            effect.update(frame_no)
    assert any(call[0] == "scroll" for call in screen.calls)
    assert background.scene is scene


@pytest.mark.depends_on("test_static_renderer_animation_and_reset_are_public", "test_print_effect_speed_gates_repaints")
def test_renderer_reset_and_effect_speed_form_a_repeatable_workflow():
    screen = RecordingScreen()
    renderer = StaticRenderer(images=["A", "B"])
    effect = Print(screen, renderer, 0, x=0, speed=2)
    effect.reset()
    effect.update(0)
    effect.update(1)
    effect.update(2)
    effect.reset()
    effect.update(0)
    assert [call[1] for call in screen.calls if call[0] == "paint"] == ["A", "B", "A"]


@pytest.mark.depends_on("test_dynamic_path_starts_at_configured_position_and_moves_on_event", "test_sprite_forwards_events_to_dynamic_paths")
def test_dynamic_sprite_event_then_render_workflow():
    screen = RecordingScreen()
    path = RecordingPath(screen, 2, 2)
    sprite = Sprite(screen, {"default": StaticRenderer(images=["X"])}, path, speed=1)
    assert sprite.process_event(MouseEvent(9, 7, MouseEvent.LEFT_CLICK)) is None
    sprite.update(0)
    assert path.next_pos() == (9, 7)
    assert screen.calls[-1][0] == "paint"


@pytest.mark.depends_on("test_button_keyboard_event_invokes_callback", "test_checkbox_toggle_and_callback")
def test_button_and_checkbox_form_workflow_records_actions():
    actions = []
    button = Button("Save", lambda: actions.append("save"))
    checkbox = CheckBox("Ready", on_change=lambda: actions.append("checked"))
    checkbox.process_event(KeyboardEvent(ord(" ")))
    button.process_event(KeyboardEvent(13))
    assert (checkbox.value, actions) == (True, ["checked", "save"])


@pytest.mark.depends_on("test_radio_buttons_navigation_and_value_selection", "test_text_editing_and_validator_state")
def test_radio_and_text_workflow_combines_selection_and_validation():
    radio = RadioButtons([("Small", "s"), ("Large", "l")])
    text = Text(validator=lambda value: value.isalpha())
    radio.process_event(KeyboardEvent(Screen.KEY_DOWN))
    text.value = "note"
    text.process_event(KeyboardEvent(ord("!")))
    assert radio.value == "l"
    assert text.is_valid is False


@pytest.mark.depends_on("test_textbox_multiline_value_and_enter_transition", "test_frame_data_round_trip_with_named_widgets")
def test_textbox_frame_save_workflow_persists_multiline_content():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 10, 30, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    box = layout.add_widget(TextBox(3, name="notes"))
    frame.fix()
    box.value = ["alpha", "beta"]
    frame.save()
    assert frame.data == {"notes": ["alpha", "beta"]}


@pytest.mark.depends_on("test_listbox_selection_and_start_line_projection", "test_widget_constants_and_label_value_contract")
def test_listbox_and_label_workflow_tracks_selected_record():
    listbox = ListBox(2, [("Alpha", "a"), ("Beta", "b")], name="items")
    label = Label("Selected", name="selected")
    listbox.value = "b"
    label.text = str(listbox.value)
    assert (listbox.value, label.text) == ("b", "b")


@pytest.mark.depends_on("test_dropdown_value_and_options_projection", "test_layout_focus_and_find_widget")
def test_dropdown_options_and_layout_lookup_workflow():
    dropdown = DropdownList([("One", 1), ("Two", 2)], name="choice")
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    stored = layout.add_widget(dropdown)
    frame.fix()
    dropdown.value = 2
    assert layout.find_widget("choice") is stored
    assert dropdown.value == 2


@pytest.mark.depends_on("test_layout_focus_and_find_widget", "test_frame_update_flushes_canvas_to_recording_screen")
def test_layout_focus_then_frame_render_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    first = layout.add_widget(Text(name="first"))
    second = layout.add_widget(Button("Go", lambda: None, name="go"))
    first.value = ""
    frame.fix()
    layout.focus(force_first=True)
    layout.process_event(KeyboardEvent(Screen.KEY_TAB), hover_focus=False)
    frame.update(0)
    assert layout.get_current_widget() is second
    assert any(call[0] == "block_transfer" for call in screen.calls)
    assert first.value == ""


@pytest.mark.depends_on("test_frame_data_round_trip_with_named_widgets", "test_text_editing_and_validator_state")
def test_frame_initial_data_updates_text_and_checkbox_widgets():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, data={"title": "Loaded", "enabled": True},
                  has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    title = layout.add_widget(Text(name="title"))
    enabled = layout.add_widget(CheckBox("Enabled", name="enabled"))
    frame.fix()
    assert (title.value, enabled.value) == ("Loaded", True)


@pytest.mark.depends_on("test_frame_theme_and_title_are_public", "test_frame_update_flushes_canvas_to_recording_screen")
def test_frame_theme_title_and_render_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, title="Settings", has_border=True, can_scroll=False)
    frame.set_theme("default")
    frame.fix()
    frame.update(0)
    assert frame.title.startswith(" Settings")
    assert len([call for call in screen.calls if call[0] == "block_transfer"]) == 1


@pytest.mark.depends_on("test_effect_reset_delete_count_and_default_properties", "test_frame_update_flushes_canvas_to_recording_screen")
def test_frame_child_effect_and_frame_render_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    frame.add_effect(Print(frame.canvas, StaticRenderer(images=["child"]), 1, x=1, speed=1))
    frame.fix()
    frame.update(0)
    assert any(call[0] == "block_transfer" for call in screen.calls)
    assert frame.frame_update_count >= 0


@pytest.mark.depends_on("test_print_effect_uses_renderer_projection_and_screen_paint", "test_effect_reset_delete_count_and_default_properties")
def test_print_clear_delete_workflow_replaces_previous_projection():
    screen = RecordingScreen()
    effect = Print(screen, StaticRenderer(images=["erase"]), 1, x=1, clear=True, stop_frame=3, speed=1)
    effect.update(0)
    effect.update(2)
    assert any(call[0] == "print_at" and set(call[1]) == {" "} for call in screen.calls)


@pytest.mark.depends_on("test_sprite_overlap_uses_last_positions", "test_path_straight_motion_reaches_endpoint")
def test_two_sprite_motion_workflow_rechecks_overlap_after_updates():
    screen = RecordingScreen()
    path_a = Path()
    path_a.jump_to(10, 2)
    path_a.move_straight_to(10, 2, 1)
    path_b = Path()
    path_b.jump_to(10, 2)
    one = Sprite(screen, {"default": StaticRenderer(images=["A"])}, path_a, speed=1)
    two = Sprite(screen, {"default": StaticRenderer(images=["B"])}, path_b, speed=1)
    one.update(0)
    two.update(0)
    assert one.overlaps(two)
    one.update(1)
    assert one.overlaps(two)


@pytest.mark.depends_on("test_path_jump_and_wait_replays_positions", "test_path_straight_motion_reaches_endpoint")
def test_path_reset_workflow_replays_same_route():
    path = Path()
    path.jump_to(1, 1)
    path.wait(1)
    path.move_straight_to(5, 3, 2)
    path.reset()
    first = [path.next_pos() for _ in range(4)]
    path.reset()
    second = [path.next_pos() for _ in range(4)]
    assert first == second


@pytest.mark.depends_on("test_scene_projects_name_duration_clear_and_effects", "test_effect_reset_delete_count_and_default_properties")
def test_scene_exit_workflow_saves_effect_state():
    effect = SpyEffect()
    scene = Scene([effect], duration=2, name="save")
    scene.reset()
    scene.exit()
    assert effect.reset_count == 1
    assert effect.saved == 1


@pytest.mark.depends_on("test_scene_sends_events_in_reverse_effect_order", "test_button_keyboard_event_invokes_callback")
def test_scene_topmost_button_like_effect_swallow_workflow():
    lower = SpyEffect()
    upper = SpyEffect(swallow=True)
    scene = Scene([lower, upper], duration=-1)
    event = KeyboardEvent(13)
    assert scene.process_event(event) is event
    assert upper.events == [event]
    assert lower.events == []


@pytest.mark.depends_on("test_static_renderer_animation_and_reset_are_public", "test_print_effect_uses_renderer_projection_and_screen_paint")
def test_animated_renderer_print_workflow_cycles_images():
    screen = RecordingScreen()
    renderer = StaticRenderer(images=["one", "two"])
    effect = Print(screen, renderer, 0, x=0, speed=1)
    effect.update(0)
    effect.update(1)
    assert [call[1] for call in screen.calls if call[0] == "paint"] == ["one", "two"]


@pytest.mark.depends_on("test_canvas_location_and_visibility_are_stable", "test_static_renderer_projects_dimensions_and_images")
def test_canvas_and_renderer_dimensions_drive_a_print_position():
    screen = RecordingScreen(width=20, height=8)
    renderer = StaticRenderer(images=["wide"])
    effect = Print(screen, renderer, 3)
    effect.update(0)
    paint = next(call for call in screen.calls if call[0] == "paint")
    assert paint[2:4] == (8, 3)


@pytest.mark.depends_on("test_print_effect_uses_renderer_projection_and_screen_paint", "test_static_renderer_projects_colour_sequences_without_ansi_snapshot")
def test_coloured_renderer_print_workflow_keeps_colour_map_shape():
    screen = RecordingScreen()
    effect = Print(screen, StaticRenderer(images=["${2}green"]), 1, x=0, speed=1)
    effect.update(0)
    paint = next(call for call in screen.calls if call[0] == "paint")
    assert len(paint[-1]) == len("green")
    assert paint[-1][0][0] == 2


@pytest.mark.depends_on("test_checkbox_toggle_and_callback", "test_radio_buttons_navigation_and_value_selection")
def test_checkbox_radio_callback_workflow_tracks_form_state():
    state = []
    checkbox = CheckBox("Use", on_change=lambda: state.append(("check", checkbox.value)))
    radio = RadioButtons([("A", "a"), ("B", "b")], on_change=lambda: state.append(("radio", radio.value)))
    checkbox.process_event(KeyboardEvent(ord(" ")))
    radio.process_event(KeyboardEvent(Screen.KEY_DOWN))
    assert state == [("check", True), ("radio", "b")]


@pytest.mark.depends_on("test_text_editing_and_validator_state", "test_frame_update_flushes_canvas_to_recording_screen")
def test_text_validation_and_render_workflow_exposes_current_value():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    text = layout.add_widget(Text(name="code", validator="^[0-9]+$"))
    frame.fix()
    text.value = "42"
    frame.update(0)
    assert text.is_valid is True
    assert any(call[0] == "block_transfer" for call in screen.calls)


@pytest.mark.depends_on("test_textbox_multiline_value_and_enter_transition", "test_frame_update_flushes_canvas_to_recording_screen")
def test_textbox_edit_and_render_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    box = layout.add_widget(TextBox(3, name="body"))
    frame.fix()
    box.value = ["a"]
    box.process_event(KeyboardEvent(10))
    box.process_event(KeyboardEvent(ord("b")))
    frame.update(0)
    assert box.value == ["a", "b"]
    assert any(call[0] == "block_transfer" for call in screen.calls)


@pytest.mark.depends_on("test_listbox_selection_and_start_line_projection", "test_canvas_location_and_visibility_are_stable")
def test_listbox_keyboard_and_render_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    listbox = layout.add_widget(ListBox(2, [("A", 1), ("B", 2), ("C", 3)]))
    frame.fix()
    listbox.process_event(KeyboardEvent(Screen.KEY_DOWN))
    frame.update(0)
    assert listbox.value == 2
    assert any(call[0] == "block_transfer" for call in screen.calls)


@pytest.mark.depends_on("test_button_keyboard_event_invokes_callback", "test_frame_data_round_trip_with_named_widgets", "test_frame_update_flushes_canvas_to_recording_screen")
def test_complete_form_workflow_edits_saves_and_renders():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    actions = []
    frame = Frame(screen, 10, 30, data={"name": "Ada", "enabled": False},
                  has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    name = layout.add_widget(Text(name="name"))
    enabled = layout.add_widget(CheckBox("Enabled", name="enabled"))
    layout.add_widget(Button("Save", lambda: actions.append("save")))
    frame.fix()
    name.process_event(KeyboardEvent(Screen.KEY_END))
    name.process_event(KeyboardEvent(ord("!")))
    enabled.process_event(KeyboardEvent(ord(" ")))
    frame.save()
    frame.update(0)
    assert frame.data == {"name": "Ada!", "enabled": True}
    assert actions == []
    assert any(call[0] == "block_transfer" for call in screen.calls)


@pytest.mark.depends_on("test_dropdown_value_and_options_projection", "test_frame_update_flushes_canvas_to_recording_screen")
def test_selection_form_workflow_updates_dropdown_and_renders():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    dropdown = layout.add_widget(DropdownList([("Low", 1), ("High", 2)], name="priority"))
    frame.fix()
    dropdown.value = 2
    frame.update(0)
    assert frame.data == {}
    assert dropdown.value == 2
    assert any(call[0] == "block_transfer" for call in screen.calls)


@pytest.mark.depends_on("test_scene_projects_name_duration_clear_and_effects", "test_print_effect_uses_renderer_projection_and_screen_paint", "test_frame_update_flushes_canvas_to_recording_screen")
def test_scene_composes_effect_and_widget_frame_workflow():
    screen = RecordingScreen()
    from asciimatics.widgets import Frame

    frame = Frame(screen, 8, 24, has_border=False, can_scroll=False)
    layout = Layout([1])
    frame.add_layout(layout)
    layout.add_widget(Label("Panel"))
    frame.fix()
    scene = Scene([Print(screen, StaticRenderer(images=["Header"]), 0, x=0, speed=1), frame], duration=2)
    scene.reset()
    for effect in scene.effects:
        effect.update(0)
    assert scene.effects[-1] is frame
    assert any(call[0] in {"paint", "block_transfer"} for call in screen.calls)


@pytest.mark.depends_on("test_screen_control_and_key_constants_are_deterministic", "test_text_editing_and_validator_state")
def test_control_key_and_text_edit_workflow_uses_public_constants():
    text = Text()
    text.value = "ab"
    text.process_event(KeyboardEvent(Screen.KEY_HOME))
    text.process_event(KeyboardEvent(Screen.ctrl("X")))
    text.process_event(KeyboardEvent(ord("X")))
    assert text.value == "Xab"


@pytest.mark.depends_on("test_effect_reset_delete_count_and_default_properties", "test_scene_projects_name_duration_clear_and_effects")
def test_background_scene_lifecycle_workflow_is_local_and_repeatable():
    screen = RecordingScreen()
    effect = Background(screen, bg=4, stop_frame=2)
    scene = Scene([effect], duration=2, name="background")
    scene.reset()
    effect.update(0)
    scene.exit()
    scene.reset()
    effect.update(0)
    assert effect.scene is scene
    assert scene.duration == 2
