"""Interface graphique Tkinter pour Bataille Navale."""

from __future__ import annotations

import argparse
import logging
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Sequence

from .controller import GameController, Settings
from .i18n_fr import tr
from .model import Coordinate, Orientation
from .rules import ShipSpec, ship_cells
from .storage import default_save_path
from .utils import configure_logging

LOGGER = logging.getLogger(__name__)
CELL_SIZE = 36


class BoardCanvas(tk.Canvas):
    """Canvas représentant une grille de bataille navale."""

    def __init__(
        self,
        master: tk.Misc,
        grid_size: int,
        show_ships: bool,
        click_callback: Callable[[Coordinate], None] | None = None,
        motion_callback: Callable[[Coordinate], None] | None = None,
    ) -> None:
        super().__init__(
            master,
            width=grid_size * CELL_SIZE,
            height=grid_size * CELL_SIZE,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#3a3a3a",
        )
        self.grid_size = grid_size
        self.show_ships = show_ships
        self.click_callback = click_callback
        self.motion_callback = motion_callback
        self.interactive = True
        self._draw_grid()
        if click_callback is not None:
            self.bind("<Button-1>", self._on_click)
        if motion_callback is not None:
            self.bind("<Motion>", self._on_motion)

    def configure_board(self, grid_size: int) -> None:
        self.grid_size = grid_size
        self.config(width=grid_size * CELL_SIZE, height=grid_size * CELL_SIZE)
        self.delete("grid")
        self._draw_grid()

    def set_interactive(self, enabled: bool) -> None:
        self.interactive = enabled
        cursor = "hand2" if enabled else "arrow"
        self.configure(cursor=cursor)

    def _draw_grid(self) -> None:
        for idx in range(self.grid_size + 1):
            offset = idx * CELL_SIZE
            self.create_line(0, offset, self.grid_size * CELL_SIZE, offset, tags="grid", fill="#b0b0b0")
            self.create_line(offset, 0, offset, self.grid_size * CELL_SIZE, tags="grid", fill="#b0b0b0")

    def _on_click(self, event: tk.Event[tk.Misc]) -> None:
        if not self.interactive or self.click_callback is None:
            return
        coord = self._event_to_coordinate(event)
        if coord:
            self.click_callback(coord)

    def _on_motion(self, event: tk.Event[tk.Misc]) -> None:
        if self.motion_callback is None:
            return
        coord = self._event_to_coordinate(event)
        if coord:
            self.motion_callback(coord)

    def _event_to_coordinate(self, event: tk.Event[tk.Misc]) -> Coordinate | None:
        column = int(event.x // CELL_SIZE)
        row = int(event.y // CELL_SIZE)
        if 0 <= row < self.grid_size and 0 <= column < self.grid_size:
            return Coordinate(row=row, column=column)
        return None

    def render(self, game_grid, reveal: bool) -> None:
        self.delete("content")
        if reveal:
            for ship in game_grid.ships:
                color = "#8ca5ff" if not ship.is_sunk else "#ff6f6f"
                for cell in ship.cells:
                    self._draw_rectangle(cell, fill=color, tags="content", outline="")
        for coord, result in game_grid.shots().items():
            if result.name == "MISS":
                self._draw_miss(coord)
            elif result.name == "HIT":
                self._draw_hit(coord)
            elif result.name == "SUNK":
                ship = next((s for s in game_grid.ships if coord in s.cells), None)
                if ship:
                    for cell in ship.cells:
                        self._draw_rectangle(cell, fill="#ff6f6f", tags="content", outline="")

    def _draw_rectangle(self, coord: Coordinate, fill: str, tags: str, outline: str = "#2b2b2b") -> int:
        x0 = coord.column * CELL_SIZE + 2
        y0 = coord.row * CELL_SIZE + 2
        x1 = x0 + CELL_SIZE - 4
        y1 = y0 + CELL_SIZE - 4
        return int(self.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=2, tags=tags))

    def _draw_miss(self, coord: Coordinate) -> None:
        x0 = coord.column * CELL_SIZE + CELL_SIZE / 2
        y0 = coord.row * CELL_SIZE + CELL_SIZE / 2
        radius = CELL_SIZE / 6
        self.create_oval(
            x0 - radius,
            y0 - radius,
            x0 + radius,
            y0 + radius,
            fill="#444444",
            outline="",
            tags="content",
        )

    def _draw_hit(self, coord: Coordinate) -> None:
        x0 = coord.column * CELL_SIZE + 6
        y0 = coord.row * CELL_SIZE + 6
        x1 = x0 + CELL_SIZE - 12
        y1 = y0 + CELL_SIZE - 12
        self.create_line(x0, y0, x1, y1, fill="#d32f2f", width=3, tags="content")
        self.create_line(x0, y1, x1, y0, fill="#d32f2f", width=3, tags="content")

    def show_preview(self, cells: Sequence[Coordinate], valid: bool) -> None:
        self.delete("preview")
        color = "#5cb85c" if valid else "#d9534f"
        for coord in cells:
            if 0 <= coord.row < self.grid_size and 0 <= coord.column < self.grid_size:
                self._draw_rectangle(coord, fill=color, tags="preview")

    def clear_preview(self) -> None:
        self.delete("preview")

    def flash(self, coord: Coordinate, color: str) -> None:
        marker = self._draw_rectangle(coord, fill=color, tags="flash", outline="")
        self.after(150, lambda: self.delete(marker))


@dataclass
class FleetOption:
    name: str
    length: int
    enabled: tk.BooleanVar
    length_var: tk.IntVar


class SettingsDialog(tk.Toplevel):
    """Boîte de dialogue pour modifier les paramètres."""

    def __init__(self, master: tk.Misc, settings: Settings) -> None:
        super().__init__(master)
        self.title(tr("dialog_settings_title"))
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result: tuple[int, Sequence[ShipSpec], str] | None = None
        self.grid_var = tk.IntVar(value=settings.grid_size)
        self.ai_var = tk.StringVar(value=settings.ai_level)
        self.options: List[FleetOption] = []
        self._build(settings)

    def _build(self, settings: Settings) -> None:
        padding = {"padx": 12, "pady": 6}
        size_label = ttk.Label(self, text=tr("dialog_settings_grid_size"))
        size_label.grid(row=0, column=0, sticky="w", **padding)
        size_spin = ttk.Spinbox(self, from_=8, to=12, textvariable=self.grid_var, width=5)
        size_spin.grid(row=0, column=1, sticky="e", **padding)
        ai_label = ttk.Label(self, text=tr("dialog_settings_ai"))
        ai_label.grid(row=1, column=0, sticky="w", **padding)
        ai_combo = ttk.Combobox(self, textvariable=self.ai_var, values=["basique", "chasseur"], state="readonly", width=10)
        ai_combo.grid(row=1, column=1, sticky="e", **padding)
        fleet_frame = ttk.LabelFrame(self, text=tr("dialog_settings_fleet"))
        fleet_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 12))
        for idx, spec in enumerate(settings.fleet):
            enabled = tk.BooleanVar(value=True)
            length_var = tk.IntVar(value=spec.length)
            option = FleetOption(spec.name, spec.length, enabled, length_var)
            self.options.append(option)
            check = ttk.Checkbutton(fleet_frame, text=spec.name, variable=enabled)
            check.grid(row=idx, column=0, sticky="w", padx=8, pady=2)
            spin = ttk.Spinbox(fleet_frame, from_=2, to=5, textvariable=length_var, width=5)
            spin.grid(row=idx, column=1, sticky="e", padx=8, pady=2)
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 12))
        ok_btn = ttk.Button(button_frame, text=tr("dialog_settings_confirm"), command=self._on_confirm)
        ok_btn.grid(row=0, column=0, padx=6)
        cancel_btn = ttk.Button(button_frame, text=tr("dialog_settings_cancel"), command=self._on_cancel)
        cancel_btn.grid(row=0, column=1, padx=6)

    def _on_confirm(self) -> None:
        fleet = [ShipSpec(opt.name, opt.length_var.get()) for opt in self.options if opt.enabled.get()]
        if not fleet:
            messagebox.showerror(tr("dialog_settings_title"), tr("placement_error"), parent=self)
            return
        self.result = (self.grid_var.get(), fleet, self.ai_var.get())
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


class GameApp(tk.Tk):
    """Application Tkinter principale."""

    def __init__(self, settings: Settings, seed: int | None) -> None:
        super().__init__()
        self.title(tr("app_title"))
        self.minsize(900, 520)
        self.controller = GameController(settings=settings, seed=seed)
        self.controller.new_game(manual=True)
        self.pending_ships: List[str] = list(self.controller.available_ship_names())
        self.orientation = Orientation.HORIZONTAL
        self.waiting_ai = False
        self.status_var = tk.StringVar(value=tr("placement_instruction"))
        self.turn_var = tk.StringVar(value=tr("status_turn_player"))
        self.shots_var = tk.StringVar()
        self.remaining_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        self._build_menu()
        self._build_layout()
        self.bind_all("<KeyPress-r>", self._rotate)
        self.bind_all("<KeyPress-R>", self._rotate)
        self.bind_all("<KeyPress-n>", lambda _: self._new_game())
        self.bind_all("<KeyPress-N>", lambda _: self._new_game())
        self.bind_all("<KeyPress-s>", lambda _: self._save())
        self.bind_all("<KeyPress-S>", lambda _: self._save())
        self.bind_all("<KeyPress-c>", lambda _: self._load())
        self.bind_all("<KeyPress-C>", lambda _: self._load())
        self.bind_all("<KeyPress-p>", lambda _: self._open_settings())
        self.bind_all("<KeyPress-P>", lambda _: self._open_settings())
        self.bind_all("<KeyPress-q>", lambda _: self.destroy())
        self.bind_all("<KeyPress-Q>", lambda _: self.destroy())
        self._refresh_ui()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        game_menu = tk.Menu(menubar, tearoff=False)
        game_menu.add_command(label=tr("menu_new_game"), command=self._new_game, accelerator="N")
        game_menu.add_command(label=tr("menu_save"), command=self._save, accelerator="S")
        game_menu.add_command(label=tr("menu_load"), command=self._load, accelerator="C")
        game_menu.add_separator()
        game_menu.add_command(label=tr("menu_settings"), command=self._open_settings, accelerator="P")
        game_menu.add_command(label=tr("menu_quit"), command=self.destroy, accelerator="Q")
        menubar.add_cascade(label=tr("app_title"), menu=game_menu)
        self.config(menu=menubar)

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self, padding=12)
        root_frame.pack(fill=tk.BOTH, expand=True)
        boards_frame = ttk.Frame(root_frame)
        boards_frame.pack(fill=tk.BOTH, expand=True)
        self.player_board = BoardCanvas(
            boards_frame,
            grid_size=self.controller.settings.grid_size,
            show_ships=True,
            click_callback=self._on_player_board_click,
            motion_callback=self._on_player_motion,
        )
        self.player_board.grid(row=0, column=0, padx=(0, 12))
        self.target_board = BoardCanvas(
            boards_frame,
            grid_size=self.controller.settings.grid_size,
            show_ships=False,
            click_callback=self._on_target_board_click,
        )
        self.target_board.grid(row=0, column=1)
        info_frame = ttk.Frame(root_frame)
        info_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(info_frame, textvariable=self.status_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.turn_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.shots_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.remaining_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.stats_var).pack(anchor="w")

    def _refresh_ui(self) -> None:
        self.player_board.render(self.controller.game.player_state.grid, True)
        self.target_board.render(self.controller.game.ai_state.grid, False)
        self._update_status()

    def _update_status(self) -> None:
        game = self.controller.game
        self.shots_var.set(
            tr(
                "status_shots",
                shots=game.stats.player_shots,
                hits=game.stats.player_hits,
                accuracy=game.player_state.accuracy,
            )
        )
        self.remaining_var.set(tr("status_remaining", count=self.controller.remaining_ai_ships()))
        self.stats_var.set(
            f"Stats: {self.controller.stats.games_played} parties, {self.controller.stats.wins} victoires, "
            f"précision {self.controller.stats.accuracy():.1f}%"
        )

    def _on_player_motion(self, coord: Coordinate) -> None:
        if not self.pending_ships:
            self.player_board.clear_preview()
            return
        ship_name = self.pending_ships[0]
        spec = next(spec for spec in self.controller.settings.fleet if spec.name == ship_name)
        cells = ship_cells(coord, self.orientation, spec.length)
        valid = self.controller.game.player_state.grid.can_place_ship(cells)
        self.player_board.show_preview(cells, valid)

    def _on_player_board_click(self, coord: Coordinate) -> None:
        if not self.pending_ships:
            return
        ship_name = self.pending_ships[0]
        spec = next(spec for spec in self.controller.settings.fleet if spec.name == ship_name)
        cells = ship_cells(coord, self.orientation, spec.length)
        if not self.controller.game.player_state.grid.can_place_ship(cells):
            messagebox.showerror(tr("app_title"), tr("placement_error"), parent=self)
            return
        try:
            self.controller.place_ship(ship_name, coord, self.orientation)
        except ValueError as exc:
            messagebox.showerror(tr("app_title"), str(exc), parent=self)
            return
        self.pending_ships = list(self.controller.available_ship_names())
        if not self.pending_ships:
            self.status_var.set(tr("placement_done"))
            self.player_board.clear_preview()
            self.target_board.set_interactive(True)
        else:
            self.status_var.set(f"{tr('placement_instruction')} ({self.pending_ships[0]})")
        self._refresh_ui()

    def _on_target_board_click(self, coord: Coordinate) -> None:
        if self.waiting_ai or self.pending_ships:
            return
        try:
            outcome, winner = self.controller.player_shot(coord)
        except ValueError as exc:
            messagebox.showerror(tr("app_title"), str(exc), parent=self)
            return
        self._handle_player_outcome(outcome, winner)

    def _handle_player_outcome(self, outcome, winner: str | None) -> None:
        if outcome.result.name == "MISS":
            self.turn_var.set(tr("status_turn_ai"))
        else:
            self.turn_var.set(tr("status_turn_player"))
            self.player_board.flash(outcome.coordinate, "#b1ffb1")
        self._refresh_ui()
        if winner:
            messagebox.showinfo(tr("app_title"), tr("console_victory" if winner == "player" else "console_defeat"), parent=self)
        else:
            self.waiting_ai = True
            self.after(600, self._ai_turn)

    def _ai_turn(self) -> None:
        outcome, winner = self.controller.ai_shot()
        self.turn_var.set(tr("status_turn_player"))
        self.player_board.flash(outcome.coordinate, "#ffb1b1")
        self._refresh_ui()
        self.waiting_ai = False
        if winner:
            messagebox.showinfo(tr("app_title"), tr("console_victory" if winner == "player" else "console_defeat"), parent=self)

    def _rotate(self, event: tk.Event[tk.Misc]) -> None:  # noqa: ARG002
        self.orientation = Orientation.VERTICAL if self.orientation is Orientation.HORIZONTAL else Orientation.HORIZONTAL
        self.status_var.set(
            f"{tr('placement_instruction')} ({self.pending_ships[0] if self.pending_ships else ''})"
        )

    def _new_game(self) -> None:
        self.controller.new_game(manual=True)
        self.pending_ships = list(self.controller.available_ship_names())
        self.orientation = Orientation.HORIZONTAL
        self.status_var.set(tr("placement_instruction"))
        self.waiting_ai = False
        self.player_board.configure_board(self.controller.settings.grid_size)
        self.target_board.configure_board(self.controller.settings.grid_size)
        self.target_board.set_interactive(False)
        self._refresh_ui()

    def _save(self) -> None:
        path = filedialog.asksaveasfilename(
            title=tr("menu_save"),
            initialfile=default_save_path().name,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tous", "*.*")],
        )
        if not path:
            return
        try:
            saved_path = self.controller.save(Path(path))
            messagebox.showinfo(tr("app_title"), tr("dialog_save_success"), parent=self)
            LOGGER.info("Sauvegarde %s", saved_path)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Erreur sauvegarde")
            messagebox.showerror(tr("app_title"), tr("dialog_save_error", error=str(exc)), parent=self)

    def _load(self) -> None:
        path = filedialog.askopenfilename(
            title=tr("menu_load"),
            filetypes=[("JSON", "*.json"), ("Tous", "*.*")],
        )
        if not path:
            return
        try:
            self.controller.load(Path(path))
            self.pending_ships = []
            self.waiting_ai = False
            self.player_board.configure_board(self.controller.settings.grid_size)
            self.target_board.configure_board(self.controller.settings.grid_size)
            self.target_board.set_interactive(True)
            self.status_var.set(tr("dialog_load_success"))
            self._refresh_ui()
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Erreur chargement")
            messagebox.showerror(tr("app_title"), tr("dialog_load_error", error=str(exc)), parent=self)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, self.controller.settings)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        grid_size, fleet, ai_level = dialog.result
        self.controller.update_settings(grid_size, fleet, ai_level)
        self.pending_ships = list(self.controller.available_ship_names())
        self.orientation = Orientation.HORIZONTAL
        self.player_board.configure_board(grid_size)
        self.target_board.configure_board(grid_size)
        self.target_board.set_interactive(False)
        self.status_var.set(tr("placement_instruction"))
        self._refresh_ui()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m bataille_navale.view_tk")
    parser.add_argument("--ai-level", choices=["basique", "chasseur"], default="basique")
    parser.add_argument("--grid-size", type=int, default=10, choices=range(8, 13))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    settings = Settings(grid_size=args.grid_size, ai_level=args.ai_level)
    app = GameApp(settings=settings, seed=args.seed)
    app.target_board.set_interactive(False)
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
