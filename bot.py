import os
import telebot
from telebot import types

# --- Import your existing engine ---
from engine import Student, MatchingEngine

# ==========================================
# CONFIGURATION
# ==========================================

BOT_TOKEN = os.environ["BOT_TOKEN"]  # Set this as an environment variable — never hardcode it

# ==========================================
# CANDIDATE POOL
# Replace this list with however you store registered students
# (e.g. load from a JSON file, SQLite DB, etc.)
# ==========================================

CANDIDATE_POOL = [
    Student("Alice",   "@alice_studies", "CS2040S", {"Mon 6PM", "Wed 6PM"},              {"Concept understanding"}),
    Student("Bob",     "@bob_codes",     "CS2040S", {"Mon 6PM", "Wed 6PM", "Fri 6PM"},   {"Concept understanding", "Tutorial Help"}),
    Student("Charlie", "@charlie_hacks", "CS2040S", {"Tue 6PM", "Thu 6PM"},              {"Exam paper practice"}),
    Student("Diana",   "@diana_ml",      "DSA1101", {"Mon 6PM", "Wed 6PM"},              {"Concept understanding"}),
    Student("Eve",     "@eve_sec",       "CS2040S", {"Wed 6PM", "Fri 6PM"},              {"Tutorial Help", "Exam paper practice"}),
    Student("Frank",   "@frank_math",    "MH1811",  {"Mon 6PM"},                         {"Concept understanding"}),
    Student("Grace",   "@grace_eng",     "CV2020",  {"Tue 6PM"},                         {"Tutorial Help"}),
    Student("Heidi",   "@heidi_sec",     "CS2030",  {"Mon 6PM", "Tue 6PM"},              {"Exam paper practice"}),
    Student("Ivan",    "@ivan_dev",      "CS2040S", {"Mon 6PM", "Wed 6PM"},              {"Concept understanding", "Exam paper practice"}),
    Student("Judy",    "@judy_data",     "DSA1101", {"Mon 6PM", "Wed 6PM", "Fri 6PM"},   {"Concept understanding", "Tutorial Help"}),
]

# Predefined options shown to the user as inline buttons.
# Add or remove slots/objectives to match your system.
AVAILABLE_TIMES = [
    "Mon 6PM", "Tue 6PM", "Wed 6PM", "Thu 6PM", "Fri 6PM",
    "Sat 10AM", "Sun 10AM",
]
AVAILABLE_OBJECTIVES = [
    "Concept understanding",
    "Tutorial Help",
    "Exam paper practice",
]

# ==========================================
# BOT SETUP
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)
engine = MatchingEngine()

# ==========================================
# CONVERSATION STATE
# Keyed by Telegram user_id.
# Each entry: {"step": str, "data": dict}
# ==========================================

user_sessions: dict[int, dict] = {}

STEP_NAME       = "name"
STEP_COURSE     = "course"
STEP_TIMES      = "times"
STEP_OBJECTIVES = "objectives"


# ==========================================
# HELPER: INLINE KEYBOARDS
# ==========================================

def _make_multiselect_keyboard(options: list[str], selected: set[str], done_label: str) -> types.InlineKeyboardMarkup:
    """
    Builds an inline keyboard where each option toggles on/off.
    A "Done" button is shown at the bottom to confirm the selection.
    Callback data format: "toggle::<option text>"
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for option in options:
        tick = "✅ " if option in selected else ""
        buttons.append(
            types.InlineKeyboardButton(
                text=f"{tick}{option}",
                callback_data=f"toggle::{option}",
            )
        )
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton(text=f"✔ {done_label}", callback_data="done"))
    return keyboard


# ==========================================
# HELPER: FORMAT MATCH RESULTS
# ==========================================

def _format_results(target: Student, matches: list[tuple[Student, float]]) -> str:
    if not matches:
        return (
            "😕 No compatible study partners found yet.\n\n"
            "This usually means no one in the pool shares your course *and* "
            "has at least one overlapping time slot.\n"
            "Try /start again to update your availability."
        )

    lines = [
        f"🎯 *Top study group matches for {target.name}*",
        f"📚 Course: `{target.course}`\n",
    ]

    for rank, (match, score) in enumerate(matches, start=1):
        shared_times = sorted(target.time_slots & match.time_slots)
        shared_goals = sorted(target.objectives & match.objectives)

        lines.append(f"*{rank}. {match.name}*  —  Score: `{score:.0%}`")
        lines.append(f"   Telegram: {match.telegram_handle}")
        lines.append(f"   🕐 Shared slots: {', '.join(shared_times) or 'None'}")
        lines.append(f"   🎯 Shared goals: {', '.join(shared_goals) or 'None'}")
        lines.append("")

    lines.append("_Reach out to your matches above to form a study group!_")
    return "\n".join(lines)


# ==========================================
# COMMAND HANDLERS
# ==========================================

@bot.message_handler(commands=["start", "find"])
def cmd_start(message: types.Message):
    """Entry point — begins the onboarding conversation."""
    user_sessions[message.from_user.id] = {
        "step": STEP_NAME,
        "data": {
            "name":       None,
            "course":     None,
            "times":      set(),
            "objectives": set(),
        },
    }
    bot.send_message(
        message.chat.id,
        "👋 Welcome to the *Study Group Matcher*!\n\n"
        "I'll ask you a few quick questions to find your best study partners.\n\n"
        "What is your *full name*?",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message: types.Message):
    user_sessions.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "❌ Cancelled. Type /start whenever you're ready.")


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    bot.send_message(
        message.chat.id,
        "*Study Group Matcher — Commands*\n\n"
        "/start or /find — Begin finding a study group\n"
        "/cancel — Cancel the current session\n"
        "/help — Show this message",
        parse_mode="Markdown",
    )


# ==========================================
# TEXT MESSAGE HANDLER (name & course steps)
# ==========================================

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message: types.Message):
    uid = message.from_user.id
    session = user_sessions.get(uid)

    if not session:
        bot.send_message(
            message.chat.id,
            "Type /start to find a study group, or /help for more info.",
        )
        return

    step = session["step"]
    text = message.text.strip()

    # --- Step 1: collect name ---
    if step == STEP_NAME:
        if len(text) < 2:
            bot.send_message(message.chat.id, "Please enter a valid name (at least 2 characters).")
            return
        session["data"]["name"] = text
        session["step"] = STEP_COURSE
        bot.send_message(
            message.chat.id,
            f"Nice to meet you, *{text}*! 👋\n\n"
            "What is your *module code*? (e.g. `CS2040S`, `DSA1101`)",
            parse_mode="Markdown",
        )

    # --- Step 2: collect course ---
    elif step == STEP_COURSE:
        course = text.upper()
        session["data"]["course"] = course
        session["step"] = STEP_TIMES
        keyboard = _make_multiselect_keyboard(AVAILABLE_TIMES, set(), "Done — confirm times")
        bot.send_message(
            message.chat.id,
            f"Got it — *{course}*.\n\n"
            "Now select *all the time slots* you are available for study sessions.\n"
            "Tap a slot to toggle it, then press ✔ Done when finished.",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    # Ignore unexpected text during multi-select steps
    elif step in (STEP_TIMES, STEP_OBJECTIVES):
        bot.send_message(
            message.chat.id,
            "Please use the buttons above to make your selection.",
        )


# ==========================================
# CALLBACK QUERY HANDLER (multi-select steps)
# ==========================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: types.CallbackQuery):
    uid = call.from_user.id
    session = user_sessions.get(uid)

    if not session:
        bot.answer_callback_query(call.id, "Session expired. Type /start to begin.")
        return

    step = session["step"]
    data = call.data

    # --- Toggle a selection ---
    if data.startswith("toggle::"):
        option = data.split("::", 1)[1]

        if step == STEP_TIMES:
            selected = session["data"]["times"]
            if option in selected:
                selected.discard(option)
            else:
                selected.add(option)
            keyboard = _make_multiselect_keyboard(AVAILABLE_TIMES, selected, "Done — confirm times")

        elif step == STEP_OBJECTIVES:
            selected = session["data"]["objectives"]
            if option in selected:
                selected.discard(option)
            else:
                selected.add(option)
            keyboard = _make_multiselect_keyboard(AVAILABLE_OBJECTIVES, selected, "Done — find matches!")

        else:
            bot.answer_callback_query(call.id)
            return

        # Update the existing message in place so the chat stays clean
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
            )
        except Exception:
            pass  # Message unchanged — ignore Telegram's "not modified" error

        bot.answer_callback_query(call.id)

    # --- Done button ---
    elif data == "done":

        if step == STEP_TIMES:
            selected_times = session["data"]["times"]
            if not selected_times:
                bot.answer_callback_query(call.id, "⚠️ Please select at least one time slot.", show_alert=True)
                return

            # Remove the keyboard from the times message
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None,
            )
            session["step"] = STEP_OBJECTIVES
            keyboard = _make_multiselect_keyboard(AVAILABLE_OBJECTIVES, set(), "Done — find matches!")
            bot.send_message(
                call.message.chat.id,
                f"✅ Saved {len(selected_times)} time slot(s).\n\n"
                "Last step! Select your *learning objectives*.\n"
                "Tap each goal that applies, then press ✔ Done.",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            bot.answer_callback_query(call.id)

        elif step == STEP_OBJECTIVES:
            selected_objectives = session["data"]["objectives"]
            if not selected_objectives:
                bot.answer_callback_query(call.id, "⚠️ Please select at least one objective.", show_alert=True)
                return

            # Remove the keyboard
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None,
            )
            bot.answer_callback_query(call.id)

            # --- Build the Student and run the engine ---
            d = session["data"]
            telegram_handle = f"@{call.from_user.username}" if call.from_user.username else f"tg://user?id={uid}"

            new_student = Student(
                name=d["name"],
                telegram_handle=telegram_handle,
                course=d["course"],
                time_slots=d["times"],
                objectives=d["objectives"],
            )

            bot.send_message(call.message.chat.id, "🔍 Searching for your best matches...")

            matches = engine.find_best_matches(new_student, CANDIDATE_POOL, top_n=3)
            result_text = _format_results(new_student, matches)

            bot.send_message(
                call.message.chat.id,
                result_text,
                parse_mode="Markdown",
            )

            # Clean up session
            user_sessions.pop(uid, None)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    print("Bot is running... Press Ctrl+C to stop.")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
