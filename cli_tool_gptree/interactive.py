import curses


def interactive_file_selector(file_list):
    """Interactive file selector with a scrollable list using curses."""
    selected_files = set()
    display_limit = 15  # Number of files shown at a time

    def draw_menu(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight color
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default color

        current_row = 0
        offset = 0  # For scrolling
        max_rows = len(file_list)

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Use ↑/↓/j/k to scroll, SPACE to toggle selection, 'a' to select all, ENTER to confirm, ESC to quit")
            stdscr.addstr(1, 0, "-" * 80)

            for idx in range(display_limit):
                file_idx = offset + idx
                if file_idx >= max_rows:
                    break
                file = file_list[file_idx]
                prefix = "[X]" if file in selected_files else "[ ]"

                if file_idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(idx + 2, 0, f"{prefix} {file[:70]}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(idx + 2, 0, f"{prefix} {file[:70]}")
                    stdscr.attroff(curses.color_pair(2))

            # Add ellipsis indicators if there are more files above or below
            if offset > 0:
                stdscr.addstr(2, 78, "↑")
            if offset + display_limit < max_rows:
                stdscr.addstr(display_limit + 1, 78, "↓")

            stdscr.addstr(display_limit + 3, 0, "-" * 80)
            stdscr.addstr(display_limit + 4, 0, f"Selected: {len(selected_files)} / {len(file_list)}")

            key = stdscr.getch()
            if key in (curses.KEY_DOWN, ord('j')):
                if current_row < max_rows - 1:
                    current_row += 1
                    if current_row >= offset + display_limit:
                        offset += 1
            elif key in (curses.KEY_UP, ord('k')):
                if current_row > 0:
                    current_row -= 1
                    if current_row < offset:
                        offset -= 1
            elif key == ord(' '):
                file = file_list[current_row]
                if file in selected_files:
                    selected_files.remove(file)
                else:
                    selected_files.add(file)
            elif key == ord('a'):
                if len(selected_files) < len(file_list):
                    selected_files.update(file_list)
                else:
                    selected_files.clear()
            elif key == 27:  # ESC key
                raise SystemExit("Interactive mode canceled by user.")
            elif key == 10:  # ENTER key
                break

    curses.wrapper(draw_menu)
    return selected_files 