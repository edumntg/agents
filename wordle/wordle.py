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
        "- You must guess a 5-letter target word in 6 or fewer turns",
        "- Each guess must be a valid 5-letter English lowercase word",
        "- You must not repeat previously used words",
        "- After each guess, you receive feedback:",
        "  '+' = correct letter in correct position (Green).",
        "  '*' = correct letter in wrong position (Yellow).",
        "  '#' = letter not in word (Wrong/Gray).",
        """
        For example, if the hidden word is 'scary' and your guess is 'sappy', the board will
        be updated with: '+*##+'. It means:
        - The letter at index 0 is in the correct position
        - The letter at index 1 is in the word but in wrong position
        - The letter at index 2 is not in the hidden word
        - The letter at index 3 is not in the hidden word
        - The letter at index 4 is in the correct position
        
        So the next guess should contain the letter 's' at index 0, the letter 'y' at index 4 an the letter 'a' at any other index different from 1
        NOTE: This is just an example. Use the same analysis for all guesses
        """
        
        "Strategy/Critical:",
        "1. Start with words that contain common letters (E,A,R,I,O,T,S)",
        "2. Prioritize finding new correct letters in early guesses",
        "3. Use confirmed letters (+/*) in subsequent guesses",
        "4. Never use letters marked as # (wrong) in future guesses",
        "5. If you have multiple good (+) positions, always maintain those letters in the same indexes",
        "7. CRITICAL: Always maintain correct letters (+) in correct positions",
        "8. Analyze previous word, check for letters in incorrect positions (*) and ensure your next guess contains them in different indexes but not where correct letter '+' are present",
        "9. Always re-position bad (*) letters in unused indexes/positions",
        "10. CRITICAL: Keep the HIDDEN_WORD_PATTERN. ALWAYS KEEP THAT PATTERN WITH VISIBLE LETTERS. THIS IS CRUCIAL",

        "Output format:",
        """
        - In your response include your guess as a JSON object where keys are the indexes (quoted) and the values are the letters
        - For example, if the letter is 'chair', an example of your output will be:
        ```json
        {
            '0': 'c',
            '1': 'h',
            '2': 'a',
            '3': 'i',
            '4': 'r'
        }
        ```
        Additionally, include a sentence specifying a value between (0, 1), on how sure you are about your guess. Use two decimal places
        """
    ],
    reasoning = True
)

double_check_agent = Agent(
    model = DeepSeekChat(),
    instructions = [
        "Your task is to analyze the Wordle guess of a previous agent",

        """
        You will receive the current board state, previous words used,
        a list of JSON objects containing the index and letters of each word, and the new guess
        For example, if the used words are ['chair'], the list of JSON will be:
        ```json
        [{
            '0': 'c',
            '1': 'h',
            '2': 'a',
            '3': 'i',
            '4': 'r'
        }]
        ```
        """,

        """
        You receive the new guess/word before being evaluated in the game.
        You will receive it as a JSON object containing the indexes as keys (quoted) and the letters as values
        Example for 'sassy':
        ```json
        [{
            '0': 's',
            '1': 'a',
            '2': 's',
            '3': 's',
            '4': 'y'
        }]
        ```
        """,
        """
        Perform the following analysis for the word/guess
        ## WORD_ANALYSIS
        - Check if it contains letters marked as correct '+' in previous guesses. If so, keep these letters in these same indexes/positions.
        - Check if it contains letters marked as bad '*' which means they have to be used in the next guess/word, but in different index.
        - Check for letters marked as '#'. Those are not present in the hidden word and must be avoided at all cost in future words/guess.
        """,
        "Carefully analyze the positions/indexes of each letter, do not make mistakes."
        "Always double check."
        "Use a python code if needed to compare indexes and letters",

        "Analyze the words and the index position of each letter. First index is always zero",
        "If you think the new guess is good enough, do not change it and just return it",
        "If you change it, ensure is different from previous words used",
        "If you decide to change it, remember to perform the WORD_ANALYSIS on it an ensure it contains more correct letters '+' than the initial one"
        "Return the explanation and analysis of why the word/guess was or was not changed",
        """
        # Strategy/Critical:
        - Prioritize finding new correct letters in early guesses
        - Remember, correct letters in correct positions are marked as: +
        - Remember, correct letters but in incorrect positions are marked as: *
        - Remember, letters not in word are marked as: #
        - Use letters marked as correct '+' in subsequent guesses
        - If you have multiple good (+) letters in correct positions, always maintain those letters in those exact positions
        - Word can contain repeated letters. For example: sassy
        CRITICAL: Keep the HIDDEN_WORD_PATTERN. ALWAYS KEEP THAT PATTERN WITH VISIBLE LETTERS. THIS IS CRUCIAL
        """,

        "# CRITICAL: ENSURE THAT THE NEW WORD IS NOT IN THE LIST OF PREVIOUS WORDS. ENSURE IT HAS NOT BEEN USED"
        "Your response should follow this exact format:",
        """
        ## Analysis Steps
        1. In the first step..
        2. In the second step..
        ...
        N. In the N step...
        ... etc
        
        Additionally, include a sentence specifying a value between (0, 1), on how sure you are about your guess. Use two decimal places

        Then provide your JSON response in this format (always include the ```json ``` markdown):
        ```json
        {
            "initial_guess": <new_guess_json>,
            "final_guess": <new_guess_or_old_one_if_not_changed_json>,
            "explanation": <explanation of why you changed or not the word>
        }
        ```
        """,
        "If your response already contains a JSON object, just append the properties to it"
    ],
    tools=[PythonTools()],
    show_tool_calls=True,
    reasoning = True
)

def extract_json(s):
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
            # HIDDEN_WORD_PATTERN
            The next guess should be similar to {game.get_discovered_word_state()}. Complete the missing letters
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
        first_word = ''.join(list(json_response.values()))

        prompt = f"""
        # Current board state
        {game.pretty_board()}
        
        # Previous words
        {game.previous_words}
        
        # New guess word an analysis of why it was chosen
        Study the given analysis to see if it makes sense. Analyze the pattern of the hidden word.
        {guess_response.content}

        # Previous evaluations
        ```python {game.evaluations_to_dict()}```
        
        # Previous evaluations in JSON format
        ```json {previous_evals_json}```
        
        Analyze the new guess and if you consider it needs to be changed, make a new one
        
        """

        if game.get_discovered_word_state() != '$$$$$':
            prompt += f"""
            # HIDDEN_WORD_PATTERN
            The next guess should be similar to {game.get_discovered_word_state()}. Complete the missing letters
            """

        if game.letters_not_in_word:
            prompt += f"""

            # AVOID THE FOLLOWING LETTERS
            The following letters are not in the word. DO NOT SUGGEST WORDS CONTAINING THESE LETTERS
            The letters not in the target word are: **{','.join(game.letters_not_in_word)}**
            """

        # Double-check
        double_check_response = double_check_agent.run(prompt)

        # Get refined word
        json_obj = extract_json(double_check_response.content)
        # word = response.content.split("<word>")[1].replace("</word>", "")
        print("Refiner agent response:", double_check_response.content)
        final_word = ''.join(list(json_obj['final_guess'].values()))
        print(f"New word: {final_word}")

        # Get agent response
        print(f"Final agent guess: {final_word}")

        previous_evals_json.append(json_obj['final_guess'])

        # Play turn
        is_correct = game.play_turn(final_word)

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