title: Landing page with a theme toggle
kind: code
check: python3 {case_dir}/verify/landing-page.py
expect: index.html, styles.css, script.js, REPORT.md
timeout: 1800
---
Build a one-page landing site for a fictional app "Pocket Planner", a calm to-do and calendar app.
Use plain HTML, CSS and JavaScript in three files: index.html, styles.css and script.js. No frameworks,
no CDNs, no build step.

Requirements:
- index.html has a <title>, a viewport meta tag, links styles.css and includes script.js;
- it uses <header>, <main> and <footer>;
- a hero section with a headline, a short pitch and a call-to-action button;
- at least three feature cards, each an element with class "feature";
- a pricing section with id "pricing" and three plans;
- a contact form with a name field, an email field (input type="email") and a submit button;
- a button with id "theme-toggle" switches between light and dark themes by setting data-theme="dark"
  or data-theme="light" on <html>; styles.css has [data-theme="dark"] rules; the choice is remembered in
  localStorage, and on the first visit the theme follows prefers-color-scheme;
- the layout works on a 375 px wide phone (use a @media query) and on a desktop;
- good contrast in both themes and visible focus styles.

When you are done, write REPORT.md in this folder: the structure of the page, the files you created,
how you checked it, and anything that did not work.
