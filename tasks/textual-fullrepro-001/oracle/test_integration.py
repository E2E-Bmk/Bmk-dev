"""Integration tests for public Textual projections."""

from __future__ import annotations

import pytest
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.coordinate import Coordinate
from textual.events import Key
from textual.geometry import Offset
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Tab, Tabs, Tree


pytestmark = pytest.mark.asyncio


class DashboardApp(App[None]):
    CSS = """
    #stack {
        width: 100%;
        height: 100%;
    }

    Tabs {
        height: 2;
    }

    Input {
        height: 3;
    }

    DataTable {
        height: 6;
    }

    Tree {
        height: 6;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="stack"):
            yield Tabs("Inbox", "Archive", id="tabs")
            yield Input("", id="input", select_on_focus=False)
            yield DataTable(id="table")
            yield Tree("Root", id="tree")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Name", key="Name")
        table.add_column("State", key="State")
        table.add_row("alpha", "open", key="alpha")
        table.add_row("beta", "closed", key="beta")
        tree = self.query_one(Tree)
        tree.root.add("alpha")
        tree.root.add("beta")
        self.query_one(Input).focus()

    @on(Input.Changed)
    @on(Input.Submitted)
    @on(Input.Blurred)
    @on(Tabs.TabActivated)
    @on(Tabs.TabHidden)
    @on(Tabs.TabShown)
    @on(Tabs.TabDisabled)
    @on(Tabs.TabEnabled)
    @on(Tabs.Cleared)
    @on(DataTable.CellHighlighted)
    @on(DataTable.CellSelected)
    @on(DataTable.RowHighlighted)
    @on(DataTable.RowSelected)
    @on(DataTable.ColumnHighlighted)
    @on(DataTable.ColumnSelected)
    @on(DataTable.HeaderSelected)
    @on(DataTable.RowLabelSelected)
    @on(Tree.NodeHighlighted)
    @on(Tree.NodeSelected)
    @on(Tree.NodeExpanded)
    @on(Tree.NodeCollapsed)
    def record(self, event: Message) -> None:
        self.messages.append(event)


class InputFocusApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        yield Input("seed", id="input", select_on_focus=False)
        yield Tabs("One", "Two", id="tabs")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Changed)
    @on(Input.Submitted)
    @on(Input.Blurred)
    @on(Tabs.TabActivated)
    def record(self, event: Message) -> None:
        self.messages.append(event)


class TableTreeApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield DataTable(id="table")
            yield Tree("Root", id="tree")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Name", key="Name")
        table.add_column("State", key="State")
        table.add_row("draft", "open", key="draft")
        table.add_row("review", "closed", key="review")
        table.add_row("done", "closed", key="done")
        self.query_one(Tree).root.add("draft")
        self.query_one(Tree).root.add("review")
        self.query_one(Tree).root.add("done")
        table.focus()

    @on(DataTable.CellHighlighted)
    @on(DataTable.CellSelected)
    @on(DataTable.RowHighlighted)
    @on(DataTable.RowSelected)
    @on(DataTable.ColumnHighlighted)
    @on(DataTable.ColumnSelected)
    @on(DataTable.HeaderSelected)
    @on(DataTable.RowLabelSelected)
    @on(Tree.NodeHighlighted)
    @on(Tree.NodeSelected)
    @on(Tree.NodeExpanded)
    @on(Tree.NodeCollapsed)
    def record(self, event: Message) -> None:
        self.messages.append(event)


class TabsWorkApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        yield Tabs("One", "Two", "Three", id="tabs")

    def on_mount(self) -> None:
        self.query_one(Tabs).focus()

    @on(Tabs.TabActivated)
    @on(Tabs.TabHidden)
    @on(Tabs.TabShown)
    @on(Tabs.TabDisabled)
    @on(Tabs.TabEnabled)
    @on(Tabs.Cleared)
    def record(self, event: Message) -> None:
        self.messages.append(event)


class TreeWorkApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        yield Tree("Root", id="tree")

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.add("draft")
        tree.root.add("review")
        tree.root.add("done")
        tree.focus()

    @on(Tree.NodeHighlighted)
    @on(Tree.NodeSelected)
    @on(Tree.NodeExpanded)
    @on(Tree.NodeCollapsed)
    def record(self, event: Message) -> None:
        self.messages.append(event)


@pytest.mark.depends_on(
    "test_input_press_updates_value_and_emits_changed",
    "test_input_submit_emits_submitted_message",
    "test_input_blur_emits_blurred_message_when_focus_moves",
)
async def test_input_edit_submit_and_blur_workflow():
    async with InputFocusApp().run_test() as pilot:
        await pilot.pause()
        pilot.app.messages.clear()
        await pilot.press("h", "i", "enter")
        await pilot.click("#tabs")
        input_widget = pilot.app.query_one(Input)
        assert input_widget.value == "seedhi"
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "Changed",
            "Changed",
            "Submitted",
            "Blurred",
        ]


@pytest.mark.depends_on(
    "test_input_cursor_and_selection_follow_arrow_keys",
    "test_input_selection_and_delete_programmatic_helpers",
)
async def test_input_click_selection_delete_and_retype_workflow():
    async with InputFocusApp().run_test() as pilot:
        input_widget = pilot.app.query_one(Input)
        await pilot.click("#input", offset=Offset(2, 1))
        await pilot.press("shift+left", "backspace", "o")
        assert input_widget.value == "oseed"
        assert input_widget.cursor_position == 1


@pytest.mark.depends_on(
    "test_input_restrict_and_max_length_block_invalid_replacement",
    "test_input_submit_emits_submitted_message",
)
async def test_input_restrict_submit_and_blur_workflow():
    class RestrictedInputApp(InputFocusApp):
        def compose(self) -> ComposeResult:
            yield Input("", id="input", select_on_focus=False, restrict=r"\d*", max_length=3)
            yield Tabs("One", "Two", id="tabs")

    async with RestrictedInputApp().run_test() as pilot:
        await pilot.press("1", "2", "3", "4", "enter")
        await pilot.click("#tabs")
        input_widget = pilot.app.query_one(Input)
        assert input_widget.value == "123"
        assert [type(message).__name__ for message in pilot.app.messages][-2:] == [
            "Submitted",
            "Blurred",
        ]


@pytest.mark.depends_on(
    "test_datatable_add_columns_and_rows_preserve_order",
    "test_datatable_update_cell_and_coordinate_lookup_round_trip",
    "test_datatable_sort_changes_coordinate_projection",
)
async def test_datatable_add_update_sort_and_coordinate_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        priority = table.add_column("Priority", key="Priority")
        table.update_cell("draft", "State", "reviewing")
        table.update_cell("draft", "Priority", 2)
        table.update_cell("review", "Priority", 3)
        table.update_cell("done", "Priority", 1)
        table.sort(priority, reverse=True)
        assert table.get_cell("draft", "State") == "reviewing"
        assert table.get_row_at(0) == ["review", "closed", 3]
        assert table.get_cell_at(Coordinate(0, 2)) == 3


@pytest.mark.depends_on(
    "test_datatable_cell_cursor_highlight_and_select_messages",
    "test_datatable_sort_changes_coordinate_projection",
)
async def test_datatable_click_then_sort_keeps_row_identity_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.clear(columns=True)
        column_key = table.add_column("Priority")
        row_key = table.add_row(3, key="alpha")
        table.add_row(1, key="beta")
        await pilot.click(DataTable, offset=Offset(1, 2))
        table.sort(column_key)
        assert table.get_cell(row_key, column_key) == 3
        assert table.get_row("alpha") == [3]
        assert type(pilot.app.messages[1]).__name__ == "CellHighlighted"


@pytest.mark.depends_on(
    "test_datatable_row_cursor_highlight_and_select_messages",
    "test_datatable_column_cursor_highlight_and_select_messages",
)
async def test_datatable_row_and_column_cursor_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.cursor_type = "row"
        await pilot.click(DataTable, offset=Offset(1, 2))
        await pilot.press("down", "enter")
        table.cursor_type = "column"
        await pilot.press("right", "enter")
        assert [type(message).__name__ for message in pilot.app.messages if "Selected" in type(message).__name__][-2:] == [
            "RowSelected",
            "ColumnSelected",
        ]


@pytest.mark.depends_on(
    "test_datatable_header_click_emits_header_selected",
    "test_datatable_row_label_click_emits_row_label_selected",
)
async def test_datatable_header_and_row_label_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("Name")
        table.add_row("alpha", label="A")
        await pilot.click(DataTable, offset=Offset(3, 0))
        await pilot.click(DataTable, offset=Offset(1, 1))
        assert [type(message).__name__ for message in pilot.app.messages][-2:] == [
            "HeaderSelected",
            "RowLabelSelected",
        ]


@pytest.mark.depends_on(
    "test_tree_expand_and_collapse_messages_are_public",
    "test_tree_keyboard_selection_and_auto_expand_messages",
)
async def test_tree_expand_select_collapse_workflow():
    async with TreeWorkApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        tree.root.expand()
        await pilot.press("down", "enter", "space")
        names = [type(message).__name__ for message in pilot.app.messages]
        assert "NodeSelected" in names
        assert names[-1] == "NodeCollapsed"


@pytest.mark.depends_on(
    "test_tree_root_and_added_nodes_have_parent_links",
    "test_tree_keyboard_selection_and_auto_expand_messages",
)
async def test_tree_move_cursor_and_reset_workflow():
    async with TreeWorkApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        node = tree.root.children[1]
        tree.move_cursor(node)
        tree.move_cursor(None)
        tree.reset("Root Again")
        assert tree.root.label.plain == "Root Again"
        assert "NodeHighlighted" in [type(message).__name__ for message in pilot.app.messages]


@pytest.mark.depends_on(
    "test_tree_clear_resets_root_and_cursor",
    "test_tree_root_and_added_nodes_have_parent_links",
)
async def test_tree_clear_and_repopulate_workflow():
    async with TreeWorkApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        tree.clear()
        tree.root.add("fresh")
        tree.root.expand()
        assert tree.root.children[0].label.plain == "fresh"
        assert tree.root.children[0].parent is tree.root


@pytest.mark.depends_on(
    "test_tabs_empty_and_populated_states_are_distinct",
    "test_tabs_keyboard_navigation_wraps_across_edges",
)
async def test_tabs_add_navigate_and_remove_workflow():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await tabs.add_tab("Four")
        await pilot.press("right", "right")
        await tabs.remove_tab("tab-2")
        assert tabs.active_tab is not None
        assert tabs.tab_count == 3
        assert tabs.active_tab.id in {"tab-1", "tab-3", "tab-4"}


@pytest.mark.depends_on(
    "test_tabs_hide_show_disable_enable_emit_public_messages",
    "test_tabs_keyboard_navigation_wraps_across_edges",
)
async def test_tabs_hide_show_disable_enable_workflow():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        tabs.hide("tab-2")
        tabs.show("tab-2")
        tabs.disable("tab-3")
        await pilot.press("right")
        tabs.enable("tab-3")
        await pilot.pause()
        names = [type(message).__name__ for message in pilot.app.messages]
        assert "TabHidden" in names
        assert "TabShown" in names
        assert "TabDisabled" in names
        assert "TabEnabled" in names


@pytest.mark.depends_on(
    "test_tabs_clicking_a_tab_changes_active_tab",
    "test_tabs_keyboard_navigation_wraps_across_edges",
)
async def test_tabs_mouse_and_keyboard_navigation_share_active_state():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await pilot.click("#tab-2")
        await pilot.press("right")
        await pilot.click("#tab-1")
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-1"


@pytest.mark.depends_on(
    "test_tabs_empty_and_populated_states_are_distinct",
    "test_tabs_hide_show_disable_enable_emit_public_messages",
)
async def test_tabs_clear_and_readd_workflow():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await tabs.clear()
        await tabs.add_tab("Rebuilt")
        assert tabs.tab_count == 1
        assert tabs.active_tab is not None
        assert tabs.active_tab.label_text == "Rebuilt"


@pytest.mark.depends_on(
    "test_css_layout_projects_widget_regions",
    "test_css_style_projection_sets_expected_widget_sizes",
)
async def test_layout_regions_remain_stable_after_interactions():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        tabs = pilot.app.query_one("#tabs", Tabs)
        input_widget = pilot.app.query_one("#input", Input)
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        await pilot.press("h")
        await pilot.click("#tabs")
        await pilot.click("#table", offset=Offset(1, 2))
        await pilot.click("#tree", offset=Offset(1, 1))
        assert (tabs.region.y, input_widget.region.y, table.region.y, tree.region.y) == (0, 2, 5, 11)


@pytest.mark.depends_on(
    "test_input_submit_emits_submitted_message",
    "test_tabs_clicking_a_tab_changes_active_tab",
    "test_datatable_cell_cursor_highlight_and_select_messages",
)
async def test_combined_input_submit_tab_click_and_table_selection_workflow():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        input_widget = pilot.app.query_one("#input", Input)
        table = pilot.app.query_one("#table", DataTable)
        await pilot.press("a", "b", "enter")
        await pilot.click("#tabs")
        await pilot.click("#table", offset=Offset(1, 2))
        assert input_widget.value == "ab"
        assert table.get_row("alpha") == ["alpha", "open"]
        names = [type(message).__name__ for message in pilot.app.messages]
        assert "Submitted" in names
        assert "Blurred" in names
        assert names[-1] == "CellHighlighted"


@pytest.mark.depends_on(
    "test_datatable_cell_cursor_highlight_and_select_messages",
    "test_tree_keyboard_selection_and_auto_expand_messages",
)
async def test_combined_tree_and_table_selection_messages_share_one_app_log():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        await pilot.click("#table", offset=Offset(1, 2))
        await pilot.click("#tree", offset=Offset(1, 1))
        names = [type(message).__name__ for message in pilot.app.messages]
        assert "CellHighlighted" in names
        assert "NodeHighlighted" in names
        assert tree.root.children[0].label.plain == "alpha"


@pytest.mark.depends_on(
    "test_input_blur_emits_blurred_message_when_focus_moves",
    "test_css_layout_projects_widget_regions",
)
async def test_combined_tab_click_blurs_input_and_keeps_layout_projections():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        input_widget = pilot.app.query_one("#input", Input)
        tabs = pilot.app.query_one("#tabs", Tabs)
        await pilot.press("x")
        await pilot.click("#tabs")
        assert input_widget.value == "x"
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-1"
        assert (tabs.region.height, input_widget.region.height) == (2, 3)


@pytest.mark.depends_on(
    "test_input_submit_emits_submitted_message",
    "test_datatable_add_columns_and_rows_preserve_order",
    "test_tree_root_and_added_nodes_have_parent_links",
)
async def test_combined_dashboard_rebuilds_table_and_tree_from_input_submission():
    class RebuildingDashboardApp(DashboardApp):
        def on_input_submitted(self, event: Input.Submitted) -> None:
            table = self.query_one(DataTable)
            tree = self.query_one(Tree)
            table.add_row(event.value, "submitted", key=event.value)
            tree.root.add(event.value)

    async with RebuildingDashboardApp().run_test(size=(80, 24)) as pilot:
        await pilot.press("d", "e", "l", "t", "a", "enter")
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        assert table.get_row("delta") == ["delta", "submitted"]
        assert tree.root.children[-1].label.plain == "delta"


@pytest.mark.depends_on(
    "test_app_key_event_receives_pilot_press_character",
    "test_input_submit_emits_submitted_message",
    "test_tabs_clicking_a_tab_changes_active_tab",
)
async def test_app_key_event_and_widget_messages_can_coexist_in_one_workflow():
    class MixedApp(App[None]):
        def __init__(self) -> None:
            super().__init__()
            self.keys: list[str] = []
            self.messages: list[Message] = []

        def compose(self) -> ComposeResult:
            with Vertical():
                yield Input("", id="input", select_on_focus=False)
                yield Tabs("One", "Two", id="tabs")

        def on_mount(self) -> None:
            self.query_one(Input).focus()

        def on_key(self, event: Key) -> None:
            self.keys.append(event.character or event.key)

        @on(Input.Changed)
        @on(Input.Submitted)
        @on(Input.Blurred)
        @on(Tabs.TabActivated)
        def record(self, event: Message) -> None:
            self.messages.append(event)

    async with MixedApp().run_test() as pilot:
        await pilot.pause()
        pilot.app.messages.clear()
        await pilot.press("a", "enter")
        await pilot.click("#tabs")
        assert pilot.app.keys == ["enter"]
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "Changed",
            "Submitted",
            "Blurred",
        ]


@pytest.mark.depends_on(
    "test_css_layout_projects_widget_regions",
    "test_tabs_clicking_a_tab_changes_active_tab",
    "test_datatable_cell_cursor_highlight_and_select_messages",
    "test_tree_keyboard_selection_and_auto_expand_messages",
)
async def test_pilot_clicking_multiple_widgets_preserves_event_order():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        await pilot.click("#input")
        await pilot.click("#tabs")
        await pilot.click("#table", offset=Offset(1, 2))
        await pilot.click("#tree", offset=Offset(1, 1))
        names = [type(message).__name__ for message in pilot.app.messages]
        assert "Blurred" in names
        assert "CellHighlighted" in names
        assert pilot.app.query_one(Tabs).active_tab is not None


@pytest.mark.depends_on(
    "test_datatable_add_columns_and_rows_preserve_order",
    "test_datatable_update_cell_and_coordinate_lookup_round_trip",
)
async def test_datatable_remove_row_and_column_after_selection_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        await pilot.click(DataTable, offset=Offset(1, 2))
        table.remove_row("review")
        table.remove_column("State")
        assert table.get_row("draft") == ["draft"]
        assert table.row_count == 2


@pytest.mark.depends_on(
    "test_tabs_empty_and_populated_states_are_distinct",
    "test_tabs_clicking_a_tab_changes_active_tab",
)
async def test_tabs_remove_active_and_clear_message_workflow():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await pilot.click("#tab-2")
        await tabs.remove_tab("tab-2")
        await tabs.clear()
        assert tabs.active_tab is None
        assert [type(message).__name__ for message in pilot.app.messages][-1] == "Cleared"


@pytest.mark.depends_on(
    "test_tree_root_and_added_nodes_have_parent_links",
    "test_tree_keyboard_selection_and_auto_expand_messages",
)
async def test_tree_show_root_and_keyboard_navigation_workflow():
    async with TreeWorkApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        tree.root.expand()
        tree.show_root = False
        await pilot.press("down", "enter")
        assert tree.show_root is False
        assert tree.cursor_node is not None
        assert tree.cursor_node.label.plain in {"draft", "review"}


@pytest.mark.depends_on(
    "test_input_cursor_and_selection_follow_arrow_keys",
    "test_input_selection_and_delete_programmatic_helpers",
)
async def test_input_home_selection_and_replacement_workflow():
    async with InputFocusApp().run_test() as pilot:
        input_widget = pilot.app.query_one(Input)
        await pilot.press("end", "shift+home", "x")
        assert input_widget.value == "x"
        assert input_widget.cursor_position == 1


@pytest.mark.depends_on(
    "test_datatable_clear_rows_preserves_public_columns",
    "test_datatable_sort_changes_coordinate_projection",
)
async def test_datatable_clear_rebuild_and_sort_workflow():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("Name", key="Name")
        priority = table.add_column("Priority", key="Priority")
        table.add_row("alpha", 3, key="alpha")
        table.add_row("beta", 1, key="beta")
        table.add_row("gamma", 2, key="gamma")
        table.sort(priority)
        assert [table.get_row_at(index) for index in range(3)] == [
            ["beta", 1],
            ["gamma", 2],
            ["alpha", 3],
        ]
        assert table.get_row("alpha") == ["alpha", 3]


@pytest.mark.depends_on(
    "test_tree_add_leaf_and_remove_preserve_parent_projection",
    "test_tree_expand_and_collapse_messages_are_public",
)
async def test_tree_nested_add_remove_and_cursor_workflow():
    async with TreeWorkApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        branch = tree.root.add("branch")
        leaf = branch.add_leaf("leaf")
        tree.root.expand()
        branch.expand()
        tree.move_cursor(leaf)
        leaf.remove()
        assert branch.parent is tree.root
        assert list(branch.children) == []
        assert tree.cursor_node is not leaf


@pytest.mark.depends_on(
    "test_tabs_empty_and_populated_states_are_distinct",
    "test_tabs_hide_show_disable_enable_emit_public_messages",
)
async def test_tabs_relabel_and_programmatic_activation_workflow():
    async with TabsWorkApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        second = tabs.get_tab("tab-2")
        assert second is not None
        second.label = "Renamed"
        tabs.active = "tab-2"
        await pilot.pause()
        assert tabs.active_tab is second
        assert second.label_text == "Renamed"


@pytest.mark.depends_on(
    "test_datatable_add_columns_and_rows_preserve_order",
    "test_tree_root_and_added_nodes_have_parent_links",
)
async def test_table_and_tree_rebuild_keep_shared_item_identity():
    async with TableTreeApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        tree = pilot.app.query_one(Tree)
        table.remove_row("review")
        tree.root.children[1].remove()
        table.add_row("review", "reopened", key="review")
        tree.root.add_leaf("review")
        assert table.get_row("review") == ["review", "reopened"]
        assert [child.label.plain for child in tree.root.children] == [
            "draft",
            "done",
            "review",
        ]


@pytest.mark.depends_on(
    "test_css_layout_projects_widget_regions",
    "test_tabs_empty_and_populated_states_are_distinct",
)
async def test_dashboard_reset_workflow_keeps_widget_regions_stable():
    async with DashboardApp().run_test(size=(80, 24)) as pilot:
        tabs = pilot.app.query_one("#tabs", Tabs)
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        await tabs.clear()
        await tabs.add_tab("Rebuilt")
        table.clear(columns=True)
        table.add_columns("Name", "State")
        table.add_row("fresh", "open", key="fresh")
        tree.clear()
        tree.root.add_leaf("fresh")
        assert tabs.active_tab is not None
        assert table.get_row("fresh") == ["fresh", "open"]
        assert tree.root.children[0].label.plain == "fresh"
        assert (tabs.region.height, table.region.height, tree.region.height) == (2, 6, 6)
