"""
Story Engine: Contains StoryPlanner, Storyteller, and Judge classes.
"""

import json
import re
from typing import Callable

from app.prompts import (
    JUDGE_PROMPT,
    PLANNER_PROMPT,
    REFINER_PROMPT,
    STORYTELLER_PROMPT,
)

MAX_REFINEMENT_ITERATIONS = 2


def extract_json(text: str) -> dict:
    """Extract JSON from a response that might contain extra text."""
    text = text.strip()

    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block_match:
        text = code_block_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


class StoryPlanner:
    """Creates structured story outlines from user requests."""

    def __init__(self, model_fn: Callable[[str], str]):
        self.model_fn = model_fn

    def plan(self, user_request: str) -> dict:
        """Generate a story outline from the user's request."""
        prompt = PLANNER_PROMPT.format(user_request=user_request)
        response = self.model_fn(prompt)
        return extract_json(response)


class Storyteller:
    """Generates and refines stories from outlines."""

    def __init__(self, model_fn: Callable[[str], str]):
        self.model_fn = model_fn

    def generate(self, outline: dict) -> str:
        """Generate a story from an outline."""
        outline_str = json.dumps(outline, indent=2)
        prompt = STORYTELLER_PROMPT.format(outline=outline_str)
        return self.model_fn(prompt)

    def refine(self, story: str, feedback: str) -> str:
        """Refine a story based on judge feedback."""
        prompt = REFINER_PROMPT.format(story=story, feedback=feedback)
        return self.model_fn(prompt)


class Judge:
    """Evaluates stories for quality and age-appropriateness."""

    PASS_THRESHOLD = 7.0

    def __init__(self, model_fn: Callable[[str], str]):
        self.model_fn = model_fn

    def evaluate(self, story: str) -> dict:
        """Evaluate a story and return scores with feedback."""
        prompt = JUDGE_PROMPT.format(story=story)
        response = self.model_fn(prompt)
        result = extract_json(response)
        result["passed"] = result.get("overall_score", 0) >= self.PASS_THRESHOLD
        return result

    def format_evaluation(self, evaluation: dict) -> str:
        """Format evaluation results for display."""
        return format_evaluation(evaluation)


def format_evaluation(evaluation: dict) -> str:
    """Format evaluation results for display."""
    lines = [
        "**Story Evaluation**",
        f"- Age Appropriateness: {evaluation['age_appropriateness']['score']}/10 — {evaluation['age_appropriateness']['comment']}",
        f"- Engagement: {evaluation['engagement']['score']}/10 — {evaluation['engagement']['comment']}",
        f"- Story Structure: {evaluation['story_structure']['score']}/10 — {evaluation['story_structure']['comment']}",
        f"- Moral/Lesson: {evaluation['moral_lesson']['score']}/10 — {evaluation['moral_lesson']['comment']}",
        f"- Overall Score: {evaluation['overall_score']}/10",
        f"- Status: {'PASSED' if evaluation['passed'] else 'Needs Refinement'}",
    ]
    if not evaluation["passed"]:
        lines.append(f"- Feedback: {evaluation['feedback']}")
    return "\n".join(lines)


def judge_and_refine_story(
    story: str,
    model_fn: Callable[[str], str],
    max_iterations: int = MAX_REFINEMENT_ITERATIONS,
) -> tuple[str, dict]:
    """Evaluate a story and refine it until it passes or iterations are exhausted."""
    judge = Judge(model_fn)
    storyteller = Storyteller(model_fn)
    evaluation: dict = {}

    for iteration in range(max_iterations):
        evaluation = judge.evaluate(story)
        if evaluation["passed"]:
            break
        if iteration < max_iterations - 1:
            story = storyteller.refine(story, evaluation["feedback"])

    return story, evaluation
