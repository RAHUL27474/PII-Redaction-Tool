import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from faker import Faker

logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(0)


FAKE_MAP = {
    "email": lambda: fake.safe_email(),
    "phone": lambda: fake.phone_number(),
    "ssn": lambda: fake.ssn(),
    "dob": lambda: fake.date_of_birth().strftime("%m/%d/%Y"),
    "ipv4": lambda: fake.ipv4(),
    "credit_card": lambda: fake.credit_card_number(),
    "company": lambda: fake.company(),
    "address": lambda: fake.address().replace("\n", ", "),
    "full_name": lambda: fake.name(),
}


class ReplacementManager:
    def __init__(self, mapping_path: str = "mapping.json") -> None:
        self.mapping_path = mapping_path
        self.mapping: Dict[str, str] = {}

    def load(self) -> None:
        self.mapping = self._load_from_file()
        logger.info("Loaded mapping with %d entries", len(self.mapping))

    def _load_from_file(self) -> Dict[str, str]:
        path = Path(self.mapping_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save(self) -> None:
        path = Path(self.mapping_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.mapping, f, indent=2, ensure_ascii=False)
        logger.info("Saved mapping with %d entries", len(self.mapping))

    def get_replacement(self, original: str, pii_type: Optional[str] = None) -> str:
        if original in self.mapping:
            return self.mapping[original]
        replacement = self._generate_fake(pii_type)
        self.mapping[original] = replacement
        return replacement

    def build_mapping(self, detections: Dict[str, List[str]]) -> Dict[str, str]:
        sorted_pii_types = [
            "email",
            "phone",
            "ssn",
            "dob",
            "ipv4",
            "credit_card",
            "company",
            "address",
            "full_name",
        ]
        for pii_type in sorted_pii_types:
            values = detections.get(pii_type, [])
            for value in values:
                self.get_replacement(value, pii_type)
        self.save()
        return self.mapping

    def _generate_fake(self, pii_type: Optional[str]) -> str:
        if pii_type is None:
            return fake.name()
        pii_type = pii_type.lower()
        generator = FAKE_MAP.get(pii_type)
        if generator is not None:
            return generator()
        return fake.name()