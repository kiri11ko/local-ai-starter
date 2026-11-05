title: SEO audit of klukyanov.ru
kind: code
expect: SEO_AUDIT.md, REPORT.md
contains: SEO_AUDIT.md: title, description, h1, canonical, robots.txt, sitemap, schema, open graph, priority
timeout: 1800
---
Do an SEO audit of the website https://klukyanov.ru/?theme=light (a personal site of a software engineer
who also sells development services). Use your web fetch tool to download the pages you need:
the home page, https://klukyanov.ru/robots.txt, https://klukyanov.ru/sitemap.xml and two or three
internal pages linked from the home page.

Write the audit to SEO_AUDIT.md with these sections:
1. Summary: overall state in 3-5 sentences and a score from 0 to 100.
2. On-page: title and meta description (quote them, give their length), h1 and the heading structure,
   canonical, language and hreflang, image alt texts, internal links.
3. Technical: robots.txt, sitemap.xml (how many URLs, are they valid), HTTP status and redirects you saw,
   page weight and render-blocking resources you can infer from the HTML.
4. Structured data: which Schema.org types are present (JSON-LD), what is missing.
5. Social: Open Graph and Twitter card tags.
6. Content: does the page clearly say who it is for and what to do next.
7. Priority list: the 10 most important fixes, each with impact (high/medium/low) and effort.

Only report what you actually saw in the fetched pages; write "not checked" when you could not fetch
something. Do not invent numbers.

When you are done, write REPORT.md in this folder: which URLs you fetched, what failed, how long the
audit took you in steps, and anything you are unsure about.
