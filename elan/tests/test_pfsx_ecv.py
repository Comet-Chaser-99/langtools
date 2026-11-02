"""Per-document preferences (.pfsx) and external vocabularies (.ecv), §3.3-§3.4."""

from __future__ import annotations

import pytest

from elan_ng.io.eaf_reader import EAFError
from elan_ng.io.ecv import parse_ecv
from elan_ng.io.pfsx import Preferences

PFSX = b"""<?xml version="1.0" encoding="UTF-8"?>
<preferences version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <prefList key="TierOrder">
        <String>tx@A</String>
        <String>wd@A</String>
    </prefList>
    <pref key="ActiveTierName"><String>tx@A</String></pref>
    <pref key="TimeScaleBeginTime"><Long>1500</Long></pref>
    <pref key="TimeLineViewer.ZoomLevel"><Float>100.0</Float></pref>
    <pref key="SomeFlag"><Boolean>true</Boolean></pref>
    <prefGroup key="TierColors">
        <pref key="tx@A"><Object class="java.awt.Color">255,0,0</Object></pref>
    </prefGroup>
    <pref key="UnknownToUs"><Object class="mpi.Something">opaque</Object></pref>
</preferences>
"""


def test_pfsx_values_are_typed() -> None:
    prefs = Preferences.parse(PFSX)
    assert prefs.get("TierOrder") == ["tx@A", "wd@A"]
    assert prefs.get("ActiveTierName") == "tx@A"
    assert prefs.get("TimeScaleBeginTime") == 1500
    assert prefs.get("TimeLineViewer.ZoomLevel") == 100.0
    assert prefs.get("SomeFlag") is True
    assert prefs.get("TierColors") == {"tx@A": "255,0,0"}
    assert prefs.get("missing") is None


def test_pfsx_set_keeps_unknown_keys() -> None:
    prefs = Preferences.parse(PFSX)
    prefs.set("ActiveTierName", "wd@A")
    prefs.set("TierOrder", ["wd@A", "tx@A"])
    prefs.set("elan-ng.new", 3)
    reread = Preferences.parse(prefs.to_bytes())
    assert reread.get("ActiveTierName") == "wd@A"
    assert reread.get("TierOrder") == ["wd@A", "tx@A"]
    assert reread.get("elan-ng.new") == 3
    assert b'<Object class="mpi.Something">opaque</Object>' in prefs.to_bytes()
    assert reread.keys()[:2] == ["TierOrder", "ActiveTierName"]


ECV = b"""<?xml version="1.0" encoding="UTF-8"?>
<CV_RESOURCE AUTHOR="me" DATE="2026-01-01T00:00:00+00:00" VERSION="0.2">
    <LANGUAGE LANG_DEF="http://cdb.iso.org/lg/CDB-00138502-001" LANG_ID="eng"/>
    <CONTROLLED_VOCABULARY CV_ID="Function 2011">
        <DESCRIPTION LANG_REF="eng">Gesture functions</DESCRIPTION>
        <CV_ENTRY_ML CVE_ID="cveid_1">
            <CVE_VALUE DESCRIPTION="pointing" LANG_REF="eng">deictic</CVE_VALUE>
        </CV_ENTRY_ML>
    </CONTROLLED_VOCABULARY>
</CV_RESOURCE>
"""


def test_ecv_is_read() -> None:
    resource = parse_ecv(ECV)
    assert resource.author == "me"
    assert [lang.id for lang in resource.languages] == ["eng"]
    (cv,) = resource.vocabularies
    assert cv.id == "Function 2011"
    assert cv.entries[0].value_in("eng") == "deictic"


def test_ecv_root_is_checked() -> None:
    with pytest.raises(EAFError, match="CV_RESOURCE"):
        parse_ecv(b"<ANNOTATION_DOCUMENT/>")
