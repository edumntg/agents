from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel


from utils.utils import extract_json
from wordle_game import WordleGame

load_dotenv()

from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat

# Create a model
model: DeepSeekChat = DeepSeekChat(id = "deepseek-chat")
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
        "2. After receiving feedback, immediately eliminate words that cannot possibly match the pattern",
        "3. Avoid letters marked as # in future guesses",
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
        json_response = extract_json(player_response.content)

        if 'guess' in json_response:
            if isinstance(json_response['guess'], str):
                guess_word = json_response['guess']
            else:
                guess_word = ''.join(list(json_response['guess'].values()))
        else:
            guess_word = ''.join(list(json_response.values()))

        rprint(f"[cyan]Player guess:[/] [yellow]{guess_word}[/]")

        is_correct = game.update_turn(guess_word)
        prev_guess = guess_word

        # Evaluate
        evaluator_response = evaluator_agent.run(f"""The hidden word is: {game.target_word}
The player guess is: {guess_word}

The feedback from the game for player guess is: '{' '.join(list(guess_word))}' -> '{' '.join(game.evaluations[game.tries-1])}'

Tries left: {game.max_tries - game.tries - 1}""")
        rprint(f"[cyan]Evaluator response:[/] [yellow]{evaluator_response.content}[/]")
        prev_eval_response += evaluator_response.content + "\n\n"

        if is_correct:
            rprint("[bold green]You won![/]")
            break

    # Display board
    game.display_details()
    game.display_board()
    if not is_correct:
        rprint("[bold red]You lose![/]")


if __name__ == '__main__':
    play_with_evaluator()