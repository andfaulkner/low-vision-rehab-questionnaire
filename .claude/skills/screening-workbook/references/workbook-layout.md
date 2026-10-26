# Workbook layout: data/LVR_screening_sheet_2.xlsx

Concrete findings from unzipping the workbook on 25 Oct 2026. Re-check
anything here against the file before relying on it after the reviewer has
saved it again from Excel (Excel rewrites every part on save).

## Package parts

| Part | What it is |
|---|---|
| `xl/workbook.xml` | sheet list, `_xlnm._FilterDatabase` defined name, calcPr |
| `xl/_rels/workbook.xml.rels` | rId -> part path for the sheets, styles, sharedStrings, calcChain |
| `xl/worksheets/sheet1.xml` | **Instructions** (sheetId 1, rId1), `A1:B21` |
| `xl/worksheets/sheet2.xml` | **Screening** (sheetId 2, rId2), `A1:S136`, 141 KB |
| `xl/worksheets/sheet3.xml` | **Counts** (sheetId 3, rId3), `A2:C32`, holds every formula |
| `xl/worksheets/sheet4.xml` | **Lists** (sheetId 4, rId4), `A1:C11` |
| `xl/worksheets/_rels/sheet2.xml.rels` | the 127 DOI hyperlink targets (rId1..rId127, TargetMode External) |
| `xl/sharedStrings.xml` | 796 unique strings, `count="1264"` (stale; actual references 1272) |
| `xl/styles.xml` | 23 cellXfs, 6 fills, 9 dxfs (conditional-format colours) |
| `xl/calcChain.xml` | the 31 formula cells, all on sheet 3 (`i="3"`) |
| `docProps/app.xml`, `docProps/core.xml` | metadata only |

Sheet names map to files through `workbook.xml` + the rels, never assume
`sheetN` = tab N. `lvrwb.Workbook.sheet_files` does this lookup.

The file was last saved by Excel for Mac (`lastEdited="7"`, path
`/Users/monamoossavi/Downloads/`), then patched by hand: rows 129-136,
Counts!A5/C5, and the Q-S columns are inline strings (`t="inlineStr"`),
which Excel itself never writes. Both forms read back identically.

## Screening (sheet2.xml)

- `<dimension ref="A1:S136"/>`; 136 `<row>` elements (header + 135 records);
  every data row has `ht="90" customHeight="1"` and `spans="1:19"`.
- Frozen panes: `xSplit="4" ySplit="1"` (ID..Title and the header stay visible).
- `<autoFilter ref="A1:S136"/>`, and in workbook.xml
  `<definedName name="_xlnm._FilterDatabase" localSheetId="1" hidden="1">Screening!$A$1:$P$136</definedName>`
  (note it still says `$P$`; harmless).
- Column widths are in `<cols>`; nothing to touch.

### Columns and headers (row 1)

| Col | Header | Owner | Style (data rows) |
|---|---|---|---|
| A | ID | bibliographic | 9 (number) |
| B | Year | bibliographic | 9 (number; blank for ID 1) |
| C | Authors ("Surname, Given et al.") | bibliographic | 9 |
| D | Title | bibliographic | 9 |
| E | Journal | bibliographic | 9 |
| F | DOI link: text "Open" (sst 44) or "No link" (sst 129) + hyperlink | bibliographic | 10 (blue underlined) or 9 |
| G | Abstract, or "Missing" | bibliographic | 9, or 13 (italic) |
| H | Title/abstract decision | **reviewer** | 11 (yellow FFF2CC) |
| I | Exclusion reason (T/A) | **reviewer** | 11 |
| J | Full-text decision | **reviewer** | 11 |
| K | Exclusion reason (FT) | **reviewer** | 11 |
| L | Notes | **reviewer** | 11 |
| M | Zotero key | bibliographic | 9 |
| N | Suggested decision (AI) | AI | 12 (grey EDEDED) |
| O | Suggested reason (AI) | AI | 12 |
| P | AI rationale | AI | 12 |
| Q | Independent T/A decision (AI) | AI | 12 |
| R | Independent exclusion reason (AI) | AI | 12 |
| S | Independent rationale (AI) | AI | 12 |

Header styles: 7 (navy 1F3864, white bold) for A-M, 8 (grey 595959) for N-S.
CLAUDE.md describes A-P; Q-S were added later as a second, independent AI
pass and are not in the Counts formulas.

State on 25 Oct 2026: H filled for rows 2-41 (IDs 1-40: 27 Exclude, 9 Maybe,
4 Include), I for the 27 excludes, J/K/L empty, N-P filled for IDs 1-127,
Q-S filled for IDs 1-127, nothing in N-S for the hand-added IDs 128-135.

### Cell encodings seen

```xml
<c r="A3" s="9"><v>2</v></c>                       <!-- number -->
<c r="H2" s="11" t="s"><v>19</v></c>               <!-- shared string #19 = "Exclude" -->
<c r="Q2" s="12" t="inlineStr"><is><t>Exclude</t></is></c>   <!-- inline string -->
<c r="J2" s="11"/>                                 <!-- blank, styled -->
```

Strings with leading spaces use `<t xml:space="preserve">`. No rich-text
runs, no booleans, no formulas on this sheet.

### Hyperlinks

```xml
<hyperlinks><hyperlink ref="F2" r:id="rId1" xr:uid="{...}"/> ... <hyperlink ref="F136" r:id="rId127"/></hyperlinks>
```
rId -> URL lives in `xl/worksheets/_rels/sheet2.xml.rels`. Rows without a
DOI (F49, F66, F69, F94, F109, F128, F133) have no hyperlink and show "No link".
The CSV export writes the URL in place of "Open".

### Conditional formatting (colours the decision cells)

```xml
<conditionalFormatting sqref="H2:H136">
  <cfRule type="expression" dxfId="8" priority="2"><formula>H2="Include"</formula></cfRule>
  <cfRule type="expression" dxfId="7" priority="3"><formula>H2="Exclude"</formula></cfRule>
  <cfRule type="expression" dxfId="6" priority="4"><formula>H2="Maybe"</formula></cfRule>
</conditionalFormatting>
```
Same for `J2:J136` (dxf 5/4/3), `N2:N136` (dxf 2/1/0) and `Q2:Q136` (dxf 2/1/0).
dxf colours: C6EFCE green = Include, FFC7CE red = Exclude, FFEB9C amber = Maybe.

### Drop-down validations (x14 extension only; there is no plain `<dataValidations>`)

```xml
<extLst><ext uri="{CCE6A557-97BC-4b89-ADB6-D9C93CAAB3DF}" xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main">
<x14:dataValidations count="3" xmlns:xm="http://schemas.microsoft.com/office/excel/2006/main">
  <x14:dataValidation type="list" allowBlank="1" xr:uid="{...0000}"><x14:formula1><xm:f>Lists!$A$2:$A$4</xm:f></x14:formula1><x14:formula2><xm:f>0</xm:f></x14:formula2><xm:sqref>H2:H136</xm:sqref></x14:dataValidation>
  <x14:dataValidation type="list" allowBlank="1" xr:uid="{...0001}"><x14:formula1><xm:f>Lists!$C$2:$C$11</xm:f></x14:formula1><x14:formula2><xm:f>0</xm:f></x14:formula2><xm:sqref>I2:I136 K2:K136</xm:sqref></x14:dataValidation>
  <x14:dataValidation type="list" allowBlank="1" xr:uid="{...0002}"><x14:formula1><xm:f>Lists!$B$2:$B$3</xm:f></x14:formula1><x14:formula2><xm:f>0</xm:f></x14:formula2><xm:sqref>J2:J136</xm:sqref></x14:dataValidation>
</x14:dataValidations></ext></extLst>
```
openpyxl warns "Data Validation extension is not supported and will be
removed" on load and drops this whole block on save. That is why the source
workbook is never saved through openpyxl.

## Lists (sheet4.xml)

| A: Decisions (H) | B: Full-text decisions (J) | C: Exclusion reasons (I, K) |
|---|---|---|
| Include | Include | Wrong population (not adults) |
| Exclude | Exclude | No questionnaire/screening item |
| Maybe | | No accuracy/validation data |
| | | Intervention study only |
| | | Not about low vision/visual function |
| | | Review/opinion/editorial |
| | | Conference abstract only |
| | | Language (not English/French) |
| | | Full text not available |
| | | Other (see notes) |

The strings are shared-string entries 17, 19, 76 (decisions) and 47, 24, 62,
55, 95, 69, 787, 788, 789, 696 (reasons); Counts!A19:A28 reuse the same
entries, so the labels there and in Lists cannot drift apart.

## Counts (sheet3.xml): every formula, with its cached value on 25 Oct 2026

Hand-typed inputs (plain numbers, no formula): B3 = 78 (PubMed), B4 = 88
(Scopus), B5 = 8 (other sources, records 128-135).

| Cell | Formula | Cached |
|---|---|---|
| B6 | `B3+B4+B5` | 174 |
| B7 | `B6-B8` | 39 |
| B8 | `COUNTA(Screening!$D$2:$D$136)` | 135 |
| B9 | `COUNTA(Screening!$H$2:$H$136)` | 40 |
| B10 | `COUNTIF(Screening!$H$2:$H$136,"Exclude")` | 27 |
| B11 | `COUNTIF(Screening!$H$2:$H$136,"Include")+COUNTIF(Screening!$H$2:$H$136,"Maybe")` | 13 |
| B12 | `COUNTA(Screening!$J$2:$J$136)` | 0 |
| B13 | `COUNTIF(Screening!$J$2:$J$136,"Exclude")` | 0 |
| B14 | `COUNTIF(Screening!$J$2:$J$136,"Include")` | 0 |
| B19..B28 | `COUNTIF(Screening!$I$2:$I$136,A19)` .. `A28` (one per reason label in A) | 2, 18, 0, 1, 6, 0, 0, 0, 0, 0 |
| C19..C28 | `COUNTIF(Screening!$K$2:$K$136,A19)` .. `A28` | all 0 |
| B31 | `SUMPRODUCT((Screening!$H$2:$H$136<>"")*(Screening!$H$2:$H$136=Screening!$N$2:$N$136))` | 25 |
| B32 | `SUMPRODUCT((Screening!$H$2:$H$136<>"")*(Screening!$H$2:$H$136<>Screening!$N$2:$N$136))` | 15 |

In the XML `<` and `>` are `&lt;` `&gt;`, e.g.
`<c r="B31" s="22"><f>SUMPRODUCT((Screening!$H$2:$H$136&lt;&gt;"")*...)</f><v>25</v></c>`.
`lvrwb.Evaluator` reproduces all 31 cached values from the Screening cells
(checked 25 Oct 2026), so `set_cells.py` can patch `<v>` after an edit.
COUNTIF and `=` on text are case-insensitive in Excel and in the evaluator,
but the drop-downs and the reviewer's eye are not: keep the exact spelling.

Every range ends at row 136. `Workbook.extend_ranges(n)` bumps the row in:
sheet2 `dimension/@ref`, `autoFilter/@ref`, each `conditionalFormatting/@sqref`,
each `<xm:sqref>`, workbook.xml `definedName`, and every Counts `<f>`.
Row references elsewhere (hyperlink refs, cfRule formulas like `H2="Include"`)
are deliberately left alone.

## Styles (styles.xml)

cellXfs indexes used on Screening: 7 header navy, 8 header grey, 9 body,
10 hyperlink (font 9, blue underline), 11 reviewer yellow (fill 4), 12 AI grey
(fill 5), 13 italic body. Counts uses 14-22, Lists 15/19. Fills: 2 = 1F3864,
3 = 595959, 4 = FFF2CC, 5 = EDEDED. Nothing in the skill ever edits styles;
new cells copy the column's most common style index.

## CSV export convention (data/LVR_screening_sheet_2_<Sheet>.csv)

- One file per tab, named after the workbook stem plus the tab name.
- Rows 1..max_row and columns 1..max_col of the cells present (so Counts
  starts with an empty `,,` line for its blank row 1).
- UTF-8, no BOM, LF line endings, Python `csv` minimal quoting (`"` doubled;
  fields with commas, quotes or newlines quoted; abstracts keep their
  embedded newlines, which is why Screening.csv has more lines than rows).
- Numbers as Excel stored them (`2020`, `78`), formulas as their cached `<v>`.
- Hyperlinked cells export the URL (the DOI column shows the URL, not "Open").
- Two legacy quirks reproduced on purpose so the exports stay byte-identical
  to the committed files: `Screening.csv` begins with a line holding
  `LVR_screening_sheet_2_Screening` and has no trailing newline; the other
  three start at row 1 and end with a newline.

On 25 Oct 2026 `xlsx_to_csv.py --check` found Instructions, Lists and Counts
byte-identical and Screening stale only in content (the committed file still
had a stray row with ID " " and lacked IDs 129-135).
