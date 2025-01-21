# Wordle Game Logic and methods

import requests
import json
from typing import List
import random

from phi.agent import Agent
from utils.utils import extract_json

class WordleGame(object):
    words: List[str] = None
    target_word: str = None
    tries: int
    max_tries: int = 6
    board: List[List[str]] = None
    evaluations: List[List[str]] = None
    previous_words: List[str] = None
    score: int = 0
    letters_not_in_word: List[str] = None
    agent: Agent = None
    turn: int = 0
    debug: bool = False

    def __init__(self, agent: Agent = None, debug: bool = False, max_tries: int = 6):
        self.agent = agent
        self.turn = 0
        self.debug = debug
        self.max_tries = max_tries

    def get_words(self):
        # Fetch for 5-letter words and return them in a list
        try:
            response = requests.get(
                'https://raw.githubusercontent.com/tabatkins/wordle-list/main/words'
            )

            words = [line.strip() for line in response.text.splitlines()]

            self.words = words
        except Exception as e:
            print(f"Failed to fetch words: {e}")

    def chose_word(self):
        if not self.words:
            self.get_words()

        self.target_word = random.choice(self.words)
        # self.target_word = "sassy"

    def init_board(self):
        """Initialize an empty 6x5 game board."""
        self.board = [['_' for _ in range(5)] for _ in range(self.max_tries)]

    def init(self):
        # Init board
        self.init_board()

        # Chose word
        self.chose_word()

        self.evaluations = [[] for _ in range(self.max_tries)]

        self.letters_not_in_word = []
        self.tries = 0
        self.score = 0

        self.previous_words = []

    @staticmethod
    def is_valid_guess(guess: str) -> bool:
        """Check if the guess is valid (5 letters and in word list)."""
        return len(guess) == 5

    def evaluate_guess(self, guess: str, update_score = True) -> List[str]:
        """
        Evaluate the guess and return a list of results:
        '+' - correct letter in correct position (green) (+10 points)
        '*' - correct letter in wrong position (yellow) (-5 points)
        '#' - letter not in word (gray) (-20 points)
        """
        result = ['#'] * 5  # Initialize with '#' instead of 'X'
        target_chars = list(self.target_word)
        guess_chars = list(guess)

        # First check for correct positions
        for i in range(5):
            if guess_chars[i] == target_chars[i]:
                if update_score:
                    self.score += 10  # Add 10 points for correct letter in correct position
                result[i] = '+'
                target_chars[i] = '*'
                guess_chars[i] = '#'

        # Then check for correct letters in wrong positions
        for i in range(5):
            if guess_chars[i] != '#':  # Skip already matched letters
                if guess_chars[i] in target_chars:  # Check if letter exists in remaining target chars
                    for j in range(5):
                        if target_chars[j] != '*' and guess_chars[i] == target_chars[j]:
                            if update_score:
                                self.score -= 5  # Subtract 5 points for correct letter in wrong position
                            result[i] = '*'
                            target_chars[j] = '*'
                            break
                # No need for else case as result[i] is already '#'

        # Update letters_not_in_word list
        for i, result_char in enumerate(result):
            if result_char == '#' and guess_chars[i] not in self.letters_not_in_word:
                self.letters_not_in_word.append(guess[i])

        # Add penalty for letters not in word
        if update_score:
            self.score -= result.count('#')*20  # Subtract 20 points for each letter not in word

        return result

    def play_turn(self):
        prompt = f"""# Current board state
{self.pretty_board()}

# Previous words
{self.previous_words}

# Previous evaluations
```python {self.evaluations_to_dict()}```

"""
        if self.get_discovered_word_state() != '$$$$$':
            prompt += f"HIDDEN_WORD_PATTERN={self.get_discovered_word_state()}"

        if self.letters_not_in_word:
            prompt += f"""# AVOID THE FOLLOWING LETTERS
The following letters are not in the word. DO NOT SUGGEST WORDS CONTAINING THESE LETTERS
The letters not in the target word are: [{','.join(self.letters_not_in_word)}]
"""
        agent_response = self.agent.run(prompt)

        if self.debug: print("Agent response:", agent_response.content)
        json_response = extract_json(agent_response.content)

        if 'guess' in json_response:
            if isinstance(json_response['guess'], str):
                guess_word = json_response['guess']
            else:
                guess_word = ''.join(list(json_response['guess'].values()))
        else:
            guess_word = ''.join(list(json_response.values()))

        is_correct = self.update_turn(guess_word)

        return is_correct

    def update_turn(self, guess: str) -> bool:
        """
        Play a single turn of Wordle. Returns updated board and whether the guess was correct.
        """
        # Add guess to board
        for i in range(5):
            self.board[self.tries][i] = guess[i]

        # Evaluate guess
        result = self.evaluate_guess(guess)

        # Add to evaluations
        self.evaluations[self.tries] = result

        self.previous_words.append(guess)

        self.tries += 1

        # Check if guess is correct
        return guess.lower() == self.target_word.lower()

    def display_board(self) -> None:
        """Display the current state of the board with color indicators."""
        for row_idx, (row, eval_row) in enumerate(zip(self.board, self.evaluations)):
            # Add spaces between letters and format each row
            formatted_row = ' '.join(row)
            # Use consistent symbols: + for correct, * for wrong position, # for not in word
            eval_string = ' '.join(eval_row) if eval_row else ' '.join('_'*5)
            print(f"{eval_string}")

    def pretty_board(self) -> str:
        """Return the current state of the board with color indicators as a string."""
        out = ""
        for row_idx, (row, eval_row) in enumerate(zip(self.board, self.evaluations)):
            # Add spaces between letters and format each row
            formatted_row = ' '.join(row)
            # Use consistent symbols: + for correct, * for wrong position, # for not in word
            eval_string = ' '.join(eval_row) if eval_row else ' '.join('_'*5)
            out += f"{eval_string}\n"
        return out

    def evaluations_to_dict(self):
        if len(self.previous_words) == 0:
            return {}

        output = {}
        for word in self.previous_words:
            result = self.evaluate_guess(word, False)
            output[word] = ''.join(result)

        return output

    def is_over(self):
        return self.tries == self.max_tries and '$' not in self.get_discovered_word_state()

    def play(self):
        """Interactive method to play Wordle in the console."""
        self.init()  # Initialize the game
        print("Welcome to Wordle!")
        print("Enter a 5-letter word guess (or 'quit' to exit)")
        print(f"The score starts at 0. Get points for correct letters (+10)")
        print(f"Lose points for wrong position (-5) or wrong letters (-20)")

        while self.tries < self.max_tries:
            self.display_board()
            print(f"Current score: {self.score}")
            guess = input(f"Enter guess {self.tries + 1}/{self.max_tries}: ").lower()

            if guess == 'quit':
                print(f"The word was: {self.target_word}")
                return

            if not self.is_valid_guess(guess):
                print("Invalid guess. Please enter a valid 5-letter word.")
                continue

            is_correct = self.play_turn(guess)

            if is_correct:
                self.display_board()
                print(f"Congratulations! You won in {self.tries} tries!")
                print(f"Final score: {self.score}")
                return

        self.display_board()
        print(f"Game Over! The word was: {self.target_word}")
        print(f"Final score: {self.score}")

    def get_discovered_word_state(self):
        """Returns the current state of the discovered word, where:
        - Known letters in correct positions are shown
        - Unknown positions are shown as '*'
        """
        if not self.previous_words:  # If no guesses made yet
            return '$$$$$'
            
        result = ['$'] * 5
        
        # Check all previous guesses to find correct letters
        for guess, eval_str in zip(self.previous_words, self.evaluations):
            for i, (letter, eval_char) in enumerate(zip(guess, eval_str)):
                if eval_char == '+':  # Correct letter in correct position
                    result[i] = letter
                    
        return ''.join(result)

    def display_details(self):
        print(f"Hidden word: {self.target_word} <- not seen by the agent.")
        print(f"State of hidden word: {self.get_discovered_word_state()}")
        print(f"Previous words: {','.join(self.previous_words)}")
        print(f"Current score: {self.score}")
        print("Previous evaluations", self.evaluations_to_dict())
        print("Letters not in hidden word:", self.letters_not_in_word)


