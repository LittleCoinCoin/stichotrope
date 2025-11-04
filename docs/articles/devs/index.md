# Developer Documentation

Welcome to the Stichotrope developer documentation. This section provides information for contributors and developers working on Stichotrope.

## Development Status

**Current Phase**: Phase 1 - Infrastructure Foundation  
**Current Version**: v0.1.0-dev.1  
**Target Release**: v1.0.0

## Development Setup

### Prerequisites

- Python 3.9 or later
- Git
- pip package manager

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/LittleCoinCoin/stichotrope.git
cd stichotrope

# Install in development mode with all dependencies
pip install -e .[dev,docs]
```

### Development Dependencies

The `dev` optional dependencies include:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking
- `python-semantic-release` - Automated versioning

## Project Structure

```
stichotrope/
├── stichotrope/          # Main package
│   ├── __init__.py       # Package initialization and exports
│   ├── profiler.py       # Core Profiler class
│   ├── export.py         # Export functions (CSV, JSON)
│   ├── types.py          # Type definitions
│   └── timing.py         # Timing utilities
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── performance/      # Performance tests and benchmarks
├── docs/                 # Documentation source
├── __design__/           # Design documents and roadmap
├── __report__/           # Implementation reports
└── pyproject.toml        # Project configuration
```

## Development Workflow

### Git Workflow

Stichotrope follows a milestone-based branching strategy:

```
main (production releases only)
  └── dev (development integration branch)
      └── milestone/X.Y-description
          └── task/X.Y.Z-description
```

**Workflow:**

1. All work branches from `dev`
2. Create milestone branches for each roadmap milestone
3. Create task branches from milestone branches
4. Use conventional commits
5. Merge task → milestone → dev

### Conventional Commits

All commits must follow the conventional commit format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Test additions or updates
- `refactor`: Code refactoring
- `style`: Code formatting
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `perf`: Performance improvements

**Examples:**
```bash
feat(profiler): add per-track enable/disable functionality
fix(export): resolve CSV formatting issue with special characters
docs(api): update Profiler class documentation
test(performance): add overhead benchmark for large workloads
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=stichotrope --cov-report=html

# Run performance benchmarks
pytest tests/performance/test_overhead.py -v -s
```

### Test Organization

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Performance tests**: Measure overhead and performance characteristics

### Writing Tests

Follow these guidelines when writing tests:

1. Use descriptive test names: `test_profiler_tracks_function_execution_time`
2. Follow AAA pattern: Arrange, Act, Assert
3. Use fixtures from `conftest.py` for common setup
4. Add docstrings explaining test purpose
5. Test edge cases and error conditions

## Code Quality

### Formatting with Black

```bash
# Format all code
black stichotrope/ tests/

# Check formatting without changes
black --check stichotrope/ tests/
```

### Linting with Ruff

```bash
# Run linter
ruff check stichotrope/ tests/

# Auto-fix issues
ruff check --fix stichotrope/ tests/
```

### Type Checking with Mypy

```bash
# Run type checker
mypy stichotrope/
```

### Pre-Commit Checklist

Before committing:

- [ ] All tests pass
- [ ] Code formatted with black
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated if needed
- [ ] Conventional commit message

## Documentation

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install -e .[docs]

# Serve documentation with live reload
mkdocs serve

# Build static documentation
mkdocs build
```

The documentation will be available at `http://127.0.0.1:8000`.

### Documentation Guidelines

- Use Google-style docstrings for all public APIs
- Include examples in docstrings
- Keep documentation up-to-date with code changes
- Add new pages to `mkdocs.yml` navigation

## Contributing

### Contribution Process

1. Fork the repository
2. Create a feature branch from `dev`
3. Make your changes following code quality standards
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request to `dev`

### Pull Request Guidelines

- Use descriptive PR titles following conventional commit format
- Reference related issues
- Include test results
- Update CHANGELOG.md if applicable
- Ensure all CI checks pass

## Roadmap

See the [Product Roadmap](https://github.com/LittleCoinCoin/stichotrope/blob/dev/__design__/02-product_roadmap_v2.md) for detailed development plans.

### Current Milestone

**Milestone 1.4**: Documentation Infrastructure (In Progress)

### Upcoming Milestones

- **Phase 2**: Core Architecture & Features
  - Thread-safe architecture redesign
  - Configuration system (TOML)
  - Input validation and error handling
  - Repetition testing framework

- **Phase 3**: Release Preparation
  - Documentation completion
  - Final validation
  - v1.0.0 release

## Resources

- [GitHub Repository](https://github.com/LittleCoinCoin/stichotrope)
- [Issue Tracker](https://github.com/LittleCoinCoin/stichotrope/issues)
- [Product Roadmap](https://github.com/LittleCoinCoin/stichotrope/blob/dev/__design__/02-product_roadmap_v2.md)

