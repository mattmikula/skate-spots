"""Tests for GeoJSON Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models.skate_spot import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONFeatureProperties,
    GeoJSONPoint,
)


def test_geojson_point_valid():
    """Test creating a valid GeoJSON Point."""
    point = GeoJSONPoint(coordinates=(-122.4194, 37.7749))

    assert point.type == "Point"
    assert point.coordinates == (-122.4194, 37.7749)
    assert point.coordinates[0] == -122.4194  # longitude
    assert point.coordinates[1] == 37.7749  # latitude


def test_geojson_point_defaults():
    """Test that GeoJSON Point has correct default type."""
    point = GeoJSONPoint(coordinates=(0.0, 0.0))
    assert point.type == "Point"


def test_geojson_feature_properties_all_fields():
    """Test creating GeoJSON feature properties with all fields."""
    props = GeoJSONFeatureProperties(
        id="123",
        name="Test Spot",
        description="A test skate spot",
        spot_type="park",
        difficulty="intermediate",
        city="San Francisco",
        country="USA",
        address="123 Test St",
        is_public=True,
        requires_permission=False,
    )

    assert props.id == "123"
    assert props.name == "Test Spot"
    assert props.address == "123 Test St"


def test_geojson_feature_properties_without_address():
    """Test creating GeoJSON feature properties without optional address."""
    props = GeoJSONFeatureProperties(
        id="123",
        name="Test Spot",
        description="A test skate spot",
        spot_type="park",
        difficulty="intermediate",
        city="San Francisco",
        country="USA",
        is_public=True,
        requires_permission=False,
    )

    assert props.address is None


def test_geojson_feature_properties_missing_required_field():
    """Test that missing required fields raise validation errors."""
    with pytest.raises(ValidationError) as exc_info:
        GeoJSONFeatureProperties(
            id="123",
            name="Test Spot",
            # Missing description
            spot_type="park",
            difficulty="intermediate",
            city="San Francisco",
            country="USA",
            is_public=True,
            requires_permission=False,
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("description",)
    assert errors[0]["type"] == "missing"


def test_geojson_feature_complete():
    """Test creating a complete GeoJSON Feature."""
    feature = GeoJSONFeature(
        geometry=GeoJSONPoint(coordinates=(-122.4194, 37.7749)),
        properties=GeoJSONFeatureProperties(
            id="123",
            name="Test Spot",
            description="A test skate spot",
            spot_type="park",
            difficulty="intermediate",
            city="San Francisco",
            country="USA",
            is_public=True,
            requires_permission=False,
        ),
    )

    assert feature.type == "Feature"
    assert feature.geometry.type == "Point"
    assert feature.properties.name == "Test Spot"


def test_geojson_feature_defaults():
    """Test that GeoJSON Feature has correct default type."""
    feature = GeoJSONFeature(
        geometry=GeoJSONPoint(coordinates=(0.0, 0.0)),
        properties=GeoJSONFeatureProperties(
            id="123",
            name="Test",
            description="Test",
            spot_type="park",
            difficulty="beginner",
            city="City",
            country="Country",
            is_public=True,
            requires_permission=False,
        ),
    )

    assert feature.type == "Feature"


def test_geojson_feature_collection_empty():
    """Test creating an empty GeoJSON FeatureCollection."""
    collection = GeoJSONFeatureCollection(features=[])

    assert collection.type == "FeatureCollection"
    assert collection.features == []


def test_geojson_feature_collection_with_features():
    """Test creating a GeoJSON FeatureCollection with features."""
    feature1 = GeoJSONFeature(
        geometry=GeoJSONPoint(coordinates=(-122.4194, 37.7749)),
        properties=GeoJSONFeatureProperties(
            id="1",
            name="Spot 1",
            description="First spot",
            spot_type="park",
            difficulty="beginner",
            city="San Francisco",
            country="USA",
            is_public=True,
            requires_permission=False,
        ),
    )

    feature2 = GeoJSONFeature(
        geometry=GeoJSONPoint(coordinates=(-74.0060, 40.7128)),
        properties=GeoJSONFeatureProperties(
            id="2",
            name="Spot 2",
            description="Second spot",
            spot_type="street",
            difficulty="advanced",
            city="New York",
            country="USA",
            is_public=True,
            requires_permission=False,
        ),
    )

    collection = GeoJSONFeatureCollection(features=[feature1, feature2])

    assert collection.type == "FeatureCollection"
    assert len(collection.features) == 2
    assert collection.features[0].properties.name == "Spot 1"
    assert collection.features[1].properties.name == "Spot 2"


def test_geojson_feature_collection_defaults():
    """Test that GeoJSON FeatureCollection has correct default type."""
    collection = GeoJSONFeatureCollection(features=[])
    assert collection.type == "FeatureCollection"


def test_geojson_serialization():
    """Test that GeoJSON models serialize to correct JSON structure."""
    feature = GeoJSONFeature(
        geometry=GeoJSONPoint(coordinates=(-122.4194, 37.7749)),
        properties=GeoJSONFeatureProperties(
            id="123",
            name="Test Spot",
            description="Test description",
            spot_type="park",
            difficulty="intermediate",
            city="San Francisco",
            country="USA",
            address="123 Test St",
            is_public=True,
            requires_permission=False,
        ),
    )

    collection = GeoJSONFeatureCollection(features=[feature])

    # Serialize to dict
    data = collection.model_dump()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["type"] == "Feature"
    assert data["features"][0]["geometry"]["type"] == "Point"
    assert data["features"][0]["geometry"]["coordinates"] == (-122.4194, 37.7749)
    assert data["features"][0]["properties"]["name"] == "Test Spot"


def test_geojson_coordinates_as_list():
    """Test that coordinates can be provided as a list and converted to tuple."""
    # Pydantic will coerce list to tuple
    point = GeoJSONPoint(coordinates=[-122.4194, 37.7749])  # type: ignore

    assert point.coordinates == (-122.4194, 37.7749)
    assert isinstance(point.coordinates, tuple)
