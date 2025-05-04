import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class IndexEventLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.events = self._load_events()

    def _load_events(self) -> Dict[str, List[Tuple[datetime, datetime]]]:
        df = pd.read_excel(self.file_path, sheet_name="Data")
        df = df[df['Trade Date'].notna()].copy()
        df['Announced'] = pd.to_datetime(df['Announced']).dt.tz_localize(None)
        df['Trade Date'] = pd.to_datetime(df['Trade Date']).dt.tz_localize(None)

        events_dict = {}
        for ticker, group in df.groupby('Ticker'):
            events_dict[ticker.split()[0]] = list(zip(
                group['Announced'].dt.to_pydatetime(),
                group['Trade Date'].dt.to_pydatetime()
            ))
        return events_dict

    def get_events_for_instrument(self, instrument_id: str) -> List[Tuple[datetime, datetime]]:
        return self.events.get(instrument_id, [])