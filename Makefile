.PHONY: test run agents analyze stop

test:
	uv run pytest

run:
	uv run python -m claim_trace run $(EXPERIMENT)

agents:
	uv run python -m claim_trace agents $(RUN)

analyze:
	uv run python -m claim_trace analyze $(RUN)

stop:
	uv run python -m claim_trace stop $(RUN)
