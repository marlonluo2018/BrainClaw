"""Small, dependency-free helpers for creating simple OOXML workbooks."""

from __future__ import annotations

import zipfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from xml.sax.saxutils import escape

Cell = tuple[object | None, int, str | None]


class SharedStrings:
    """Collect shared strings and render the OOXML shared-string table."""

    def __init__(self) -> None:
        self.values: list[str] = []
        self.index: dict[str, int] = {}
        self.uses: Counter[str] = Counter()

    def add(self, value: object) -> int:
        text = str(value)
        if text not in self.index:
            self.index[text] = len(self.values)
            self.values.append(text)
        self.uses[text] += 1
        return self.index[text]

    def xml(self) -> str:
        items = []
        for value in self.values:
            attributes = ' xml:space="preserve"' if value != value.strip() else ""
            items.append(f"<si><t{attributes}>{escape(value)}</t></si>")
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'count="{sum(self.uses.values())}" uniqueCount="{len(self.values)}">'
            + "".join(items)
            + "</sst>\n"
        )


def column_letter(column: int) -> str:
    if column < 1:
        raise ValueError("column must be at least 1")
    result = ""
    while column:
        column, remainder = divmod(column - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_xml(
    shared: SharedStrings,
    address: str,
    value: object | None = None,
    *,
    style: int = 0,
    formula: str | None = None,
) -> str:
    if formula is not None:
        return f'<c r="{address}" s="{style}"><f>{escape(formula)}</f><v></v></c>'
    if value is None or value == "":
        return ""
    return f'<c r="{address}" t="s" s="{style}"><v>{shared.add(value)}</v></c>'


def sheet_xml(
    shared: SharedStrings,
    rows: list[list[Cell]],
    widths: Sequence[float],
    *,
    selected: bool = False,
    autofilter: str | None = None,
) -> str:
    if not rows or not any(rows):
        raise ValueError("rows must contain at least one cell")
    max_row = len(rows)
    max_column = max(len(row) for row in rows)
    dimension = f"A1:{column_letter(max_column)}{max_row}"
    columns = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(widths, start=1)
    )
    xml_rows = []
    for row_number, row in enumerate(rows, start=1):
        cells = [
            _cell_xml(
                shared,
                f"{column_letter(column_number)}{row_number}",
                value,
                style=style,
                formula=formula,
            )
            for column_number, (value, style, formula) in enumerate(row, start=1)
        ]
        xml_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    pane = (
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        if max_row > 1
        else ""
    )
    tab_selected = ' tabSelected="1"' if selected else ""
    auto_filter_xml = f'<autoFilter ref="{escape(autofilter)}"/>' if autofilter else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews><sheetView{tab_selected} workbookViewId="0">{pane}</sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{columns}</cols>
  <sheetData>{"".join(xml_rows)}</sheetData>
  {auto_filter_xml}
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>
'''


def prepare_workbook_tree(work_dir: Path) -> None:
    """Create the directory structure and root relationship for an XLSX package."""
    (work_dir / "_rels").mkdir(parents=True, exist_ok=True)
    (work_dir / "xl" / "_rels").mkdir(parents=True, exist_ok=True)
    (work_dir / "xl" / "worksheets").mkdir(parents=True, exist_ok=True)
    (work_dir / "_rels" / ".rels").write_text(
        '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
''',
        encoding="utf-8",
    )


def write_workbook_parts(work_dir: Path, sheet_names: Sequence[str]) -> None:
    """Write content types, workbook metadata, and relationships."""
    if not sheet_names:
        raise ValueError("sheet_names must not be empty")

    worksheet_types = "\n".join(
        f'  <Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, len(sheet_names) + 1)
    )
    (work_dir / "[Content_Types].xml").write_text(
        f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{worksheet_types}
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
''',
        encoding="utf-8",
    )

    sheets = "\n".join(
        f'    <sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    (work_dir / "xl" / "workbook.xml").write_text(
        f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
{sheets}
  </sheets>
  <calcPr calcId="191029" fullCalcOnLoad="1" forceFullCalc="1"/>
</workbook>
''',
        encoding="utf-8",
    )

    worksheet_relationships = "\n".join(
        f'  <Relationship Id="rId{index}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(sheet_names) + 1)
    )
    style_id = len(sheet_names) + 1
    strings_id = len(sheet_names) + 2
    (work_dir / "xl" / "_rels" / "workbook.xml.rels").write_text(
        f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{worksheet_relationships}
  <Relationship Id="rId{style_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId{strings_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>
''',
        encoding="utf-8",
    )


def write_styles(path: Path) -> None:
    """Write a small style table with normal and bold-header styles."""
    path.write_text(
        '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
''',
        encoding="utf-8",
    )


def pack_workbook(work_dir: Path, output_path: Path) -> None:
    """Pack an OOXML directory into an XLSX file using only the standard library."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(path for path in work_dir.rglob("*") if path.is_file()):
            archive.write(source, source.relative_to(work_dir).as_posix())
