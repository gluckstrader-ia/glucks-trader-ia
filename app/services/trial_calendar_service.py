from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd


B3_CALENDAR_NAME = "BVMF"
B3_TIMEZONE = ZoneInfo("America/Sao_Paulo")
DEFAULT_TRIAL_SESSIONS = 5


def _normalize_to_utc(value: datetime | None) -> datetime:
    """
    Garante que a data/hora utilizada pelo cálculo esteja em UTC.

    - None -> horário atual em UTC
    - datetime sem timezone -> assume UTC
    - datetime com timezone -> converte para UTC
    """
    if value is None:
        return datetime.now(timezone.utc)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def calculate_trial_expiration(
    started_at: datetime | None = None,
    sessions: int = DEFAULT_TRIAL_SESSIONS,
) -> datetime:
    """
    Calcula a expiração do trial com base em pregões reais da B3.

    Regra:

    1. Trial padrão = 5 pregões completos.
    2. Sábados e domingos não contam.
    3. Dias em que o calendário BVMF não possui sessão não contam.
    4. Se o cadastro acontecer antes da abertura do pregão,
       o pregão daquele dia conta como o primeiro.
    5. Se o cadastro acontecer depois que o pregão já começou,
       o usuário continua tendo acesso imediatamente, mas aquele
       pregão parcial não consome um dos 5 pregões completos.
    6. A expiração ocorre no fechamento do último pregão contado.

    Retorna:
        datetime timezone-aware em UTC.
    """
    if sessions <= 0:
        raise ValueError("A quantidade de pregões deve ser maior que zero.")

    started_at_utc = _normalize_to_utc(started_at)
    started_at_brazil = started_at_utc.astimezone(B3_TIMEZONE)

    start_date = started_at_brazil.date()

    calendar = xcals.get_calendar(B3_CALENDAR_NAME)

    # Janela folgada para encontrar pelo menos 5 pregões,
    # mesmo havendo finais de semana e feriados.
    search_end_date = start_date + timedelta(days=45)

    available_sessions = calendar.sessions_in_range(
        start_date.isoformat(),
        search_end_date.isoformat(),
    )

    if len(available_sessions) == 0:
        raise RuntimeError(
            "Não foi possível localizar pregões da B3 para calcular o trial."
        )

    today_session = pd.Timestamp(start_date)

    should_skip_today = False

    if today_session in available_sessions:
        today_schedule = calendar.schedule.loc[today_session]

        market_open = today_schedule["open"].to_pydatetime()

        if market_open.tzinfo is None:
            market_open = market_open.replace(tzinfo=timezone.utc)
        else:
            market_open = market_open.astimezone(timezone.utc)

        # Se o pregão já começou, não consumimos esse dia como
        # um dos 5 pregões completos.
        if started_at_utc >= market_open:
            should_skip_today = True

    if should_skip_today:
        eligible_sessions = available_sessions[
            available_sessions > today_session
        ]
    else:
        eligible_sessions = available_sessions

    if len(eligible_sessions) < sessions:
        raise RuntimeError(
            "Quantidade insuficiente de pregões encontrada para calcular o trial."
        )

    counted_sessions = eligible_sessions[:sessions]
    last_session = counted_sessions[-1]

    last_schedule = calendar.schedule.loc[last_session]
    expiration = last_schedule["close"].to_pydatetime()

    if expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=timezone.utc)
    else:
        expiration = expiration.astimezone(timezone.utc)

    return expiration