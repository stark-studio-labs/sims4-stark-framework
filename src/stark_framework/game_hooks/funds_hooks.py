"""
Funds Hooks -- intercept Simoleon transactions via _Funds.add.

The game's _Funds class manages household money.  Every transaction --
career pay, object purchase, cheat codes, lot bills -- flows through
_Funds.add(amount, reason, sim).  Hooking it gives mods full visibility
into the household economy and the ability to modify or block transactions.

Targets:
    sims.funds._Funds.add

Events published:
    FundsChangedEvent  -- before _Funds.add commits (cancellable)

The event exposes the amount, reason enum, and (optionally) the Sim that
triggered the transaction.  Cancelling the event prevents the transaction.
Modifying event.amount changes the transaction value.
"""

from dataclasses import dataclass

from stark_framework.core.events import EventBus, Event
from stark_framework.core.injection import InjectionManager, InjectionError
from stark_framework.utils.logging import get_logger

log = get_logger("stark.hooks.funds")

MOD_ID = "stark_framework.game_hooks.funds"


# ── Events ──────────────────────────────────────────────────────────────


@dataclass
class FundsChangedEvent(Event):
    """Published before _Funds.add commits a Simoleon transaction.

    Cancel to prevent the transaction entirely.
    Modify ``amount`` to change the transaction value (e.g. double career pay).

    Attributes:
        household_id: The household whose funds are changing.
        amount: The Simoleon delta (positive = income, negative = expense).
        reason: The game's Funds reason enum value (career, purchase, cheat, etc.).
        sim_id: The Sim that triggered the transaction, or 0 if system-initiated.
    """
    household_id: int
    amount: int
    reason: object  # sims.funds.FundsReason enum
    sim_id: int = 0

    def __post_init__(self):
        super().__init__()


# ── Hook Registration ───────────────────────────────────────────────────

_hooks_active = False


def register_hooks():
    """Apply the _Funds.add hook.  Safe to call multiple times."""
    global _hooks_active
    if _hooks_active:
        return
    _hooks_active = True

    def _on_funds_add(original, self, amount, reason=None, sim=None, **kwargs):
        household = getattr(self, "_household", None)
        household_id = getattr(household, "id", 0) if household else 0
        sim_id = 0
        if sim is not None:
            sim_id = getattr(sim, "sim_id", 0) or getattr(
                getattr(sim, "sim_info", None), "sim_id", 0
            )

        event = FundsChangedEvent(
            household_id=household_id,
            amount=amount,
            reason=reason,
            sim_id=sim_id,
        )
        EventBus.publish(event, source_mod=MOD_ID)

        if event.cancelled:
            log.info(
                "Transaction blocked by event handler",
                household_id=household_id,
                amount=amount,
            )
            return

        # Allow subscribers to modify the amount
        return original(self, event.amount, reason, sim, **kwargs)

    try:
        InjectionManager.inject(
            "sims.funds._Funds", "add",
            _on_funds_add, kind="replace", mod_id=MOD_ID,
        )
        log.info("Hooked _Funds.add")
    except InjectionError as exc:
        log.debug("Skip funds hook (not in game)", reason=str(exc))


try:
    register_hooks()
except Exception as exc:
    log.debug("Funds hooks not registered (not in game environment)", reason=str(exc))
