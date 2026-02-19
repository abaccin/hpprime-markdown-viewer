# MarkdownViewer for HP Prime

## The First Markdown Renderer for Your Calculator!

Read beautifully formatted documents right on your HP Prime.
No PC required. See also: [Link Demo](demo.md)

## Navigation

![Navigation](Navigation_1.png)

### File Browser

- Tap a **column header** to sort by that column
- Tap the **★** star on a row to pin/unpin it
- Tap **Recent** to see recently opened files
- Tap **Theme** to switch light/dark theme
- Press **Up/Down** to navigate the file list
- Press **Enter** or tap a file to open it
- Press **ESC** or **ON** to exit

### Document Viewer

- Press **Up/Down** to scroll line by line
- Press **+/-** to scroll page by page
- Press **Backspace** to jump to start
- Press **LOG** to jump to end
- Press **ESC** to go back to file browser
- Drag on the **touchscreen** to scroll
- Press **ON** to exit

## Features

### File Browser Enhancements

#### Favorites / Pinned Files

Tap the **★** yellow star icon in the star column
of any file row to pin or unpin it.

Pinned files show a yellow **★** star. When sorting
by the star column, favorites appear at the top.
Favorites persist across app restarts.

#### Recently Opened Files

Tap **Recent** in the menu bar (or press **F1**)
to see a list of your last 10 opened files.
Select one to open it directly.

#### Column Sorting

The browser has three sortable columns:

- **★** (Star) — sort favorites first
- **Name** — sort alphabetically
- **Size** — sort by file size

Tap a column header to sort by it.
Tap the same header again to reverse direction.
The active column shows **▲** (ascending)
or **▼** (descending).

#### File Organization

To organize many files, use the underscore naming
convention: `folder_filename.md`. The browser shows
these as `folder/filename.md` for visual grouping.
Files with a common prefix naturally sort together.

For example, the included `docs_lorem.md` appears
as `docs/lorem.md` in the file list. You can create
multiple "folders" this way:

- `notes_math.md` → `notes/math.md`
- `notes_physics.md` → `notes/physics.md`
- `docs_setup.md` → `docs/setup.md`

This is purely a display convention — all files
remain in the same app directory on the calculator.

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

### Math Formulas

Use a fenced code block tagged with `math`, `formula`,
or `cas` to render CAS expressions in pretty-print:

```math
integrate(sin(x)^2,x)
```

```math
sum(1/n^2,n,1,infinity)
```

Each line inside a math block becomes a separate
formatted formula, centered with a bordered frame.
Formula dimensions are cached for fast scrolling.

Supported CAS functions include `integrate`, `sum`,
`diff`, `limit`, `sqrt`, `matrix`, and any valid
HP Prime CAS expression.

## Search

Tap **Find** in the menu bar to search for text.
Tap **Next** to jump to the next match.
Matching text is highlighted in the document.

## Table of Contents

Tap **TOC** in the menu bar (or press **F3**) to
see a list of all headers in the document.
Select a header to jump directly to that section.

## Document Info

Tap **Info** in the menu bar (or press **F5**) to
see document statistics:
- Filename
- Line count
- Word count
- Estimated reading time

## Internal Links

Links to other `.md` files (e.g. `[See setup](setup.md)`)
are tappable. Tap to open the linked file.
Press **ESC** to go back to the previous file.
Multiple levels of back-navigation are supported.

## Reading Progress

A percentage indicator is shown at the bottom of
the screen, showing how far you have scrolled
through the document.

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

