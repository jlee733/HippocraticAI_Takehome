from app.story_output import parse_story, story_only


class TestStoryOnly:
    def test_returns_story_unchanged_when_already_clean(self):
        story = "Once upon a time, there was a brave turtle named Terry."
        assert story_only(story) == story

    def test_strips_leading_preamble(self):
        response = "Here's a bedtime story for you:\n\nOnce upon a time, Terry dreamed of flying."
        assert story_only(response) == "Once upon a time, Terry dreamed of flying."

    def test_strips_trailing_commentary(self):
        response = (
            "Once upon a time, Terry dreamed of flying.\n\n"
            "I hope you enjoy the story! Let me know if you'd like any changes."
        )
        assert story_only(response) == "Once upon a time, Terry dreamed of flying."

    def test_strips_trailing_clarifying_question(self):
        response = (
            "Once upon a time, Terry dreamed of flying.\n\n"
            "What kind of animal should be Terry's best friend?"
        )
        assert story_only(response) == "Once upon a time, Terry dreamed of flying."


class TestParseStory:
    def test_splits_title_and_body(self):
        response = "Terry the Flying Turtle\n\nOnce upon a time, Terry dreamed of flying."
        assert parse_story(response) == (
            "Terry the Flying Turtle",
            "Once upon a time, Terry dreamed of flying.",
        )

    def test_strips_markdown_title_prefix(self):
        response = "# The Brave Little Fox\n\nThe fox woke up at dawn."
        assert parse_story(response) == ("The Brave Little Fox", "The fox woke up at dawn.")

    def test_handles_title_only_response(self):
        response = "A Cozy Night Adventure"
        assert parse_story(response) == ("A Cozy Night Adventure", "")

    def test_strips_line_number_labels(self):
        response = (
            "line 1: The Rusty Robots of Rainbow Valley\n"
            "line 2: line 3: Once upon a time, there were little robots."
        )
        assert parse_story(response) == (
            "The Rusty Robots of Rainbow Valley",
            "Once upon a time, there were little robots.",
        )
