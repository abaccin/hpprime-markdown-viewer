# MarkdownViewer for HP Prime

## The First Markdown Renderer for Your Calculator!

Read beautifully formatted documents right on your HP Prime.
No PC required.

## Navigation

![Navigation](Navigation_1.png)

- Press **Up/Down** to scroll line by line
- Press **+/-** to scroll page by page
- Press **Backspace** to jump to start
- Press **LOG** to jump to end
- Press **ESC** to go back to file browser
- Drag on the **touchscreen** to scroll
- Press **ON** to exit

## Features

### Rich Text Rendering

- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical docs
- ~~Strikethrough text~~ for deleted content
- [Links](https://example.com) displayed in color
- Headers from H1 to H6

### Blockquotes

> This is a blockquote.
> It can span multiple lines.

>> Nested blockquotes are also supported.

### Lists

Bullet lists:
- First item
- Second item
  - Nested item
  - Another nested item
    - Even deeper nesting

Numbered lists:
1. First step
2. Second step
  1. Sub-step
  2. Another sub-step

### Task Lists

- [x] Completed task
- [ ] Pending task
- [x] Another done item

### Tables

| Function | HP Prime | Python |
|---|---|---|
| Print | PRINT() | print() |
| Input | INPUT() | input() |
| Wait | WAIT() | time.sleep() |

### Code Snippets

Inline code like `viewer.render()` is highlighted.

Code fences are also supported:

```
from markdown_viewer import MarkdownViewer
viewer = MarkdownViewer(0)
viewer.load_markdown_file("help.md")
viewer.render()
```

## Search

Tap **Find** in the menu bar to search for text.
Tap **Next** to jump to the next match.
Matching text is highlighted in the document.

## Themes

Tap **Theme** in the menu bar to toggle between
light and dark themes. Works in both the file
browser and the document viewer.

## Bookmarks

Long-press anywhere in the document to add a bookmark
at the current scroll position.

Bookmarks appear as **red marks** on the scrollbar.

Tap **Marks** in the menu bar to open the bookmark
manager where you can:
- Jump to any saved bookmark
- Delete bookmarks you no longer need

Multiple bookmarks per file are supported and
stored automatically.

Your last opened file and scroll position are also
automatically saved. When you return to the file
browser, your last file is marked with a triangle.

## Why MarkdownViewer?

This is the *first* Markdown renderer built entirely
in MicroPython for the HP Prime graphing calculator.

### Image Support

Images can be embedded using base64-encoded raw
pixel data:

![heart](data:image/raw;base64,AAwAC////////9wUPNwUPP///////////9wUPNwUPP///////////////9wUPNwUPNwUPNwUPP///9wUPNwUPNwUPNwUPP///////9wUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPP///9wUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPP///9wUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPP///////9wUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPNwUPP///////////////9wUPNwUPNwUPNwUPNwUPNwUPNwUPP///////////////////////9wUPNwUPNwUPNwUPNwUPP///////////////////////////////9wUPNwUPNwUPP///////////////////////////////////////9wUPP///////////////////////////////////////////////////////////////////////w==)

Or loaded directly from a file:

![icon](icon.png)

Write your notes, docs, and guides in standard
Markdown on your PC, drop them onto your calculator,
and read them anywhere.

No more squinting at plain text files!

## Getting Started

1. Place your `.md` file in the app folder
2. Launch MarkdownViewer
3. Scroll and read

*Enjoy your docs on the go!*

---

*Brought to you with love by Andrea Baccin*

