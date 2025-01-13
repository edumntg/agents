from dotenv import load_dotenv

load_dotenv()

from phi.model.deepseek import DeepSeekChat
from phi.agent import Agent

# Player X
player_x = Agent(
    name="Player X",
    # model=Gemini(id="gemini-2.0-flash-exp", api_key=st.session_state.google_api_key),
    model = DeepSeekChat(),
    instructions=[
        "You are a Tic-Tac-Toe player using the symbol 'X'.",
        "Your opponent is using the symbol 'O'. Block their potential winning moves.",
        "Make your move in the format 'row, col' based on the current board state.",
        "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
        "Do not include any explanations or extra text. Only provide the move.",
        "Row and column indices start from 0 and their max. value is 2.",
    ],
    markdown=True,
)

# Player X
player_o = Agent(
    name="Player O",
    model=DeepSeekChat(),
    instructions=[
        "You are a Tic-Tac-Toe player using the symbol 'O'.",
        "Your opponent is using the symbol 'X'. Block their potential winning moves.",
        "Make your move in the format 'row, col' based on the current board state.",
        "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
        "Do not include any explanations or extra text. Only provide the move.",
        "Row and column indices start from 0 and their max. value is 2.",
    ],
    markdown=True,
)

judge = Agent(
    name="Judge",
    model=DeepSeekChat(),
    instructions=[
        "You are the judge of a Tic-Tac-Toe game.",
        "The board is presented as rows with positions separated by '|'.",
        "Rows are labeled from 0 to 2, and columns from 0 to 2.",
        "Example board state:",
        "Row 0: (0,0) X | (0,1)   | (0,2) O",
        "Row 1: (1,0) O | (1,1) X | (1,2) X",
        "Row 2: (2,0) X | (2,1) O | (2,2) O",
        "Determine the winner based on this board state.",
        "If there is no winner and board is no full, return 'Keep Playing'",
        "The winner is the player with three of their symbols in a straight line (row, column, or diagonal).",
        "If the board is full, you cannot return 'Keep Playing'. If there is no winner, declare a draw.",
        "Provide only the result (e.g., 'Player X wins', 'Player O wins', 'Draw', 'keep Playing').",
        "If you think there is a winner, always double check it"
    ],
)

def pretty_board(board):
    result = ""
    for i, row in enumerate(board):
        row_str = "Row {}: ".format(i)
        for j, cell in enumerate(row):
            row_str += "({},{}) ".format(i, j)
            if cell == "X":
                row_str += "X | "
            elif cell == "O":
                row_str += "O | "
            else:
                row_str += "  | "
        result += row_str.strip()[:-1] + " \n"
    return result



if __name__ == "__main__":
    # Initialize board
    board = [
        [None, None, None],
        [None, None, None],
        [None, None, None],
    ]

    turn = player_x # Player X always starts

    status = 'Keep Playing'
    while status == 'Keep Playing':
        # Make a move
        response = turn.run(f"""
        # Current board status
        ```python {board}```
        
        Make your move in the format: 'row, col'
        """)

        print(response.content)

        # Get move
        while True:
            content = response.content if hasattr(response, 'content') else str(response)
            row, col = (int(value) for value in content.split(','))
            if board[row][col] is None:
                board[row][col] = 'X' if turn == player_x else 'O'
                break
            else:
                response = turn.run(f"""
                # Current board status
                ```python {board}```
                
                Your previous move was invalid. Please analyze the board and make a valid move in the format: 'row, col'
                """)

        # Print board
        print(pretty_board(board))

        # Ask judge
        judge_response = judge.run(f"""
        # Current board status
        {pretty_board(board)}
        
        Determine is there is a winner and announce the result. If not winner, return 'Keep Playing'. If draw, return 'Draw'
        """)
        status = judge_response.content if hasattr(judge_response, 'content') else str(judge_response)
        print("JUDGE RESPONSE", judge_response.content)
        # Switch turns
        turn = player_o if turn == player_x else player_x

    print(f"GAME OVER! Result {status}")


