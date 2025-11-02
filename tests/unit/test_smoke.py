"""
Smoke tests for Stichotrope.

These tests verify basic functionality and API availability.
They serve as a sanity check that the profiler can be imported and instantiated.
"""

import pytest


def test_import_stichotrope():
    """Test that stichotrope package can be imported."""
    import stichotrope
    assert stichotrope is not None


def test_import_version():
    """Test that version information is available."""
    from stichotrope import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)


class TestProfilerAPI:
    """Test profiler API availability (skipped if not implemented)."""
    
    def test_profiler_import(self):
        """Test that Profiler class can be imported."""
        from stichotrope import Profiler
        assert Profiler is not None
    
    def test_profiler_instantiation(self, get_profiler):
        """Test that Profiler can be instantiated."""
        profiler = get_profiler("SmokeTest")
        assert profiler is not None
    
    def test_profiler_decorator_exists(self, get_profiler):
        """Test that profiler.track decorator exists."""
        profiler = get_profiler("SmokeTest")
        assert hasattr(profiler, 'track')
        assert callable(profiler.track)
    
    def test_profiler_context_manager_exists(self, get_profiler):
        """Test that profiler.block context manager exists."""
        profiler = get_profiler("SmokeTest")
        assert hasattr(profiler, 'block')
        assert callable(profiler.block)
    
    def test_profiler_get_results_exists(self, get_profiler):
        """Test that profiler.get_results method exists."""
        profiler = get_profiler("SmokeTest")
        assert hasattr(profiler, 'get_results')
        assert callable(profiler.get_results)
    
    def test_basic_decorator_usage(self, get_profiler):
        """Test basic decorator usage."""
        profiler = get_profiler("SmokeTest")
        
        @profiler.track(0, "test_function")
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42
    
    def test_basic_context_manager_usage(self, get_profiler):
        """Test basic context manager usage."""
        profiler = get_profiler("SmokeTest")
        
        result = None
        with profiler.block(0, "test_block"):
            result = 42
        
        assert result == 42
    
    def test_get_results_returns_data(self, get_profiler):
        """Test that get_results returns profiling data."""
        profiler = get_profiler("SmokeTest")
        
        @profiler.track(0, "test_function")
        def test_func():
            return 42
        
        test_func()
        results = profiler.get_results()
        assert results is not None


def test_global_enable_disable_exists():
    """Test that global enable/disable functions exist (if implemented)."""
    try:
        from stichotrope import set_global_enabled, is_global_enabled
        assert callable(set_global_enabled)
        assert callable(is_global_enabled)
    except ImportError:
        pytest.skip("Global enable/disable not implemented yet")

