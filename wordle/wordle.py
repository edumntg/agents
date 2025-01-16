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
    reasoning = False
)

def extract_json(s):
    # Attempt to extract JSON directly if not wrapped in markdown
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Fallback to extracting JSON from markdown format
        pattern = r'```json\s*({.*?})\s*```'
        match = re.search(pattern, s, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
                return None
        else:
            return None

if __name__ == '__main__':
    # Initialize a game instance
    game = WordleGame()
    game.init()

    previous_evals_json = []

    # Start
    while not game.is_over():
        # Display board
        print(f"Target word: {game.target_word} <- not seen by the agent.")
        print(f"State of target word: {game.get_discovered_word_state()}")
        print(f"Previous words: {','.join(game.previous_words)}")
        print(f"Current score: {game.score}")
        print("Previous evaluations", game.evaluations_to_dict())
        print("Letters not in target:", game.letters_not_in_word)
        game.display_board()

        prompt = f"""
        # Current board state
        {game.pretty_board()}
        
        # Previous words
        {game.previous_words}

        # Previous evaluations
        ```python {game.evaluations_to_dict()}```
        
        """

        if game.get_discovered_word_state() != '$$$$$':
            prompt += f"""
            HIDDEN_WORD_PATTERN={game.get_discovered_word_state()}
            """

        if game.letters_not_in_word:
            prompt += f"""
            
            # AVOID THE FOLLOWING LETTERS
            The following letters are not in the word. DO NOT SUGGEST WORDS CONTAINING THESE LETTERS
            The letters not in the target word are: **{','.join(game.letters_not_in_word)}**
            """

        guess_response = guess_agent.run(prompt)

        print("Guess agent response:", guess_response.content)
        json_response = extract_json(guess_response.content)

        if 'guess' in json_response:
            guess_word = ''.join(list(json_response['guess'].values()))
            if isinstance(json_response['guess'], str):
                guess_word = json_response['guess']
            else:
                guess_word = ''.join(list(json_response['guess'].values()))
        else:
            guess_word = ''.join(list(json_response.values()))


        is_correct = game.play_turn(guess_word)

        if is_correct:
            print("Congratulations, you won!!")
            break

    # Display board
    print(f"Target word: {game.target_word}")
    print(f"Previous words: {','.join(game.previous_words)}")
    print(f"Current score: {game.score}")
    print("Previous evaluations", game.evaluations_to_dict())
    game.display_board()
    if game.is_over():
        print("You lose!")