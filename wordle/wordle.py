from dotenv import load_dotenv

from wordle_game import WordleGame

load_dotenv()

from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
import re
import json
from phi.tools.python import PythonTools

guess_agent = Agent(
    model = DeepSeekChat(),
    instructions = [
        "You are a professional Wordle player",
        "Rules:",
        "- Guess a 5-letter target word in 6 or fewer turns",
        "- Each guess must be a valid 5-letter English lowercase word",
        "- Do not repeat previously used words",
        "- Feedback after each guess:",
        "  '+' = correct letter in correct position (Green).",
        "  '*' = correct letter in wrong position (Yellow).",
        "  '#' = letter not in word (Wrong/Gray).",
        "Example: If the hidden word is 'scary' and your guess is 'sappy', the feedback is '+*##+'.",
        "Strategy:",
        "1. Start with words containing common letters (E,A,R,I,O,T,S)",
        "2. Prioritize finding new correct letters in early guesses",
        "3. Use confirmed letters (+/*) in subsequent guesses",
        "4. Avoid letters marked as # in future guesses",
        "5. Maintain correct letters (+) in correct positions",
        "6. Re-position incorrect (*) letters in unused indexes",
        "7. Analyze the 'HIDDEN_WORD_PATTERN' to discover all letters",
        "8. Adjust strategy dynamically based on feedback",
        "9. Balance exploration of new letters with exploitation of known patterns",
        "10. Always maintain confirmed letter positions in subsequent guesses",
        "Output format:",
        "- Respond with your guess as a JSON object with indexes as keys and letters as values"
    ],
    reasoning = True
)

if __name__ == '__main__':
    # Initialize a game instance
    game = WordleGame(
        agent = guess_agent,
        debug = True
    )
    game.init()

    # Start
    is_correct = False
    while not game.is_over():
        # Display board
        game.display_details()
        game.display_board()

        is_correct = game.play_turn()

        if is_correct:
            print("Congratulations! You won!")

    # Display board
    game.display_details()
    game.display_board()
    if not is_correct:
        print("You lose!")