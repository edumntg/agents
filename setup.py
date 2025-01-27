from setuptools import setup, find_packages

setup(
    name="agents",
    version="0.1.0",
    description="A collection of AI-powered game agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Eduardo Montilva",
    author_email="eduardojmg.dev@gmail.com",
    url="https://github.com/edumntg/agents",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "python-dotenv",
        "phidata",
        "requests",
        "rich",
        "openai"
    ],
    entry_points={
        "console_scripts": [
            "wordle=wordle.wordle:play_with_evaluator",
            "tictactoe=tic_tac_toe.tic_tac_toe:main"
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
) 