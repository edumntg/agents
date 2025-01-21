from dotenv import load_dotenv
from phi.model.openai import OpenAIChat
from sympy.concrete.guess import guess

from utils.utils import extract_json
from wordle_game import WordleGame

load_dotenv()

from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
import re
import json
from phi.tools.python import PythonTools

# Create a model
model: DeepSeekChat = DeepSeekChat(id = "deepseek-reasoner")
guess_agent = Agent(
    model = model,
    instructions = [
        "You are a professional Wordle player",
        "Rules:",
        "- Guess a 5-letter hidden word in 6 or fewer turns",
        "- Each guess must be a valid 5-letter English lowercase word",
        "- Do not repeat previously used words",
        "- Feedback after each guess:",
        "  '+' = letter in correct position.",
        "  '*' = letter in wrong position.",
        "  '#' = letter not in hidden word.",
        "Example: If the hidden word is 'chair' and your guess is 'scary', the feedback is '#*+*#'.",
        "Strategy:",
        "1. Start with words containing the most common letters in 5-letter words (E,A,R,I,O,T,S,L,N,C)",
        # "2. Use frequency analysis to prioritize letters that appear most often in the remaining possible words",
        "2. After receiving feedback, immediately eliminate words that cannot possibly match the pattern",
        # "4. Use confirmed letters (+/*) in subsequent guesses, ensuring they are in the correct or new positions",
        "3. Avoid letters marked as # in future guesses",
        # "6. Re-position incorrect (*) letters in unused indexes, ensuring they are not placed in previously incorrect positions",
        # "7. Analyze the 'HIDDEN_WORD_PATTERN' to discover all letters and their potential positions",
        # "8. Adjust strategy dynamically based on feedback, focusing on reducing the pool of possible words",
        # "9. Balance exploration of new letters with exploitation of known patterns, aiming to maximize information gain",
        # "10. Always maintain confirmed letter positions in subsequent guesses",
        # "11. Consider using a word list optimized for common 5-letter words to improve guess accuracy",
        # "Output format:",
        "- Respond with your guess as a JSON object with indexes as keys and letters as values"
    ],
    reasoning = False
)

evaluator_agent = Agent(
    model = model,
    instructions = [
        "You are the judge in the game Wordle",
        "On each input, you will receive a guess for the hidden word",
        "You also know the hidden word (Given in your input)",
        "You should NEVER REVEAL the hidden word, unless the input/guess is equal to the hidden word",
        "On each round, you will provide feedback about the guess",
        "You'll use the following symbols:",
        "+: means a letter in correct position",
        "*: means a letter in the word but not in the correct position",
        "#: means a letter not in the word",
        "Critical: Do not include the hidden word in your response. Never show it",
        "Provide the most efficient feedback so the player guesses the hidden word in the fewer amount of turns",
        "All your feedbacks and previous feedbacks are provided to the player, so ensure a optimized format"
    ]
)


def play_with_evaluator():

    game = WordleGame(
        agent = guess_agent,
        debug = True
    )
    game.init()

    prev_eval_response = ""
    prev_guess = None
    while not game.is_over():
        game.display_details()
        game.display_board()
        prompt = f"""# Previous words used: {game.previous_words}"""

        if game.get_discovered_word_state() != '$$$$$':
            prompt += f"The hidden word follows the following pattern: {game.get_discovered_word_state()} (Discover all missing letters)"

        if game.letters_not_in_word:
            prompt += f"""# AVOID THE FOLLOWING LETTERS
        The following letters are not in the word. DO NOT USE WORDS CONTAINING THESE LETTERS
        The letters not in the target word are: [{','.join(game.letters_not_in_word)}]
        """

        if prev_eval_response:
            prompt += f"""Your previous guess was: {prev_guess}
The feedback provided by the game from your previous guesses os:
{prev_eval_response}

--------------------
Analyze previous feedbacks to choose a new word"""

        player_response = guess_agent.run(prompt)
        print("Player:", player_response.content)
        json_response = extract_json(player_response.content)

        if 'guess' in json_response:
            if isinstance(json_response['guess'], str):
                guess_word = json_response['guess']
            else:
                guess_word = ''.join(list(json_response['guess'].values()))
        else:
            guess_word = ''.join(list(json_response.values()))

        is_correct = game.update_turn(guess_word)
        prev_guess = guess_word

        # Evaluate
        evaluator_response = evaluator_agent.run(f"""The hidden word is: {game.target_word}
The player guess is: {guess_word}

The feedback from the game for player guess is: '{' '.join(list(guess_word))}' -> '{' '.join(game.evaluations[game.tries-1])}'

Tries left: {game.max_tries - game.tries - 1}""")
        print("Evaluator:", evaluator_response.content)
        prev_eval_response += evaluator_response.content + "\n\n"

        if is_correct:
            print("You won!")
            break

    # Display board
    game.display_details()
    game.display_board()
    if not is_correct:
        print("You lose!")


if __name__ == '__main__':
    play_with_evaluator()
    # # Initialize a game instance
    # game = WordleGame(
    #     agent = guess_agent,
    #     debug = True,
    #     max_tries = 10
    # )
    # game.init()
    #
    # # Start
    # is_correct = False
    # while not game.is_over():
    #     # Display board
    #     game.display_details()
    #     game.display_board()
    #
    #     is_correct = game.play_turn()
    #
    #     if is_correct:
    #         print("Congratulations! You won!")
    #         break
    #
    # # Display board
    # game.display_details()
    # game.display_board()
    # if not is_correct:
    #     print("You lose!")