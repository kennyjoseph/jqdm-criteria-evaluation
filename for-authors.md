# Criteria evaluation (draft text for the submission instructions)

Before you submit your full paper, we're asking that you:

1. Run this JQD:DM criteria evaluation tool on your manuscript
2. If you wish, make changes to your paper based on the tool's output.
3. Submit the final iteration of the output of this tool, alongside your paper, and optionally, a response that helps to explain why you didn't address various points made by the tool, and anything else you'd like to say.

**What this tool is.** Running as an AI coding agent such as Claude Code, this tool reads your manuscript and your accepted Letter of Inquiry and scores the paper 0–3 on 16 criteria: how well it carries out the accepted aim, describes its data and measures, presents its results and matches its claims to the evidence. It gives page references, quotes and one potential fix for each gap. It does not recommend acceptance or rejection. A score of 2 ("Mostly") is common in published JQD:DM papers.

**How to run it.** Download the `jqd-paper-review` folder [link], put it where your agent finds skills, and ask the agent to run it on your manuscript and LOI. The folder's `README.md` gives the steps. A run takes about five minutes. The tool runs on your computer and does not use the web; your manuscript is sent to the model your agent uses, under that provider's terms.

**What you must respond to.** The evaluation lists these items under "Response required at submission", each with a label such as "D2-1". They are the gaps in criteria scored 0 or 1 that seem to impact the paper the most. For each one, either change the manuscript or explain in your associated letter  why you left it unchanged. **The suggested fix by the model is one way to address a point,** not the expected one: we trust you to make or not make fixes as you see fit. Similarly, if a point misreads your paper, just let us know.

**Who reads it.** The reviewers and the handling editor read the output from this tool, as well as your responses.

**If your AI tool cannot run code.** Some tools only chat: a chat window with code execution off, a university chat portal, or a local model in a chat app such as LM Studio or Ollama. Give the tool the file `manual-mode-single-file.md` and the full text of your manuscript, and ask it to follow the instructions in that file. It writes the evaluation in the same format, but nothing in it is checked by the tool's scripts, so verify the quotes and page numbers before you submit. Check that the tool could see your whole manuscript: some chat apps pass a long attachment to the model in pieces. Some institutional tools copy uploaded files to your institution's cloud storage (Microsoft Copilot saves them to your OneDrive); check that this is acceptable for an unpublished manuscript. A capable model matters. In our tests with Microsoft Copilot, the evaluation looked complete but was more lenient than the full tool and missed one of the paper's two main problems.

**What to submit.** The evaluation's HTML file, or the Markdown evaluation if you used the single-file version, with your responses.
