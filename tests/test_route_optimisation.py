from app.model import Trip, CollectionRequest


def test_optimisation_caching(testapp, db):
    def cache_optimisation():
        trip.collection_ordering = [0]
        db.session.commit()
        assert trip.collection_ordering is not None

    trip = Trip()
    coll1 = CollectionRequest(collector_name="", collector_phone="0987654456", waste_entries=[])
    trip.collections.append(coll1)
    db.session.add(trip)
    db.session.commit()
    assert trip.collection_ordering is None

    cache_optimisation()

    coll2 = CollectionRequest(collector_name="", collector_phone="0987789987", waste_entries=[])
    trip.collections.append(coll2)
    db.session.commit()
    assert trip.collection_ordering is None

    cache_optimisation()

    trip.collections.remove(coll1)
    db.session.commit()
    assert trip.collection_ordering is None

    cache_optimisation()

    trip.collections = []
    db.session.commit()
    assert trip.collection_ordering is None
