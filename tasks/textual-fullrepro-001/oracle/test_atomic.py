"""Atomic public API tests for Textual."""

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


class KeyEventApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.keys: list[str] = []

    def on_key(self, event: Key) -> None:
        self.keys.append(event.character or event.key)


class InputLogApp(App[None]):
    def __init__(
        self,
        value: str = "",
        *,
        select_on_focus: bool = False,
        restrict: str | None = None,
        max_length: int = 0,
    ) -> None:
        super().__init__()
        self.value = value
        self.select_on_focus = select_on_focus
        self.restrict = restrict
        self.max_length = max_length
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        yield Input(
            self.value,
            id="input",
            select_on_focus=self.select_on_focus,
            restrict=self.restrict,
            max_length=self.max_length,
        )

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Changed)
    @on(Input.Submitted)
    @on(Input.Blurred)
    def record(self, event: Input.Changed | Input.Submitted | Input.Blurred) -> None:
        self.messages.append(event)


class InputBlurApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        yield Input("seed", id="input", select_on_focus=False)
        yield Button("Focus", id="focus")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Changed)
    @on(Input.Submitted)
    @on(Input.Blurred)
    def record(self, event: Input.Changed | Input.Submitted | Input.Blurred) -> None:
        self.messages.append(event)


class DataTableLogApp(App[None]):
    def __init__(self, *, cursor_type: str = "cell") -> None:
        super().__init__()
        self.cursor_type = cursor_type
        self.messages: list[Message] = []

    def compose(self) -> ComposeResult:
        table = DataTable(id="table", cursor_type=self.cursor_type)
        table.focus()
        yield table

    @on(DataTable.CellHighlighted)
    @on(DataTable.CellSelected)
    @on(DataTable.RowHighlighted)
    @on(DataTable.RowSelected)
    @on(DataTable.ColumnHighlighted)
    @on(DataTable.ColumnSelected)
    @on(DataTable.HeaderSelected)
    @on(DataTable.RowLabelSelected)
    def record(
        self,
        event: (
            DataTable.CellHighlighted
            | DataTable.CellSelected
            | DataTable.RowHighlighted
            | DataTable.RowSelected
            | DataTable.ColumnHighlighted
            | DataTable.ColumnSelected
            | DataTable.HeaderSelected
            | DataTable.RowLabelSelected
        ),
    ) -> None:
        self.messages.append(event)


class TreeLogApp(App[None]):
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
    def record(
        self,
        event: (
            Tree.NodeHighlighted
            | Tree.NodeSelected
            | Tree.NodeExpanded
            | Tree.NodeCollapsed
        ),
    ) -> None:
        self.messages.append(event)


class TabsLogApp(App[None]):
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
    def record(
        self,
        event: (
            Tabs.TabActivated
            | Tabs.TabHidden
            | Tabs.TabShown
            | Tabs.TabDisabled
            | Tabs.TabEnabled
            | Tabs.Cleared
        ),
    ) -> None:
        self.messages.append(event)


class LayoutApp(App[None]):
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
        height: 5;
    }

    Tree {
        height: 6;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="stack"):
            yield Tabs("Alpha", "Beta", id="tabs")
            yield Input("seed", id="input", select_on_focus=False)
            yield DataTable(id="table")
            yield Tree("Root", id="tree")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "State")
        table.add_row("alpha", "open", key="alpha")
        table.add_row("beta", "closed", key="beta")
        tree = self.query_one(Tree)
        tree.root.add("alpha")
        tree.root.add("beta")
        self.query_one(Input).focus()


async def test_app_key_event_receives_pilot_press_character():
    async with KeyEventApp().run_test() as pilot:
        await pilot.press("a")
        assert pilot.app.keys == ["a"]


async def test_run_test_exposes_pilot_and_mounts_input():
    async with InputLogApp().run_test() as pilot:
        input_widget = pilot.app.query_one(Input)
        assert input_widget.value == ""
        assert input_widget.cursor_position == 0
        assert pilot.app.messages == []


async def test_input_press_updates_value_and_emits_changed():
    async with InputLogApp().run_test() as pilot:
        await pilot.press("h", "i")
        input_widget = pilot.app.query_one(Input)
        assert input_widget.value == "hi"
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "Changed",
            "Changed",
        ]


async def test_input_cursor_and_selection_follow_arrow_keys():
    async with InputLogApp("hello").run_test() as pilot:
        await pilot.press("end", "shift+left")
        input_widget = pilot.app.query_one(Input)
        assert input_widget.cursor_position == 4
        assert input_widget.selected_text == "o"


async def test_input_submit_emits_submitted_message():
    async with InputLogApp().run_test() as pilot:
        await pilot.press("h", "i", "enter")
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "Changed",
            "Changed",
            "Submitted",
        ]


async def test_input_blur_emits_blurred_message_when_focus_moves():
    async with InputBlurApp().run_test() as pilot:
        await pilot.press("end")
        await pilot.click("#focus")
        assert [type(message).__name__ for message in pilot.app.messages][-1] == "Blurred"


async def test_input_restrict_and_max_length_block_invalid_replacement():
    async with InputLogApp(restrict=r"\d*", max_length=3).run_test() as pilot:
        await pilot.press("1", "2", "3", "4", "a")
        input_widget = pilot.app.query_one(Input)
        assert input_widget.value == "123"


async def test_input_selection_and_delete_programmatic_helpers():
    async with InputLogApp("hello").run_test() as pilot:
        input_widget = pilot.app.query_one(Input)
        input_widget.selection = (1, 4)
        input_widget.delete_selection()
        assert input_widget.value == "ho"
        input_widget.replace("ell", 1, 1)
        assert input_widget.value == "hello"


async def test_datatable_add_columns_and_rows_preserve_order():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.add_columns("Name", "Priority")
        table.add_rows([("alpha", 2), ("beta", 1), ("gamma", 3)])
        assert table.row_count == 3
        assert table.get_row_at(0) == ["alpha", 2]
        assert table.get_row_at(1) == ["beta", 1]
        assert table.get_row_at(2) == ["gamma", 3]


async def test_datatable_row_and_column_keys_round_trip():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        name_key, state_key = table.add_columns("Name", "State")
        row_key = table.add_row("alpha", "open", key="alpha")
        assert table.get_row("alpha") == ["alpha", "open"]
        assert list(table.get_column(name_key)) == ["alpha"]
        assert list(table.get_column(state_key)) == ["open"]
        assert table.get_cell(row_key, name_key) == "alpha"


async def test_datatable_update_cell_and_coordinate_lookup_round_trip():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        name_key, _ = table.add_columns("Name", "State")
        row_key = table.add_row("alpha", "open", key="alpha")
        table.update_cell(row_key, name_key, "ALPHA")
        table.update_cell_at(Coordinate(0, 1), "closed")
        assert table.get_cell(row_key, name_key) == "ALPHA"
        assert table.get_cell_at(Coordinate(0, 1)) == "closed"
        assert table.coordinate_to_cell_key(Coordinate(0, 0)) == (row_key, name_key)


async def test_datatable_sort_changes_coordinate_projection():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        column = table.add_column("Priority")
        low = table.add_row(3)
        mid = table.add_row(2)
        high = table.add_row(1)
        table.sort(column)
        assert table.get_cell(low, column) == 3
        assert table.get_cell(mid, column) == 2
        assert table.get_cell(high, column) == 1
        assert table.get_row_at(0) == [1]


async def test_datatable_cell_cursor_highlight_and_select_messages():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        column_key = table.add_column("ABC")
        table.add_row("123")
        row_key = table.add_row("456")
        await pilot.click(DataTable, offset=Offset(1, 2))
        await pilot.click(DataTable, offset=Offset(1, 2))
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "CellHighlighted",
            "CellHighlighted",
            "CellSelected",
        ]
        highlighted = pilot.app.messages[1]
        selected = pilot.app.messages[2]
        assert highlighted.coordinate == Coordinate(1, 0)
        assert highlighted.cell_key == (row_key, column_key)
        assert selected.coordinate == Coordinate(1, 0)


async def test_datatable_row_cursor_highlight_and_select_messages():
    async with DataTableLogApp(cursor_type="row").run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.add_column("ABC")
        first = table.add_row("123")
        second = table.add_row("456")
        await pilot.click(DataTable, offset=Offset(1, 2))
        await pilot.click(DataTable, offset=Offset(1, 2))
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "RowHighlighted",
            "RowHighlighted",
            "RowSelected",
        ]
        highlighted = pilot.app.messages[1]
        selected = pilot.app.messages[2]
        assert highlighted.row_key == second
        assert highlighted.cursor_row == 1
        assert selected.row_key == second


async def test_datatable_column_cursor_highlight_and_select_messages():
    async with DataTableLogApp(cursor_type="column").run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        first, second = table.add_columns("A", "B")
        table.add_row(0, 1)
        table.add_row(2, 3)
        await pilot.click(DataTable, offset=Offset(1, 2))
        await pilot.click(DataTable, offset=Offset(1, 2))
        assert [type(message).__name__ for message in pilot.app.messages] == [
            "ColumnHighlighted",
            "ColumnHighlighted",
            "ColumnSelected",
        ]
        highlighted = pilot.app.messages[1]
        selected = pilot.app.messages[2]
        assert highlighted.column_key == first
        assert highlighted.cursor_column == 0
        assert selected.column_key == first


async def test_datatable_header_click_emits_header_selected():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        column_key = table.add_column("number")
        table.add_row(3)
        await pilot.click(DataTable, offset=Offset(3, 0))
        message = pilot.app.messages[-1]
        assert type(message).__name__ == "HeaderSelected"
        assert message.column_key == column_key
        assert message.column_index == 0


async def test_datatable_row_label_click_emits_row_label_selected():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.add_column("number")
        row_key = table.add_row(3, label="A")
        await pilot.click(DataTable, offset=Offset(1, 1))
        message = pilot.app.messages[-1]
        assert type(message).__name__ == "RowLabelSelected"
        assert message.row_key == row_key
        assert message.row_index == 0


async def test_tree_root_and_added_nodes_have_parent_links():
    async with TreeLogApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        draft = tree.root.children[0]
        review = tree.root.children[1]
        assert tree.root.parent is None
        assert draft.parent is tree.root
        assert review.parent is tree.root
        assert draft.is_last is False
        assert review.is_last is False


async def test_tree_expand_and_collapse_messages_are_public():
    async with TreeLogApp().run_test() as pilot:
        await pilot.pause()
        pilot.app.messages.clear()
        tree = pilot.app.query_one(Tree)
        tree.root.expand()
        tree.root.collapse()
        await pilot.pause()
        assert [type(message).__name__ for message in pilot.app.messages][:2] == [
            "NodeExpanded",
            "NodeCollapsed",
        ]


async def test_tree_keyboard_selection_and_auto_expand_messages():
    async with TreeLogApp().run_test() as pilot:
        await pilot.press("enter", "down")
        assert [type(message).__name__ for message in pilot.app.messages][:4] == [
            "NodeHighlighted",
            "NodeSelected",
            "NodeExpanded",
            "NodeHighlighted",
        ]


async def test_tree_clear_resets_root_and_cursor():
    async with TreeLogApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        tree.clear()
        assert tree.root.label.plain == "Root"
        assert len(tree.root.children) == 0
        assert tree.cursor_node is not None
        assert tree.cursor_node.label.plain == "Root"


async def test_tabs_empty_and_populated_states_are_distinct():
    class EmptyTabsApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Tabs(id="tabs")

    async with EmptyTabsApp().run_test() as pilot:
        empty = pilot.app.query_one(Tabs)
        assert empty.tab_count == 0
        assert empty.active_tab is None

    async with TabsLogApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        assert tabs.tab_count == 3
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-1"


async def test_tabs_clicking_a_tab_changes_active_tab():
    async with TabsLogApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await pilot.click("#tab-2")
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-2"
        assert [type(message).__name__ for message in pilot.app.messages][-1] == "TabActivated"


async def test_tabs_keyboard_navigation_wraps_across_edges():
    async with TabsLogApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        await pilot.press("right", "right", "right", "right")
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-2"
        await pilot.press("left", "left", "left")
        assert tabs.active_tab is not None
        assert tabs.active_tab.id == "tab-2"


async def test_tabs_hide_show_disable_enable_emit_public_messages():
    async with TabsLogApp().run_test() as pilot:
        tabs = pilot.app.query_one(Tabs)
        tabs.hide("tab-2")
        tabs.show("tab-2")
        tabs.disable("tab-3")
        tabs.enable("tab-3")
        await pilot.pause()
        names = [type(message).__name__ for message in pilot.app.messages]
        assert names[-4:] == [
            "TabHidden",
            "TabShown",
            "TabDisabled",
            "TabEnabled",
        ]


async def test_css_layout_projects_widget_regions():
    async with LayoutApp().run_test(size=(80, 24)) as pilot:
        tabs = pilot.app.query_one("#tabs", Tabs)
        input_widget = pilot.app.query_one("#input", Input)
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        assert (tabs.region.x, tabs.region.y, tabs.region.width, tabs.region.height) == (0, 0, 80, 2)
        assert (input_widget.region.x, input_widget.region.y, input_widget.region.width, input_widget.region.height) == (0, 2, 80, 3)
        assert (table.region.x, table.region.y, table.region.width, table.region.height) == (0, 5, 80, 5)
        assert (tree.region.x, tree.region.y, tree.region.width, tree.region.height) == (0, 10, 80, 6)


async def test_css_style_projection_sets_expected_widget_sizes():
    async with LayoutApp().run_test(size=(80, 24)) as pilot:
        tabs = pilot.app.query_one("#tabs", Tabs)
        input_widget = pilot.app.query_one("#input", Input)
        table = pilot.app.query_one("#table", DataTable)
        tree = pilot.app.query_one("#tree", Tree)
        assert tabs.styles.height.value == 2
        assert input_widget.styles.height.value == 3
        assert table.styles.height.value == 5
        assert tree.styles.height.value == 6


async def test_input_home_and_end_actions_update_cursor_position():
    async with InputLogApp(value="alpha").run_test() as pilot:
        input_widget = pilot.app.query_one(Input)
        await pilot.press("end")
        assert input_widget.cursor_position == 5
        await pilot.press("home")
        assert input_widget.cursor_position == 0


async def test_datatable_clear_rows_preserves_public_columns():
    async with DataTableLogApp().run_test() as pilot:
        table = pilot.app.query_one(DataTable)
        table.add_columns("Name", "State")
        table.add_row("alpha", "open")
        table.clear()
        table.add_row("beta", "closed")
        assert table.row_count == 1
        assert len(table.columns) == 2
        assert table.get_row_at(0) == ["beta", "closed"]


async def test_tree_add_leaf_and_remove_preserve_parent_projection():
    async with TreeLogApp().run_test() as pilot:
        tree = pilot.app.query_one(Tree)
        tree.clear()
        branch = tree.root.add("branch")
        leaf = branch.add_leaf("leaf")
        assert leaf.parent is branch
        assert branch.children[0] is leaf
        leaf.remove()
        assert list(branch.children) == []
