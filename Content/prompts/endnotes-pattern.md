# Footnotes and Endnotes Pattern

Use this pattern when a page needs standard footnotes plus a separate end-of-page notes section.

```html
<p>
  Main text with a footnote<a id="fnref:1" href="#fn:1" class="footnote"><sup>1</sup></a>
  and an endnote<a id="enref:1" href="#en:1" class="endnote"><sup>1</sup></a>.
</p>

<ol class="footnotes">
  <li id="fn:1">
    <p>
      Footnote text. <a href="#fnref:1" class="footnote__back" aria-label="Back to reference">↩</a>
    </p>
  </li>
</ol>

<ol class="endnotes">
  <li id="en:1">
    <p>
      Endnote text. <a href="#enref:1" class="endnote__back" aria-label="Back to endnote reference">↩</a>
    </p>
  </li>
</ol>
```

Notes:
- Keep footnotes in `<ol class="footnotes">`.
- Keep end-of-page notes in `<ol class="endnotes">`.
- Use separate back-link classes so the two systems can be styled independently.
