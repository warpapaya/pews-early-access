#!/usr/bin/env python3
"""Create or update the Pews Early Access survey in the existing Formbricks workspace.

Reads FORMBRICKS_API_KEY from the environment or the existing CTM Formbricks
.api.env. Never prints the key. The script is idempotent by survey name.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("FORMBRICKS_BASE_URL", "https://intake.clearlinetechmethods.com")
WORKSPACE_ID = os.environ.get("FORMBRICKS_WORKSPACE_ID", "cmqpyibx2000301o21q2nx6y7")
SURVEY_NAME = "Pews Early Access"
API_ENV = Path("/Users/citadel/Projects/CTMWebsite2025/formbricks/.api.env")
RESULT_PATH = Path(__file__).resolve().parents[1] / "formbricks" / "survey-result.json"


def stable_id(label: str) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    digest = hashlib.sha256(("pews-early-access:" + label).encode()).digest()
    return "c" + "".join(alphabet[b % len(alphabet)] for b in digest[:23])


def i18n(text: str) -> dict[str, str]:
    return {"default": text}


def choice(prefix: str, label: str) -> dict:
    return {"id": stable_id(prefix + ":" + label), "label": i18n(label)}


def single(qid: str, headline: str, options: list[str], *, required: bool = True, subheader: str | None = None) -> dict:
    question = {
        "id": stable_id(qid),
        "type": "multipleChoiceSingle",
        "headline": i18n(headline),
        "required": required,
        "choices": [choice(qid, option) for option in options],
        "shuffleOption": "none",
        "displayType": "list",
    }
    if subheader:
        question["subheader"] = i18n(subheader)
    return question


def multi(qid: str, headline: str, options: list[str], *, required: bool = True, subheader: str | None = None) -> dict:
    question = single(qid, headline, options, required=required, subheader=subheader)
    question["type"] = "multipleChoiceMulti"
    return question


def open_text(qid: str, headline: str, *, required: bool = True, subheader: str | None = None, placeholder: str | None = None) -> dict:
    question = {
        "id": stable_id(qid),
        "type": "openText",
        "headline": i18n(headline),
        "required": required,
        "inputType": "text",
        "longAnswer": True,
        "charLimit": {"enabled": False},
    }
    if subheader:
        question["subheader"] = i18n(subheader)
    if placeholder:
        question["placeholder"] = i18n(placeholder)
    return question


def contact_info() -> dict:
    def field(show: bool, required: bool, placeholder: str) -> dict:
        return {"show": show, "required": required, "placeholder": i18n(placeholder)}

    return {
        "id": stable_id("contact"),
        "type": "contactInfo",
        "headline": i18n("Where should we follow up?"),
        "subheader": i18n("Clearline Technology Methods operates Pews. No automatic enrollment or generic newsletter; these details are used only for Pews research and follow-up."),
        "required": True,
        "firstName": field(True, True, "First name"),
        "lastName": field(True, False, "Last name (optional)"),
        "email": field(True, True, "Best email"),
        "phone": field(False, False, "Phone"),
        "company": field(True, True, "Church name"),
    }


QUESTIONS = [
    multi(
        "daily_friction",
        "What is taking too much time in your church today?",
        [
            "Planning services and worship",
            "Scheduling volunteers",
            "Keeping people records current",
            "Following up with guests and members",
            "Check-ins and attendance",
            "Giving records and reporting",
            "Care, prayer, and pastoral follow-up",
            "Too many disconnected tools",
            "Something else",
        ],
        subheader="Choose everything that regularly creates extra work or dropped handoffs.",
    ),
    multi(
        "current_system",
        "Which tools support that work today?",
        [
            "Planning Center",
            "Another church management platform",
            "A separate giving platform",
            "A separate email or SMS platform",
            "Spreadsheets, forms, or shared documents",
            "Paper or other manual processes",
            "A custom-built tool",
            "Something else or not sure",
        ],
        subheader="Choose every system involved in the workflow.",
    ),
    single(
        "church_size",
        "About how many people attend in a typical week?",
        ["Under 100", "100–249", "250–499", "500–999", "1,000+"],
    ),
    single(
        "role",
        "Which best describes your role?",
        [
            "Lead or executive pastor",
            "Worship pastor or ministry leader",
            "Church administrator or operations",
            "Finance or giving administration",
            "IT or systems volunteer",
            "Other church leadership",
        ],
    ),
    open_text(
        "workflow_example",
        "Where does information get re-entered, delayed, or dropped today?",
        required=False,
        placeholder="A recent handoff, how often it happens, and what went wrong are most useful.",
    ),
    single(
        "beta_timing",
        "If there is mutual fit, when could your church evaluate a bounded beta?",
        ["Now, if the scope is relevant", "Within the next 3 months", "Later this year", "Just following the build for now"],
    ),
    single(
        "price_range",
        "If Pews replaced several current tools, what monthly range could be realistic for your church?",
        [
            "Under $50 per month",
            "$50–$99 per month",
            "$100–$149 per month",
            "$150+ per month",
            "I need scope and savings details before I can estimate",
        ],
        subheader="This is budget context, not a commitment. Pricing and private-beta scope are still being validated.",
    ),
    contact_info(),
]

STYLING = {
    "overwriteThemeStyling": True,
    "brandColor": {"light": "#2f7374"},
    "elementHeadlineColor": {"light": "#17333f"},
    "elementDescriptionColor": {"light": "#4f626a"},
    "elementUpperLabelColor": {"light": "#36525d"},
    "buttonBgColor": {"light": "#2f7374"},
    "buttonTextColor": {"light": "#ffffff"},
    "inputBgColor": {"light": "#f7fbf9"},
    "inputBorderColor": {"light": "#a9c5bd"},
    "inputTextColor": {"light": "#17333f"},
    "optionBgColor": {"light": "#f7fbf9"},
    "optionLabelColor": {"light": "#17333f"},
    "optionBorderColor": {"light": "#a9c5bd"},
    "cardBackgroundColor": {"light": "#ffffff"},
    "cardBorderColor": {"light": "#d7e5e0"},
    "highlightBorderColor": {"light": "#2f7374"},
    "progressIndicatorBgColor": {"light": "#2f7374"},
    "progressTrackBgColor": {"light": "#d7e5e0"},
    "background": {"bg": "#edf5f2", "bgType": "color", "brightness": 100},
    "fontFamily": "Inter",
    "isDarkModeEnabled": False,
    "roundness": 8,
    "cardArrangement": {"linkSurveys": "simple", "appSurveys": "simple"},
    "linkSurveyCardWidth": "default",
    "isLogoHidden": True,
    "hideProgressBar": False,
    "buttonBorderRadius": 6,
    "buttonFontSize": 16,
    "buttonFontWeight": 600,
    "buttonPaddingX": 16,
    "buttonPaddingY": 12,
    "inputBorderRadius": 6,
    "optionBorderRadius": 6,
    "optionPaddingX": 16,
    "optionPaddingY": 16,
    "elementHeadlineFontSize": 18,
    "elementHeadlineFontWeight": 600,
    "elementDescriptionFontSize": 14,
    "elementDescriptionFontWeight": 400,
    "progressTrackHeight": 6,
}

BODY = {
    "workspaceId": WORKSPACE_ID,
    "name": SURVEY_NAME,
    "type": "link",
    "status": "inProgress",
    "displayOption": "displayOnce",
    "questions": QUESTIONS,
    "welcomeCard": {
        "enabled": True,
        "headline": i18n("Could your church help shape Pews?"),
        "subheader": i18n("Eight focused questions about your church, current tools, and where the week breaks down. About 2 minutes."),
        "buttonLabel": i18n("Start the early-access fit check"),
        "timeToFinish": True,
        "showResponseCount": False,
    },
    "endings": [
        {
            "id": stable_id("done"),
            "type": "endScreen",
            "headline": i18n("Thanks. Petie will read this."),
            "subheader": i18n("If a conversation seems useful, he will follow up personally. This does not guarantee beta access, timing, or pricing. No automatic enrollment or generic drip campaign."),
        }
    ],
    "hiddenFields": {
        "enabled": True,
        "fieldIds": [
            "brand", "page", "placement", "intent", "landing_page",
            "initial_referrer", "utm_source", "utm_medium", "utm_campaign",
            "utm_content", "utm_term", "gclid", "fbclid", "li_fat_id", "msclkid", "ttclid",
        ],
    },
    "styling": STYLING,
    "singleUse": {"enabled": False, "isEncrypted": True},
    "isVerifyEmailEnabled": False,
    "languages": [],
    "triggers": [],
}


def load_key() -> str:
    if os.environ.get("FORMBRICKS_API_KEY"):
        return os.environ["FORMBRICKS_API_KEY"]
    for raw in API_ENV.read_text().splitlines():
        if "=" not in raw or raw.lstrip().startswith("#"):
            continue
        key, value = raw.split("=", 1)
        if key.strip() == "FORMBRICKS_API_KEY":
            return value.strip().strip('"').strip("'")
    raise RuntimeError("FORMBRICKS_API_KEY not found")


def request(method: str, path: str, api_key: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"content-type": "application/json", "x-api-key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw[:1000]}
        return error.code, payload


def main() -> None:
    api_key = load_key()
    status, listed = request("GET", "/api/v1/management/surveys", api_key)
    if status != 200:
        raise SystemExit(f"Unable to list surveys: HTTP {status} {listed}")
    surveys = listed.get("data", [])
    existing = next((survey for survey in surveys if survey.get("name") == SURVEY_NAME), None)
    if existing:
        survey_id = existing["id"]
        status, response = request("PUT", f"/api/v1/management/surveys/{survey_id}", api_key, BODY)
        action = "updated"
    else:
        status, response = request("POST", "/api/v1/management/surveys", api_key, BODY)
        action = "created"
    if status not in (200, 201):
        raise SystemExit(f"Unable to configure survey: HTTP {status} {response}")
    survey = response.get("data", response)
    survey_id = survey["id"]
    public_url = f"{BASE_URL}/s/{survey_id}"
    result = {
        "action": action,
        "id": survey_id,
        "name": survey.get("name"),
        "status": survey.get("status"),
        "public_url": public_url,
        "question_count": len(survey.get("questions", [])),
        "styling": survey.get("styling"),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
