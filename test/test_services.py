import dsl



def test_get_providers():
    c=dsl.api.get_providers()
    assert len(list(c)) == 6

def test_get_services():
    c=dsl.api.get_services()
    assert len(list(c)) == 15

