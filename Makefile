.PHONY: lint format install-dev serve test coverage

install-dev:
	uv pip install -e ".[dev]" && uv pip install -e ".[test]"

format:
	uv run black --preview .

lint:
	uv run black --check .

serve:
	uv run server.py --reload

test:
	uv run pytest unittests/

langgraph-dev:
	uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.12 langgraph dev --allow-blocking

coverage:
	uv run pytest --cov=src unittests/ --cov-report=term-missing --cov-report=xml

