"""Unit tests for the matching rules (no network)."""
from app.ai import MeetRecord, PersonRecord, fallback_person, scrub
from app.matching import cosine, fits, score_meet, score_person, soundex
from app.seed import DEMO_ABOUT_REC, OLD

AARAV = next(p for p in OLD if p["id"] == "seed-aarav")
FARAH = next(p for p in OLD if p["id"] == "seed-farah")
ZOYA = next(p for p in OLD if p["id"] == "seed-zoya")

EXAMPLE = fallback_person({"name": "Aarav", "nick": "Chintu", "school": "St. Stanislaus", "year": "2014", "area": "Pali Hill"})


def test_soundex_spelling_variants():
    assert soundex("Bunty") == soundex("Bunti")
    assert soundex("Chintu") == soundex("Chintoo")
    assert soundex("Golu") != soundex("Monu")


def test_example_request_matches_aarav_both_ways():
    p1, why_me = score_person(EXAMPLE, AARAV["about"])
    assert p1 >= 4 and {"name", "nickname", "school", "year", "area"} <= set(why_me)
    p2, why_them = score_person(AARAV["looking"]["rec"], DEMO_ABOUT_REC)
    assert p2 >= 4 and "nickname" in why_them


def test_same_school_and_year_alone_is_not_enough():
    p, _ = score_person(EXAMPLE, FARAH["about"])
    assert p < 4  # school + year only = 3 points


def test_zoya_finds_demo_persona_by_name_and_area():
    p, why = score_person(ZOYA["looking"]["rec"], DEMO_ABOUT_REC)
    assert p >= 4 and "name" in why and "area" in why


def test_classmates_looking_for_same_friend_dont_match_each_other():
    # Two "Rahul/Golu" users both looking for Aarav: school + year + area, but no identity detail
    p, why = score_person(EXAMPLE, DEMO_ABOUT_REC)
    assert p >= 4 and not fits(p, why, 4)
    # Real matches carry an identity detail
    p, why = score_person(EXAMPLE, AARAV["about"])
    assert fits(p, why, 4)


def test_phone_hash_is_strong_signal():
    looking = PersonRecord(names=["Someone"])
    p, why = score_person(looking, PersonRecord(), looking_phone="abc", about_phone="abc")
    assert why == ["phone"] and p == 5


def test_nothing_known_matches_nothing():
    assert score_person(PersonRecord(), AARAV["about"]) == (0, [])


def test_meet_overlap_and_city():
    me = MeetRecord(activities=["Music", "Sunsets"], city="Mumbai")
    dev = MeetRecord(activities=["Music", "Sunsets", "Movies"], city="Mumbai")
    assert score_meet(me, dev) == ["Music", "Sunsets"]
    delhi = MeetRecord(activities=["Music"], city="Delhi")
    assert score_meet(me, delhi) == []


def test_scrub_removes_contact_details():
    s = scrub("call me on 98201 44120 or mail a.b@x.com, see www.site.com")
    assert "98201" not in s and "@" not in s and "www." not in s


def test_cosine():
    assert round(cosine([1, 0], [1, 0]), 3) == 1.0
    assert cosine(None, [1]) == 0.0


def test_demo_identity_detection():
    from app.store import is_demo_identity
    assert is_demo_identity({"about_raw": {"name": "Rahul Sharma", "nick": "Golu"}})
    assert not is_demo_identity({"about_raw": {"name": "Nayan Goyal", "nick": ""}})
    assert not is_demo_identity({})


def test_nayan_and_manav_match_both_ways_with_their_own_details():
    nayan_about = fallback_person({"name": "Nayan Goyal", "school": "Army Public School", "year": "2012", "area": "Nasirabad"})
    manav_about = fallback_person({"name": "Manav Sharma", "school": "Army Public School", "year": "2012", "area": "Nasirabad"})
    nayan_looks = fallback_person({"name": "Manav", "school": "Army Public School", "year": "2012", "area": "Nasirabad"})
    manav_looks = fallback_person({"name": "Nayan", "school": "Army Public School", "year": "2012", "area": "Nasirabad"})
    p1, w1 = score_person(nayan_looks, manav_about)
    p2, w2 = score_person(manav_looks, nayan_about)
    assert fits(p1, w1, 4) and fits(p2, w2, 4)
    assert {"name", "school", "year", "area"} <= set(w1)
