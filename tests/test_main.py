import json
from unittest.mock import patch

from main import generate_story


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


class TestGenerateStory:
    @patch("main.call_model")
    def test_returns_story_when_judge_passes(self, mock_call_model):
        mock_call_model.side_effect = [
            json.dumps(SAMPLE_OUTLINE),
            "Once upon a time, Terry dreamed of flying.",
            json.dumps(make_evaluation(8.5)),
        ]

        story = generate_story(
            "A turtle who wants to fly",
            model_fn=mock_call_model,
            verbose=False,
        )

        assert story == "Once upon a time, Terry dreamed of flying."
        assert mock_call_model.call_count == 3

    @patch("main.call_model")
    def test_refines_story_when_judge_fails(self, mock_call_model):
        mock_call_model.side_effect = [
            json.dumps(SAMPLE_OUTLINE),
            "Draft story.",
            json.dumps(make_evaluation(6.0)),
            "Refined story.",
            json.dumps(make_evaluation(8.0)),
        ]

        story = generate_story(
            "A turtle who wants to fly",
            model_fn=mock_call_model,
            verbose=False,
        )

        assert story == "Refined story."
        assert mock_call_model.call_count == 5
