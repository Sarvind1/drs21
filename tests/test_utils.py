"""Tests for utility functions."""

import pytest
from src.utils import (
    format_status_tag,
    format_portal_status,
    generate_comparison_pairs
)

def test_format_status_tag():
    """Test status tag formatting."""
    reviewed = format_status_tag('reviewed')
    not_reviewed = format_status_tag('not-reviewed')
    
    assert 'status-reviewed' in reviewed
    assert 'Reviewed' in reviewed
    assert 'status-not-reviewed' in not_reviewed
    assert 'Not Reviewed' in not_reviewed

def test_format_portal_status():
    """Test portal status formatting."""
    status = format_portal_status('Pending', 'In progress')
    assert 'portal-status' in status
    assert 'Pending' in status
    assert 'title=\'In progress\'' in status

    status_no_reason = format_portal_status('Accepted')
    assert 'portal-status' in status_no_reason
    assert 'Accepted' in status_no_reason
    assert 'title' not in status_no_reason

def test_generate_comparison_pairs():
    """Test version comparison pair generation."""
    # Test with empty list
    assert generate_comparison_pairs([]) == []
    
    # Test with single version
    assert generate_comparison_pairs([1]) == []
    
    # Test with two versions
    assert generate_comparison_pairs([1, 2]) == [(1, 2)]
    
    # Test with three versions
    pairs = generate_comparison_pairs([1, 2, 3])
    assert len(pairs) == 3
    assert (1, 2) in pairs
    assert (2, 3) in pairs
    assert (1, 3) in pairs 