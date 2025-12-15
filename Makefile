.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running ty"
	@uv run ty check
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry src

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules

.PHONY: type-check
type-check: ## Type check the code with ty
	@echo "🚀 Type checking code: Running ty"
	@uv run ty check

.PHONY: lint
lint: ## Lint the code with ruff
	@echo "🚀 Linting code: Running ruff"
	@uv run ruff check src

.PHONY: format
format: ## Format the code with ruff and black
	@echo "🚀 Formatting code: Running ruff"
	@uv run ruff check src --fix

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: screenshot
screenshot: ## Generate screenshots of the CLI for the README
	@echo "🚀 Generating screenshot of the terminal"
	@freeze --execute "uv run argus lookup --help" -o images/argus_help.png -c full
	@freeze --execute "uv run argus lookup 64.233.185.138" -o images/argus_lookup.png -c full
	@freeze --execute "uv run argus lookup -f sample/ips.txt" -o images/argus_lookup_file.png -c full

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
