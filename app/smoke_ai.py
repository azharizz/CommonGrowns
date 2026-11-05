"""Opt-in live SDK smoke test. Sends synthetic data only; incurs provider usage."""
import logging

from commongrown.ai import AgentModel, STRING, obj


def main():
    logging.disable(logging.CRITICAL)
    try:
        model = AgentModel()
        result = model.generate('Synthetic smoke test. Return reply exactly SDK_OK.', obj({'reply': STRING}))
        assert result == {'reply': 'SDK_OK'}
        assert model.last_run['context_reads'] >= 1
        assert model.last_run['submissions'] >= 1 and model.last_run['accepted']
    except Exception as exc:
        print(f'FAIL: {type(exc).__name__}; check configured endpoint/model tool support and credentials.')
        return 1
    print('PASS: live Agents SDK run executed scoped context and validated submission tools.')
    print('Tool audit:', model.last_run)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
