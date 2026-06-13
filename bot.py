import os, gc, logging, tempfile, shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from mods.cloth      import mod_cloth
from mods.gunskin    import mod_gunskin
from mods.charector  import mod_charector
from mods.hologram   import mod_hologram
from mods.wall_hack  import mod_wall_hack
from mods.mini_gloo  import mod_mini_gloo
from mods.fileinfo   import mod_fileinfo

# ═══════════════════════════════════════════
#  CONFIG — apna token aur user ID daalo
# ═══════════════════════════════════════════
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "APNA_TOKEN_YAHAN")
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))   # apna Telegram user ID
WORK_DIR    = "/tmp/ff_bot_work"
os.makedirs(WORK_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# ═══════════════════════════════════════════
#  OWNER GUARD — sirf owner access kar sake
# ═══════════════════════════════════════════
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id if update.effective_user else 0
        if uid != OWNER_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Access denied.", show_alert=True)
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper

# ═══════════════════════════════════════════
#  USER STATE
# ═══════════════════════════════════════════
# state[uid] = {
#   "step": "select_mod" | "wait_folder1" | "wait_folder2" | "wait_file" | "processing"
#   "mod":  mod name
#   "sub":  sub-option (wall mode etc)
#   "folders": {}   # collected folder paths
#   "files":   {}   # collected file paths (for multi-file mods)
# }
state = {}

def gs(uid):
    if uid not in state:
        state[uid] = {"step": "select_mod", "mod": None, "sub": None,
                      "folders": {}, "files": {}}
    return state[uid]

def reset(uid):
    state[uid] = {"step": "select_mod", "mod": None, "sub": None,
                  "folders": {}, "files": {}}

# ═══════════════════════════════════════════
#  MOD DEFINITIONS
#  Each mod defines what folders/files it needs
# ═══════════════════════════════════════════
MODS = {
    # name          : (label,          emoji, folder_prompts,                           sub_needed)
    "cloth"         : ("Cloth Mod",         "👗", ["📁 Normal clothes folder path bhejo:", "📁 REF (ob52 modified) folder path:", "📁 Output folder path:"], None),
    "gunskin"       : ("Gunskin Mod",       "🔫", ["📁 Normal Gunskin folder path:", "📁 Modified output folder path:"], None),
    "charector"     : ("Character Mod",     "🧍", ["📁 Normal Character folder path:", "📁 Output folder path:"], None),
    "hologram"      : ("Hologram Mod",      "🌈", ["📁 Normal file folder path:", "📁 Output folder path:"], None),
    "wall_hack"     : ("Wall Hack",         "🧱", ["📁 Normal file folder path:", "📁 Output folder path:"], "wall_sub"),
    "mini_gloo"     : ("Mini Gloo",         "🔹", ["📁 Normal gloo file folder path:", "📁 Output folder path:"], None),
    "fileinfo"      : ("File Info Update",  "📋", ["📁 Folder with modified files:", "📄 fileinfo.txt ka path bhejo:"], None),
}

# ═══════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════
def main_menu_kb():
    rows = []
    items = list(MODS.items())
    for i in range(0, len(items), 2):
        row = []
        for key, val in items[i:i+2]:
            row.append(InlineKeyboardButton(f"{val[1]} {val[0]}", callback_data=f"mod_{key}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def wall_sub_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👻 Trigger (wall se guzro)", callback_data="sub_trigger")],
        [InlineKeyboardButton("📏 Mide (patli wall)",       callback_data="sub_mide")],
        [InlineKeyboardButton("🔙 Cancel",                  callback_data="cancel")],
    ])

def cancel_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ]])

# ═══════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════
@owner_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reset(uid)
    await update.message.reply_text(
        "🎮 *FF MOD BOT*\n\n"
        "Niche se modification choose karo:",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )

# ═══════════════════════════════════════════
#  CALLBACK HANDLER
# ═══════════════════════════════════════════
@owner_only
async def button_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    uid = q.from_user.id
    await q.answer()
    data = q.data
    s    = gs(uid)

    # ── Cancel ──
    if data == "cancel":
        reset(uid)
        await q.edit_message_text("❌ Cancel ho gaya.", reply_markup=main_menu_kb())
        return

    # ── Mod select ──
    if data.startswith("mod_"):
        mod_key = data[4:]
        if mod_key not in MODS:
            return
        s["mod"]  = mod_key
        s["folders"] = {}
        s["files"]   = {}
        mod_info = MODS[mod_key]

        # Wall hack needs sub-selection first
        if mod_info[3] == "wall_sub":
            s["step"] = "wait_sub"
            await q.edit_message_text(
                f"{mod_info[1]} *{mod_info[0]}*\n\nMode select karo:",
                parse_mode="Markdown",
                reply_markup=wall_sub_kb()
            )
        else:
            # Ask first folder
            s["step"]         = "wait_folder"
            s["folder_idx"]   = 0
            prompt = mod_info[2][0]
            await q.edit_message_text(
                f"{mod_info[1]} *{mod_info[0]}*\n\n{prompt}",
                parse_mode="Markdown",
                reply_markup=cancel_kb()
            )
        return

    # ── Wall sub ──
    if data.startswith("sub_"):
        s["sub"]  = data[4:]
        s["step"] = "wait_folder"
        s["folder_idx"] = 0
        prompt = MODS[s["mod"]][2][0]
        await q.edit_message_text(
            f"✅ Mode: *{s['sub'].upper()}*\n\n{prompt}",
            parse_mode="Markdown",
            reply_markup=cancel_kb()
        )
        return

# ═══════════════════════════════════════════
#  MESSAGE HANDLER — folder paths + file uploads
# ═══════════════════════════════════════════
@owner_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    s   = gs(uid)

    # ── Collecting folder paths ──
    if s["step"] == "wait_folder":
        text = (update.message.text or "").strip()
        if not text:
            await update.message.reply_text("⚠️ Folder path text mein bhejo.")
            return

        mod_key  = s["mod"]
        prompts  = MODS[mod_key][2]
        idx      = s.get("folder_idx", 0)

        s["folders"][idx] = text
        idx += 1
        s["folder_idx"] = idx

        if idx < len(prompts):
            # Ask next folder/file
            await update.message.reply_text(prompts[idx], reply_markup=cancel_kb())
        else:
            # All paths collected — start processing
            s["step"] = "processing"
            await process_mod(update, context, uid, s)
        return

    # ── Default ──
    await update.message.reply_text(
        "👇 Pehle mod choose karo:",
        reply_markup=main_menu_kb()
    )

# ═══════════════════════════════════════════
#  PROCESS MOD
# ═══════════════════════════════════════════
async def process_mod(update, context, uid, s):
    mod_key = s["mod"]
    folders = s["folders"]
    sub     = s.get("sub")
    msg     = await update.message.reply_text("⏳ Processing...")

    try:
        result = ""

        if mod_key == "cloth":
            src, ref, dst = folders[0], folders[1], folders[2]
            os.makedirs(dst, exist_ok=True)
            ok, skip, err = mod_cloth(src, ref, dst)
            result = f"✅ *Cloth Done!*\n✔ OK: {ok}\n⏭ Skip: {skip}\n❌ Error: {err}\n\n📂 Output: `{dst}`"

        elif mod_key == "gunskin":
            src, dst = folders[0], folders[1]
            os.makedirs(dst, exist_ok=True)
            cm, cg = mod_gunskin(src, dst)
            result = f"✅ *Gunskin Done!*\n🔫 V4: {cm}\n🧱 Gloo: {cg}\n\n📂 Output: `{dst}`"

        elif mod_key == "charector":
            src, dst = folders[0], folders[1]
            os.makedirs(dst, exist_ok=True)
            cm, cant = mod_charector(src, dst)
            result = f"✅ *Character Done!*\n🎨 Mat: {cm}\n📡 Ant: {cant}\n\n📂 Output: `{dst}`"

        elif mod_key == "hologram":
            src, dst = folders[0], folders[1]
            os.makedirs(dst, exist_ok=True)
            done, skip = mod_hologram(src, dst)
            result = f"✅ *Hologram Done!*\n💉 Done: {done}\n⏭ Skip: {skip}\n\n📂 Output: `{dst}`"

        elif mod_key == "wall_hack":
            src, dst = folders[0], folders[1]
            os.makedirs(dst, exist_ok=True)
            saved, skipped = mod_wall_hack(src, dst, sub or "trigger")
            result = (f"✅ *Wall Hack Done!*\nMode: *{(sub or 'trigger').upper()}*\n"
                      f"✔ Saved: {saved}\n⏭ Skip: {skipped}\n\n📂 Output: `{dst}`")

        elif mod_key == "mini_gloo":
            src, dst = folders[0], folders[1]
            os.makedirs(dst, exist_ok=True)
            saved, skipped = mod_mini_gloo(src, dst)
            result = f"✅ *Mini Gloo Done!*\n✔ Saved: {saved}\n⏭ Skip: {skipped}\n\n📂 Output: `{dst}`"

        elif mod_key == "fileinfo":
            mod_folder   = folders[0]
            fileinfo_path = folders[1]
            changes = mod_fileinfo(fileinfo_path, mod_folder)
            result = f"✅ *FileInfo Updated!*\n📝 Changes: {changes}\n\n📄 Updated: `{fileinfo_path}`"

        await msg.edit_text(result, parse_mode="Markdown")

    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

    finally:
        reset(uid)
        # Show menu again
        await update.message.reply_text(
            "Koi aur mod karna hai?",
            reply_markup=main_menu_kb()
        )

# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════
def main():
    if OWNER_ID == 0:
        print("❌ OWNER_ID set nahi hai! .env mein daalo.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CallbackQueryHandler(button_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ FF MOD Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
