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
        "1. Start with words containing the most common letters in 5-letter words (E,A,R,I,O,T,S,L,N,C)",
        "2. Use frequency analysis to prioritize letters that appear most often in the remaining possible words",
        "3. After receiving feedback, immediately eliminate words that cannot possibly match the pattern",
        "4. Use confirmed letters (+/*) in subsequent guesses, ensuring they are in the correct or new positions",
        "5. Avoid letters marked as # in future guesses",
        "6. Re-position incorrect (*) letters in unused indexes, prioritizing positions that maximize new information",
        "7. Analyze the 'HIDDEN_WORD_PATTERN' to discover all letters and their potential positions",
        "8. Adjust strategy dynamically based on feedback, focusing on reducing the pool of possible words",
        "9. Balance exploration of new letters with exploitation of known patterns, aiming to maximize information gain",
        "10. Always maintain confirmed letter positions in subsequent guesses",
        "11. Consider using a word list optimized for common 5-letter words to improve guess accuracy",
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