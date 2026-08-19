from __future__ import annotations

from .models import AuthorityEnvelope


def naive_copy_authority(envelope: AuthorityEnvelope) -> tuple[str, ...]:
    """Deliberately unsafe falsifier.

    It copies upstream permitted actions without consulting relation survival.
    This exists only to prove the attenuation gate is load-bearing.
    """
    return envelope.permitted_actions
