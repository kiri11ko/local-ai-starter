# Test cases

Tasks for comparing local models on the same work. Run them from the wizard: start menu
→ "Test cases". The wizard runs each case, measures it and writes the results to
`local-ai/test-results/` (see the main README).

## Layout

```
test-cases/
  code/<id>.md      coding tasks, run through `opencode run`
  code/fixtures/    starting files copied into the model's work folder
  code/verify/      hidden checks; the model never sees them
  image/<id>.md     image prompts
  video/<id>.md     video prompts
  speech/<id>.md    texts to read aloud
```

## Case file format

`key: value` lines, a line with `---`, then the prompt. Code prompts are sent as they are;
image, video and speech prompts are joined into one line.

| Key | Kinds | Meaning |
|---|---|---|
| `title` | all | name shown in the wizard |
| `kind` | all | `code`, `image`, `video` or `speech` (required) |
| `fixtures` | code | folder, relative to the case file, copied into the work folder |
| `check` | code | command run in the work folder after the model finishes; exit code 0 means pass. `python3` is replaced by the wizard's Python, `{case_dir}` by the folder of the case file |
| `expect` | code | comma-separated files that must exist and not be empty |
| `contains` | code | `FILE: word, word, ...`: words that must appear in the file (case-insensitive) |
| `timeout` | code | seconds before the run is stopped (default 1800) |
| `seed` | image, video | fixed seed so models are compared on the same noise (default 42) |
| `size` | image, video | `WIDTHxHEIGHT`, overrides the model's default |
| `steps` | image, video | sampling steps, overrides the model's default |
| `frames` | video | number of frames, overrides the model's default |
| `lang` | speech | `en`, `ru`, ... (default: Russian for Cyrillic text, English otherwise) |

A case passes the check only if all of `expect`, `contains` and `check` pass. Each code
prompt should end by asking for `REPORT.md`, so the model describes its own work.
