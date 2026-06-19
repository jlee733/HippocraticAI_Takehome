import os
import openai

from app.models import get_model_fn, resolve_model_name
from app.story_engine import (
    Judge,
    StoryPlanner,
    Storyteller,
    judge_and_refine_story,
)

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

App
- Implement story categories (adventure, fantasy, animal, friendship) with tailored prompts
- Since one of the points in the "Methodology" section of the README file was that the word count range was based off picture books I would create 
a simple web UI with illustrations generated via DALL-E. This would be done by calling DALL-E after the story is generated to create pictures and 
display them alongside the story.

Infrastructure
- I would create a public Dockerhub repository for the Dockerfile and push the image to it. This would allow for quicker deployment by reducing the
time it takes to build the image locally at the "docker compose up --build" command. This would also lead me to incorporate a Github Action that
rebuilds the image to ensure that any new changes to the Docker image can run the existing application code.
- In addition, I would incorporate a linting on every commit to the repository to ensure that the code is consistent and follows best practices.
"""

def call_model(prompt: str, max_tokens=3000, temperature=0.1) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")  # please use your own openai api key here.
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message["content"]  # type: ignore


example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def generate_story(
    user_request: str,
    model_fn=None,
    verbose: bool = True,
) -> str:
    """
    Generate a bedtime story using the Planner -> Storyteller -> Judge pipeline.

    Args:
        user_request: The user's story request
        model_fn: Callable that sends prompts to the selected LLM
        verbose: Whether to print progress and evaluation details

    Returns:
        The final story text
    """
    model_fn = model_fn or call_model
    planner = StoryPlanner(model_fn)
    storyteller = Storyteller(model_fn)
    judge = Judge(model_fn)

    if verbose:
        print("\n📝 Planning your story...")
    outline = planner.plan(user_request)
    if verbose:
        print(f"   Title: {outline.get('title', 'Untitled')}")
        print(f"   Setting: {outline.get('setting', 'Unknown')}")

    if verbose:
        print("\n✍️  Writing the story...")
    story = storyteller.generate(outline)

    if verbose:
        print(f"\n🔍 Evaluating story...")
    story, evaluation = judge_and_refine_story(story, model_fn)
    if verbose:
        print(judge.format_evaluation(evaluation))
        if evaluation["passed"]:
            print("\n✨ Story approved!")

    return story


def main():
    print("=" * 60)
    print("🌙 Welcome to the Bedtime Story Generator! 🌙")
    print("=" * 60)
    print("\nThis tool creates age-appropriate stories for children ages 5-10.")
    print(f"Example: {example_requests}\n")

    model_name = resolve_model_name()
    model_fn = get_model_fn(model_name, call_model)
    print(f"\nUsing model: {model_name}")

    user_input = input("What kind of story do you want to hear? ")

    if not user_input.strip():
        print("No input provided. Using example request.")
        user_input = example_requests

    story = generate_story(user_input, model_fn=model_fn)

    print("\n" + "=" * 60)
    print("📖 YOUR BEDTIME STORY")
    print("=" * 60)
    print(story)
    print("\n" + "=" * 60)
    print("🌟 The End 🌟")
    print("=" * 60)


if __name__ == "__main__":
    main()
