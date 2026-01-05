"""
Bulk On-Screen Caption Generator

Generates 1000 viral-style captions for video overlays based on the
100captions.txt examples and 100captionsrules.txt style guide.

All captions are lowercase and evenly distributed across 10 categories.
"""

import anthropic
import csv
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MODEL = "claude-sonnet-4-5-20250929"

# The 10 caption categories from the rules
CATEGORIES = [
    "fake_innocence",      # "We're just friends" also us:
    "pov_situation",       # POV: / When... setups
    "fake_study",          # A new study found that...
    "shock_humor",         # Overt sexual innuendo, one-liners
    "female_desire",       # Girl math, my toxic trait, feral energy
    "kink_subculture",     # Gooning, niche internet slang
    "mock_qa",             # Genuine question to men...
    "comment_bait",        # Be honest in the comments...
    "chaotic_relatable",   # Chaotic bedroom/relationship behavior
    "visual_punchline",    # Setup that works with any flirty visual
]

GENERATION_PROMPT = """You are generating viral TikTok/Instagram on-screen captions.

## Style Rules
- ALL LOWERCASE - every single character must be lowercase
- NO QUOTATION MARKS - never use " in any caption
- NO PERIODS at the end of sentences
- Keep it short (1-3 lines max)
- Use casual chat grammar: u, ur, idc, rn, lowkey, highkey
- Confident, playful, slightly shameless tone
- Use emojis sparingly to dodge filters when needed (like the examples)
- Can use deliberate misspellings to dodge filters

## Category: {category}

{category_description}

## Example Captions (for reference style)
{examples}

## Your Task
Generate {count} UNIQUE captions in this category.
- Each caption on its own line
- ALL LOWERCASE
- NO QUOTATION MARKS (never use ")
- NO PERIODS at the end
- No numbering, no bullets, just the caption text
- Make them feel fresh, not copies of examples
- They should work as overlay text on a video of a girl being cute/flirty on camera

Output ONLY the captions, one per line, nothing else."""

CATEGORY_DESCRIPTIONS = {
    "fake_innocence": """Fake innocence / "we're just friends"
- Plays on mismatch between words and obviously sexual/romantic behavior
- Pattern: Setup with a "wholesome" claim, punchline shows it's clearly sexual
- Examples: "we're just friends" also us: / "he just wants to sleep with you" i want to sleep with him too""",

    "pov_situation": """POV / situation setups
- Uses POV or "when..." to drop the viewer into a specific moment
- Pattern: Start with "pov:" or "when..." then describe a hyper-specific micro-moment
- Examples: pov: you facetime your bumble match before meeting irl / when you're halfway through an argument and start to realise he's right""",

    "fake_study": """Fake "studies" / mock-informational
- Poses as research, statistics, rules, or how-to content
- Pattern: "a new study found...", "rule number 1:", "4 disadvantages of..."
- Then slide into obviously sexual or absurd content
- Examples: a new study found that women who used a man's face instead of a chair had their bloating reduced by 95%""",

    "shock_humor": """Overt sexual innuendo / shock humor
- Very explicit, uses emojis/slang to dodge filters
- Pattern: One sentence punchline, mixes wholesome framing with explicit act
- Examples: i'm so nice i pretend to gag on the small ones too / just the tip never hurt a friendship""",

    "female_desire": """Female desire / power and "feral" energy
- Centers her horniness, standards, or control
- Pattern: "girl math", "my toxic trait", "i think my biggest turn on..."
- Flip the usual dynamic into her dictating terms
- Examples: girl math is not wanting to get pregnant + having the feral urge to scream creampie me during ovulation""",

    "kink_subculture": """"Gooning" / kink-coded subculture captions
- Uses niche internet sex slang and meta-horny behavior
- Pattern: Casual lowercase, internet slang, treats niche kink as normal daily activity
- Examples: why do people get mad when you goon to them. i'd lowkey feel chosen""",

    "mock_qa": """Mock Q&A / "genuine question"
- Asks guys something that exposes sexual curiosity or humor
- Pattern: "genuine question:" / "men please be honest..." followed by weirdly specific curiosity
- Examples: genuine question: what do guys do with it when they poop... let it dangle down, put it on the seat, hold it?""",

    "comment_bait": """Textbook "hook" questions for comments
- Direct prompts to engage men/women in comments
- Pattern: Call out audience ("boys", "men", "ladies"), ask about mistakes/preferences
- Examples: boys let's be honest in the comments: which mistakes do people make when it comes to bjs?""",

    "chaotic_relatable": """Relatable chaotic bedroom / relationship behavior
- Sexual but framed as chaotic daily life
- Pattern: Start with "when i...", "me...", pair normal behavior with an overshare
- Examples: me preparing to get on top for a total of 34 seconds / when he likes lasting for ages but ur legs are already failing after 5 min""",

    "visual_punchline": """Text + visual punchline format
- Caption is only the setup; the video carries the joke
- Pattern: Setup ends with colon or implied "then this happens"
- Works with any flirty/thirsty shot
- Examples: when your selfies aren't hitting so you have to pull out this forbidden move: / the pose i gotta hit when our chats get a lil too intense""",
}


def load_examples():
    """Load example captions from 100captions.txt"""
    examples_file = Path(__file__).parent / "100captions.txt"
    if examples_file.exists():
        with open(examples_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Clean up the examples - remove empty lines and normalize
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return lines
    return []


def get_examples_for_category(all_examples, category):
    """Get relevant examples for a category (just return a sample for reference)"""
    # Return 10-15 random examples as style reference
    import random
    sample_size = min(15, len(all_examples))
    return random.sample(all_examples, sample_size)


def generate_captions_for_category(client, category, count, all_examples):
    """Generate captions for a specific category"""
    examples = get_examples_for_category(all_examples, category)
    examples_text = "\n".join(examples)

    prompt = GENERATION_PROMPT.format(
        category=category,
        category_description=CATEGORY_DESCRIPTIONS[category],
        examples=examples_text,
        count=count
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    response_text = message.content[0].text.strip()
    # Split into individual captions and clean them
    captions = []
    for line in response_text.split('\n'):
        line = line.strip()
        if line:
            # Ensure lowercase
            line = line.lower()
            # Remove quotation marks
            line = line.replace('"', '').replace('"', '').replace('"', '')
            # Remove trailing periods
            line = line.rstrip('.')
            captions.append(line)
    return captions


def main():
    if not API_KEY:
        api_key = input("Enter your Anthropic API key: ").strip()
        if not api_key:
            print("API key required")
            return
    else:
        api_key = API_KEY

    client = anthropic.Anthropic(api_key=api_key)

    # Load examples
    print("Loading examples...")
    all_examples = load_examples()
    print(f"Loaded {len(all_examples)} example captions")

    # Calculate how many captions per category
    total_target = 1000
    per_category = total_target // len(CATEGORIES)  # 100 per category

    print(f"\nGenerating {total_target} captions ({per_category} per category)...")
    print(f"Categories: {len(CATEGORIES)}")
    print("-" * 50)

    # Store captions by category
    captions_by_category = {category: [] for category in CATEGORIES}

    for i, category in enumerate(CATEGORIES):
        print(f"\n[{i+1}/{len(CATEGORIES)}] Generating {category}...")

        # Generate in batches of 50 to avoid token limits
        remaining = per_category

        while remaining > 0:
            batch_size = min(50, remaining)
            print(f"  Batch: {batch_size} captions...")

            try:
                captions = generate_captions_for_category(
                    client, category, batch_size, all_examples
                )
                captions_by_category[category].extend(captions)
                remaining -= len(captions)
                print(f"  Got {len(captions)} captions (total: {len(captions_by_category[category])})")
            except Exception as e:
                print(f"  Error: {e}")
                break

        print(f"  Category complete: {len(captions_by_category[category])} captions")

    # Save results as CSV with categories as columns
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    output_file = Path(__file__).parent / f"onscreen_captions_{timestamp}.csv"

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header row with category names
        writer.writerow(CATEGORIES)
        # Write rows - each row has one caption from each category
        for row_idx in range(per_category):
            row = []
            for category in CATEGORIES:
                if row_idx < len(captions_by_category[category]):
                    row.append(captions_by_category[category][row_idx])
                else:
                    row.append("")  # Empty if we didn't get enough
            writer.writerow(row)

    total_generated = sum(len(caps) for caps in captions_by_category.values())
    print(f"\n{'='*50}")
    print(f"DONE! Generated {total_generated} captions")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
