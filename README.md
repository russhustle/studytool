# Study Tools

The `pdf2image` library needs `poplar` installed.

```shell
brew install poppler
```

Course
---

```
stutytool --course tinyml
```

Before

```sh
tinyml
└── slides
    ├── lec01.pdf
    └── lec02.pdf
```

After

```
tinyml
├── docs
│   ├── README.md
│   ├── imgs
│   │   ├── lec01
│   │   └── lec02
│   ├── lec01.md
│   └── lec02.md
├── mkdocs.yaml
└── slides
    ├── lec01.pdf
    └── lec02.pdf
```

Playlist
---

```shell
studytool --playlist url
```

Example

[Example playlist](https://youtube.com/playlist?list=PL7BBhk26UQOsO1ZqGkD9GjAnNmKAUNr9k&si=miGOUCdJd7bfCS7o)

```shell
studytool --playlist https://youtube.com/playlist?list=PL7BBhk26UQOsO1ZqGkD9GjAnNmKAUNr9k&si=miGOUCdJd7bfCS7o
```

Output

```
How To Make More Money (With Less Effort)
What They Don't Teach You About Money & Happiness
The Worst Financial Mistake You Can Make
How Much Money Is Enough? The Story Of The Mexican Fisherman
The 4 Hour Work Week by Tim Ferriss (animated book summary) - Escape The 9-5
```

