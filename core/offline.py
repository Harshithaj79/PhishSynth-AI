"""Template-based generator. Used when no Groq key is set, when Groq fails, and for fast bulk dataset builds."""
import random
from .taxonomy import CATEGORIES

GREET = {"formal": ["Dear [USER],", "Hello [USER],"], "casual": ["Hi [USER],", "Hey [USER],"],
         "terse": ["[USER] -", "[USER],"], "polished": ["Hello [USER],", "Good morning [USER],"]}
CLOSE = {"formal": ["Sincerely,\n[COMPANY] Customer Care", "Regards,\n[COMPANY] Support Team"],
         "casual": ["Thanks!\n[COMPANY] Team", "Cheers,\n[COMPANY]"], "terse": ["- [COMPANY]", "[COMPANY] Support"],
         "polished": ["Thank you for your prompt attention,\n[COMPANY] Account Services", "Warm regards,\n[COMPANY] Trust & Safety"]}

PHISH_EXTRA = {
    "easy": ["Failure to respond will result in further action.", "Act now to avoid interruption.", "This is an automated message, do not reply.",
             "Do not ignore this notice.", "Your cooperation is mandatory."],
    "hard": ["If you have already done this, you can disregard this message.", "This is part of our routine review.",
             "You can also reach us through the help centre.", "Thanks for helping us keep things running smoothly.", "It only takes a minute."],
}
LEGIT_EXTRA = ["Let me know if you have any questions.", "No action is needed from you.", "Thanks for your help with this.",
               "Feel free to reply to this email.", "Have a great week."]

# category -> {"subjects": {diff: [...]}, "bodies": {diff: [...]}}
T = {
 "urgency": {"subjects": {"easy": ["URGENT: action required", "Final notice - verify now"], "hard": ["Quick confirmation needed", "Account review - one step left"]},
   "bodies": {"easy": ["URGENT: your [COMPANY] account needs attention. You must verify your details within [DATE] or it will be limited. Verify now: [SAFE-LINK]",
                       "Immediate action required. Confirm your information before [DATE] to avoid losing access: [SAFE-LINK]"],
              "hard": ["We're completing a routine review of [COMPANY] accounts and still need a quick confirmation from you before [DATE]. It takes about a minute: [SAFE-LINK]",
                       "Before [DATE], could you confirm your details are up to date? We'd like to finish this review: [SAFE-LINK]"]}},
 "authority": {"subjects": {"easy": ["Message from the Director", "Confidential - sign immediately"], "hard": ["Quick task from leadership", "Can you help with this today?"]},
   "bodies": {"easy": ["This is the Office of the Director at [COMPANY]. Review and sign the attached policy update immediately: [SAFE-LINK]. Keep this strictly confidential.",
                       "Management requires your acknowledgement of the new compliance notice today: [SAFE-LINK]. Do not discuss with colleagues."],
              "hard": ["I'm between meetings and need a hand with something for [COMPANY] leadership. Could you open the document here and confirm the figures by end of day? [SAFE-LINK]",
                       "Do you have a minute? I need the attached review signed off before the board call, details here: [SAFE-LINK]"]}},
 "fear": {"subjects": {"easy": ["Your account will be suspended", "WARNING: account compromised"], "hard": ["New sign-in to your account", "Security notice for [USER]"]},
   "bodies": {"easy": ["Your [COMPANY] account has been compromised and will be suspended in [DATE]. Confirm your identity immediately to avoid permanent closure: [SAFE-LINK]",
                       "Unauthorized access was detected. Your account is locked until you verify your identity: [SAFE-LINK]"],
              "hard": ["We detected a sign-in to your [COMPANY] account from a device we don't recognise. If this wasn't you, please review recent activity: [SAFE-LINK]",
                       "A new device signed in to your account. Please confirm it was you so we can keep your account protected: [SAFE-LINK]"]}},
 "reward": {"subjects": {"easy": ["You have won a reward!", "Claim your [AMOUNT] prize"], "hard": ["Refund available on your account", "Overpayment credit pending"]},
   "bodies": {"easy": ["Congratulations! You have been selected to receive a [AMOUNT] reward from [COMPANY]. Claim your prize before [DATE]: [SAFE-LINK]",
                       "You are our lucky winner! Claim your free gift of [AMOUNT] now: [SAFE-LINK]"],
              "hard": ["Our records show an overpayment on your [COMPANY] account. A refund of [AMOUNT] is ready; please confirm where to send it: [SAFE-LINK]",
                       "A credit of [AMOUNT] is available on your account. Confirm your preferences to receive it: [SAFE-LINK]"]}},
 "shared_doc": {"subjects": {"easy": ["Confidential file shared with you", "Open this document now"], "hard": ["[USER], a file was shared with you", "Document awaiting your comments"]},
   "bodies": {"easy": ["A file called 'Salary_Review_Confidential' was shared with you. Open it now to view: [SAFE-LINK]",
                       "You have 1 new secure document waiting. Click to open before it expires on [DATE]: [SAFE-LINK]"],
              "hard": ["A colleague at [COMPANY] shared 'Q3 planning notes' with you and asked for your comments. Open it here: [SAFE-LINK]",
                       "The team shared a folder with you. You can view and edit it from this page: [SAFE-LINK]"]}},
 "invoice": {"subjects": {"easy": ["Invoice overdue - pay immediately", "Payment required today"], "hard": ["Updated invoice and remittance details", "Invoice for [AMOUNT] due [DATE]"]},
   "bodies": {"easy": ["Invoice overdue! Payment of [AMOUNT] is required immediately. Our bank details have changed; pay via the portal: [SAFE-LINK]",
                       "Final reminder: [AMOUNT] is past due. Pay today to avoid penalties: [SAFE-LINK]"],
              "hard": ["Attached is the updated invoice for [AMOUNT], due [DATE]. Please note our remittance details changed this quarter; the new details are on the payment page: [SAFE-LINK]",
                       "Following our last call, here is the revised invoice for [AMOUNT]. Payment instructions are updated here: [SAFE-LINK]"]}},
 "credential_reset": {"subjects": {"easy": ["Your password expires today!", "Re-enter your login details"], "hard": ["Password reset requested", "Confirm your sign-in details"]},
   "bodies": {"easy": ["Your password expires today! Log in to [COMPANY] and re-enter your credentials to keep access: [SAFE-LINK]",
                       "Your mailbox is full. Login now to restore service by entering your username and password: [SAFE-LINK]"],
              "hard": ["A password reset was requested for your [COMPANY] account. Use the secure page to continue: [SAFE-LINK]. We'll need you to sign in again to finish.",
                       "To keep your account active, please sign in again and confirm your details on this page: [SAFE-LINK]"]}},
 "callback": {"subjects": {"easy": ["Your subscription was renewed", "Charge of [AMOUNT] - call now"], "hard": ["Receipt for your payment", "Billing confirmation [DATE]"]},
   "bodies": {"easy": ["Your [COMPANY] subscription was renewed for [AMOUNT]. If you did not authorise this, call [PHONE] immediately to cancel.",
                       "A charge of [AMOUNT] will be taken today. Call [PHONE] right away to dispute it."],
              "hard": ["Thanks for your payment of [AMOUNT]. If anything looks wrong with this charge, our billing team can help on [PHONE] before [DATE].",
                       "Your plan renewed on [DATE] for [AMOUNT]. Questions about this receipt? Call our billing line on [PHONE]."]}},
 "legitimate": {"subjects": {"easy": ["Team meeting notes", "Your order has shipped", "Lunch on Friday?"], "hard": ["Reminder: password expires on [DATE]", "Invoice [AMOUNT] due [DATE]", "Please confirm attendance"]},
   "bodies": {"easy": ["Thanks for joining today's session. Notes and next steps are saved in the shared team folder: [SAFE-LINK]",
                       "Your order has shipped and should arrive in 3-5 business days. You can track it any time from your account page.",
                       "Are we still on for lunch on Friday? I was thinking around 12:30."],
              "hard": ["Reminder: your [COMPANY] password expires on [DATE]. You can change it any time from the account settings page; there is no need to click anything in this email.",
                       "Your invoice for [AMOUNT] is due on [DATE]. You can view it by signing in to your account the usual way.",
                       "Quick heads-up: the team meeting moved to tomorrow morning. Please confirm your attendance in the calendar invite: [SAFE-LINK]"]}},
}

def generate(category, style="formal", difficulty="easy", n=3, rng=None):
    rng = rng or random.Random()
    t, out, seen = T[category], [], set()
    for _ in range(n * 6):
        if len(out) >= n: break
        d = difficulty
        body = rng.choice(t["bodies"][d])
        extra = rng.choice(LEGIT_EXTRA if category == "legitimate" else PHISH_EXTRA[d]) if rng.random() < 0.7 else ""
        text = "\n\n".join(x for x in [rng.choice(GREET[style]), body, extra, rng.choice(CLOSE[style])] if x)
        if style == "terse": text = "\n".join(x for x in [rng.choice(GREET[style]), body, rng.choice(CLOSE[style])] if x)
        subj = rng.choice(t["subjects"][d])
        if (subj, text) in seen: continue
        seen.add((subj, text))
        out.append({"subject": subj, "body": text, "indicators": rng.sample(CATEGORIES[category]["indicators"], 2)})
    return out
