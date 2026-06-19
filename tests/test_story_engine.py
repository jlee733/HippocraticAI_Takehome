import json

import pytest

from app.story_engine import Judge, StoryPlanner, Storyteller, extract_json, judge_and_refine_story


SAMPLE_OUTLINE = {
    "title": "Terry the Flying Turtle",
    "setting": "A sunny pond",
    "characters": [{"name": "Terry", "description": "A brave turtle"}],
    "beginning": "Terry watches birds fly.",
    "rising_action": "Terry tries to fly with leaves.",
    "climax": "Terry glides briefly on the wind.",
    "resolution": "Terry learns his own way to soar.",
    "moral": "Be yourself and keep trying.",
}


def make_evaluation(overall_score: float) -> dict:
    return {
        "age_appropriateness": {"score": 9, "comment": "Appropriate vocabulary."},
        "engagement": {"score": 8, "comment": "Fun and lively."},
        "story_structure": {"score": 8, "comment": "Clear arc."},
        "moral_lesson": {"score": 7, "comment": "Gentle lesson."},
        "overall_score": overall_score,
        "passed": overall_score >= 7.0,
        "feedback": "Story meets quality standards."
        if overall_score >= 7.0
        else "Add more dialogue and humor.",
    }


class TestExtractJson:
    def test_parses_plain_json(self):
        payload = {"title": "Test Story", "setting": "Forest"}
        assert extract_json(json.dumps(payload)) == payload

    def test_parses_json_in_code_block(self):
        text = '```json\n{"title": "Test Story"}\n```'
        assert extract_json(text) == {"title": "Test Story"}

    def test_parses_json_embedded_in_text(self):
        text = 'Here is the outline:\n{"title": "Test Story"}\nThanks!'
        assert extract_json(text) == {"title": "Test Story"}

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json("not json at all")


class TestStoryPlanner:
    def test_plan_returns_outline(self):
        planner = StoryPlanner(lambda prompt: json.dumps(SAMPLE_OUTLINE))
        assert planner.plan("A turtle who wants to fly") == SAMPLE_OUTLINE


class TestStoryteller:
    def test_generate_returns_story(self):
        storyteller = Storyteller(lambda prompt: "Once upon a time...")
        story = storyteller.generate(SAMPLE_OUTLINE)
        assert story == "Once upon a time..."

    def test_refine_returns_improved_story(self):
        storyteller = Storyteller(lambda prompt: "Improved story text.")
        story = storyteller.refine("Draft story.", "Add more dialogue.")
        assert story == "Improved story text."


class TestJudge:
    def test_evaluate_marks_story_as_passed(self):
        judge = Judge(lambda prompt: json.dumps(make_evaluation(8.5)))
        result = judge.evaluate("A cozy bedtime story.")
        assert result["passed"] is True
        assert result["overall_score"] == 8.5

    def test_evaluate_marks_story_as_failed(self):
        judge = Judge(lambda prompt: json.dumps(make_evaluation(6.0)))
        result = judge.evaluate("A draft story.")
        assert result["passed"] is False
        assert result["overall_score"] == 6.0

    def test_format_evaluation_includes_scores(self):
        judge = Judge(lambda prompt: json.dumps(make_evaluation(8.0)))
        formatted = judge.format_evaluation(make_evaluation(8.0))
        assert "Age Appropriateness: 9/10" in formatted
        assert "Overall Score: 8.0/10" in formatted
        assert "PASSED" in formatted

    def test_format_evaluation_includes_feedback_when_failed(self):
        judge = Judge(lambda prompt: json.dumps(make_evaluation(6.0)))
        formatted = judge.format_evaluation(make_evaluation(6.0))
        assert "Needs Refinement" in formatted
        assert "Add more dialogue and humor." in formatted


class TestJudgeAndRefineStory:
    def test_refines_story_when_judge_fails(self):
        responses = iter(
            [
                json.dumps(make_evaluation(6.0)),
                "Refined story.",
                json.dumps(make_evaluation(8.0)),
            ]
        )
        model_fn = lambda prompt: next(responses)

        story, evaluation = judge_and_refine_story("Draft story.", model_fn)

        assert story == "Refined story."
        assert evaluation["passed"] is True

    def test_returns_story_when_judge_passes(self):
        model_fn = lambda prompt: json.dumps(make_evaluation(8.5))

        story, evaluation = judge_and_refine_story("Final story.", model_fn)

        assert story == "Final story."
        assert evaluation["passed"] is True
