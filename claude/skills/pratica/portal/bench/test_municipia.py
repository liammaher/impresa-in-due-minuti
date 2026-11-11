#!/usr/bin/env python3
"""municipia/extract.py's parsers offline, on text shaped like the portals' code, and the committed
catalogue (no network, no portal):

  python3 claude/skills/pratica/portal/bench/test_municipia.py
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "municipia"))
sys.dont_write_bytecode = True
import extract  # noqa: E402

CAT = HERE.parent / "municipia" / "catalogue" / "napoli"
results = []


def case(name):
    def run(fn):
        try:
            fn()
            results.append(True)
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            results.append(False)
            print(f"FAIL  {name}: {e!r}")
    return run


RUNTIME = ('i.src=function(e){return u.p+""+({}[e]||e)+"-es2015."+{7:"f181e3ef8364a0be3ec7",'
           '9:"75d193a2152dc93a97ab"}[e]+".js"}(e);')

MENU = ('{title:"Imposta di Soggiorno",path:"/personale/geis",roles:["GESTORE_STRUTTURA","DELEGATO_STRUTTURA"],'
        'children:[{path:"/personale/geis/comunicazionecomponent",title:"Dichiarazione Periodica",'
        'roles:["GESTORE_STRUTTURA","DELEGATO_STRUTTURA"]},{path:"/personale/geis/versamentocomponent",title:"",'
        'roles:["GESTORE_STRUTTURA"]}]},{path:"/personale/dati",title:"I Tuoi dati",roles:["CITTADINO"]},'
        '{path:"geis",loadChildren:x},{path:"genericpage/:page"},{path:"${t}"}')


class Fake(extract.Fetcher):
    def __init__(self, files):
        super().__init__(pause=0)
        self.files = files

    def get(self, url):
        return self.files[url].encode()


@case("lazy chunks come from the runtime, named by id when no name is given")
def _():
    assert extract.chunk_map(RUNTIME) == {"7": "7-es2015.f181e3ef8364a0be3ec7.js", "9": "9-es2015.75d193a2152dc93a97ab.js"}
    assert extract.chunk_map("no chunks here") == {}


@case("a menu entry is read in either key order, with its roles and its parent's")
def _():
    by = {r["path"]: r for r in extract.routes(MENU)}
    assert by["/personale/geis"]["title"] == "Imposta di Soggiorno"
    assert by["/personale/geis"]["roles"] == ["GESTORE_STRUTTURA", "DELEGATO_STRUTTURA"]
    assert by["/personale/geis/comunicazionecomponent"]["title"] == "Dichiarazione Periodica"
    assert by["/personale/geis/versamentocomponent"]["roles"] == ["GESTORE_STRUTTURA"]
    assert by["/personale/dati"]["roles"] == ["CITTADINO"]
    assert extract.roles_of(extract.routes(MENU)) == ["CITTADINO", "DELEGATO_STRUTTURA", "GESTORE_STRUTTURA"]


@case("router segments without a slash are kept, junk is dropped")
def _():
    assert extract.route_segments(MENU) == ["geis", "genericpage/:page"]


@case("template text is read through both spellings of the compiler's call, escapes decoded")
def _():
    js = ('y["\\u0275\\u0275text"](9,"Elabora Documento"),y["\\u0275\\u0275text"](3,"Importo totale"),'
          'y["\\u0275\\u0275text"](4,"Attenzione: Il pagamento sar\\xe0 registrato"),y["\\u0275\\u0275text"](5,"Elabora Documento"),'
          'ɵɵtext(6,"Invia"),y["\\u0275\\u0275text"](7," ")')
    assert extract.labels(js) == ["Elabora Documento", "Importo totale", "Attenzione: Il pagamento sarà registrato", "Invia"]


@case("a paragraph of help text is not a label")
def _():
    long = "x" * (extract.MAX_LABEL + 1)
    js = f'y["\\u0275\\u0275text"](1,"Invia"),y["\\u0275\\u0275text"](2,"{long}")'
    assert extract.labels(js) == ["Invia"]


@case("selectors, modules, backend paths and messages")
def _():
    js = ('selectors:[["app-comunicazione"]],selectors:[["app-tracciato-ospiti"]],selectors:[["app-comunicazione"]],'
          'class GeisModule{},FormsModule,"/rest/dichPeriodiche/inviaDich","/rest/dichPeriodiche/inviaDich",'
          '"ms-jdomandeonline/jwt/api/nuovaPratica/listaModelli","/personale/geis",'
          'confirm("Premendo il pulsante si procedera alla creazione di una nuova Dichiarazione"),alert("No")')
    assert extract.selectors(js) == ["app-comunicazione", "app-tracciato-ospiti"]
    assert extract.modules(js) == ["GeisModule"]
    assert extract.rest_paths(js) == ["/rest/dichPeriodiche/inviaDich", "ms-jdomandeonline/jwt/api/nuovaPratica/listaModelli"]
    assert extract.messages(js) == ["Premendo il pulsante si procedera alla creazione di una nuova Dichiarazione"]


@case("an index page's scripts, relative or absolute, deduplicated")
def _():
    html = ('<script src="runtime-es2015.aaa.js" type="module"></script><script src="main-es2015.bbb.js"></script>'
            '<script async src="https://cdn.example/app.js"></script><script src="main-es2015.bbb.js"></script>')
    assert extract.script_srcs(html) == ["runtime-es2015.aaa.js", "main-es2015.bbb.js", "https://cdn.example/app.js"]
    assert extract._scripts("https://h.example/", html, "main-es2015") == ["https://h.example/main-es2015.bbb.js"]


@case("a module's imports and lazy loads are found, a bare package is not")
def _():
    js = 'import{a as l}from"./chunk-A.js";import("./chunk-B.js");import x from"rxjs";import{y}from"../other/c.js"'
    assert extract.imports(js) == ["./chunk-A.js", "./chunk-B.js", "../other/c.js"]


@case("the crawl follows imports once each, relative to the importing file, and stops at its cap")
def _():
    base = "https://h.example/"
    fake = Fake({base + "main.js": 'import"./a.js";import("./sub/b.js")', base + "a.js": 'import"./sub/b.js"',
                 base + "sub/b.js": 'import"../a.js";import"./c.js"', base + "sub/c.js": "x"})
    got = extract.crawl([base + "main.js"], fake)
    assert sorted(got) == sorted([base + "main.js", base + "a.js", base + "sub/b.js", base + "sub/c.js"])
    old, extract.MAX_FILES = extract.MAX_FILES, 2
    try:
        assert len(extract.crawl([base + "main.js"], Fake({base + "main.js": 'import"./a.js"', base + "a.js": 'import"./b.js"', base + "b.js": ""}))) == 2
    finally:
        extract.MAX_FILES = old


@case("translation files flatten to dotted keys")
def _():
    assert extract.flatten({"a": {"b": "x", "c": {"d": "y"}}, "e": "z"}) == {"a.b": "x", "a.c.d": "y", "e": "z"}


@case("a build's names are read from the index and the runtime alone, and a changed hash shows")
def _():
    base = "https://geis-web-portal.municipia.eng.it/"
    files = {base: '<script src="runtime-es2015.r1.js"></script><script src="main-es2015.m1.js"></script>',
             base + "runtime-es2015.r1.js": RUNTIME}
    names = extract.roots_now("geis", Fake(files))
    assert names == sorted(["main-es2015.m1.js", "runtime-es2015.r1.js", "7-es2015.f181e3ef8364a0be3ec7.js",
                            "9-es2015.75d193a2152dc93a97ab.js"])
    files[base] = files[base].replace("m1", "m2")
    assert "main-es2015.m2.js" in extract.roots_now("geis", Fake(files))


@case("the portal's federation manifest gives the citizen portal's names")
def _():
    base = "https://cizrm.municipia.eng.it/"
    files = {base: '<script src="main-X.js" type="module"></script>',
             base + "assets/federation.manifest.json": json.dumps({"tax-mfe": "remotes/tax/b1/remoteEntry.json"}),
             base + "remotes/tax/b1/remoteEntry.json": json.dumps({"exposes": [{"key": "./Feature", "outFileName": "Feature-A.js"}]})}
    assert extract.roots_now("multiservizi", Fake(files)) == ["Feature-A.js", "main-X.js", "remoteEntry.json"]


# ---- the committed catalogue ----------------------------------------------------------------------------

@case("the registration form's catalogue lists each field once, with no value of a person")
def _():
    path = CAT / "domande-online" / "GESTORE.json"
    if not path.is_file():
        raise AssertionError("catalogue/napoli/domande-online/GESTORE.json is missing")
    doc = json.loads(path.read_text(encoding="utf-8"))
    codes = [f["code"] for f in doc["fields"]]
    assert len(codes) == len(set(codes)), "a field code appears twice"
    assert all({"code", "kind", "type", "required", "label", "step"} <= set(f) for f in doc["fields"])
    assert {f["step"] for f in doc["fields"]} == {1, 2, 3, 4}
    assert not any("value" in f or "default" in f for f in doc["fields"]), "a value was kept"
    required = [f["code"] for f in doc["fields"] if f["required"]]
    assert "SOG_INTESTATARIO-1_CODICEFISCALE" in required and "ATT_STRUTSUBAL" in required


@case("each app's catalogue names its build files, and the gestore area is gated by two roles")
def _():
    for name in ("geis", "multiservizi"):
        path = CAT / f"{name}.json"
        if not path.is_file():
            raise AssertionError(f"{path.name} is missing: run extract.py run")
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["build"]["roots"] and set(doc["build"]["roots"]) <= set(doc["build"]["names"])
        assert set(doc["build"]["sha256"]) == set(doc["build"]["names"])
    geis = json.loads((CAT / "geis.json").read_text(encoding="utf-8"))
    assert any(r["path"] == "/personale/geis" and r["roles"] == ["GESTORE_STRUTTURA", "DELEGATO_STRUTTURA"]
               for r in geis["routes"])
    screens = {s for rec in geis["files"].values() for s in rec["screens"]}
    assert {"app-comunicazione", "app-tracciato-ospiti", "app-conto-gestione"} <= screens


if not all(results):
    print(f"\n{results.count(False)} of {len(results)} failed")
    sys.exit(1)
print(f"\n{len(results)} passed")
