from slidepoise.rendered_text import compare_cell


def word(text, x, y):
    return {"text": text, "box": [x, y, x+35, y+10]}


def test_complete_word_elsewhere_does_not_hide_a_broken_table_word():
    evidence = compare_cell("Adoption", [word("Adoptio", 10, 10), word("n", 20, 23),
                                          word("Adoption", 150, 10)], [0, 0, 100, 50])
    assert evidence["missing_complete_tokens"] == ["adoption"]
    assert evidence["rendered"] == "Adoptio n"


def test_intentional_word_wrap_and_punctuation_are_retained():
    evidence = compare_cell("Research\nsynthesis.", [word("Research", 10, 10), word("synthesis", 10, 23)], [0, 0, 100, 50])
    assert evidence["missing_complete_tokens"] == []


def test_pdf_words_follow_office_slide_order(tmp_path, monkeypatch):
    import subprocess
    from zipfile import ZipFile
    from slidepoise.rendered_text import collect_rendered_table_text
    pptx = tmp_path / "reordered.pptx"
    pdf = tmp_path / "reordered.pdf"
    pdf.write_bytes(b"mock PDF")
    with ZipFile(pptx, "w") as package:
        package.writestr("ppt/presentation.xml", '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId r:id="second"/><p:sldId r:id="first"/></p:sldIdLst><p:sldSz cx="1000" cy="500"/></p:presentation>')
        package.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="first" Type="x/slide" Target="slides/slide1.xml"/><Relationship Id="second" Type="x/slide" Target="slides/slide2.xml"/></Relationships>')
        for number, text in [(1, "First"), (2, "Second")]:
            package.writestr(f"ppt/slides/slide{number}.xml", f'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:graphicFrame><p:nvGraphicFramePr><p:cNvPr name="table"/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/></p:xfrm><a:graphic><a:tbl><a:tblGrid><a:gridCol w="1000"/></a:tblGrid><a:tr h="500"><a:tc><a:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></a:graphic></p:graphicFrame></p:spTree></p:cSld></p:sld>')
    xml = '<doc>' + ''.join(f'<page width="100" height="50"><word xMin="10" yMin="10" xMax="30" yMax="20">{word}</word></page>' for word in ["Second", "First"]) + '</doc>'
    monkeypatch.setattr("slidepoise.rendered_text.shutil.which", lambda _: "pdftotext")
    monkeypatch.setattr("slidepoise.rendered_text.subprocess.run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, xml.encode()))
    evidence = collect_rendered_table_text(pptx, pdf)
    assert evidence["available"] and evidence["discrepancies"] == []
    assert [cell["expected"] for cell in evidence["cells"]] == ["Second", "First"]
    xml = '<doc><page width="100" height="50"/></doc>'
    assert collect_rendered_table_text(pptx, pdf)["available"] is False
