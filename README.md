# Hippocratic AI Coding Assignment

This bedtime story generator app uses a multi-agent LLM pipeline to create high-quality, age-appropriate stories for children ages 5-10.

## Requirements
This program requires [Docker](https://www.docker.com/products/docker-desktop/) with Docker Compose.

## Instructions
1. Set your OpenAI key:
   ```bash
   export OPENAI_API_KEY=<your_openai_api_key>
   ```
2. Start the app:
   ```bash
   docker compose up --build
   ```
3. Open [http://localhost:8501](http://localhost:8501) in your web browser

---

## Methodology
- In addition to the "ages 5-10" requirement, I added that the story should be rated "PG", to provide a reference point to a common content maturity standard for the LLM to reference. 
- According to [BookFox](https://thejohnfox.com/2023/08/whats-the-perfect-length-for-a-childrens-picture-book/), the ideal length for a picture book is 500-800 words, so I'll use this for our bedtime story word count range. 
- I tested first on gemma, Google's open source model, and then on ChatGPT-3.5-turbo via the API to optimize on costs
   -Total Open AI API Usage: 1211 input tokens + 707 output tokens (~$.0017) [pricing](https://openrouter.ai/openai/gpt-3.5-turbo)

# Story Arc Planner + Judge System Architecture

## Block Diagram


┌─────────────────────────────────────────────────────────────────────────────┐
│                           BEDTIME STORY GENERATOR                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────────┐
                              │     USER      │
                              │   (Request)   │
                              └───────┬───────┘
                                      │
                                      │ "A story about a brave turtle 
                                      │  who wants to fly"
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PLANNING PHASE                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        STORY PLANNER                                │    │
│  │                         (LLM Agent)                                 │    │
│  │                                                                     │    │
│  │  Input:  User's story request                                       │    │
│  │  Output: Structured outline (JSON)                                  │    │
│  │          - Title, Setting, Characters                               │    │
│  │          - Beginning, Rising Action, Climax, Resolution             │    │
│  │          - Moral/Lesson                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Story Outline
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           GENERATION PHASE                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         STORYTELLER                                 │   │
│  │                         (LLM Agent)                                 │   │
│  │                                                                     │   │
│  │  Input:  Story outline OR (story + feedback for refinement)         │   │
│  │  Output: Complete bedtime story (400-600 words)                     │   │
│  │          - Age-appropriate vocabulary                               │   │
│  │          - Engaging dialogue                                        │   │
│  │          - Sensory details                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Story Draft
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVALUATION PHASE                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          LLM JUDGE                                  │    │
│  │                         (LLM Agent)                                 │    │
│  │                                                                     │    │
│  │  Input:  Generated story                                            │    │
│  │  Output: Evaluation scores (1-10) + feedback                        │    │
│  │          - Age Appropriateness                                      │    │
│  │          - Engagement                                               │    │
│  │          - Story Structure                                          │    │
│  │          - Moral/Lesson                                             │    │
│  │          - Overall Score                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                    Score >= 7.0            Score < 7.0
                     (PASS)                  (REFINE)
                          │                       │
                          ▼                       │
                 ┌─────────────┐                  │
                 │ FINAL STORY │                  │
                 │   OUTPUT    │                  │
                 └─────────────┘                  │
                                                  │
                          ┌───────────────────────┘
                          │ Feedback
                          ▼
                 ┌─────────────────┐
                 │   REFINEMENT    │
                 │     LOOP        │──────────────┐
                 │ (max 2 passes)  │              │
                 └─────────────────┘              │
                          │                       │
                          └───────────────────────┘
                                 Back to Storyteller


## Data Flow Summary


┌──────────┐    ┌─────────┐    ┌─────────────┐    ┌───────┐    ┌────────┐
│   USER   │───▶│ PLANNER │───▶│ STORYTELLER │───▶│ JUDGE │───▶│ OUTPUT │
└──────────┘    └─────────┘    └─────────────┘    └───────┘    └────────┘
  Request        Outline          Story            Eval         Final
                 (JSON)           Draft           Scores        Story
                                    ▲               │
                                    │   Feedback    │
                                    └───────────────┘
                                      (if score < 7)


## Component Responsibilities

| Component   | Role                                      |
|-------------|-------------------------------------------|
| Planner     | Creates structured story outline          |
| Storyteller | Generates/refines the narrative           |
| Judge       | Evaluates quality, provides feedback      |

## Files

| File                  | Description                                    |
|-----------------------|------------------------------------------------|
| `main.py`             | CLI entry point and story generation pipeline  |
| `app/web.py`          | Streamlit web UI                               |
| `app/prompts.py`      | All prompt templates for each agent            |
| `app/story_engine.py` | StoryPlanner, Storyteller, Judge classes       |
| `app/models.py`       | LLM provider integrations                      |
| `app/story_output.py` | Story text cleanup and title parsing           |

## Evaluation Criteria

The Judge evaluates each story on:

1. **Age Appropriateness (1-10)**: Vocabulary, themes, no scary content
2. **Engagement (1-10)**: Fun, interesting, captivating for children
3. **Story Structure (1-10)**: Clear beginning, middle, climax, resolution
4. **Moral/Lesson (1-10)**: Gentle, positive takeaway

**Pass Threshold**: Overall score >= 7.0