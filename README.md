# MaxiDict

An offline **English–Simplified Chinese learner dictionary**, made as a personal
project to demonstrate how to build a dictionary using LLMs. Version **0.1.0**
contains **55,378 words and 105,123 senses**, with definitions, examples,
pronunciation, and usage notes.

The dictionary is [`dict.jsonl`](dict.jsonl). Keep it beside [`lookup.py`](lookup.py)
and run with **Python 3.10+** (standard library with SQLite; no extra packages needed):

```sh
python3 lookup.py demo
```

For syntax highlighting in a terminal, pipe the output through `jq` (installed separately):

```sh
python3 lookup.py demo | jq
```

Output, showing noun and verb senses, pronunciation variants, and a usage note:

```json
{
  "cefr": "B2",
  "entries": [
    {
      "definition_cn": "演示",
      "definition_en": "a visual presentation showing how something works",
      "example_cn": "该公司演示了他们的新软件。",
      "example_en": "The company gave a demo of their new software.",
      "pos": "noun",
      "pronunciations": [
        {
          "dialect": "UK",
          "ipa": "/ˈdɛm.əʊ/"
        },
        {
          "dialect": "US",
          "ipa": "/ˈdɛm.oʊ/"
        }
      ],
      "usage": [
        {
          "label": "informal",
          "pattern": "noun"
        }
      ]
    },
    {
      "definition_cn": "演示",
      "definition_en": "give an exhibition of to an interested audience",
      "example_cn": "魔术师今晚将展示他最新的戏法。",
      "example_en": "The magician will demo his latest tricks tonight.",
      "pos": "verb",
      "pronunciations": [
        {
          "dialect": "UK",
          "ipa": "/ˈdɛm.əʊ/"
        }
      ]
    }
  ],
  "ipa": "/ˈdɛm.oʊ/",
  "source_references": {
    "oewn_synsets": [
      "02153218-v",
      "06892230-n"
    ],
    "wiktionary_page": "https://en.wiktionary.org/wiki/demo#English"
  },
  "word": "demo"
}
```

In `dict.jsonl`, each complete word record occupies a single line.

The demonstration accepts one word, has no options, and prints its record as
formatted JSON, including the first six senses. It works offline and creates
`.cache/dict.sqlite3` on first use. Later lookups reuse the cache; changes to the
JSONL trigger rebuilding.
The script's folder must be writable.

**Accuracy and warranty:** Entries have **not been manually reviewed**. This is
an experiment, and automated checks do not guarantee correct meanings,
translations, examples, or pronunciation. The dictionary and software are
provided **as is, without warranty or any guarantee of accuracy or completeness**.

## Files and format

`dict.jsonl` contains one UTF-8 JSON object per word:

| Field | Content |
| --- | --- |
| `word`, `ipa` | Headword and available pronunciation |
| `cefr` | Frequency-based difficulty estimate, not certified CEFR |
| `entries` | Ordered senses: part of speech, English/Chinese definitions and examples, optional pronunciation and usage |
| `source_references` | Wiktionary page and applicable Open English WordNet synsets |

## How it was built

1. **Select and ground words.** Combine learner, academic, frequency, and WordNet
   wordlists; rank with wordfreq. Use Open English WordNet 2025 and
   Wiktionary/Wiktextract for meanings, pronunciation, forms, and usage evidence.
2. **Generate and revise.** Use LLMs to draft bilingual definitions and examples,
   then automatically review and revise proposed changes against source evidence.
3. **Sample and audit.** Independent automated checks covered 1,082 words and
   produced accepted repairs for 647. The audit was stopped before completion;
   19,550 of the original 20,632 unchanged words had no completed independent check.
4. **Freeze and export.** The snapshot preserves the resulting
   definitions and examples. Export puts selected senses first, keeps all remaining
   senses, removes build metadata, and validates inventory counts and checksums.

## License and sources

This adaptation is by **Maxime Song and contributors**. Dictionary data uses
**CC BY-SA 4.0**; the lookup script and original documentation use **MIT**.
Upstream materials retain their applicable terms. [`LICENSE`](LICENSE) includes
the full code/data terms and the original WordNet notices.

| Source and credit | Terms |
| --- | --- |
| [English Wiktionary contributors](https://en.wiktionary.org/), extracted with [Wiktextract/Kaikki](https://kaikki.org/dictionary/rawdata.html) | CC BY-SA 4.0; [Wikimedia reuse terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/en#7._Licensing_of_Content) |
| [Open English WordNet 2025](https://en-word.net/downloads), Open English WordNet Team and community; derived from Princeton WordNet | CC BY 4.0 and Princeton WordNet notice |
| [NGSL-GR 1.0](https://charliebrownecompany.squarespace.com/ngsl-graded-reader), Charles Browne and Brent Culligan (2024) | CC BY-SA 4.0 |
| [NAWL 1.2](https://charliebrownecompany.squarespace.com/new-academic-word-list), Charles Browne, Brent Culligan, and Joseph Phillips | CC BY-SA 4.0 |
| [FrequencyWords](https://github.com/hermitdave/FrequencyWords/tree/master/content/2018/en), hermitdave; derived from OPUS OpenSubtitles 2018 | CC BY-SA 4.0 content |
| [wordfreq 3.1.1](https://github.com/rspeer/wordfreq), Robyn Speer and Luminoso Technologies | CC BY-SA 4.0 frequency data |

The adaptation selects and orders senses, paraphrases and repairs definitions,
and generates Chinese translations and bilingual examples. Upstream authors do
not endorse these changes. Record-level source references retain attribution;
Wiktionary links point to current pages and their contributor histories, not
pinned historical revisions.

When redistributing, retain this README, LICENSE, and source credits, and identify
your changes. The complete license texts govern.
