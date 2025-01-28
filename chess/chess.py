from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.layout import Layout

console = Console()


def print_board(board, current_player):
    light_square = Style(color="black", bgcolor="bright_white")
    dark_square = Style(color="white", bgcolor="#306082")
    white_piece = Style(color="#ffffff", bold=True)
    black_piece = Style(color="#000000", bold=True)

    layout = Layout(name="board")

    # Add column labels (top)
    top_labels = Text("   a  b  c  d  e  f  g  h  ", style="bold white")
    layout.split_column(
        Layout(top_labels, name="top_labels", size=1),
        Layout(name="main_board", size=8),
        Layout(Text("   a  b  c  d  e  f  g  h  ", style="bold white"), name="bottom_labels", size=1)
    )

    # Create main board rows
    main_board = Layout(name="main_board")
    main_board.split_column(*[Layout(name=f"row_{i}", size=1) for i in range(8)])

    for row_idx in range(8):
        row = board[row_idx]
        row_text = Text()
        row_text.append(f"{8 - row_idx} ", style="bold white")

        for col_idx in range(8):
            piece = row[col_idx]
            square_style = dark_square if (row_idx + col_idx) % 2 else light_square
            piece_style = white_piece if piece.isupper() else black_piece if piece != '.' else square_style

            cell = Text(f" {piece} ", style=piece_style + square_style)
            row_text.append(cell)

        row_text.append(f" {8 - row_idx}", style="bold white")
        main_board[f"row_{row_idx}"].update(row_text)

    layout["main_board"].update(main_board)

    console.print(
        Panel.fit(
            layout,
            title="[bold cyan]Chess Game[/bold cyan]",
            border_style="bold yellow",
            padding=(0, 2),
            subtitle=f"[italic]Current turn: [bold]{'White' if current_player == 'white' else 'Black'}[/bold][/italic]",
        )
    )


def is_in_check(board, player):
    king = 'K' if player == 'white' else 'k'
    king_pos = None
    for row in range(8):
        for col in range(8):
            if board[row][col] == king:
                king_pos = (row, col)
                break
        if king_pos:
            break
    if not king_pos:
        return False

    opponent = 'black' if player == 'white' else 'white'
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece == '.':
                continue
            if (opponent == 'white' and piece.isupper()) or (opponent == 'black' and piece.islower()):
                if is_valid_move(board, row, col, king_pos[0], king_pos[1], opponent, check_safe=False):
                    return True
    return False


def is_valid_move(board, start_row, start_col, end_row, end_col, player, check_safe=True):
    if not (0 <= start_row < 8 and 0 <= start_col < 8 and 0 <= end_row < 8 and 0 <= end_col < 8):
        return False
    piece = board[start_row][start_col]
    if piece == '.':
        return False
    if (player == 'white' and not piece.isupper()) or (player == 'black' and not piece.islower()):
        return False

    target_piece = board[end_row][end_col]
    if target_piece != '.':
        if (player == 'white' and target_piece.isupper()) or (player == 'black' and target_piece.islower()):
            return False

    temp_board = [row.copy() for row in board]
    temp_piece = temp_board[start_row][start_col]
    temp_board[start_row][start_col] = '.'
    temp_board[end_row][end_col] = temp_piece

    if check_safe and is_in_check(temp_board, player):
        return False

    piece_type = piece.lower()
    if piece_type == 'p':
        return validate_pawn(start_row, start_col, end_row, end_col, player, board)
    elif piece_type == 'n':
        return validate_knight(start_row, start_col, end_row, end_col)
    elif piece_type == 'b':
        return validate_bishop(start_row, start_col, end_row, end_col, board)
    elif piece_type == 'r':
        return validate_rook(start_row, start_col, end_row, end_col, board)
    elif piece_type == 'q':
        return validate_queen(start_row, start_col, end_row, end_col, board)
    elif piece_type == 'k':
        return validate_king(start_row, start_col, end_row, end_col, board)
    return False


def validate_pawn(sr, sc, er, ec, player, board):
    direction = -1 if player == 'white' else 1
    start_row = 6 if player == 'white' else 1

    if sc == ec:
        if er == sr + direction and board[er][ec] == '.':
            return True
        if sr == start_row and er == sr + 2 * direction and board[er][ec] == '.' and board[sr + direction][ec] == '.':
            return True
    elif abs(ec - sc) == 1 and er == sr + direction:
        if board[er][ec] != '.':
            return True
    return False


def validate_knight(sr, sc, er, ec):
    return (abs(er - sr) == 2 and abs(ec - sc) == 1) or (abs(er - sr) == 1 and abs(ec - sc) == 2)


def validate_bishop(sr, sc, er, ec, board):
    if abs(er - sr) != abs(ec - sc):
        return False
    dr = 1 if er > sr else -1
    dc = 1 if ec > sc else -1
    for i in range(1, abs(er - sr)):
        if board[sr + dr * i][sc + dc * i] != '.':
            return False
    return True


def validate_rook(sr, sc, er, ec, board):
    if sr != er and sc != ec:
        return False
    if sr == er:
        step = 1 if ec > sc else -1
        for c in range(sc + step, ec, step):
            if board[sr][c] != '.':
                return False
    else:
        step = 1 if er > sr else -1
        for r in range(sr + step, er, step):
            if board[r][sc] != '.':
                return False
    return True


def validate_queen(sr, sc, er, ec, board):
    return validate_rook(sr, sc, er, ec, board) or validate_bishop(sr, sc, er, ec, board)


def validate_king(sr, sc, er, ec, board):
    return abs(er - sr) <= 1 and abs(ec - sc) <= 1


def has_legal_moves(board, player):
    for sr in range(8):
        for sc in range(8):
            if (player == 'white' and board[sr][sc].isupper()) or (player == 'black' and board[sr][sc].islower()):
                for er in range(8):
                    for ec in range(8):
                        if is_valid_move(board, sr, sc, er, ec, player):
                            return True
    return False


def main():
    board = [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
        ['p'] * 8,
        ['.'] * 8,
        ['.'] * 8,
        ['.'] * 8,
        ['.'] * 8,
        ['P'] * 8,
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
    ]
    current_player = 'white'

    while True:
        print_board(board, current_player)

        try:
            current_row = int(console.input("[bold green]Enter current row (1-8): [/bold green]"))
            current_col = console.input("[bold green]Enter current column (a-h): [/bold green]").strip().lower()
            new_row = int(console.input("[bold green]Enter new row (1-8): [/bold green]"))
            new_col = console.input("[bold green]Enter new column (a-h): [/bold green]").strip().lower()
        except ValueError:
            console.print("[bold red]Invalid input format![/bold red]")
            continue

        if not (1 <= current_row <= 8) or not (1 <= new_row <= 8):
            console.print("[bold red]Row numbers must be between 1 and 8![/bold red]")
            continue
        if len(current_col) != 1 or current_col < 'a' or current_col > 'h':
            console.print("[bold red]Invalid current column![/bold red]")
            continue
        if len(new_col) != 1 or new_col < 'a' or new_col > 'h':
            console.print("[bold red]Invalid new column![/bold red]")
            continue

        cr = 8 - current_row
        cc = ord(current_col) - ord('a')
        nr = 8 - new_row
        nc = ord(new_col) - ord('a')

        if not is_valid_move(board, cr, cc, nr, nc, current_player):
            console.print("[bold red]Invalid move![/bold red]")
            continue

        piece = board[cr][cc]
        board[cr][cc] = '.'
        board[nr][nc] = piece

        if piece.lower() == 'p' and (nr == 0 or nr == 7):
            promo = console.input("[bold yellow]Promote pawn to (Q/R/B/N): [/bold yellow]").upper()
            while promo not in ['Q', 'R', 'B', 'N']:
                promo = console.input("[bold red]Invalid choice! Promote to (Q/R/B/N): [/bold red]").upper()
            board[nr][nc] = promo if current_player == 'white' else promo.lower()

        current_player = 'black' if current_player == 'white' else 'white'

        opponent = 'black' if current_player == 'white' else 'white'
        if is_in_check(board, current_player):
            if not has_legal_moves(board, current_player):
                print_board(board, current_player)
                console.print(
                    Panel.fit(
                        f"[blink bold white on red] CHECKMATE! {current_player.capitalize()} loses! [/]",
                        border_style="red",
                        padding=(1, 2)
                    )
                )
                break
            else:
                console.print(
                    Panel.fit(
                        f"[bold white on red] {current_player.capitalize()} is in check! [/]",
                        border_style="yellow",
                        padding=(1, 2)
                    )
                )
        elif not has_legal_moves(board, current_player):
            print_board(board, current_player)
            console.print(
                Panel.fit(
                    "[bold white on blue] STALEMATE! Game over. [/]",
                    border_style="blue",
                    padding=(1, 2)
                )
            )
            break


if __name__ == "__main__":
    main()