from app.scoring.rules import score_contact, score_company, combined_score

def test_head_of_voice_scores_high():
    assert score_contact("Head of Voice") >= 20

def test_irrelevant_title_scores_low():
    assert score_contact("Marketing Manager") <= 5

def test_combined_score():
    assert combined_score(100, 100) == 100
    assert combined_score(80, 50) == 68
