# 🤖 Reviewer Bot

A modern Discord bot for managing code and task reviews in your server!  
Reviewer Bot helps your community organize, track, and complete reviews with ease, using intuitive slash commands and interactive buttons.

---

## ✨ Features

- **Slash Commands** for all major actions
- **Active Reviews** and **Reviewed Tasks** channels, auto-managed
- **Role-based Review Assignment**: Assign reviews to specific roles
- **Interactive Buttons** for marking tasks as reviewed, moving them back, or deleting
- **DM Notifications** for review completions
- **Permission-aware**: Only authors or assigned roles can mark reviews as complete
- **Persistent Data**: All reviews are stored in a JSON file
- **Easy Setup**: One command to get started!

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/MassimoNodin/reviewer-bot.git
cd reviewer-bot
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

> **Note:** This bot requires Python 3.9+ and the latest version of `discord.py`.

### 3. Add Your Bot Token

- Create a file named `token.txt` in the project root.
- Paste your Discord bot token inside (no spaces or newlines).

`.gitignore` already excludes this file for your safety.

### 4. Run the Bot

```bash
python reviewer.py
```

---

## 🛠️ Usage

### Setup

- `/create`  
  *Admin only.* Creates the `active-reviews` and `reviewed-tasks` channels.

### Submitting a Review

- `/review title:"Task Title" role:@Role link:"URL"`  
  Submit a task for review.  
  - `role` and `link` are optional.
  - Or use the **Create Review** button in the `active-reviews` channel.

### Managing Reviews

- **Mark as Reviewed**  
  Only the author or assigned roles can mark a review as complete.

- **Move Back**  
  Move a reviewed task back to active reviews.

- **Delete**  
  Delete a review (only the author can delete their own).

### Help

- `/help`  
  Get a DM with a full guide to using the bot.

- `/delete`  
  *Admin only.* Delete the review channels after confirmation.

---

## 📁 Project Structure

```
reviewer.py
cogs/
  review_commands.py
  review_views.py
  review_modals.py
  review_utils.py
  review_events.py
reviews.json
token.txt
.gitignore
README.md
```

---

## 📝 Customization

- **Channel Names:**  
  Change `'active-reviews'` and `'reviewed-tasks'` in `review_commands.py` if you want custom names.

- **Permissions:**  
  The bot needs permission to manage channels, send messages, use slash commands, and manage messages.

---

## 🛡️ Security

- **Never share your `token.txt`!**
- The bot will not commit your token or review data thanks to `.gitignore`.

---

## 💡 Tips

- Pin the bot's help message in your channels for easy access.
- Use roles to organize who can review what.
- Only admins can create or delete review channels.

---

## 🤝 Contributing

Pull requests and suggestions are welcome!  
Open an issue or submit a PR to help improve Reviewer Bot.

---

## 📜 License

MIT License

---

## 👤 Author

Made with ❤️ by Massimo Nodin

---

Enjoy organized, efficient reviews with Reviewer Bot! 🚀
