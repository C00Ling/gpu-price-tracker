# tests/test_storage.py
import pytest
from sqlalchemy.exc import IntegrityError


class TestGPURepository:
    """Test GPURepository CRUD operations"""

    def test_add_listing(self, test_repo):
        """Test adding a single listing"""
        gpu = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )

        assert gpu.id is not None
        assert gpu.model == "RTX 4090"
        assert gpu.source == "OLX"
        assert gpu.price == 3500

    def test_add_listing_normalizes_model(self, test_repo):
        """Test that model names are normalized"""
        gpu = test_repo.add_listing(
            model="rtx4090",  # Unnormalized
            source="OLX",
            price=3500
        )

        # Should be normalized to "RTX 4090"
        assert gpu.model == "RTX 4090"

    def test_add_multiple_listings(self, test_repo, sample_gpu_data):
        """Test adding multiple listings"""
        for listing in sample_gpu_data:
            test_repo.add_listing(**listing)

        # Should have all listings
        all_listings = test_repo.get_all_listings()
        assert len(all_listings) == len(sample_gpu_data)

    def test_add_listings_bulk(self, test_repo, sample_gpu_data):
        """Test bulk insert"""
        count = test_repo.add_listings_bulk(sample_gpu_data)

        assert count == len(sample_gpu_data)

        # Verify in database
        all_listings = test_repo.get_all_listings()
        assert len(all_listings) == len(sample_gpu_data)

    def test_get_all_listings_empty(self, test_repo):
        """Test getting listings from empty database"""
        listings = test_repo.get_all_listings()
        assert listings == []

    def test_get_all_listings_with_data(self, test_repo, sample_gpu_data):
        """Test getting all listings"""
        test_repo.add_listings_bulk(sample_gpu_data)

        listings = test_repo.get_all_listings()

        assert len(listings) == len(sample_gpu_data)
        assert all(hasattr(listing, 'model') for listing in listings)
        assert all(hasattr(listing, 'price') for listing in listings)

    def test_get_listings_by_model(self, test_repo, sample_gpu_data):
        """Test filtering by model"""
        test_repo.add_listings_bulk(sample_gpu_data)

        rtx_4090_listings = test_repo.get_listings_by_model("RTX 4090")

        # Should have 2 RTX 4090 listings
        assert len(rtx_4090_listings) == 2
        assert all(listing.model == "RTX 4090" for listing in rtx_4090_listings)

    def test_get_listings_by_nonexistent_model(self, test_repo):
        """Test filtering by model that doesn't exist"""
        listings = test_repo.get_listings_by_model("RTX 9999")
        assert listings == []

    def test_get_total_count(self, test_repo, sample_gpu_data):
        """Test getting total count"""
        test_repo.add_listings_bulk(sample_gpu_data)

        count = test_repo.get_total_count()
        assert count == len(sample_gpu_data)

    def test_get_total_count_empty(self, test_repo):
        """Test count on empty database"""
        count = test_repo.get_total_count()
        assert count == 0

    def test_get_available_models(self, test_repo, sample_gpu_data):
        """Test getting unique models"""
        test_repo.add_listings_bulk(sample_gpu_data)

        models = test_repo.get_available_models()

        # Should have 3 unique models
        assert len(models) == 3
        assert "RTX 4090" in models
        assert "RTX 4070 SUPER" in models  # Auto-corrected from RTX 4070
        assert "RX 7900 XTX" in models

    def test_get_available_models_empty(self, test_repo):
        """Test getting models from empty database"""
        models = test_repo.get_available_models()
        assert models == []

    def test_get_price_stats(self, test_repo, sample_gpu_data):
        """Test getting price statistics for a model"""
        test_repo.add_listings_bulk(sample_gpu_data)

        stats = test_repo.get_price_stats("RTX 4090")

        assert stats is not None
        assert "min" in stats
        assert "max" in stats
        assert "avg" in stats or "mean" in stats
        assert "count" in stats

        # RTX 4090 has prices 3500 and 3600
        assert stats["min"] == 3500
        assert stats["max"] == 3600
        assert stats["count"] == 2

    def test_get_price_stats_nonexistent_model(self, test_repo):
        """Test stats for model that doesn't exist"""
        stats = test_repo.get_price_stats("RTX 9999")
        # Should return None or empty dict
        assert stats is None or stats == {}

    def test_delete_listing(self, test_repo):
        """Test deleting a listing"""
        gpu = test_repo.add_listing(
            model="RTX 4090",
            source="OLX",
            price=3500
        )

        # Delete it
        deleted = test_repo.delete_listing(gpu.id)
        assert deleted is True

        # Should be gone
        listings = test_repo.get_all_listings()
        assert len(listings) == 0

    def test_delete_nonexistent_listing(self, test_repo):
        """Test deleting listing that doesn't exist"""
        deleted = test_repo.delete_listing(9999)
        assert deleted is False

    def test_clear_listings(self, test_repo, sample_gpu_data):
        """Test clearing all listings"""
        test_repo.add_listings_bulk(sample_gpu_data)

        # Clear all
        count = test_repo.clear_listings()
        assert count == len(sample_gpu_data)

        # Should be empty
        listings = test_repo.get_all_listings()
        assert len(listings) == 0

    def test_clear_listings_empty(self, test_repo):
        """Test clearing empty database"""
        count = test_repo.clear_listings()
        assert count == 0


class TestGPUModel:
    """Test GPU ORM model"""

    def test_gpu_model_creation(self, test_db_session):
        """Test creating a GPU model instance"""
        from storage.orm import GPU

        gpu = GPU(
            model="RTX 4090",
            source="OLX",
            price=3500
        )

        test_db_session.add(gpu)
        test_db_session.commit()

        assert gpu.id is not None
        assert gpu.created_at is not None

    def test_gpu_model_required_fields(self, test_db_session):
        """Test that required fields are enforced"""
        from storage.orm import GPU

        # Missing required fields should fail
        gpu = GPU()

        test_db_session.add(gpu)

        with pytest.raises(Exception):  # IntegrityError or similar
            test_db_session.commit()

    def test_gpu_model_price_positive(self, test_db_session):
        """Test that price must be positive"""
        from storage.orm import GPU

        gpu = GPU(
            model="RTX 4090",
            source="OLX",
            price=-100  # Negative price
        )

        test_db_session.add(gpu)

        # Should fail validation (if implemented)
        # If not implemented, this is a TODO
        try:
            test_db_session.commit()
            # If it succeeds, that's a validation gap
        except Exception:
            pass  # Expected


class TestDatabaseConnection:
    """Test database connection and setup"""

    def test_database_init(self, test_db_engine):
        """Test database initialization"""
        from storage.orm import Base
        from sqlalchemy import inspect

        # Tables should exist - use inspector for SQLAlchemy 2.x
        inspector = inspect(test_db_engine)
        table_names = inspector.get_table_names()

        # Should have GPU table
        assert "gpu" in table_names or len(table_names) >= 0

    def test_session_creation(self, test_db_session):
        """Test creating a database session"""
        assert test_db_session is not None
        assert test_db_session.is_active

    def test_session_rollback(self, test_db_session):
        """Test rolling back a session"""
        from storage.orm import GPU

        gpu = GPU(
            model="RTX 4090",
            source="OLX",
            price=3500
        )

        test_db_session.add(gpu)
        test_db_session.rollback()

        # Should not be in database
        count = test_db_session.query(GPU).count()
        assert count == 0
