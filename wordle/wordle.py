from dotenv import load_dotenv

from wordle_game import WordleGame

load_dotenv()

from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
import re
import json

guess_agent = Agent(
    model = DeepSeekChat(),
    instructions = [
        "You are an expert Wordle player who uses optimal strategy to solve the puzzle",
        "Rules:",
        "- You must guess a 5-letter target word in 6 or fewer turns",
        "- Each guess must be a valid 5-letter lowercase word",
        "- You cannot repeat previously used words",
        "- After each guess, you receive feedback:",
        "  '+' = correct letter in correct position (Green).",
        "  '*' = correct letter in wrong position (Yellow).",
        "  '#' = letter not in word (Wrong/Gray).",
        
        "Strategy/Critical:",
        "1. Start with words that contain common letters (E,A,R,I,O,T,S)",
        "2. Prioritize finding new correct letters in early guesses",
        "3. Use confirmed letters (+/*) in subsequent guesses",
        "4. Never use letters marked as # (wrong) in future guesses",
        "5. If you have multiple good (+) positions, always maintain those letters in those exact positions",
        "6. Always use words containing letters in correct positions.",
        "7. CRITICAL: Always maintain correct letters (+) in correct positions",
        "8. Analyze previous word, check for letters in incorrect positions (*) and ensure your next guess contains them but in different positions (use wrong letters (#) positions).",
        "9. Try to position bad (*) letters in unused positions",
        "10. ALWAYS MAXIMIZE YOUR SCORE."
        
        "Output format:",
        """
        - In your response, after the explanation, the letters inside a python list.
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

        "You receive the new guess before being evaluated in the game",
        "You also receive the new guess in the same JSON format specified before",
        "You need to analyze the outcome of the new guess",
        "If the new guess is not good, change it",
        "Carefully analyze the positions of each letter, do not make mistakes",

        "Analyze the words and the index position of each letter. First index is always zero",
        "If you think the new guess is good enough, do not change it and just return it",
        "If you change it, ensure is different from previous words used",
        "Return an explanation of why you chose the new word",
        "Strategy/Critical:",
        "- Prioritize finding new correct letters in early guesses",
        "- Use confirmed letters in subsequent guesses",
        "- Remember, correct letters in correct positions are marked as: +",
        "- Remember, correct letters but in incorrect positions are marked as: *",
        "- Remember, letters not in word are marked as: #",
        "- Minimize the use of letters marked as # (wrong) in future guesses",
        "- If you have multiple good (+) letters in correct positions, always maintain those letters in those exact positions",
        "- Always use words containing letters in correct positions.",
        "- CRITICAL: Always maintain correct letters (+) in those positions",
        "- Analyze previous words, check for letters in incorrect positions (*) and ensure your next guess contains them but in different positions (use wrong letters (#) positions).",
        "- Try to position letters in incorrect positions (*) letters in unused positions",
        "- Word can contain repeated letters. For example: sassy"
        "# CRITICAL: ENSURE THAT THE NEW WORD IS NOT IN THE LIST OF PREVIOUS WORDS. ENSURE IT HAS NOT BEEN USED"
        "Your response should follow this exact format:",
        """
        First, provide your step-by-step reasoning:
        1. [First analysis step]
        2. [Second analysis step]
        3. [Final decision]

        Then provide your JSON response in this format:
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

        if game.get_discovered_word_state() != '*****':
            prompt += f"""
            # CRITICAL
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
        
        # New guess (unevaluated)
        {first_word}

        # Previous evaluations
        ```python {game.evaluations_to_dict()}```
        
        # Previous evaluations in JSON format
        ```json {previous_evals_json}```
        
        Analyze the new guess and if you consider it needs to be changed, make a new one
        
        """

        if game.get_discovered_word_state() != '*****':
            prompt += """
            # CRITICAL
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