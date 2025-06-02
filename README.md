# studytool 💼

[![GitHub version](https://badge.fury.io/gh/russhustle%2Fstudytool.svg)](https://badge.fury.io/gh/russhustle%2Fstudytool) [![PyPI version](https://badge.fury.io/py/studytool.svg)](https://badge.fury.io/py/studytool)

## To do

- Documentation
- Testing

## Installation

```shell
pip install studytool
```

> The `pdf2image` library needs `poppler` installed.
>
> ```shell
> brew install poppler
> ```

## Course

```
stt course tinyml
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

## Playlist

```shell
stt playlist url
```

Example

[Example playlist](https://youtube.com/playlist?list=PL7BBhk26UQOsO1ZqGkD9GjAnNmKAUNr9k&si=miGOUCdJd7bfCS7o)

```shell
stt playlist https://youtube.com/playlist?list=PL7BBhk26UQOsO1ZqGkD9GjAnNmKAUNr9k&si=miGOUCdJd7bfCS7o
```

Output

```
How To Make More Money (With Less Effort)
What They Don't Teach You About Money & Happiness
The Worst Financial Mistake You Can Make
How Much Money Is Enough? The Story Of The Mexican Fisherman
The 4 Hour Work Week by Tim Ferriss (animated book summary) - Escape The 9-5
```
