# Setup guide (Windows)

## 1. Install the tools (one time, about 30 minutes)
| Tool | Where | Notes |
|---|---|---|
| Python 3 | python.org/downloads | On the first installer screen tick **Add python.exe to PATH**, then Install Now |
| Git | git-scm.com | Accept the defaults. When asked for the initial branch name, choose **Override** and enter `main` |
| VS Code (optional) | code.visualstudio.com | Tick "Add to PATH" and "Open with Code". Not the same as Visual Studio |
| GitHub account | github.com | Use a professional username. In Settings > Emails, tick **Keep my email addresses private** and use the `...@users.noreply.github.com` address for commits |

Check it worked: open a new terminal and run

    python --version
    git --version

Both should print a version number.

## 2. Get the project
    git clone https://github.com/<your-username>/dataguard.git
    cd dataguard

(No Git? Download the zip, extract it, and open the folder in VS Code with File > Open Folder.)

## 3. Run it
No installs needed for these:

    python run_dataguard.py            # good run + all bug runs, writes reports/dataguard_report.html
    python run_etl.py                  # correct ETL, prints row counts
    python run_etl.py B3               # ETL with a planted bug
    python practice/check_my_work.py   # grade your practice checks

## 4. Run the tests (needs pytest)
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pytest

## 5. Put your own copy on GitHub
1. On GitHub: **+ > New repository**, name it `dataguard`, set it to Public, and tick nothing else.
2. Tell Git who you are (once):

        git config --global user.name "Your Name"
        git config --global user.email "<your-noreply-email>"

3. In the project folder:

        git init
        git add .
        git commit -m "Initial DataGuard framework"
        git branch -M main
        git remote add origin https://github.com/<your-username>/dataguard.git
        git push -u origin main

4. A browser window opens for sign-in. Approve **Authorize git-ecosystem**. Refresh the repository page to see your files.

Later changes: `git add .`, `git commit -m "what you changed"`, `git push`.

## Troubleshooting
| Problem | Fix |
|---|---|
| `python` is not recognized, or opens the Microsoft Store | Python was installed without the PATH box ticked. Reinstall it with the box ticked, then restart the terminal |
| `git` is not recognized | Close and reopen VS Code or the terminal. If it still fails, reinstall Git |
| Warnings about "LF will be replaced by CRLF" | Harmless line-ending notices on Windows. Ignore them |
| `.venv\Scripts\activate` is blocked ("running scripts is disabled") | In PowerShell run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again. Or use Command Prompt instead |
| GitHub sign-in asks for a password but you signed up with Google | Click **Continue with Google** on the sign-in page |
| The **Authorize** button stays disabled | Wait 10 seconds, scroll down, or refresh the page. Otherwise choose **Sign in with a code** when Git asks you to sign in |
