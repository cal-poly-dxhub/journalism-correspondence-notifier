from aws_utils import invoke_llm
from lazerfiche_utils import get_document_text, get_doc_url_from_id
import re
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os


def get_most_common_words(text, n=3):
    words = re.findall(r"\w+", text.lower())
    with open("stopwords.txt", "r") as file:
        stop_words = [line.strip() for line in file]
    filtered_words = [
        word for word in words if word not in stop_words and len(word) >= 4
    ]
    return Counter(filtered_words).most_common(n)


def generate_word_cloud(analysis):
    # Generate HTML for word cloud
    word_cloud_html = ""
    for word, count in analysis["word_frequencies"]:
        word_cloud_html += f'<span class="word-item">{word}: {count}</span>'

    return word_cloud_html


def analyze_sentiment(document_text):
    instructions = """
    Decide whether a citizens message is in SUPPORT, NEUTRAL, or AGAINST a bill.
    Do not explain yourself. Be succinct.
    Return your answer in the format <polarity>YOUR_ANSWER</polarity>
    Ex: <polarity>SUPPORT</polarity>
    """

    response = invoke_llm(document_text, instructions, 150)

    answer = response.split("<polarity>")[1].split("</polarity>")[0]

    return answer


def analyze_correspondence(entry):
    """Process single correspondence entry and return its analysis"""
    document_text = get_document_text(entry[1])
    if not document_text:
        return None

    summary = get_email_summary(document_text)
    polarity = analyze_sentiment(document_text)

    return {
        "text": document_text,
        "summary": summary,
        "polarity": polarity,
        "email_details": (entry[2], summary, get_doc_url_from_id(entry[1])),
    }


def count_polarities(analyses):
    """Count different polarity types"""
    counts = {"SUPPORT": 0, "NEUTRAL": 0, "AGAINST": 0}
    for analysis in analyses:
        if analysis:
            counts[analysis["polarity"]] += 1
    return counts


def get_email_summary(text):
    """Get summary for single email"""
    return invoke_llm(text, os.getenv("CITIZEN_SENTIMENT_PROMPT"))


def get_overall_summary(full_text):
    """Get overall summary of all correspondence"""
    if not full_text:
        return ""
    return invoke_llm(full_text, os.getenv("OVERALL_SENTIMENT_PROMPT"), 500)


def analyze_sentiment_value(text):
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    return scores["compound"]


def process_summaries(summaries):
    html_summaries = ""
    for name, content, link in summaries:
        if not content:
            continue
        sentiment = analyze_sentiment_value(content)

        civility_text = ""
        rounded_polarity = int(round(sentiment, 2) * 100)

        if rounded_polarity > 0:
            civility_text = f"%{rounded_polarity} Positive"
        elif rounded_polarity == 0:
            civility_text = "Neutral"
        else:
            civility_text = f"%{abs(rounded_polarity)} Negative"

        html_summaries += f"""
            <div class="citizen">
                <div class="citizen-header">
                    <h3>{name}</h3>
                    <a href="{link}" class="link-button" target="_blank">Link</a>
                    <p>Civility: {civility_text}</p>
                </div>
                <p>{content.strip()}</p>
            </div>
            """
    return html_summaries


def get_issue_summary_and_polarity(correspondence_data, agenda_item):
    """Main function to analyze all correspondence"""
    # Filter relevant entries
    relevant_entries = [
        entry for entry in correspondence_data if entry and entry[0] == agenda_item
    ]

    # Analyze each correspondence
    analyses = [analyze_correspondence(entry) for entry in relevant_entries]
    analyses = [a for a in analyses if a]  # Remove None values

    # Get counts
    counts = count_polarities(analyses)

    # Compile full text and email summaries
    full_text = " ".join(analysis["text"] for analysis in analyses)

    individual_email_summaries = process_summaries(
        [analysis["email_details"] for analysis in analyses]
    )

    # Get most common words and their frequencies
    word_frequencies = get_most_common_words(full_text)

    # Get overall summary
    overall_summary = get_overall_summary(full_text)

    return {
        "overall_summary": overall_summary,
        "individual_summaries": individual_email_summaries,
        "word_frequencies": word_frequencies,
        "polarity": analyses[0]["polarity"] if analyses else None,
        "support_count": counts["SUPPORT"],
        "neutral_count": counts["NEUTRAL"],
        "against_count": counts["AGAINST"],
    }
