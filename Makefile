.PHONY: test run agents analyze compare stop

test:
	uv run pytest

run:
	uv run python -m claim_trace run $(EXPERIMENT)

agents:
	uv run python -m claim_trace agents $(RUN)

analyze:
	uv run python -m claim_trace analyze $(RUN)

compare:
	uv run python -m claim_trace compare $(BASE) $(RUN)

stop:
	uv run python -m claim_trace stop $(RUN)
