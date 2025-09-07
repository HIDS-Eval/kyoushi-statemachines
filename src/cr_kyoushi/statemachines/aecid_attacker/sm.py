from datetime import datetime, timedelta
from typing import Union

from cr_kyoushi.simulation import sm
from cr_kyoushi.simulation.states import FinalState, SequentialState
from cr_kyoushi.simulation.transitions import DelayedTransition
from cr_kyoushi.simulation.util import now

from . import actions, states
from .config import StatemachineConfig
from .context import ContextModel


__all__ = ["Statemachine", "StatemachineFactory"]


class Statemachine(sm.StartEndTimeStatemachine):
    """Minimal attacker state machine (webshell upload only)"""

    def setup_context(self):
        self.context = ContextModel()

    def destroy_context(self):
        # No reverse shell or VPN cleanup needed anymore
        super().destroy_context()


def _to_datetime(v: Union[timedelta, datetime], base: datetime) -> datetime:
    if isinstance(v, timedelta):
        return base + v
    return v


class StatemachineFactory(sm.StatemachineFactory):
    """Webshell-only attacker state machine"""

    @property
    def name(self) -> str:
        return "WebShellOnlyAttackerFactory"

    @property
    def config_class(self):
        return StatemachineConfig

    def build(self, config: StatemachineConfig):
        idle = config.idle
        start_time: datetime = _to_datetime(config.attack_start_time, now())

        # Transition: upload webshell
        upload_rce_shell = DelayedTransition(
            actions.UploadWebShell(
                config.wordpress.url,
                config.wordpress.rce_image,
                admin_ajax=config.wordpress.admin_ajax,
            ),
            name="upload_rce_shell",
            target="end",
            delay_after=idle.small,
        )

        # States
        initial = SequentialState(
            "initial",
            transition=upload_rce_shell,
        )

        end = FinalState("end")

        return Statemachine(
            initial_state=initial.name,
            states=[initial, end],
            start_time=start_time,
        )
